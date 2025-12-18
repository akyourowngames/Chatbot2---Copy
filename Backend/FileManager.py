import os
import shutil
import json
import hashlib
import glob
from pathlib import Path
from datetime import datetime
from fuzzywuzzy import process

class FileManager:
    def __init__(self, config_dir="Backend"):
        self.config_dir = config_dir
        self.safe_paths_file = os.path.join(config_dir, "safe_paths.json")
        self.permissions_file = os.path.join(config_dir, "permissions.json")
        self.allowed_paths = []
        self.permissions = {}
        self.load_config()
        self.last_accessed_file = None
        self.current_directory = Path.home()

    def load_config(self):
        try:
            with open(self.safe_paths_file, 'r') as f:
                self.allowed_paths = json.load(f).get("allowed_paths", [])
            with open(self.permissions_file, 'r') as f:
                self.permissions = json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            self.allowed_paths = []
            self.permissions = {}

    def _resolve_path(self, path_str):
        """Resolves system paths like 'Downloads', 'Desktop' to absolute paths."""
        user_home = Path.home()
        path_map = {
            "Documents": user_home / "Documents",
            "Downloads": user_home / "Downloads",
            "Desktop": user_home / "Desktop",
            "Pictures": user_home / "Pictures",
            "Music": user_home / "Music",
            "Videos": user_home / "Videos"
        }
        
        # Drive letter check (e.g. C:, D:)
        if len(path_str) == 2 and path_str[1] == ':':
            return Path(path_str + '/')
            
        # Check if it's a known alias with improved matching
        path_keys = list(path_map.keys())
        
        # Exact or fuzzy match for the root folder
        root_part = path_str.split('/')[0].split('\\')[0]
        
        # Try finding a close match for the root part (e.g. 'dektop' -> 'Desktop')
        best_match, score = process.extractOne(root_part, path_keys)
        
        if score > 80: # High confidence fuzzy match
            mapped_root = path_map[best_match]
            # Replace the fuzzy root with the real path
            if len(path_str) > len(root_part):
                # Append the rest of the path
                rest = path_str[len(root_part):].lstrip('/\\')
                return mapped_root / rest
            else:
                return mapped_root

        # Check path map manually if fuzzy failed or for exact startswith
        for key, val in path_map.items():
            if path_str.lower() == key.lower():
                return val
            if path_str.lower().startswith(key.lower() + os.sep) or path_str.lower().startswith(key.lower() + '/'):
                return val / path_str[len(key)+1:]
        
        # Absolute path check
        p = Path(path_str)
        if p.is_absolute():
            return p
            
        # Check relative to current_directory first
        if self.current_directory:
            possible_path = self.current_directory / path_str
            if possible_path.exists():
                return possible_path
                
        return user_home / path_str # Default relative to home

    def _is_safe_path(self, path):
        """Checks if the path is within allowed directories."""
        try:
            path_obj = Path(path)
            # If path is just a filename or relative, resolve it first against home or safe base
            if not path_obj.is_absolute():
                path_obj = self._resolve_path(str(path))
            
            resolved_path = path_obj.resolve()
            
            allowed_dirs = []
            user_home = Path.home()
            path_map = {
                "Documents": user_home / "Documents",
                "Downloads": user_home / "Downloads",
                "Desktop": user_home / "Desktop",
                "Pictures": user_home / "Pictures",
                "Music": user_home / "Music",
                "Videos": user_home / "Videos"
            }

            for allowed in self.allowed_paths:
                if allowed in path_map:
                    allowed_dirs.append(path_map[allowed])
                else:
                    # Allow specifying absolute paths in safe_paths.json
                    p = Path(allowed)
                    if p.is_absolute():
                         allowed_dirs.append(p)
                    else:
                         allowed_dirs.append(user_home / allowed)

            for safe_dir in allowed_dirs:
                try:
                    # Check if resolved_path is relative to safe_dir OR is safe_dir
                    if resolved_path == safe_dir or safe_dir in resolved_path.parents:
                        return True
                except ValueError:
                    continue
            
            print(f"[FileManager] Access Denied: {resolved_path} is not in {allowed_dirs}")
            return False
            
        except Exception as e:
            print(f"Path Check Error: {e}")
            return False

    def list_files(self, path="."):
        if not self.permissions.get("can_view_files", False):
            return {"error": "Permission denied"}

        target_path = self._resolve_path(path)
        if not self._is_safe_path(target_path):
            return {"error": "Access denied: Path not in safe list"}

        if not target_path.exists():
            return {"error": "Path does not exist"}

        # Update current directory for context
        if target_path.is_dir():
            self.current_directory = target_path

        results = []
        try:
            # Sort: Directories first, then files
            items = sorted(list(target_path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for item in items:
                if item.name.startswith('.'): continue # Skip hidden files
                stats = item.stat()
                results.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stats.st_size,
                    "modified": datetime.fromtimestamp(stats.st_mtime).isoformat()
                })
        except Exception as e:
            return {"error": str(e)}

        return {"files": results[:500], "count": len(results), "path": str(target_path)}

    def search_files(self, query, path=".", recursive=True):
        if not self.permissions.get("can_view_files", False):
            return {"error": "Permission denied"}

        target_path = self._resolve_path(path)
        if not self._is_safe_path(target_path):
            return {"error": "Access denied"}

        results = []
        # Optimized: non-recursive default if huge, but user wants power. 
        # We will use rglob but with a limiter or just glob if recursive is False.
        # Actually, let's keep it simple: strict glob if not recursive.
        pattern = f"**/*{query}*" if recursive else f"*{query}*"
        
        try:
            # Using glob implementation for safer search
            # Note: glob.glob with recursive=True might be slow for huge dirs
            # ripgrep or fd would be faster but sticking to stdlib for portability as requested
            for item in target_path.glob(pattern):
                if item.name.startswith('.'): continue # Skip hidden files
                if not self._is_safe_path(item): continue
                stats = item.stat()
                results.append({
                    "name": item.name,
                    "path": str(item),
                    "type": "directory" if item.is_dir() else "file",
                    "size": stats.st_size
                })
        except Exception as e:
            return {"error": str(e)}

        return {"files": results[:100], "count": len(results), "limited": len(results) > 100}

    def move_files(self, sources, destination, dry_run=True):
        if not self.permissions.get("can_move_files", False):
            return {"error": "Permission denied"}

        dest_path = self._resolve_path(destination)
        if not self._is_safe_path(dest_path):
            return {"error": "Destination not safe"}

        preview = []
        failures = []

        for src in sources:
            src_path = self._resolve_path(src)
            if not self._is_safe_path(src_path):
                failures.append({"file": src, "error": "Source path unsafe"})
                continue
            
            if not src_path.exists():
                failures.append({"file": src, "error": "File not found"})
                continue

            target = dest_path / src_path.name
            preview.append({"from": str(src_path), "to": str(target)})
            
            if not dry_run:
                try:
                    shutil.move(str(src_path), str(target))
                except Exception as e:
                    failures.append({"file": src, "error": str(e)})

        return {
            "action": "move_files",
            "dry_run": dry_run,
            "success": len(failures) == 0,
            "affected_files": len(preview) if not failures else 0, # rough count
            "preview": preview,
            "failures": failures
        }

    def copy_files(self, sources, destination, dry_run=True):
        if not self.permissions.get("can_copy_files", False):
            return {"error": "Permission denied"}

        dest_path = self._resolve_path(destination)
        if not self._is_safe_path(dest_path):
            return {"error": "Destination not safe"}

        preview = []
        failures = []

        for src in sources:
            src_path = self._resolve_path(src)
            if not self._is_safe_path(src_path):
                failures.append({"file": src, "error": "Source path unsafe"})
                continue

            target = dest_path / src_path.name
            preview.append({"from": str(src_path), "to": str(target)})

            if not dry_run:
                try:
                    if src_path.is_dir():
                        shutil.copytree(str(src_path), str(target))
                    else:
                        shutil.copy2(str(src_path), str(target))
                except Exception as e:
                    failures.append({"file": src, "error": str(e)})

        return {
            "action": "copy_files",
            "dry_run": dry_run,
            "success": len(failures) == 0,
            "preview": preview,
            "failures": failures
        }

    def find_duplicates(self, path="."):
        if not self.permissions.get("can_view_files", False):
            return {"error": "Permission denied"}

        target_path = self._resolve_path(path)
        if not self._is_safe_path(target_path):
            return {"error": "Access denied"}

        hashes = {}
        duplicates = []

        for root, dirs, files in os.walk(str(target_path)):
            for filename in files:
                filepath = Path(root) / filename
                if not self._is_safe_path(filepath): continue
                
                try:
                    file_hash = self._get_file_hash(filepath)
                    if file_hash in hashes:
                        duplicates.append({
                            "original": str(hashes[file_hash]),
                            "duplicate": str(filepath),
                            "size": filepath.stat().st_size
                        })
                    else:
                        hashes[file_hash] = filepath
                except Exception:
                    continue
        
        return {"duplicates": duplicates, "count": len(duplicates)}

    def _get_file_hash(self, filepath):
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()

    def format_size(self, size_bytes):
        """Format file size in human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def open_file(self, path=None):
        """Opens a file or directory using the default system application."""
        if not self.permissions.get("can_view_files", False):
            return {"error": "Permission denied"}

        # Handle "open it" context
        if path is None or path == "last":
            if self.last_accessed_file:
                target_path = self.last_accessed_file
            else:
                return {"error": "No file to open (I haven't opened or found one yet)."}
        else:
            # Try exact match first
            target_path = self._resolve_path(path)
            
            # If not found, try fuzzy match in current directory
            if not target_path.exists() and self.current_directory:
                # Get all files in current dir
                files = [f.name for f in self.current_directory.iterdir()]
                best_match, score = process.extractOne(path, files)
                if score > 80:
                    target_path = self.current_directory / best_match

        if not self._is_safe_path(target_path):
            return {"error": "Access denied: Unsafe path"}
        
        if not target_path.exists():
            return {"error": f"File or folder not found: {path}"}

        try:
            self.last_accessed_file = target_path # Remember correctly opened file
            
            if os.name == 'nt':  # Windows
                os.startfile(str(target_path))
            elif os.name == 'posix':  # macOS/Linux
                subprocess.call(('open', str(target_path)))
                
            type_str = "Folder" if target_path.is_dir() else "File"
            return {"success": True, "message": f"Opened {type_str}: {target_path.name}"}
        except Exception as e:
            return {"error": f"Failed to open: {e}"}

    def get_file_details(self, path):
        """Returns details and a summary/snippet if possible."""
        target_path = self._resolve_path(path)
        if not self._is_safe_path(target_path):
             return {"error": "Access denied"}
        
        if not target_path.exists():
             return {"error": "File not found"}
             
        stats = target_path.stat()
        details = {
             "name": target_path.name,
             "path": str(target_path),
             "size": stats.st_size,
             "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
             "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
             "is_dir": target_path.is_dir()
        }
        
        # Add quick content snippet if it's a small text file
        if not target_path.is_dir() and stats.st_size < 100000: # < 100KB
            try:
                with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(500)
                    details['snippet'] = content
            except:
                pass
                
        return details

    def get_file_details(self, path):
        """Get detailed metadata for a file."""
        target_path = self._resolve_path(path)
        if not self._is_safe_path(target_path):
            return {"error": "Access denied"}
        
        if not target_path.exists():
            return {"error": "File not found"}
            
        try:
            stats = target_path.stat()
            return {
                "name": target_path.name,
                "path": str(target_path),
                "size": stats.st_size,
                "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
                "is_dir": target_path.is_dir(),
                "extension": target_path.suffix
            }
        except Exception as e:
            return {"error": str(e)}
