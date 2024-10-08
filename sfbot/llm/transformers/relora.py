#
# Copyright 2016 The BigDL Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This file is adapted from
# https://github.com/OpenAccess-AI-Collective/axolotl/blob/main/src/axolotl/monkeypatch/relora.py
#
#    Copyright 2023 OpenAccess-AI-Collective axolotl Authors.

#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at

#        http://www.apache.org/licenses/LICENSE-2.0

#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
from typing import Optional
import torch
from transformers.trainer import Trainer
import glob
import json
import logging
import os.path
import shutil
from pathlib import Path
from typing import Dict, List, Sequence
import peft
import safetensors.torch as st
import torch
from huggingface_hub import snapshot_download
from torch.optim.lr_scheduler import LRScheduler
from torch.optim.optimizer import Optimizer
from transformers import (
    TrainerCallback,
    TrainerControl,
    TrainerState,
    TrainingArguments,
)
from transformers.trainer_utils import PREFIX_CHECKPOINT_DIR
import torch.distributed as dist
from ipex_llm.transformers.qlora import LoraLowBitLinear
from ipex_llm.transformers.low_bit_linear import FP4Params
from ipex_llm.utils.common import invalidInputError

LOG = logging.getLogger("ipex_llm.relora")


class ReLoRATrainer(Trainer):
    """
    Trainer subclass that uses the OneCycleLR scheduler
    """

    def __init__(self, *args, base_model="meta-llama/Llama-2-7b-hf",
                 relora_steps=150, relora_warmup_steps=10,
                 relora_cpu_offload=False,
                 resume_from_checkpoint=False, **kwargs):
        self.lr_scheduler = None
        self.relora_steps = relora_steps
        self.relora_warmup_steps = relora_warmup_steps
        self.relora_cpu_offload = relora_cpu_offload
        callbacks = kwargs.get("callbacks", [])
        if self.relora_steps > 0:
            callbacks.append(
                ReLoRACallback(relora_steps=relora_steps,
                               relora_cpu_offload=relora_cpu_offload,
                               base_model=base_model,
                               resume_from_checkpoint=resume_from_checkpoint))
        kwargs["callbacks"] = callbacks
        super().__init__(*args, **kwargs)

    def create_scheduler(
        self,
        num_training_steps: int,
        optimizer: Optional[torch.optim.Optimizer] = None,
    ):
        optimizer = self.optimizer if optimizer is None else optimizer
        lr_scheduler = super().create_scheduler(num_training_steps, optimizer)

        if self.relora_steps:
            warmup_steps = (
                self.relora_warmup_steps if self.relora_warmup_steps else 10
            )
            self.lr_scheduler = ReLoRAScheduler(
                optimizer,
                lr_scheduler,
                self.relora_steps,
                warmup_steps,
            )
        else:
            self.lr_scheduler = lr_scheduler

        return self.lr_scheduler


def is_distributed():
    """
    Check if distributed training is initialized.
    """
    return dist.is_available() and dist.is_initialized()


def is_main_process():
    """
    Check if the current process is the main process.
    If not in distributed mode, always return True.
    """
    if not is_distributed():
        return True
    return dist.get_rank() == 0


def reset_optimizer(optimizer: torch.optim.Optimizer):
    reset_steps = 0
    reset_keys = {}
    for group in optimizer.param_groups:
        for param in group["params"]:
            param_state = optimizer.state[param]
            for key in param_state:
                if "qmap" in key:
                    continue

                if key == "step" and isinstance(param_state[key], int):
                    param_state[key] = 0
                    reset_steps += 1
                else:
                    param_state[key] = torch.zeros_like(param_state[key])
                    if key not in reset_keys:
                        reset_keys[key] = 1
                    else:
                        reset_keys[key] += 1


class ReLoRACallback(TrainerCallback):
    """Callback to merge LoRA weights into the base model and save full-weight checkpoints"""

    def __init__(self, relora_steps=150, relora_cpu_offload=False,
                 base_model="meta-llama/Llama-2-7b-hf", resume_from_checkpoint=None):
        self.relora_steps = relora_steps
        self.cpu_offload = relora_cpu_offload
        self.last_full_model = base_model
        self.resume_from_checkpoint = resume_from_checkpoint

        if not os.path.exists(self.last_full_model):
            self.last_full_model = str(Path(snapshot_download(base_model)))

        invalidInputError(os.path.exists(self.last_full_model),
                          "for ReLORA base_model must be a local path")

        self.num_lora_restarts = 0
        self.need_full_save = False

    def on_train_begin(
        self,
        _args: TrainingArguments,
        _state: TrainerState,
        control: TrainerControl,
        model: peft.LoraModel,
        **_kwargs,
    ):
        if self.resume_from_checkpoint:
            weight_path = os.path.join(self.resume_from_checkpoint, "relora")
            if not os.path.exists(weight_path):
                LOG.warning(
                    "Resuming ReLoRA from checkpoint, but no full-weight save found"
                )
            else:
                LOG.info(f"Loading adjusted base weights from {weight_path}")
                load_weight_checkpoint(model, weight_path)
        return control

    def on_step_begin(
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        model: peft.LoraModel,
        optimizer: torch.optim.Optimizer,
        **_kwargs,
    ):
        if state.global_step > 0 and state.global_step % self.relora_steps == 0:
            checkpoint_folder = os.path.join(
                args.output_dir,
                f"{PREFIX_CHECKPOINT_DIR}-{state.global_step}",
                "relora",
            )

            with torch.no_grad():
                merge_and_save(
                    model,
                    self.last_full_model,
                    checkpoint_folder,
                    reinit=True,
                    actually_save=is_main_process(),
                    cpu_offload=self.cpu_offload,
                )
                reset_optimizer(optimizer)

            self.last_full_model = checkpoint_folder
            self.num_lora_restarts += 1
        return control

    def on_save(
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        model: peft.LoraModel,
        **_kwargs,
    ):
        checkpoint_folder = os.path.join(
            args.output_dir, f"{PREFIX_CHECKPOINT_DIR}-{state.global_step}", "relora"
        )
        if (
            state.global_step >= self.relora_steps
            and state.global_step % self.relora_steps != 0
        ):
            if is_main_process() and self.last_full_model != checkpoint_folder:
                # ensure the latest full parameter save is in the latest checkpoint
                # folder, so that automatic pruning of checkpoints does not remove it
                LOG.info(f"moving last full parameter save to {checkpoint_folder}")
                os.makedirs(checkpoint_folder, exist_ok=True)
                chunks = glob.glob(
                    f"{self.last_full_model}/model*.safetensors"
                ) + glob.glob(f"{self.last_full_model}/model*.index.json")
                for path in chunks:
                    new_path = os.path.abspath(shutil.move(path, checkpoint_folder))
                    try:
                        os.symlink(new_path, path)
                    except OSError:
                        # probably on windows without permission to symlink
                        pass

                self.last_full_model = checkpoint_folder

        return control

    def on_log(
        self,
        _args: TrainingArguments,
        _state: TrainerState,
        control: TrainerControl,
        logs: Dict[str, float],
        **_kwargs,
    ):
        logs["num_lora_restarts"] = self.num_lora_restarts
        return control

    def on_train_end(
        self,
        args: TrainingArguments,
        _state: TrainerState,
        control: TrainerControl,
        model: peft.LoraModel,
        **_kwargs,
    ):
        # perform final merge and save
        with torch.no_grad():
            merge_and_save(
                model,
                self.last_full_model,
                args.output_dir,
                reinit=False,
                actually_save=is_main_process(),
                cpu_offload=self.cpu_offload,
            )
        # no need to save if unquantized, as finetune.py will call merge_and_unload()
        return control


class ReLoRAScheduler(LRScheduler):
    """Wraps another scheduler to apply per-lora-restart learning rate warmups."""

    def __init__(
        self,
        optimizer: Optimizer,
        inner_schedule: LRScheduler,
        relora_steps: int,
        warmup_steps: int,
        min_lr_scale: float = 0.001,
    ) -> None:
        self.inner_schedule = inner_schedule
        self.relora_steps = relora_steps
        self.warmup_steps = warmup_steps
        self.min_lr_scale = min_lr_scale
        super().__init__(optimizer, inner_schedule.last_epoch, inner_schedule.verbose)

    def get_lr(self) -> float:
        self.inner_schedule.last_epoch = self.last_epoch

        original = self.inner_schedule.get_lr()
        step = self.last_epoch
        if step < self.relora_steps:
            scale = 1
        else:
            cycle_t = min(1.0, (step % self.relora_steps) / self.warmup_steps)
            scale = cycle_t * (1 - self.min_lr_scale) + self.min_lr_scale

        if isinstance(original, Sequence):
            return [lr * scale for lr in original]
        return original * scale


def sharded_paths(path: str, module_names: List[str]) -> Dict[str, str]:
    model_name = "model.safetensors"
    if not os.path.exists(str(Path(path) / model_name)) and not os.path.exists(
        str(Path(path) / f"{model_name}.index.json")
    ):
        model_name = "pytorch_model.bin"

    index_path = str(Path(path) / f"{model_name}.index.json")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data["weight_map"]
    return {(module_name + ".weight"): model_name for module_name in module_names}


def lora_delta_weight(layer: peft.tuners.lora.LoraLayer, device) -> torch.Tensor:
    if isinstance(layer, LoraLowBitLinear):
        adapter = layer.active_adapter
        return (
            peft.utils.transpose(
                layer.lora_B[adapter].weight.detach().to(device)
                @ layer.lora_A[adapter].weight.detach().to(device),
                getattr(layer, "fan_in_fan_out", False),
            )
            * layer.scaling[adapter]
        )

    return layer.get_delta_weight().to(device)


def find_lora_modules(model: peft.LoraModel) -> Dict[str, peft.tuners.lora.LoraLayer]:
    modules: Dict[str, peft.tuners.lora.LoraLayer] = {}

    key_list = [key for key, _ in model.model.named_modules() if "lora" not in key]
    for key in key_list:
        try:
            # pylint: disable=protected-access
            _parent, target, _target_name = peft.utils._get_submodules(model.model, key)
        except AttributeError:
            continue

        if isinstance(target, peft.tuners.lora.LoraLayer):
            modules[key] = target

    return modules


def update_weights(
    target: peft.tuners.lora.LoraLayer, new_weight: torch.Tensor, reinit: bool, device
):
    if reinit:
        for adapter_name in target.lora_A:
            target.reset_lora_parameters(adapter_name)
        for adapter_name in target.lora_embedding_A:
            target.reset_lora_parameters(adapter_name)

    if isinstance(target, LoraLowBitLinear):
        # LOG.info(f"new fp4params {device}, {target.weight.data}, {target.weight.data.device}")
        new_low_bit_params = FP4Params(new_weight.cpu(),
                                       qtype=target.qtype).to("cpu")
        new_low_bit_params = new_low_bit_params.to(device=device)
        target._parameters['weight'] = new_low_bit_params


def merge_and_save(
    model: peft.LoraModel,
    model_src: str,
    model_dst: str,
    reinit: bool = False,
    cpu_offload: bool = False,
    actually_save: bool = True,
):
    modules = find_lora_modules(model)

    os.makedirs(model_dst, exist_ok=True)
    shard_paths = sharded_paths(model_src, modules.keys())
    out_shard_paths = {}

    unique_shards = list(set(shard_paths.values()))
    for shard_path in unique_shards:
        out_tensors = {}
        if shard_path.endswith(".safetensors"):
            in_tensors = st.load_file(str(Path(model_src) / shard_path))
        else:
            in_tensors = torch.load(Path(model_src) / shard_path)
            if "state_dict" in in_tensors:
                in_tensors = in_tensors["state_dict"]

        LOG.info(f"load from {model_src}, {shard_path}")

        for module_name, target in modules.items():
            key = module_name + ".weight"
            if key not in shard_paths or shard_paths[key] != shard_path:
                continue

            orig_weight = in_tensors[key].float()
            old_dev = target.weight.data.device
            math_dev = "cpu" if cpu_offload else old_dev

            delta_weight = lora_delta_weight(target, math_dev).float()
            new_weight = orig_weight.to(math_dev) + delta_weight
            del delta_weight

            if actually_save:
                out_tensors[key] = new_weight.half().cpu()

            update_weights(target, new_weight, reinit=reinit, device=old_dev)

        if actually_save:
            out_shard_name = shard_path
            if out_shard_name.startswith("pytorch_model"):
                out_shard_name = (
                    out_shard_name.replace("pytorch_model", "model").rstrip(".bin")
                    + ".safetensors"
                )

            for module_name in in_tensors:
                if module_name not in out_tensors:
                    out_tensors[module_name] = in_tensors[module_name].half()
                out_shard_paths[module_name] = out_shard_name

            shard_fn = str(Path(model_dst) / out_shard_name)
            LOG.info(f"saving tensors to {shard_fn}")
            st.save_file(out_tensors, shard_fn, metadata={"format": "pt"})

        del in_tensors
        del out_tensors
        torch.xpu.empty_cache()

    if actually_save and len(unique_shards) > 1:
        with open(
            str(Path(model_dst, "model.safetensors.index.json")), "w", encoding="utf-8"
        ) as file:
            json.dump({"metadata": {}, "weight_map": out_shard_paths}, file)


def load_weight_checkpoint(model: peft.LoraModel, checkpoint_path: str):
    modules = find_lora_modules(model)
    shard_paths = sharded_paths(checkpoint_path, modules.keys())
    unique_shards = list(set(shard_paths.values()))

    for shard_path in unique_shards:
        tensors = st.load_file(os.path.join(checkpoint_path, shard_path))

        for module_name, target in modules.items():
            key = module_name + ".weight"
            if key not in shard_paths or shard_paths[key] != shard_path:
                continue

            new_weight = tensors[key]
            update_weights(
                target, new_weight, reinit=False, device=target.weight.device
            )
