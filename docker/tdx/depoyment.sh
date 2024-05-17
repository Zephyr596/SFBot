script_dir=$(dirname $(readlink -f $0))
host_ip=$(hostname -I | awk '{print $1}')

# Define http_proxy, https_proxy, no_proxy variables and set their values to the host's variable values
export http_proxy=${http_proxy}
export https_proxy=${https_proxy}
export no_proxy=${no_proxy}

echo http_proxy:${http_proxy}
echo httsp_proxy:${https_proxy}
echo no_proxy:${no_proxy}

# Pull chatllm image from dockerhub
docker pull junruizh2021/trusted-bigdl-llm-serving-tdx:test

# Rename chatllm image
docker tag junruizh2021/trusted-bigdl-llm-serving-tdx:test registry.domain.local/trusted-bigdl-llm-serving-tdx:test

# Push chatllm image to local registry
docker push registry.domain.local/trusted-bigdl-llm-serving-tdx:test

# Create torchseringing pod using above image
cat > ./controller-auto.yaml << EOF
apiVersion: v1
kind: Pod
metadata:
  name: bigdl-fschat-a1234bd-controller
  labels:
    fastchat-appid: a1234bd
    fastchat-app-type: controller
spec:
  dnsPolicy: "ClusterFirst"
  runtimeClassName: kata-qemu-tdx
  containers:
  - name: fastchat-controller # fixed
    image: registry.domain.local/trusted-bigdl-llm-serving-tdx:test
    imagePullPolicy: Always
    env:
    - name: CONTROLLER_HOST # fixed
      valueFrom:
        fieldRef:
          fieldPath: status.podIP
    - name: CONTROLLER_PORT # fixed
      value: "21005"
    - name: BIGDL_TRANSFORMER_LOW_BIT
      value: "true"
    - name: ENABLE_PERF_OUTPUT
      value: "true"
    - name: API_HOST # fixed
      valueFrom:
        fieldRef:
          fieldPath: status.podIP
    - name: API_PORT # fixed
      value: "8000"
    - name: ENABLE_TLS
      value: "false"
    - name: TLS_KEYFILE
      value: /ppml/server.key
    - name: TLS_CERTFILE
      value: /ppml/server.crt
    ports:
      - containerPort: 21005
        name: con-port
      - containerPort: 8000
        name: api-port
    #resources:
    #  requests:
    #    memory: 16Gi
    #    cpu: 4
    #  limits:
    #    memory: 16Gi
    #    cpu: 4
    args: ["-m", "controller"]
    volumeMounts:
      - name: ppml-models
        mountPath: /ppml/models/
  restartPolicy: "Never"
  volumes:
  - name: ppml-models
    hostPath:
      path: $script_dir/models
---
# Service for the controller
apiVersion: v1
kind: Service
metadata:
  name: bigdl-a1234bd-fschat-controller-service
spec:
  type: NodePort
  selector:
    fastchat-appid: a1234bd
    fastchat-app-type: controller
  ports:
    - name: cont-port
      protocol: TCP
      port: 21005
      targetPort: 21005
    - name: api-port
      protocol: TCP
      port: 8000
      targetPort: 8000
EOF

cat > ./worker-auto.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bigdl-fschat-a1234bd-worker-deployment
spec:
  replicas: $2
  selector:
    matchLabels:
      fastchat: worker
  template:
    metadata:
      labels:
        fastchat: worker
    spec:
      runtimeClassName: kata-qemu-tdx
      dnsPolicy: "ClusterFirst"
      containers:
      - name: fastchat-worker # fixed
        image: registry.domain.local/trusted-bigdl-llm-serving-tdx:test
        imagePullPolicy: Always
        env:
        - name: CONTROLLER_HOST # fixed
          value: bigdl-a1234bd-fschat-controller-service
        - name: CONTROLLER_PORT # fixed
          value: "21005"
        - name: BIGDL_TRANSFORMER_LOW_BIT
          value: "true"
        - name: ENABLE_PERF_OUTPUT
          value: "true"
        - name: WORKER_HOST # fixed
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        - name: WORKER_PORT # fixed
          value: "21841"
        - name: MODEL_PATH
          value: "/ppml/models/$1"
        - name: OMP_NUM_THREADS
          value: "16"
        resources:
          requests:
            memory: 32Gi
            cpu: 16
          limits:
            memory: 32Gi
            cpu: 16
        args: ["-m", "worker"]
        volumeMounts:
          - name: ppml-models
            mountPath: /ppml/models/
      restartPolicy: "Always"
      volumes:
      - name: ppml-models
        hostPath:
          path: $script_dir/models # change this in other envs
EOF

kubectl apply -f ./controller-auto.yaml
kubectl apply -f ./worker-auto.yaml

kubectl wait --for=condition=Ready pod/bigdl-fschat-a1234bd-controller --timeouts=300s
kubectl wait --for=condition=Ready deployment/bigdl-fschat-a1234bd-worker-deployment --timeouts=300s

#!/bin/bash

keyword="bigdl-fschat-a1234bd-worker" 

pod_names=$(kubectl get pods --all-namespaces -o jsonpath='{range .items[*]}{.metadata.name}{"\n"}{end}' | grep "$keyword")

if [ -z "$pod_names" ]; then
    echo "Cannot find the pod matching with '$keyword' "
    exit 1
fi

for pod_name in $pod_names; do
    wait_time=0
    max_wait_time=300  

    while true; do
        log_output=$(kubectl logs "$pod_name" 2>/dev/null)  

        if echo "$log_output" | grep -q "Application startup complete"; then 
            echo "Pod '$pod_name' log obtain the 'Application startup complete'。"
            break
        fi

        if [ $wait_time -ge $max_wait_time ]; then 
            echo "timeout, Pod '$pod_name' don't include the keyword 'Application startup complete'。"
            break
        fi

        echo "Waiting 'Application startup complete'... in Pod '$pod_name' log "
        sleep 10  
        wait_time=$((wait_time + 10))
    done
done


controller_pod_ip=$(kubectl get pods bigdl-fschat-a1234bd-controller -o=jsonpath='{.status.podIP}')

kubectl exec -it bigdl-fschat-a1234bd-controller -- bash -c "python3 -m fastchat.serve.gradio_web_server --host 0.0.0.0 --port 8002 --controller-url http://$controller_pod_ip:21005"

kubectl delete -f ./controller-auto.py
kubectl delete -f ./worker-auto.py
