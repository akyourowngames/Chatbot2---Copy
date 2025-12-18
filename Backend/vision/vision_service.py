import os
from Backend.storage.file_service import download_file
from Backend.vision.florence_inference import analyze_image_comprehensive

def analyze_file(file_id: str) -> dict:
    temp_dir = os.path.join('temp_analysis')
    os.makedirs(temp_dir, exist_ok=True)

    local_path = download_file(file_id, temp_dir)

    result = analyze_image_comprehensive(local_path)

    try:
        os.remove(local_path)
    except Exception:
        pass

    return result
