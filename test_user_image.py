from Backend.VisionService import get_vision_service

img_path = r"C:/Users/Krish/.gemini/antigravity/brain/ab8fc356-a7f6-49e4-8411-0c21327b4069/uploaded_image_0_1766421819241.png"

print(f"Analyzing user image: {img_path}")
vision = get_vision_service()
try:
    result = vision.analyze(img_path)
    print("\nRESULT:\n" + str(result))
except Exception as e:
    print(f"Error: {e}")
