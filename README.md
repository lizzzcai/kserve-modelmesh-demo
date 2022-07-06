# Custom Model

## Build Custom MLServer

```sh
cd mlserver
docker build -t lizzzcai/my-custom-mlserver:0.0.4 .
docker push lizzzcai/my-custom-mlserver:0.0.4
cd ..
```

## Run the Custom MLServer Locally

```sh
docker run -it --rm -p 8002:8002 -p 8001:8001 -v $(pwd)/mlserver/models:/models/_mlserver_models/text-classifier -e MLSERVER_MODEL_NAME=dummy-model-fixme -e MLSERVER_MODEL_REPOSITORY_ROOT=/models/_mlserver_models/ -e MLSERVER_MODELS_DIR=/models/_mlserver_models/ -e MLSERVER_LOAD_MODELS_AT_STARTUP=false  lizzzcai/my-custom-mlserver:0.0.4 mlserver start /models/
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
