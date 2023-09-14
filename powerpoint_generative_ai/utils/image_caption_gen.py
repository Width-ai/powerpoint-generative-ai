import torch
from PIL.Image import Image
from transformers import BlipProcessor, BlipForConditionalGeneration

class ImageCaptionGenerator:
    def __init__(self, model: str = "Salesforce/blip-image-captioning-base", device: str = "cuda"):
        self.device = torch.device(device)
        self.processor = BlipProcessor.from_pretrained(model)
        self.model = BlipForConditionalGeneration.from_pretrained(model).to(self.device)

    def infer(self, image: Image, prompt: str = ""):
        inputs = self.processor(image.convert("RGB"), prompt, return_tensors="pt")
        for k, v in inputs.items():
            inputs[k] = v.to(self.device)

        out = self.model.generate(**inputs)
        caption = self.processor.decode(out[0], skip_special_tokens=True)
        return caption.lstrip(prompt).strip()