FROM python:3.9.13
# ENV LANG C.UTF-8

COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt

# The custom `MLModel` implementation should be on the Python search path
# instead of relying on the working directory of the image. If using a
# single-file module, this can be accomplished with:
COPY --chown=${USER} ./models.py /opt/models.py
ENV PYTHONPATH=/opt/
WORKDIR /opt


# environment variables to be compatible with ModelMesh Serving
#  these can also be set in the ServingRuntime, but this is recommended for
#  consistency when building and testing
ENV MLSERVER_MODELS_DIR=/models/_mlserver_models \
    MLSERVER_GRPC_PORT=8001 \
    MLSERVER_HTTP_PORT=8002 \
    MLSERVER_METRICS_PORT=8082 \
    MLSERVER_LOAD_MODELS_AT_STARTUP=false \
    MLSERVER_DEBUG=false \
    MLSERVER_MODEL_PARALLEL_WORKERS=0 \
    MLSERVER_MODEL_NAME=dummy-model

# With this setting, the implementation field is not required in the model
# settings which eases integration by allowing the built-in adapter to generate
# a basic model settings file
ENV MLSERVER_MODEL_IMPLEMENTATION=models.MyCustomModel

CMD mlserver start $MLSERVER_MODELS_DIR