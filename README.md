# Custom Model

Deploy custom model into KServe ModelMesh
## Build Custom MLServer

```sh
cd mlserver
docker build -t lizzzcai/my-custom-mlserver:0.0.5 .
docker push lizzzcai/my-custom-mlserver:0.0.5
cd ..
```

## Run the Custom MLServer Locally

```sh
docker run -it --rm -p 8001:8001 -p 8002:8002 \
  -v $(pwd)/models:/models/_mlserver_models/text-classifier \
  -e MLSERVER_MODEL_NAME=dummy-model-fixme \
  -e MLSERVER_MODELS_DIR=/models \
  -e MLSERVER_DEBUG=true \
  -e MLSERVER_LOAD_MODELS_AT_STARTUP=false \
  lizzzcai/my-custom-mlserver:0.0.5
```

## Inference - RESTful

```sh
# check repository
curl -i -X POST -H "Content-Type: application/json" "http://localhost:8002/v2/repository/index" -d "{}"

# load model
curl -i -X POST -H "Content-Type: application/json" "http://localhost:8002/v2/repository/models/text-classifier/load" -d "{}"

# unload model
curl -i -X POST -H "Content-Type: application/json" "http://localhost:8002/v2/repository/models/text-classifier/unload" -d "{}"

# infernce
curl -i -X POST -H "Content-Type: application/json" "http://localhost:8002/v2/models/text-classifier/infer" -d "{\"inputs\": [{ \"name\": \"text\", \"shape\": [2], \"datatype\": \"BYTES\", \"data\": [\"I loved this food, it was very good\", \"I don't loved this food, it was not good\"] }] }"
```

## Inference - gRPC

```sh
# check repository
grpcurl \
  -plaintext \
  -proto proto/mlserver/modelrepo/model_repository.proto \
  -d '{"repository_name": "", "ready": false}' \
  localhost:8001 \
  inference.model_repository.ModelRepositoryService/RepositoryIndex

# load modells
grpcurl \
  -plaintext \
  -proto proto/mlserver/modelrepo/model_repository.proto \
  -d '{"model_name": "text-classifier"}' \
  localhost:8001 \
  inference.model_repository.ModelRepositoryService/RepositoryModelLoad

# unload model
grpcurl \
  -plaintext \
  -proto proto/mlserver/modelrepo/model_repository.proto \
  -d '{"model_name": "text-classifier"}' \
  localhost:8001 \
  inference.model_repository.ModelRepositoryService/RepositoryModelUnload

# infernce
grpcurl \
  -plaintext \
  -proto proto/mlserver/dataplane/dataplane.proto \
  -d '{ "model_name": "text-classifier", "inputs": [{ "name": "text", "shape": [2], "datatype": "BYTES", "contents": { "bytes_contents": ["SSBsb3ZlZCB0aGlzIGZvb2QsIGl0IHdhcyB2ZXJ5IGdvb2Q=", "SSBkb24ndCBsb3ZlZCB0aGlzIGZvb2QsIGl0IHdhcyBub3QgZ29vZA=="] }}]}' \
  localhost:8001 \
  inference.GRPCInferenceService.ModelInfer
```

## Upload model

```sh
aws s3 cp --recursive ./models s3://<bucket>/path
aws s3 ls --recursive s3://<bucket>/path
```
> model must has a simple `model-settings.json`

## Create the storage secret

```sh
kubectl apply -f storage-secret.yaml 
```

## Deploy in ModelMesh

```sh
# create custom serving runtime
❯ kubectl create -f custom_servingruntime.yaml
servingruntime.serving.kserve.io/custom-mlserver-1.x created

# create predictor
❯ kubectl create -f custom_predictor.yaml
predictor.serving.kserve.io/custom-predictor created
```

Check the status

```
❯ kubectl get po
NAME                                                    READY   STATUS    RESTARTS   AGE
etcd                                                    1/1     Running   0          7h10m
minio                                                   1/1     Running   0          7h10m
modelmesh-controller-6c4cf67fd9-stk6s                   1/1     Running   0          23h
modelmesh-serving-custom-mlserver-1.x-fcdf49f9f-dt45f   4/4     Running   0          17m


❯ kubectl get predictor
NAME                          TYPE     AVAILABLE   ACTIVEMODEL   TARGETMODEL   TRANSITION   AGE
custom-predictor              custom   true        Loaded                      UpToDate     17m
```

## Send a request - RESTful

```sh
kubectl port-forward --address 0.0.0.0 service/modelmesh-serving 8008 -n modelmesh-serving

MODEL_NAME=custom-predictor
curl -i -X POST -H "Content-Type: application/json" "http://localhost:8008/v2/models/${MODEL_NAME}/infer" -d '{"inputs": [{ "name": "text", "shape": [2], "datatype": "BYTES", "data": ["SSBsb3ZlZCB0aGlzIGZvb2QsIGl0IHdhcyB2ZXJ5IGdvb2Q=", "SSBkb24ndCBsb3ZlZCB0aGlzIGZvb2QsIGl0IHdhcyBub3QgZ29vZA=="] }] }'

{"model_name":"custom-predictor__ksp-89efd40320","model_version":"v0.1.0","outputs":[{"name":"predictions","datatype":"BYTES","shape":[2],"parameters":{"content_type":{"ParameterChoice":{"StringParam":"str"}}},"data":["Y29tcGxpbWVudA==","Y29tcGxhaW50"]}]}% 
```

## Send a request - gRPC

```sh
kubectl port-forward --address 0.0.0.0 service/modelmesh-serving  8033 -n modelmesh-serving

grpcurl \
  -plaintext \
  -proto proto/mlserver/dataplane/dataplane.proto \
  -d '{ "model_name": "custom-predictor", "inputs": [{ "name": "text", "shape": [2], "datatype": "BYTES", "contents": { "bytes_contents": ["SSBsb3ZlZCB0aGlzIGZvb2QsIGl0IHdhcyB2ZXJ5IGdvb2Q=", "SSBkb24ndCBsb3ZlZCB0aGlzIGZvb2QsIGl0IHdhcyBub3QgZ29vZA=="] }}]}' \
  localhost:8033 \
  inference.GRPCInferenceService.ModelInfer

{
  "modelName": "custom-predictor__ksp-89efd40320",
  "modelVersion": "v0.1.0",
  "outputs": [
    {
      "name": "predictions",
      "datatype": "BYTES",
      "shape": [
        "2"
      ],
      "parameters": {
        "content_type": {
          "stringParam": "str"
        }
      },
      "contents": {
        "bytesContents": [
          "Y29tcGxpbWVudA==",
          "Y29tcGxhaW50"
        ]
      }
    }
  ]
}

```