# import os
# from transformers import AutoProcessor, AutoModelForCausalLM
# from PIL import Image

# # Lazy-loaded globals
# _processor = None
# _model = None

# def _load_florence():
#     global _processor, _model
#     if _model is None:
#         model_name = "microsoft/Florence-2-base"
#         _processor = AutoProcessor.from_pretrained(model_name)
#         _model = AutoModelForCausalLM.from_pretrained(model_name)
#     return _model, _processor

# def analyze_image(image_path: str) -> dict:
#     """Run Florence‑2 on the given image.
#     Returns a dict with 'description' and optional 'ocr' (both currently the same).
#     """
#     model, processor = _load_florence()
#     image = Image.open(image_path).convert("RGB")
#     inputs = processor(text="<CAPTION>", images=image, return_tensors="pt")
#     generated_ids = model.generate(**inputs, max_new_tokens=100)
#     generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
#     return {"description": generated_text.strip(), "ocr": generated_text.strip()}
