from flask import jsonify
from Backend.storage.file_service import delete_file

def delete_endpoint(file_id):
    try:
        delete_file(file_id)
        return jsonify({"success": True, "message": "File removed successfully."}), 200
    except Exception as e:
        return jsonify({"error": f"I couldn’t delete the file: {e}"}), 500
