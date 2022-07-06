# https://github.com/kserve/modelmesh-serving/blob/a77e2a9d6b494467a397d46119d794d15a090f5f/docs/runtimes/mlserver_custom.md
from os.path import exists
from joblib import load

from typing import Dict, List
from mlserver import MLModel
from mlserver.utils import get_model_uri
from mlserver.types import InferenceRequest, InferenceResponse, ResponseOutput, Parameters
WELLKNOWN_MODEL_FILENAMES = ["model.json", "model.dat", "classifier_pipeline.pkl"]

class MyCustomModel(MLModel):

  async def load(self) -> bool:
    print(self._settings)
    model_uri = await get_model_uri(self._settings, wellknown_filenames=WELLKNOWN_MODEL_FILENAMES)
    if exists(model_uri):
        print(f"Loading classifier pipeline from {model_uri}")
        with open(model_uri, "rb") as handle:
            self._model, self._classes = load(handle)
            print("Model loaded successfully")
    else:
        print(f"Model not exist in {model_uri}")
        # raise FileNotFoundError(model_uri)
        self.ready = False
        return self.ready

    self.ready = True
    return self.ready

  async def predict(self, payload: InferenceRequest) -> InferenceResponse:
    print(payload)
    input_data = self._extract_inputs(payload)
    predictions = self._model.predict(input_data["text"])
    predicted_labels = [self._classes[prediction].encode("UTF-8") for prediction in predictions]

    return InferenceResponse(
        id=payload.id,
        model_name=self.name,
        model_version=self.version,
        outputs=[
            ResponseOutput(
                name="predictions",
                shape=[len(predicted_labels)],
                datatype="BYTES",
                data=predicted_labels,
                parameters=Parameters(content_type="str")
            )
        ],
    )

  def _extract_inputs(self, payload: InferenceRequest) -> Dict[str, List[str]]:
      inputs = {}
      for inp in payload.inputs:
          if inp.name == "text":
            inputs[inp.name] = inp.data
            break
      return inputs