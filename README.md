# KServe ModelMesh Custom ServingRuntime Example

Deploy custom models into KServe ModelMesh via MLServer

## Download models from HuggingFace

```sh
python -m venv .venv
source .venv/bin/activate
pip install 'transformers[torch]'
python download_models.py
```

## Build Custom MLServer

```sh
cd mlserver
docker build -t lizzzcai/my-custom-mlserver:0.0.6 .
docker push lizzzcai/my-custom-mlserver:0.0.6
cd ..
```

## Run the Custom MLServer Locally

```sh
docker run -it --rm -p 8001:8001 -p 8002:8002 \
  -v $(pwd)/models:/models/_mlserver_models \
  -e MLSERVER_MODEL_NAME=dummy-model-fixme \
  -e MLSERVER_MODELS_DIR=/models \
  -e MLSERVER_DEBUG=true \
  -e MLSERVER_LOAD_MODELS_AT_STARTUP=false \
  lizzzcai/my-custom-mlserver:0.0.6
```

## Inference - RESTful

```sh
# check repository
curl -i -X POST -H "Content-Type: application/json" "http://localhost:8002/v2/repository/index" -d "{}"
# [{"name":"text-classifier","version":"v0.1.0","state":"UNAVAILABLE","reason":""},{"name":"text-translator","version":"v0.1.0","state":"UNAVAILABLE","reason":""}]%

# load models
curl -i -X POST -H "Content-Type: application/json" "http://localhost:8002/v2/repository/models/text-classifier/load" -d "{}"
curl -i -X POST -H "Content-Type: application/json" "http://localhost:8002/v2/repository/models/text-translator/load" -d "{}"

# check the repository again
curl -i -X POST -H "Content-Type: application/json" "http://localhost:8002/v2/repository/index" -d "{}"
# [{"name":"text-classifier","version":"v0.1.0","state":"READY","reason":""},{"name":"text-translator","version":"v0.1.0","state":"READY","reason":""}]

# inference
curl -i -X POST -H "Content-Type: application/json" "http://localhost:8002/v2/models/text-classifier/infer" -d "{\"inputs\": [{ \"name\": \"text\", \"shape\": [2], \"datatype\": \"BYTES\", \"parameters\": { \"content_type\": \"str\" }, \"data\": [\"I loved this food, it was very good\", \"I don't loved this food, it was not good\"] }] }"
# {"model_name":"text-classifier","model_version":"v0.1.0","id":"eace6fca-2f76-4ddc-ad0d-cf06d53e79be","parameters":{"content_type":null,"headers":null},"outputs":[{"name":"classifications","shape":[2],"datatype":"BYTES","parameters":{"content_type":"str","headers":null},"data":["compliment","complaint"]}]}%

curl -i -X POST -H "Content-Type: application/json" "http://localhost:8002/v2/models/text-translator/infer" -d "{\"inputs\": [{ \"name\": \"text\", \"shape\": [2], \"datatype\": \"BYTES\", \"parameters\": { \"content_type\": \"str\" }, \"data\": [\"My name is Sarah and I live in London\", \"My name is Wolfgang and I live in Berlin\"] }] }"
# {"model_name":"text-translator","model_version":"v0.1.0","id":"95619a36-83ba-4e4c-ad47-c3af05d2591c","parameters":{"content_type":null,"headers":null},"outputs":[{"name":"translations","shape":[2],"datatype":"BYTES","parameters":{"content_type":"str","headers":null},"data":["Mein Name ist Sarah und ich lebe in London","Mein Name ist Wolfgang und ich lebe in Berlin"]}]}%

# unload model
curl -i -X POST -H "Content-Type: application/json" "http://localhost:8002/v2/repository/models/text-classifier/unload" -d "{}"
curl -i -X POST -H "Content-Type: application/json" "http://localhost:8002/v2/repository/models/text-translator/unload" -d "{}"
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

# load models
grpcurl \
  -plaintext \
  -proto proto/mlserver/modelrepo/model_repository.proto \
  -d '{"model_name": "text-classifier"}' \
  localhost:8001 \
  inference.model_repository.ModelRepositoryService/RepositoryModelLoad

grpcurl \
  -plaintext \
  -proto proto/mlserver/modelrepo/model_repository.proto \
  -d '{"model_name": "text-translator"}' \
  localhost:8001 \
  inference.model_repository.ModelRepositoryService/RepositoryModelLoad

# check repository again
grpcurl \
  -plaintext \
  -proto proto/mlserver/modelrepo/model_repository.proto \
  -d '{"repository_name": "", "ready": false}' \
  localhost:8001 \
  inference.model_repository.ModelRepositoryService/RepositoryIndex
# {
#   "models": [
#     {
#       "name": "text-classifier",
#       "version": "v0.1.0",
#       "state": "READY"
#     },
#     {
#       "name": "text-translator",
#       "version": "v0.1.0",
#       "state": "READY"
#     }
#   ]
# }

# infernce
grpcurl \
  -plaintext \
  -proto proto/mlserver/dataplane/dataplane.proto \
  -d '{ "model_name": "text-classifier", "inputs": [{ "name": "text", "shape": [2], "datatype": "BYTES", "parameters": { "content_type": { "stringParam": "str" } }, "contents": { "bytes_contents": ["SSBsb3ZlZCB0aGlzIGZvb2QsIGl0IHdhcyB2ZXJ5IGdvb2Q=", "SSBkb24ndCBsb3ZlZCB0aGlzIGZvb2QsIGl0IHdhcyBub3QgZ29vZA=="] }}]}' \
  localhost:8001 \
  inference.GRPCInferenceService.ModelInfer

grpcurl \
  -plaintext \
  -proto proto/mlserver/dataplane/dataplane.proto \
  -d '{ "model_name": "text-translator", "inputs": [{ "name": "text", "shape": [2], "datatype": "BYTES", "parameters": { "content_type": { "stringParam": "str" } }, "contents": { "bytes_contents": ["TXkgbmFtZSBpcyBTYXJhaCBhbmQgSSBsaXZlIGluIExvbmRvbg==", "TXkgbmFtZSBpcyBXb2xmZ2FuZyBhbmQgSSBsaXZlIGluIEJlcmxpbg=="] }}]}' \
  localhost:8001 \
  inference.GRPCInferenceService.ModelInfer

# unload models
grpcurl \
  -plaintext \
  -proto proto/mlserver/modelrepo/model_repository.proto \
  -d '{"model_name": "text-classifier"}' \
  localhost:8001 \
  inference.model_repository.ModelRepositoryService/RepositoryModelUnload

grpcurl \
  -plaintext \
  -proto proto/mlserver/modelrepo/model_repository.proto \
  -d '{"model_name": "text-translator"}' \
  localhost:8001 \
  inference.model_repository.ModelRepositoryService/RepositoryModelUnload
```

## Upload model

```sh
aws s3 cp --recursive ./models s3://<bucket>/<path>
aws s3 ls --recursive s3://<bucket>/<path>/
```
> model must has a simple `model-settings.json`

## Create the storage secret

Refer to [this](https://github.com/kserve/modelmesh-serving/blob/main/docs/predictors/setup-storage.md) if you are using other object storage.

```sh
# update your s3 secret
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

## Reference

* https://github.com/kserve/modelmesh-serving
* https://mlserver.readthedocs.io/en/latest/examples/custom/README.html