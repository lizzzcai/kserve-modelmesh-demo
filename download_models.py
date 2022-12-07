import transformers

modelName = "translation_en_to_de"
output = "models/text-translator"

model = transformers.pipeline(modelName)
model.save_pretrained(output)