from flask import request, jsonify
from Backend.storage.file_service import upload_file
import os

def upload_endpoint():
    if 'file' not in request.files:
        return jsonify({"error": "I couldn’t find a file to upload. Please try again with a valid file."}), 400
    file = request.files['file']
    temp_dir = os.path.join('temp_uploads')
    os.makedirs(temp_dir, exist_ok=True)
    print(f"[UPLOAD] Received request for {file.filename}")
    temp_dir = os.path.join('temp_uploads')
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)
    try:
        file.save(temp_path)
        print(f"[UPLOAD] Saved to temp: {temp_path}")
        
        meta = upload_file(temp_path)
        print(f"[UPLOAD] Supabase success: {meta}")
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return jsonify({"status": "success", "file": meta, "analysis": {"analysis": f"File {meta['name']} uploaded successfully"}}), 201
    except Exception as e:
        print(f"[UPLOAD ERROR] {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"I couldn’t finish uploading this file: {e}"}), 500
