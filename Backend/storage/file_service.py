import os
import uuid
from pathlib import Path
from .supabase_client import get_bucket

def upload_file(file_path: str) -> dict:
    """Upload a local file to Supabase storage.
    Returns metadata dict with id, name, size, and public URL.
    """
    bucket = get_bucket()
    file_path_obj = Path(file_path)
    if not file_path_obj.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    # Use a UUID for the storage key to avoid collisions
    storage_key = f"{uuid.uuid4().hex}_{file_path_obj.name}"
    with open(file_path_obj, "rb") as f:
        data = f.read()
    res = bucket.upload(storage_key, data)
    # Supabase v2 upload returns an object on success, raises error on failure.
    # If we are here, it likely succeeded.
    # Check if it has 'error' attribute just in case.
    if hasattr(res, 'error') and res.error:
         raise RuntimeError(f"Supabase upload error: {res.error}")


    # Build a public URL (Supabase provides a public URL method)
    public_url = bucket.get_public_url(storage_key)
    return {
        "id": storage_key,
        "name": file_path_obj.name,
        "size": file_path_obj.stat().st_size,
        "url": public_url,
    }


def list_files() -> list:
    """Return a list of file metadata stored in the bucket."""
    bucket = get_bucket()
    res = bucket.list()
    # v2 returns a list of objects or dicts
    files = []
    
    # Handle if res is a list (v2 typical behavior)
    data_list = res if isinstance(res, list) else res.get('data', [])
    
    for item in data_list:
        # Item might be dict or object
        if isinstance(item, dict):
             files.append({
                "id": item["name"],
                "name": Path(item["name"]).name,
                "size_bytes": item.get("metadata", {}).get("size", 0),
                "uploaded_at": item.get("created_at"),
                "url": bucket.get_public_url(item["name"]),
            })
        else:
            # Assume object with attributes
             files.append({
                "id": item.name,
                "name": Path(item.name).name,
                "size_bytes": item.metadata.get("size", 0) if hasattr(item, 'metadata') else 0,
                "uploaded_at": item.created_at if hasattr(item, 'created_at') else None,
                "url": bucket.get_public_url(item.name),
            })
    return files


def download_file(file_id: str, destination: str) -> str:
    """Download a file from Supabase to a local destination.
    Returns the absolute path of the saved file.
    """
    bucket = get_bucket()
    dest_path = Path(destination)
    if dest_path.is_dir():
        # Preserve original filename from the storage key
        filename = Path(file_id).name
        dest_path = dest_path / filename
    data = bucket.download(file_id)
    # v2 returns bytes directly
    if isinstance(data, bytes):
        content = data
    elif hasattr(data, 'text'): # Requests-like object
        content = data.content
    else:
        # Fallback for old behavior key
        if hasattr(data, 'get') and data.get('error'):
             raise RuntimeError(f"Supabase download error: {data['error']}")
        content = data
        
    with open(dest_path, "wb") as f:
        f.write(content)
    return str(dest_path)

def get_file_bytes(file_id: str) -> bytes:
    """Get file content as bytes from Supabase."""
    bucket = get_bucket()
    data = bucket.download(file_id)
    if isinstance(data, bytes):
        return data
    elif hasattr(data, 'content'):
        return data.content
    return data

def delete_file(file_id: str) -> bool:
    """Delete a file from Supabase storage. Returns True on success."""
    bucket = get_bucket()
    # remove takes a list of paths
    res = bucket.remove([file_id])
    # Check for error in response if applicable
    if isinstance(res, dict) and res.get('error'):
        raise RuntimeError(f"Supabase delete error: {res['error']}")
    return True
