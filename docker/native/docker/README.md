## Build/Use IPEX-LLM-serving cpu image

### Build Image
```bash
docker build \
  --build-arg http_proxy=.. \
  --build-arg https_proxy=.. \
  --build-arg no_proxy=.. \
  --rm --no-cache -t romanticoseu/sfbot:1.0 .
```

### Use the image for doing cpu serving

```bash
#/bin/bash
export DOCKER_IMAGE=romanticoseu/sfbot:1.0
controller_host=localhost
controller_port=23000
api_host=localhost
api_port=8000
sudo docker run -itd \
        --net=host \
	--privileged \
        --cpuset-cpus="0-47" \
        --cpuset-mems="0" \
        --memory="64G" \
        --name=serving-cpu-controller \
        --shm-size="16g" \
	-e ENABLE_PERF_OUTPUT="true" \
        -e CONTROLLER_HOST=$controller_host \
        -e CONTROLLER_PORT=$controller_port \
        -e API_HOST=$api_host \
        -e API_PORT=$api_port \
        $DOCKER_IMAGE -m controller
```
To start a worker container:
```bash
#/bin/bash
export DOCKER_IMAGE=romanticoseu/sfbot:1.0
export MODEL_PATH=YOUR_MODEL_PATH
controller_host=localhost
controller_port=23000
worker_host=localhost
worker_port=23001
sudo docker run -itd \
        --net=host \
	--privileged \
        --cpuset-cpus="0-47" \
        --cpuset-mems="0" \
        --memory="64G" \
        --name="serving-cpu-worker" \
        --shm-size="16g" \
	-e ENABLE_PERF_OUTPUT="true" \
        -e CONTROLLER_HOST=$controller_host \
        -e CONTROLLER_PORT=$controller_port \
        -e WORKER_HOST=$worker_host \
        -e WORKER_PORT=$worker_port \
        -e OMP_NUM_THREADS=48 \
        -e MODEL_PATH=/llm/models/Llama-2-7b-chat-hf \
	-v $MODEL_PATH:/llm/models/ \
        $DOCKER_IMAGE -m worker
```

Then you can use `curl` for testing, an example could be:
```bash
curl -X POST -H "Content-Type: application/json" -d '{
    "model": "YOUR_MODEL_NAME",
    "prompt": "Once upon a time, there existed a little girl who liked to have adventures. She wanted to go to places and meet new people, and have fun",
    "n": 1,
    "best_of": 1,
    "use_beam_search": false,
    "stream": false
}' http://localhost:8000/v1/completions
```
