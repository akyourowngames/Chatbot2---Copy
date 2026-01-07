# ==================== FILE SHARING API ENDPOINTS ====================
# Multi-User File Sharing - Revolutionary Collaboration Feature

from Backend.SharedFileManager import shared_file_manager
from Backend.DocumentReader import extract_text_from_file

@app.route('/api/v1/files/upload', methods=['POST'])
@rate_limit("default")
def upload_shared_file():
    """Upload a file for multi-user sharing"""
    try:
        user_id = request.form.get('user_id') or request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Empty filename"}), 400
        
        # Read file data
        file_data = file.read()
        filename = file.filename
        file_type = filename.split('.')[-1].lower() if '.' in filename else 'txt'
        
        # Extract text content
        extracted_text = extract_text_from_file(file_data, file_type)
        
        # Create metadata
        from Backend.SharedFileManager import FileMetadata
        metadata = FileMetadata(
            extracted_text=extracted_text,
            summary="",  # TODO: Generate AI summary
            keywords=[]  # TODO: Extract keywords
        )
        
        # Upload file
        file_id = shared_file_manager.upload_file(
            user_id=user_id,
            file_data=file_data,
            filename=filename,
            file_type=file_type,
            metadata=metadata
        )
        
        return jsonify({
            "success": True,
            "file_id": file_id,
            "filename": filename,
            "message": "File uploaded successfully"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/files/share', methods=['POST'])
@rate_limit("default")
def share_file():
    """Share a file with other users"""
    try:
        data = request.json
        user_id = data.get('user_id') or request.headers.get('X-User-ID')
        file_id = data.get('file_id')
        share_with = data.get('share_with', [])  # List of user IDs
        permission = data.get('permission', 'read')
        
        if not all([user_id, file_id, share_with]):
            return jsonify({"error": "user_id, file_id, and share_with required"}), 400
        
        success = shared_file_manager.share_file(
            file_id=file_id,
            user_id=user_id,
            share_with=share_with,
            permission=permission
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": f"File shared with {len(share_with)} users"
            }), 200
        else:
            return jsonify({"error": "Failed to share file"}), 403
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/files/shared', methods=['GET'])
@rate_limit("default")
def get_shared_files():
    """Get all files shared with user"""
    try:
        user_id = request.args.get('user_id') or request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        files = shared_file_manager.get_shared_files(user_id)
        
        return jsonify({
            "success": True,
            "files": files,
            "count": len(files)
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/files/<file_id>', methods=['GET'])
@rate_limit("default")
def get_file_content(file_id):
    """Get file content (with permission check)"""
    try:
        user_id = request.args.get('user_id') or request.headers.get('X-User-ID')
        if not user_id:
            return jsonify({"error": "user_id required"}), 400
        
        content = shared_file_manager.get_file_content(file_id, user_id)
        
        if content is None:
            return jsonify({"error": "File not found or access denied"}), 403
        
        return jsonify({
            "success": True,
            "file_id": file_id,
            "content": content
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/v1/files/<file_id>/revoke', methods=['POST'])
@rate_limit("default")
def revoke_file_access(file_id):
    """Revoke user access to file"""
    try:
        data = request.json
        user_id = data.get('user_id') or request.headers.get('X-User-ID')
        revoke_user = data.get('revoke_user')
        
        if not all([user_id, revoke_user]):
            return jsonify({"error": "user_id and revoke_user required"}), 400
        
        success = shared_file_manager.revoke_access(file_id, user_id, revoke_user)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Access revoked successfully"
            }), 200
        else:
            return jsonify({"error": "Failed to revoke access"}), 403
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


print("[File Sharing API] ✅ Endpoints registered")
print("  - POST /api/v1/files/upload")
print("  - POST /api/v1/files/share")
print("  - GET  /api/v1/files/shared")
print("  - GET  /api/v1/files/<file_id>")
print("  - POST /api/v1/files/<file_id>/revoke")
