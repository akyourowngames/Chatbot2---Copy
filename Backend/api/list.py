from flask import jsonify
from Backend.storage.file_service import list_files

def list_endpoint():
    try:
        files = list_files()
        return jsonify({"files": files}), 200
    except Exception as e:
        return jsonify({"error": f"I couldn’t retrieve the file list: {e}"}), 500
