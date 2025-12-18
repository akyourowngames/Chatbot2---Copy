"""
Advanced File I/O Automation - Create, Read, Write, Organize Files
==================================================================
Intelligent file operations with AI assistance
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import mimetypes

class FileIOAutomation:
    def __init__(self):
        self.workspace_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "Workspace")
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        self.file_templates = {
            "python": "# Python Script\n# Created: {date}\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
            "javascript": "// JavaScript File\n// Created: {date}\n\nfunction main() {{\n    // Your code here\n}}\n\nmain();\n",
            "html": "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Document</title>\n</head>\n<body>\n    <h1>Hello World</h1>\n</body>\n</html>\n",
            "css": "/* CSS Stylesheet */\n/* Created: {date} */\n\n* {{\n    margin: 0;\n    padding: 0;\n    box-sizing: border-box;\n}}\n",
            "markdown": "# Document Title\n\nCreated: {date}\n\n## Section 1\n\nYour content here.\n",
            "json": '{{\n    "created": "{date}",\n    "data": {{}}\n}}\n',
            "text": "Text Document\nCreated: {date}\n\n"
        }
    
    def create_file(self, filename: str, content: str = None, file_type: str = None) -> Dict[str, Any]:
        """Create a new file with optional template"""
        try:
            filepath = os.path.join(self.workspace_dir, filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else self.workspace_dir, exist_ok=True)
            
            # Determine file type
            if not file_type:
                ext = Path(filename).suffix[1:].lower()
                file_type = ext if ext in self.file_templates else "text"
            
            # Get content
            if content is None:
                template = self.file_templates.get(file_type, self.file_templates["text"])
                content = template.format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return {
                "status": "success",
                "message": f"✅ Created: {filename}",
                "filepath": filepath,
                "size": os.path.getsize(filepath)
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to create file: {str(e)}"}
    
    def read_file(self, filename: str) -> Dict[str, Any]:
        """Read file content"""
        try:
            filepath = os.path.join(self.workspace_dir, filename)
            
            if not os.path.exists(filepath):
                return {"status": "error", "message": f"File not found: {filename}"}
            
            # Determine if binary or text
            mime_type, _ = mimetypes.guess_type(filepath)
            is_text = mime_type and mime_type.startswith('text')
            
            if is_text or filepath.endswith(('.txt', '.py', '.js', '.html', '.css', '.md', '.json')):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return {
                    "status": "success",
                    "filename": filename,
                    "content": content,
                    "size": os.path.getsize(filepath),
                    "lines": len(content.split('\n')),
                    "type": "text"
                }
            else:
                return {
                    "status": "success",
                    "filename": filename,
                    "size": os.path.getsize(filepath),
                    "type": "binary",
                    "message": "Binary file - cannot display content"
                }
        except Exception as e:
            return {"status": "error", "message": f"Failed to read file: {str(e)}"}
    
    def write_file(self, filename: str, content: str, mode: str = 'w') -> Dict[str, Any]:
        """Write content to file"""
        try:
            filepath = os.path.join(self.workspace_dir, filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else self.workspace_dir, exist_ok=True)
            
            with open(filepath, mode, encoding='utf-8') as f:
                f.write(content)
            
            return {
                "status": "success",
                "message": f"✅ {'Appended to' if mode == 'a' else 'Written to'}: {filename}",
                "filepath": filepath,
                "size": os.path.getsize(filepath)
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to write file: {str(e)}"}
    
    def append_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Append content to file"""
        return self.write_file(filename, content, mode='a')
    
    def delete_file(self, filename: str) -> Dict[str, Any]:
        """Delete a file"""
        try:
            filepath = os.path.join(self.workspace_dir, filename)
            
            if not os.path.exists(filepath):
                return {"status": "error", "message": f"File not found: {filename}"}
            
            os.remove(filepath)
            
            return {
                "status": "success",
                "message": f"🗑️ Deleted: {filename}"
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to delete file: {str(e)}"}
    
    def rename_file(self, old_name: str, new_name: str) -> Dict[str, Any]:
        """Rename a file"""
        try:
            old_path = os.path.join(self.workspace_dir, old_name)
            new_path = os.path.join(self.workspace_dir, new_name)
            
            if not os.path.exists(old_path):
                return {"status": "error", "message": f"File not found: {old_name}"}
            
            os.rename(old_path, new_path)
            
            return {
                "status": "success",
                "message": f"✅ Renamed: {old_name} → {new_name}"
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to rename file: {str(e)}"}
    
    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Copy a file"""
        try:
            src_path = os.path.join(self.workspace_dir, source)
            dst_path = os.path.join(self.workspace_dir, destination)
            
            if not os.path.exists(src_path):
                return {"status": "error", "message": f"File not found: {source}"}
            
            shutil.copy2(src_path, dst_path)
            
            return {
                "status": "success",
                "message": f"✅ Copied: {source} → {destination}"
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to copy file: {str(e)}"}
    
    def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """Move a file"""
        try:
            src_path = os.path.join(self.workspace_dir, source)
            dst_path = os.path.join(self.workspace_dir, destination)
            
            if not os.path.exists(src_path):
                return {"status": "error", "message": f"File not found: {source}"}
            
            shutil.move(src_path, dst_path)
            
            return {
                "status": "success",
                "message": f"✅ Moved: {source} → {destination}"
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to move file: {str(e)}"}
    
    def list_files(self, pattern: str = "*") -> Dict[str, Any]:
        """List files in workspace"""
        try:
            files = []
            
            for file in Path(self.workspace_dir).rglob(pattern):
                if file.is_file():
                    files.append({
                        "name": file.name,
                        "path": str(file.relative_to(self.workspace_dir)),
                        "size": file.stat().st_size,
                        "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
                        "extension": file.suffix
                    })
            
            return {
                "status": "success",
                "count": len(files),
                "files": sorted(files, key=lambda x: x['modified'], reverse=True)
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to list files: {str(e)}"}
    
    def organize_files(self, by: str = "extension") -> Dict[str, Any]:
        """Organize files by type or date"""
        try:
            organized = {}
            
            for file in Path(self.workspace_dir).rglob("*"):
                if file.is_file():
                    if by == "extension":
                        key = file.suffix or "no_extension"
                    elif by == "date":
                        key = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d")
                    else:
                        key = "other"
                    
                    if key not in organized:
                        organized[key] = []
                    
                    organized[key].append(file.name)
            
            return {
                "status": "success",
                "organized_by": by,
                "groups": organized,
                "total_files": sum(len(files) for files in organized.values())
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to organize files: {str(e)}"}
    
    def search_files(self, query: str) -> Dict[str, Any]:
        """Search for files by name or content"""
        try:
            results = []
            
            for file in Path(self.workspace_dir).rglob("*"):
                if file.is_file():
                    # Search in filename
                    if query.lower() in file.name.lower():
                        results.append({
                            "name": file.name,
                            "path": str(file.relative_to(self.workspace_dir)),
                            "match_type": "filename"
                        })
                    # Search in content (text files only)
                    elif file.suffix in ['.txt', '.py', '.js', '.html', '.css', '.md', '.json']:
                        try:
                            with open(file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if query.lower() in content.lower():
                                    results.append({
                                        "name": file.name,
                                        "path": str(file.relative_to(self.workspace_dir)),
                                        "match_type": "content"
                                    })
                        except:
                            pass
            
            return {
                "status": "success",
                "query": query,
                "count": len(results),
                "results": results
            }
        except Exception as e:
            return {"status": "error", "message": f"Search failed: {str(e)}"}
    
    def open_in_explorer(self, path: str = None) -> Dict[str, Any]:
        """Open folder in Windows File Explorer"""
        try:
            import subprocess
            target_path = os.path.join(self.workspace_dir, path) if path else self.workspace_dir
            
            if not os.path.exists(target_path):
                return {"status": "error", "message": f"Path not found: {path}"}
            
            subprocess.Popen(f'explorer "{target_path}"', shell=True)
            
            return {
                "status": "success",
                "message": f"📁 Opened: {target_path}"
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to open explorer: {str(e)}"}
    
    def list_directory(self, path: str = None) -> Dict[str, Any]:
        """List contents of a directory"""
        try:
            target_path = os.path.join(self.workspace_dir, path) if path else self.workspace_dir
            
            if not os.path.exists(target_path):
                return {"status": "error", "message": f"Directory not found: {path}"}
            
            items = []
            for item in Path(target_path).iterdir():
                items.append({
                    "name": item.name,
                    "type": "folder" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                })
            
            # Sort: folders first, then by name
            items.sort(key=lambda x: (0 if x['type'] == 'folder' else 1, x['name'].lower()))
            
            return {
                "status": "success",
                "path": path or ".",
                "count": len(items),
                "items": items
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to list directory: {str(e)}"}
    
    def get_file_info(self, filename: str) -> Dict[str, Any]:
        """Get detailed information about a file"""
        try:
            filepath = os.path.join(self.workspace_dir, filename)
            
            if not os.path.exists(filepath):
                return {"status": "error", "message": f"File not found: {filename}"}
            
            stat = os.stat(filepath)
            mime_type, _ = mimetypes.guess_type(filepath)
            
            return {
                "status": "success",
                "filename": filename,
                "full_path": filepath,
                "size": stat.st_size,
                "size_human": self._format_size(stat.st_size),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "mime_type": mime_type or "unknown",
                "extension": Path(filename).suffix
            }
        except Exception as e:
            return {"status": "error", "message": f"Failed to get file info: {str(e)}"}
    
    def _format_size(self, size: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    # ==================== SYSTEM-WIDE FILE ACCESS ====================
    
    def search_system(self, query: str, locations: List[str] = None, max_results: int = 20) -> Dict[str, Any]:
        """
        Search files system-wide across common user folders.
        
        Args:
            query: Search term (filename pattern)
            locations: List of locations to search (default: common user folders)
            max_results: Maximum results to return
        """
        try:
            import os
            
            # Default search locations
            if not locations:
                user_home = os.path.expanduser("~")
                locations = [
                    os.path.join(user_home, "Downloads"),
                    os.path.join(user_home, "Documents"),
                    os.path.join(user_home, "Desktop"),
                    os.path.join(user_home, "Pictures"),
                    os.path.join(user_home, "Videos"),
                    os.path.join(user_home, "Music"),
                ]
            
            results = []
            searched_paths = []
            
            for location in locations:
                if not os.path.exists(location):
                    continue
                    
                searched_paths.append(location)
                
                try:
                    for root, dirs, files in os.walk(location):
                        # Skip hidden directories
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        
                        for file in files:
                            if query.lower() in file.lower():
                                filepath = os.path.join(root, file)
                                try:
                                    stat = os.stat(filepath)
                                    results.append({
                                        "name": file,
                                        "path": filepath,
                                        "size": self._format_size(stat.st_size),
                                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                                    })
                                    
                                    if len(results) >= max_results:
                                        break
                                except:
                                    pass
                        
                        if len(results) >= max_results:
                            break
                except PermissionError:
                    continue
                
                if len(results) >= max_results:
                    break
            
            return {
                "status": "success",
                "query": query,
                "count": len(results),
                "searched": searched_paths,
                "results": results
            }
        except Exception as e:
            return {"status": "error", "message": f"System search failed: {str(e)}"}
    
    def search_drive(self, query: str, drive: str = "C:", max_results: int = 20) -> Dict[str, Any]:
        """
        Search files on a specific drive.
        
        Args:
            query: Search term
            drive: Drive letter (e.g., "C:", "D:")
            max_results: Maximum results
        """
        try:
            import subprocess
            
            # Use Windows 'where' command for faster search
            cmd = f'where /r {drive}\\ *{query}*'
            
            try:
                result = subprocess.run(
                    cmd, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=30
                )
                
                paths = result.stdout.strip().split('\n')[:max_results]
                
                results = []
                for path in paths:
                    path = path.strip()
                    if path and os.path.exists(path):
                        try:
                            stat = os.stat(path)
                            results.append({
                                "name": os.path.basename(path),
                                "path": path,
                                "size": self._format_size(stat.st_size),
                                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
                            })
                        except:
                            results.append({"name": os.path.basename(path), "path": path})
                
                return {
                    "status": "success",
                    "query": query,
                    "drive": drive,
                    "count": len(results),
                    "results": results
                }
            except subprocess.TimeoutExpired:
                return {"status": "error", "message": "Search timed out. Try a more specific query."}
                
        except Exception as e:
            return {"status": "error", "message": f"Drive search failed: {str(e)}"}
    
    def list_system_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        List contents of any folder on the system.
        
        Args:
            folder_path: Path to folder (can include shortcuts like ~ for home)
        """
        try:
            # Expand path shortcuts
            folder_path = os.path.expanduser(folder_path)
            folder_path = os.path.expandvars(folder_path)
            
            # Handle special folder names
            special_folders = {
                "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
                "documents": os.path.join(os.path.expanduser("~"), "Documents"),
                "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
                "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
                "videos": os.path.join(os.path.expanduser("~"), "Videos"),
                "music": os.path.join(os.path.expanduser("~"), "Music"),
            }
            
            folder_lower = folder_path.lower()
            if folder_lower in special_folders:
                folder_path = special_folders[folder_lower]
            
            if not os.path.exists(folder_path):
                return {"status": "error", "message": f"Folder not found: {folder_path}"}
            
            if not os.path.isdir(folder_path):
                return {"status": "error", "message": f"Not a folder: {folder_path}"}
            
            items = []
            for item in os.listdir(folder_path)[:50]:  # Limit to 50 items
                item_path = os.path.join(folder_path, item)
                try:
                    stat = os.stat(item_path)
                    is_dir = os.path.isdir(item_path)
                    items.append({
                        "name": item,
                        "type": "folder" if is_dir else "file",
                        "size": self._format_size(stat.st_size) if not is_dir else None,
                        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    })
                except:
                    items.append({"name": item, "type": "unknown"})
            
            return {
                "status": "success",
                "path": folder_path,
                "count": len(items),
                "items": items
            }
        except PermissionError:
            return {"status": "error", "message": f"Access denied: {folder_path}"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to list folder: {str(e)}"}

# Global instance
file_io = FileIOAutomation()

if __name__ == "__main__":
    print("File I/O Automation initialized!")
    print(f"Workspace: {file_io.workspace_dir}")
    
    # Test system search
    result = file_io.search_system("python")
    print(f"Found {result.get('count', 0)} files")

