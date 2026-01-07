"""
Kai Local Agent - File Manager Executor
========================================
Sandboxed file operations within approved directories only.

Allowed directories:
- Documents/Kai
- Desktop/Kai

Safety features:
- Never operates outside sandbox
- Tracks created files in manifest
- Only deletes files Kai created
"""

import os
import sys
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base import BaseExecutor

import logging
logger = logging.getLogger("KaiLocalAgent")


class FileManagerExecutor(BaseExecutor):
    """Sandboxed file manager for Kai-controlled directories."""
    
    # Allowed root directories (sandbox)
    ALLOWED_ROOTS = []
    
    # Manifest file for tracking Kai-created files
    MANIFEST_PATH = None
    
    def __init__(self):
        """Initialize with platform-specific paths."""
        home = Path.home()
        
        # Set up allowed directories
        self.ALLOWED_ROOTS = [
            home / "Documents" / "Kai",
            home / "Desktop" / "Kai"
        ]
        
        # Manifest for tracking created files
        kai_config = home / ".kai"
        kai_config.mkdir(exist_ok=True)
        self.MANIFEST_PATH = kai_config / "file_manifest.json"
        
        # Ensure sandbox directories exist
        for root in self.ALLOWED_ROOTS:
            root.mkdir(parents=True, exist_ok=True)
        
        # Load or create manifest
        self._load_manifest()
    
    def _load_manifest(self) -> Dict:
        """Load the file manifest."""
        if self.MANIFEST_PATH.exists():
            try:
                with open(self.MANIFEST_PATH, 'r') as f:
                    self.manifest = json.load(f)
            except:
                self.manifest = {"created_files": [], "created_folders": []}
        else:
            self.manifest = {"created_files": [], "created_folders": []}
        return self.manifest
    
    def _save_manifest(self):
        """Save the file manifest."""
        with open(self.MANIFEST_PATH, 'w') as f:
            json.dump(self.manifest, f, indent=2)
    
    def _track_file(self, path: Path, file_type: str = "file"):
        """Track a created file/folder in manifest."""
        entry = {
            "path": str(path),
            "created_at": datetime.now().isoformat(),
            "type": file_type
        }
        key = "created_files" if file_type == "file" else "created_folders"
        self.manifest[key].append(entry)
        self._save_manifest()
    
    def _is_kai_created(self, path: Path) -> bool:
        """Check if a file was created by Kai."""
        path_str = str(path)
        for entry in self.manifest.get("created_files", []):
            if entry["path"] == path_str:
                return True
        for entry in self.manifest.get("created_folders", []):
            if entry["path"] == path_str:
                return True
        return False
    
    def _is_in_sandbox(self, path: Path) -> bool:
        """Check if path is within allowed directories."""
        path = path.resolve()
        for root in self.ALLOWED_ROOTS:
            try:
                path.relative_to(root.resolve())
                return True
            except ValueError:
                continue
        return False
    
    def _get_default_root(self) -> Path:
        """Get the default root directory (Documents/Kai)."""
        return self.ALLOWED_ROOTS[0]
    
    def _resolve_path(self, name: str, folder: Optional[str] = None) -> Path:
        """Resolve a file/folder name to a full path within sandbox."""
        root = self._get_default_root()
        
        if folder:
            # Check if folder is a relative path within sandbox
            folder_path = root / folder
            if self._is_in_sandbox(folder_path):
                root = folder_path
        
        return root / name
    
    @property
    def command_name(self) -> str:
        return "file_manager"
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a file manager action."""
        action = params.get("action", "").lower()
        
        actions = {
            "create_folder": self._create_folder,
            "save_file": self._save_file,
            "list_files": self._list_files,
            "rename_file": self._rename_file,
            "move_file": self._move_file,
            "delete_file": self._delete_file,
            "open_folder": self._open_folder,
        }
        
        if action not in actions:
            return {"status": "error", "message": f"Unknown action '{action}'"}
        
        return actions[action](params)
    
    def _create_folder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a folder within the sandbox."""
        name = params.get("name", "").strip()
        parent = params.get("parent")
        
        if not name:
            return {"status": "error", "message": "Folder name required"}
        
        # Sanitize name
        name = self._sanitize_name(name)
        
        folder_path = self._resolve_path(name, parent)
        
        if not self._is_in_sandbox(folder_path):
            return {"status": "error", "message": "Cannot create folder outside Kai directories"}
        
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            self._track_file(folder_path, "folder")
            logger.info(f"[FILE_MANAGER] Created folder: {folder_path}")
            return {
                "status": "success",
                "message": f"📁 Created folder '{name}'",
                "data": {"path": str(folder_path)}
            }
        except Exception as e:
            logger.error(f"[FILE_MANAGER] Create folder error: {e}")
            return {"status": "error", "message": f"Failed to create folder: {str(e)}"}
    
    def _save_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Save content to a file."""
        name = params.get("name", "").strip()
        content = params.get("content", "")
        folder = params.get("folder")
        
        if not content:
            return {"status": "error", "message": "No content to save"}
        
        # Generate name if not provided
        if not name:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            name = f"kai_note_{timestamp}.txt"
        
        # Ensure .txt extension
        if not name.endswith('.txt'):
            name += '.txt'
        
        name = self._sanitize_name(name)
        file_path = self._resolve_path(name, folder)
        
        if not self._is_in_sandbox(file_path):
            return {"status": "error", "message": "Cannot save file outside Kai directories"}
        
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self._track_file(file_path, "file")
            logger.info(f"[FILE_MANAGER] Saved file: {file_path}")
            return {
                "status": "success",
                "message": f"💾 Saved as '{name}'",
                "data": {"path": str(file_path), "name": name}
            }
        except Exception as e:
            logger.error(f"[FILE_MANAGER] Save file error: {e}")
            return {"status": "error", "message": f"Failed to save file: {str(e)}"}
    
    def _list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List files and folders in the sandbox."""
        folder = params.get("folder")
        
        root = self._get_default_root()
        if folder:
            root = self._resolve_path(folder)
        
        if not self._is_in_sandbox(root):
            return {"status": "error", "message": "Cannot list files outside Kai directories"}
        
        if not root.exists():
            return {"status": "error", "message": f"Folder '{folder}' does not exist"}
        
        try:
            items = []
            for item in root.iterdir():
                item_type = "folder" if item.is_dir() else "file"
                size = item.stat().st_size if item.is_file() else None
                items.append({
                    "name": item.name,
                    "type": item_type,
                    "size": size,
                    "kai_created": self._is_kai_created(item)
                })
            
            # Sort: folders first, then files
            items.sort(key=lambda x: (x["type"] != "folder", x["name"].lower()))
            
            logger.info(f"[FILE_MANAGER] Listed {len(items)} items in {root}")
            return {
                "status": "success",
                "message": f"📂 Found {len(items)} items",
                "data": {"items": items, "path": str(root)}
            }
        except Exception as e:
            logger.error(f"[FILE_MANAGER] List files error: {e}")
            return {"status": "error", "message": f"Failed to list files: {str(e)}"}
    
    def _rename_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Rename a file or folder."""
        old_name = params.get("old_name", "").strip()
        new_name = params.get("new_name", "").strip()
        folder = params.get("folder")
        
        if not old_name or not new_name:
            return {"status": "error", "message": "Both old and new names required"}
        
        old_path = self._resolve_path(old_name, folder)
        new_name = self._sanitize_name(new_name)
        new_path = old_path.parent / new_name
        
        if not self._is_in_sandbox(old_path) or not self._is_in_sandbox(new_path):
            return {"status": "error", "message": "Cannot rename files outside Kai directories"}
        
        if not old_path.exists():
            return {"status": "error", "message": f"'{old_name}' does not exist"}
        
        try:
            old_path.rename(new_path)
            
            # Update manifest if Kai-created
            if self._is_kai_created(old_path):
                for entry in self.manifest.get("created_files", []) + self.manifest.get("created_folders", []):
                    if entry["path"] == str(old_path):
                        entry["path"] = str(new_path)
                self._save_manifest()
            
            logger.info(f"[FILE_MANAGER] Renamed: {old_path} -> {new_path}")
            return {
                "status": "success",
                "message": f"✏️ Renamed to '{new_name}'",
                "data": {"old_path": str(old_path), "new_path": str(new_path)}
            }
        except Exception as e:
            logger.error(f"[FILE_MANAGER] Rename error: {e}")
            return {"status": "error", "message": f"Failed to rename: {str(e)}"}
    
    def _move_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Move a file to another folder within sandbox."""
        name = params.get("name", "").strip()
        destination = params.get("destination", "").strip()
        source_folder = params.get("source_folder")
        
        if not name or not destination:
            return {"status": "error", "message": "File name and destination required"}
        
        source_path = self._resolve_path(name, source_folder)
        dest_folder = self._resolve_path(destination)
        dest_path = dest_folder / name
        
        if not self._is_in_sandbox(source_path) or not self._is_in_sandbox(dest_path):
            return {"status": "error", "message": "Cannot move files outside Kai directories"}
        
        if not source_path.exists():
            return {"status": "error", "message": f"'{name}' does not exist"}
        
        try:
            dest_folder.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source_path), str(dest_path))
            
            # Update manifest
            if self._is_kai_created(source_path):
                for entry in self.manifest.get("created_files", []) + self.manifest.get("created_folders", []):
                    if entry["path"] == str(source_path):
                        entry["path"] = str(dest_path)
                self._save_manifest()
            
            logger.info(f"[FILE_MANAGER] Moved: {source_path} -> {dest_path}")
            return {
                "status": "success",
                "message": f"📦 Moved '{name}' to '{destination}'",
                "data": {"old_path": str(source_path), "new_path": str(dest_path)}
            }
        except Exception as e:
            logger.error(f"[FILE_MANAGER] Move error: {e}")
            return {"status": "error", "message": f"Failed to move: {str(e)}"}
    
    def _delete_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a file (only if created by Kai)."""
        name = params.get("name", "").strip()
        folder = params.get("folder")
        force = params.get("force", False)  # Only for testing
        
        if not name:
            return {"status": "error", "message": "File name required"}
        
        file_path = self._resolve_path(name, folder)
        
        if not self._is_in_sandbox(file_path):
            return {"status": "error", "message": "Cannot delete files outside Kai directories"}
        
        if not file_path.exists():
            return {"status": "error", "message": f"'{name}' does not exist"}
        
        # Safety check: only delete Kai-created files
        if not self._is_kai_created(file_path) and not force:
            return {
                "status": "error",
                "message": f"⚠️ Cannot delete '{name}' - not created by Kai"
            }
        
        try:
            if file_path.is_dir():
                shutil.rmtree(file_path)
            else:
                file_path.unlink()
            
            # Remove from manifest
            self.manifest["created_files"] = [
                e for e in self.manifest.get("created_files", [])
                if e["path"] != str(file_path)
            ]
            self.manifest["created_folders"] = [
                e for e in self.manifest.get("created_folders", [])
                if e["path"] != str(file_path)
            ]
            self._save_manifest()
            
            logger.info(f"[FILE_MANAGER] Deleted: {file_path}")
            return {
                "status": "success",
                "message": f"🗑️ Deleted '{name}'",
                "data": {"path": str(file_path)}
            }
        except Exception as e:
            logger.error(f"[FILE_MANAGER] Delete error: {e}")
            return {"status": "error", "message": f"Failed to delete: {str(e)}"}
    
    def _open_folder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Open a folder in File Explorer."""
        folder = params.get("folder")
        
        path = self._get_default_root()
        if folder:
            path = self._resolve_path(folder)
        
        if not self._is_in_sandbox(path):
            return {"status": "error", "message": "Cannot open folders outside Kai directories"}
        
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        
        try:
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(path)])
            else:
                subprocess.run(["xdg-open", str(path)])
            
            logger.info(f"[FILE_MANAGER] Opened folder: {path}")
            return {
                "status": "success",
                "message": f"📂 Opened '{path.name}' in Explorer",
                "data": {"path": str(path)}
            }
        except Exception as e:
            logger.error(f"[FILE_MANAGER] Open folder error: {e}")
            return {"status": "error", "message": f"Failed to open folder: {str(e)}"}
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize a file/folder name."""
        # Remove invalid characters
        invalid = '<>:"/\\|?*'
        for char in invalid:
            name = name.replace(char, '_')
        # Remove leading/trailing spaces and dots
        name = name.strip('. ')
        return name or "unnamed"
