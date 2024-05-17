## Deployment ipex-llm serving service in K8S environment

## Image

To deploy serving cpu in Kubernetes environment, please use this image: `romanticoseu/sfbot:1.0`

## Before deployment

### Kubernetes config

We recommend to setup your kubernetes cluster before deployment.  Mostly importantly, please set `cpu-management-policy` to `static` by using this [tutorial](https://kubernetes.io/docs/tasks/administer-cluster/cpu-management-policies/).  Also, it would be great to also set the `topology management policy` to `single-numa-node`.

### Machine config

Set hyper-threading to off, ensure that only physical cores are used during deployment.

## Deployment

### Reminder on `OMP_NUM_THREADS`

The entrypoint of the image will try to set `OMP_NUM_THREADS` to the correct number by reading configs from the `runtime`.  However, this only happens correctly if the `core-binding` feature is enabled.  If not, please set environment variable `OMP_NUM_THREADS` manually in the yaml file.

