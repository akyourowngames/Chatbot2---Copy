from flask import request, jsonify, send_file
from Backend.storage.file_service import get_file_bytes
import io
from pathlib import Path

def download_endpoint(file_id):
    try:
        # Get bytes from Supabase
        file_data = get_file_bytes(file_id)
        
        # Determine filename from the ID (which includes UUID prefix)
        # Format: uuid_filename.ext
        filename = Path(file_id).name
        # Optionally remove the UUID prefix for nicer download name if we split by underscore
        # But keeping it unique is also fine. Let's send the full name.
        
        return send_file(
            io.BytesIO(file_data),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"error": f"I couldn’t download the file: {e}"}), 500
