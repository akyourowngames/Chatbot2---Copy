from flask import request, jsonify
from Backend.vision.vision_service import analyze_file

def analyze_endpoint(file_id):
    """API endpoint to analyze a stored file using Florence‑2.
    Returns a friendly description and OCR snippet.
    """
    try:
        result = analyze_file(file_id)
        # Friendly response
        response = {
            "success": True,
            "description": result.get('description', ''),
            "ocr": result.get('ocr', '')
        }
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": f"I couldn’t analyze that file: {e}"}), 500
