# https://github.com/kserve/modelmesh-serving/blob/a77e2a9d6b494467a397d46119d794d15a090f5f/docs/runtimes/mlserver_custom.md
import os
from os.path import exists
from typing import Dict, List
from mlserver import MLModel
from mlserver.utils import get_model_uri
from mlserver.types import InferenceRequest, InferenceResponse, ResponseOutput, Parameters
from mlserver.codecs import DecodedParameterName
from joblib import load
from transformers import pipeline

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_to_exclude = {
    "parameters": {DecodedParameterName, "headers"},
    'inputs': {"__all__": {"parameters": {DecodedParameterName, "headers"}}}
}

WELLKNOWN_MODEL_FILENAMES = ["classifier_pipeline.pkl", "pytorch_model.bin"]

class MyClassifierModel(MLModel):

  async def load(self) -> bool:
    model_uri = await get_model_uri(self._settings, wellknown_filenames=WELLKNOWN_MODEL_FILENAMES)
    if exists(model_uri):
        logger.info(f"Loading classifier pipeline from {model_uri}")
        with open(model_uri, "rb") as handle:
            self._model, self._classes = load(handle)
            logger.info("Model loaded successfully")
    else:
        logger.info(f"Model not exist in {model_uri}")
        # raise FileNotFoundError(model_uri)
        self.ready = False
        return self.ready

    self.ready = True
    return self.ready

  async def predict(self, payload: InferenceRequest) -> InferenceResponse:
    input_data = self._extract_inputs(payload)
    predictions = self._model.predict(input_data["text"])
    predicted_labels = [self._classes[prediction].encode("UTF-8") for prediction in predictions]

    return InferenceResponse(
        id=payload.id,
        model_name=self.name,
        model_version=self.version,
        outputs=[
            ResponseOutput(
                name="classifications",
                shape=[len(predicted_labels)],
                datatype="BYTES",
                data=predicted_labels,
                parameters=Parameters(content_type="str")
            )
        ],
    )

  def _extract_inputs(self, payload: InferenceRequest) -> Dict[str, List[str]]:
      inputs = {}
      for request_input in payload.inputs:
          if request_input.name == "text":
            inputs[request_input.name] = self.decode(request_input)
            break
      return inputs


class MyTranslatorModel(MLModel):

  async def load(self) -> bool:
    model_uri = await get_model_uri(self._settings, wellknown_filenames=WELLKNOWN_MODEL_FILENAMES)
    if exists(model_uri):
        model_dir = os.path.dirname(model_uri)
        logger.info(f"Loading translator pipeline from {model_uri}")
        self._model = pipeline("translation_en_to_de", model=model_dir)
        logger.info("Pipeline loaded successfully")
    else:
        logger.info(f"Model not exist in {model_uri}")
        self.ready = False
        return self.ready

    self.ready = True
    return self.ready

  async def predict(self, payload: InferenceRequest) -> InferenceResponse:
    input = self._extract_inputs(payload)
    output = self._model(input["text"])
    result = [o['translation_text'].encode("UTF-8") for o in output]
    return InferenceResponse(
        id=payload.id,
        model_name=self.name,
        model_version=self.version,
        outputs=[
            ResponseOutput(
                name="translations",
                shape=[len(result)],
                datatype="BYTES",
                data=result,
                parameters=Parameters(content_type="str")
            )
        ],
    )

  def _extract_inputs(self, payload: InferenceRequest) -> Dict[str, List[str]]:
      inputs = {}
      for request_input in payload.inputs:
          if request_input.name == "text":
            as_dict = request_input.dict(exclude=_to_exclude)  # type: ignore
            inputs[request_input.name] = [x for x in as_dict['data']]
            # inputs[request_input.name] = self.decode(request_input)
            break
      return inputs