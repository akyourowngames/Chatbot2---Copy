from flask import request, jsonify
import os
import uuid
from Backend.vision.florence_inference import analyze_image_comprehensive
from Backend.api.helpers import require_api_key

def analyze_image_endpoint():
    """
    Endpoint to analyze an image locally using Florence-2.
    Accepts 'file' in multipart/form-data.
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400

        # Save temporarily
        temp_dir = os.path.join(os.getcwd(), 'temp_vision')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Use simple trusted characters for filename
        ext = os.path.splitext(file.filename)[1]
        temp_filename = f"vision_{uuid.uuid4().hex}{ext}"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        # Save
        file.save(temp_path)
        
        try:
            # Run Analysis
            result = analyze_image_comprehensive(temp_path)
            
            return jsonify({
                "success": True,
                "analysis": result
            })
            
        finally:
            # cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
