"""
Advanced File Operations - Automation System (v2.0)
====================================================
Full-featured file operations for KAI automation:
- Keyboard shortcuts: Select All, Copy, Cut, Paste, Delete, Undo, Redo
- File system: Copy, Move, Delete, Rename, Create, List, Search
- Batch operations: Multiple files, patterns, recursive
- Natural language parsing: "copy file.txt to Documents"
- API integration ready

Author: KAI System
Version: 2.0
"""

import os
import shutil
import time
import glob
import logging
import re
from datetime import datetime
from typing import Optional, List, Dict, Tuple, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Try to import automation libraries
try:
    import pyautogui
    pyautogui.FAILSAFE = False  # Disable fail-safe for automation
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False

try:
    import pyperclip
    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False

try:
    from send2trash import send2trash
    RECYCLE_BIN_AVAILABLE = True
except ImportError:
    RECYCLE_BIN_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedFileOperations:
    """Advanced file operations with natural language support"""
    
    # Common folder mappings
    FOLDER_ALIASES = {
        "desktop": os.path.expanduser("~/Desktop"),
        "documents": os.path.expanduser("~/Documents"),
        "downloads": os.path.expanduser("~/Downloads"),
        "pictures": os.path.expanduser("~/Pictures"),
        "videos": os.path.expanduser("~/Videos"),
        "music": os.path.expanduser("~/Music"),
        "home": os.path.expanduser("~"),
        "temp": os.environ.get("TEMP", "/tmp"),
        "current": os.getcwd(),
        "here": os.getcwd(),
    }
    
    def __init__(self):
        self.clipboard_files: List[str] = []
        self.clipboard_mode: str = "copy"  # "copy" or "cut"
        self.operation_history: List[Dict] = []
        self.max_history = 50
        logger.info("[FileOps] Advanced File Operations v2.0 initialized")
    
    # ==================== KEYBOARD SHORTCUTS ====================
    
    def select_all(self, delay: float = 0.1) -> Dict:
        """Press Ctrl+A to select all"""
        return self._press_hotkey('ctrl', 'a', "Select All", delay)
    
    def copy(self, delay: float = 0.2) -> Dict:
        """Press Ctrl+C to copy"""
        return self._press_hotkey('ctrl', 'c', "Copy", delay)
    
    def cut(self, delay: float = 0.2) -> Dict:
        """Press Ctrl+X to cut"""
        return self._press_hotkey('ctrl', 'x', "Cut", delay)
    
    def paste(self, delay: float = 0.2) -> Dict:
        """Press Ctrl+V to paste"""
        return self._press_hotkey('ctrl', 'v', "Paste", delay)
    
    def delete(self, delay: float = 0.1) -> Dict:
        """Press Delete key"""
        return self._press_key('delete', "Delete", delay)
    
    def permanent_delete(self, delay: float = 0.1) -> Dict:
        """Press Shift+Delete to permanently delete"""
        return self._press_hotkey('shift', 'delete', "Permanent Delete", delay)
    
    def undo(self, delay: float = 0.1) -> Dict:
        """Press Ctrl+Z to undo"""
        return self._press_hotkey('ctrl', 'z', "Undo", delay)
    
    def redo(self, delay: float = 0.1) -> Dict:
        """Press Ctrl+Y to redo"""
        return self._press_hotkey('ctrl', 'y', "Redo", delay)
    
    def rename(self, delay: float = 0.2) -> Dict:
        """Press F2 to rename selected item"""
        return self._press_key('f2', "Rename", delay)
    
    def new_folder(self, delay: float = 0.3) -> Dict:
        """Press Ctrl+Shift+N to create new folder (Windows Explorer)"""
        return self._press_hotkey('ctrl', 'shift', 'n', "New Folder", delay)
    
    def properties(self, delay: float = 0.2) -> Dict:
        """Press Alt+Enter to show properties"""
        return self._press_hotkey('alt', 'enter', "Properties", delay)
    
    def refresh(self, delay: float = 0.2) -> Dict:
        """Press F5 to refresh"""
        return self._press_key('f5', "Refresh", delay)
    
    def select_next(self, delay: float = 0.05) -> Dict:
        """Press Down arrow to select next item"""
        return self._press_key('down', "Select Next", delay)
    
    def select_previous(self, delay: float = 0.05) -> Dict:
        """Press Up arrow to select previous item"""
        return self._press_key('up', "Select Previous", delay)
    
    def open_selected(self, delay: float = 0.1) -> Dict:
        """Press Enter to open selected item"""
        return self._press_key('enter', "Open Selected", delay)
    
    def go_back(self, delay: float = 0.1) -> Dict:
        """Press Alt+Left to go back"""
        return self._press_hotkey('alt', 'left', "Go Back", delay)
    
    def go_forward(self, delay: float = 0.1) -> Dict:
        """Press Alt+Right to go forward"""
        return self._press_hotkey('alt', 'right', "Go Forward", delay)
    
    def go_up(self, delay: float = 0.1) -> Dict:
        """Press Alt+Up to go to parent folder"""
        return self._press_hotkey('alt', 'up', "Go Up", delay)
    
    def _press_key(self, key: str, action: str, delay: float = 0.1) -> Dict:
        """Press a single key"""
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.press(key)
                time.sleep(delay)
                return {"status": "success", "action": action, "key": key}
            elif KEYBOARD_AVAILABLE:
                keyboard.press_and_release(key)
                time.sleep(delay)
                return {"status": "success", "action": action, "key": key}
            return {"status": "error", "message": "No keyboard library available"}
        except Exception as e:
            logger.error(f"[FileOps] {action} failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def _press_hotkey(self, *keys, action: str = "", delay: float = 0.1) -> Dict:
        """Press a key combination"""
        # Last arg is action name, second-to-last might be delay
        key_list = [k for k in keys if isinstance(k, str) and len(k) <= 10]
        
        try:
            if PYAUTOGUI_AVAILABLE:
                pyautogui.hotkey(*key_list)
                time.sleep(delay)
                return {"status": "success", "action": action, "keys": key_list}
            elif KEYBOARD_AVAILABLE:
                keyboard.press_and_release('+'.join(key_list))
                time.sleep(delay)
                return {"status": "success", "action": action, "keys": key_list}
            return {"status": "error", "message": "No keyboard library available"}
        except Exception as e:
            logger.error(f"[FileOps] Hotkey {key_list} failed: {e}")
            return {"status": "error", "message": str(e)}
    
    # ==================== FILE SYSTEM OPERATIONS ====================
    
    def copy_file(self, source: str, destination: str) -> Dict:
        """Copy file(s) to destination"""
        try:
            source = self._resolve_path(source)
            destination = self._resolve_path(destination)
            
            # Handle wildcards
            if '*' in source or '?' in source:
                return self._batch_copy(source, destination)
            
            if not os.path.exists(source):
                return {"status": "error", "message": f"Source not found: {source}"}
            
            # If destination is a directory, copy into it
            if os.path.isdir(destination):
                destination = os.path.join(destination, os.path.basename(source))
            
            # Create destination directory if needed
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            if os.path.isfile(source):
                shutil.copy2(source, destination)
            else:
                shutil.copytree(source, destination, dirs_exist_ok=True)
            
            self._add_history("copy", source, destination)
            logger.info(f"[FileOps] Copied: {source} -> {destination}")
            
            return {
                "status": "success", 
                "message": f"Copied to {destination}",
                "source": source,
                "destination": destination
            }
            
        except Exception as e:
            logger.error(f"[FileOps] Copy failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def move_file(self, source: str, destination: str) -> Dict:
        """Move file(s) to destination"""
        try:
            source = self._resolve_path(source)
            destination = self._resolve_path(destination)
            
            # Handle wildcards
            if '*' in source or '?' in source:
                return self._batch_move(source, destination)
            
            if not os.path.exists(source):
                return {"status": "error", "message": f"Source not found: {source}"}
            
            # If destination is a directory, move into it
            if os.path.isdir(destination):
                destination = os.path.join(destination, os.path.basename(source))
            
            # Create destination directory if needed
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            
            shutil.move(source, destination)
            
            self._add_history("move", source, destination)
            logger.info(f"[FileOps] Moved: {source} -> {destination}")
            
            return {
                "status": "success", 
                "message": f"Moved to {destination}",
                "source": source,
                "destination": destination
            }
            
        except Exception as e:
            logger.error(f"[FileOps] Move failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def delete_file(self, path: str, permanent: bool = False, pattern: str = None) -> Dict:
        """Delete file(s) or folder(s)"""
        try:
            path = self._resolve_path(path)
            
            # Handle patterns
            if pattern:
                return self._batch_delete(path, pattern, permanent)
            
            # Handle wildcards in path
            if '*' in path or '?' in path:
                files = glob.glob(path)
                if not files:
                    return {"status": "error", "message": f"No files matching: {path}"}
                
                deleted = []
                for f in files:
                    result = self.delete_file(f, permanent)
                    if result["status"] == "success":
                        deleted.append(f)
                
                return {
                    "status": "success",
                    "message": f"Deleted {len(deleted)} files",
                    "deleted": deleted
                }
            
            if not os.path.exists(path):
                return {"status": "error", "message": f"Path not found: {path}"}
            
            if permanent or not RECYCLE_BIN_AVAILABLE:
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    shutil.rmtree(path)
            else:
                send2trash(path)
            
            self._add_history("delete", path, None, permanent=permanent)
            logger.info(f"[FileOps] Deleted: {path} (permanent: {permanent})")
            
            return {
                "status": "success", 
                "message": f"Deleted {path}",
                "permanent": permanent
            }
            
        except Exception as e:
            logger.error(f"[FileOps] Delete failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def rename_file(self, path: str, new_name: str) -> Dict:
        """Rename a file or folder"""
        try:
            path = self._resolve_path(path)
            
            if not os.path.exists(path):
                return {"status": "error", "message": f"Path not found: {path}"}
            
            directory = os.path.dirname(path)
            new_path = os.path.join(directory, new_name)
            
            if os.path.exists(new_path):
                return {"status": "error", "message": f"Target already exists: {new_path}"}
            
            os.rename(path, new_path)
            
            self._add_history("rename", path, new_path)
            logger.info(f"[FileOps] Renamed: {path} -> {new_path}")
            
            return {
                "status": "success", 
                "message": f"Renamed to {new_name}",
                "old_path": path,
                "new_path": new_path
            }
            
        except Exception as e:
            logger.error(f"[FileOps] Rename failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_folder(self, path: str) -> Dict:
        """Create a new folder"""
        try:
            path = self._resolve_path(path)
            os.makedirs(path, exist_ok=True)
            
            self._add_history("create_folder", path, None)
            logger.info(f"[FileOps] Created folder: {path}")
            
            return {"status": "success", "message": f"Created folder: {path}", "path": path}
            
        except Exception as e:
            logger.error(f"[FileOps] Create folder failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def create_file(self, path: str, content: str = "") -> Dict:
        """Create a new file with optional content"""
        try:
            path = self._resolve_path(path)
            
            # Create parent directories if needed
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self._add_history("create_file", path, None)
            logger.info(f"[FileOps] Created file: {path}")
            
            return {
                "status": "success", 
                "message": f"Created file: {path}",
                "path": path,
                "size": len(content)
            }
            
        except Exception as e:
            logger.error(f"[FileOps] Create file failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def read_file(self, path: str, lines: int = None) -> Dict:
        """Read file contents"""
        try:
            path = self._resolve_path(path)
            
            if not os.path.isfile(path):
                return {"status": "error", "message": f"File not found: {path}"}
            
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                if lines:
                    content = ''.join(f.readlines()[:lines])
                else:
                    content = f.read()
            
            return {
                "status": "success",
                "path": path,
                "content": content,
                "size": len(content)
            }
            
        except Exception as e:
            logger.error(f"[FileOps] Read file failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def write_file(self, path: str, content: str, append: bool = False) -> Dict:
        """Write content to file"""
        try:
            path = self._resolve_path(path)
            
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            mode = 'a' if append else 'w'
            with open(path, mode, encoding='utf-8') as f:
                f.write(content)
            
            action = "appended" if append else "wrote"
            return {
                "status": "success",
                "message": f"Successfully {action} to {path}",
                "path": path
            }
            
        except Exception as e:
            logger.error(f"[FileOps] Write file failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def list_files(self, path: str = ".", pattern: str = "*", 
                   recursive: bool = False, include_hidden: bool = False) -> Dict:
        """List files in a directory"""
        try:
            path = self._resolve_path(path)
            
            if not os.path.isdir(path):
                return {"status": "error", "message": f"Not a directory: {path}"}
            
            files = []
            folders = []
            
            if recursive:
                search_pattern = os.path.join(path, "**", pattern)
                items = glob.glob(search_pattern, recursive=True)
            else:
                search_pattern = os.path.join(path, pattern)
                items = glob.glob(search_pattern)
            
            for item in items:
                name = os.path.basename(item)
                
                # Skip hidden files if not requested
                if not include_hidden and name.startswith('.'):
                    continue
                
                try:
                    stat = os.stat(item)
                    info = {
                        "name": name,
                        "path": item,
                        "size": stat.st_size,
                        "size_human": self._format_size(stat.st_size),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "is_dir": os.path.isdir(item)
                    }
                    
                    if os.path.isdir(item):
                        folders.append(info)
                    else:
                        info["extension"] = os.path.splitext(item)[1]
                        files.append(info)
                except:
                    pass
            
            # Sort by name
            folders.sort(key=lambda x: x["name"].lower())
            files.sort(key=lambda x: x["name"].lower())
            
            return {
                "status": "success",
                "path": path,
                "folders": folders,
                "files": files,
                "folder_count": len(folders),
                "file_count": len(files),
                "total": len(folders) + len(files)
            }
            
        except Exception as e:
            logger.error(f"[FileOps] List files failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def search_files(self, pattern: str, path: str = ".", 
                    max_results: int = 100, search_content: bool = False) -> Dict:
        """Search for files by name or content"""
        try:
            path = self._resolve_path(path)
            
            if not os.path.isdir(path):
                return {"status": "error", "message": f"Not a directory: {path}"}
            
            results = []
            pattern_lower = pattern.lower()
            
            for root, dirs, files in os.walk(path):
                # Skip hidden directories
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    if len(results) >= max_results:
                        break
                    
                    file_path = os.path.join(root, file)
                    
                    # Name search
                    if pattern_lower in file.lower():
                        results.append({
                            "name": file,
                            "path": file_path,
                            "match_type": "filename"
                        })
                        continue
                    
                    # Content search (for text files)
                    if search_content and self._is_text_file(file):
                        try:
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read(100000)  # First 100KB
                                if pattern_lower in content.lower():
                                    results.append({
                                        "name": file,
                                        "path": file_path,
                                        "match_type": "content"
                                    })
                        except:
                            pass
            
            return {
                "status": "success",
                "pattern": pattern,
                "results": results,
                "count": len(results),
                "truncated": len(results) >= max_results
            }
            
        except Exception as e:
            logger.error(f"[FileOps] Search failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_file_info(self, path: str) -> Dict:
        """Get detailed information about a file or folder"""
        try:
            path = self._resolve_path(path)
            
            if not os.path.exists(path):
                return {"status": "error", "message": f"Path not found: {path}"}
            
            stat = os.stat(path)
            is_dir = os.path.isdir(path)
            
            info = {
                "status": "success",
                "name": os.path.basename(path),
                "path": path,
                "is_file": not is_dir,
                "is_directory": is_dir,
                "size": stat.st_size,
                "size_human": self._format_size(stat.st_size),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "accessed": datetime.fromtimestamp(stat.st_atime).isoformat()
            }
            
            if not is_dir:
                info["extension"] = os.path.splitext(path)[1]
            else:
                # Count contents
                try:
                    contents = os.listdir(path)
                    info["item_count"] = len(contents)
                except:
                    pass
            
            return info
            
        except Exception as e:
            logger.error(f"[FileOps] Get file info failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def open_folder(self, path: str = ".") -> Dict:
        """Open folder in file explorer"""
        try:
            path = self._resolve_path(path)
            
            if not os.path.exists(path):
                return {"status": "error", "message": f"Path not found: {path}"}
            
            # If it's a file, open its parent folder
            if os.path.isfile(path):
                path = os.path.dirname(path)
            
            import subprocess
            if os.name == 'nt':  # Windows
                subprocess.Popen(['explorer', path])
            elif os.name == 'posix':  # Linux/Mac
                subprocess.Popen(['xdg-open', path])
            
            return {"status": "success", "message": f"Opened folder: {path}"}
            
        except Exception as e:
            logger.error(f"[FileOps] Open folder failed: {e}")
            return {"status": "error", "message": str(e)}
    
    # ==================== BATCH OPERATIONS ====================
    
    def _batch_copy(self, pattern: str, destination: str) -> Dict:
        """Copy multiple files matching pattern"""
        files = glob.glob(pattern)
        if not files:
            return {"status": "error", "message": f"No files matching: {pattern}"}
        
        destination = self._resolve_path(destination)
        os.makedirs(destination, exist_ok=True)
        
        copied = []
        errors = []
        
        for f in files:
            try:
                dest = os.path.join(destination, os.path.basename(f))
                if os.path.isfile(f):
                    shutil.copy2(f, dest)
                else:
                    shutil.copytree(f, dest, dirs_exist_ok=True)
                copied.append(f)
            except Exception as e:
                errors.append({"file": f, "error": str(e)})
        
        return {
            "status": "success",
            "message": f"Copied {len(copied)} files",
            "copied": copied,
            "errors": errors
        }
    
    def _batch_move(self, pattern: str, destination: str) -> Dict:
        """Move multiple files matching pattern"""
        files = glob.glob(pattern)
        if not files:
            return {"status": "error", "message": f"No files matching: {pattern}"}
        
        destination = self._resolve_path(destination)
        os.makedirs(destination, exist_ok=True)
        
        moved = []
        errors = []
        
        for f in files:
            try:
                dest = os.path.join(destination, os.path.basename(f))
                shutil.move(f, dest)
                moved.append(f)
            except Exception as e:
                errors.append({"file": f, "error": str(e)})
        
        return {
            "status": "success",
            "message": f"Moved {len(moved)} files",
            "moved": moved,
            "errors": errors
        }
    
    def _batch_delete(self, path: str, pattern: str, permanent: bool) -> Dict:
        """Delete multiple files matching pattern"""
        search_path = os.path.join(path, pattern)
        files = glob.glob(search_path)
        
        if not files:
            return {"status": "error", "message": f"No files matching: {pattern}"}
        
        deleted = []
        errors = []
        
        for f in files:
            try:
                if permanent or not RECYCLE_BIN_AVAILABLE:
                    if os.path.isfile(f):
                        os.remove(f)
                    else:
                        shutil.rmtree(f)
                else:
                    send2trash(f)
                deleted.append(f)
            except Exception as e:
                errors.append({"file": f, "error": str(e)})
        
        return {
            "status": "success",
            "message": f"Deleted {len(deleted)} files",
            "deleted": deleted,
            "errors": errors
        }
    
    # ==================== CLIPBOARD OPERATIONS ====================
    
    def copy_text(self, text: str) -> Dict:
        """Copy text to clipboard"""
        try:
            if CLIPBOARD_AVAILABLE:
                pyperclip.copy(text)
                return {"status": "success", "message": "Copied to clipboard"}
            return {"status": "error", "message": "Clipboard not available"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def paste_text(self) -> Dict:
        """Get text from clipboard"""
        try:
            if CLIPBOARD_AVAILABLE:
                text = pyperclip.paste()
                return {"status": "success", "text": text}
            return {"status": "error", "message": "Clipboard not available"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # ==================== NATURAL LANGUAGE PARSING ====================
    
    def parse_command(self, command: str) -> Dict:
        """
        Parse natural language file command
        
        Examples:
        - "copy file.txt to Documents"
        - "move all *.jpg to Pictures"
        - "delete old_folder"
        - "rename report.pdf to final_report.pdf"
        - "create folder Projects"
        - "list files in Downloads"
        - "search for python in Documents"
        """
        command_lower = command.lower().strip()
        
        # Copy patterns
        if re.search(r'^copy\s+', command_lower):
            match = re.search(r'copy\s+(.+?)\s+to\s+(.+)', command_lower, re.IGNORECASE)
            if match:
                return {
                    "action": "copy",
                    "source": match.group(1).strip(),
                    "destination": match.group(2).strip()
                }
        
        # Move patterns
        if re.search(r'^move\s+', command_lower):
            match = re.search(r'move\s+(.+?)\s+to\s+(.+)', command_lower, re.IGNORECASE)
            if match:
                return {
                    "action": "move",
                    "source": match.group(1).strip(),
                    "destination": match.group(2).strip()
                }
        
        # Delete patterns
        if re.search(r'^(delete|remove)\s+', command_lower):
            match = re.search(r'(?:delete|remove)\s+(.+)', command_lower, re.IGNORECASE)
            if match:
                target = match.group(1).strip()
                permanent = 'permanently' in command_lower or 'permanent' in command_lower
                return {
                    "action": "delete",
                    "target": target.replace('permanently', '').replace('permanent', '').strip(),
                    "permanent": permanent
                }
        
        # Rename patterns
        if re.search(r'^rename\s+', command_lower):
            match = re.search(r'rename\s+(.+?)\s+to\s+(.+)', command_lower, re.IGNORECASE)
            if match:
                return {
                    "action": "rename",
                    "source": match.group(1).strip(),
                    "new_name": match.group(2).strip()
                }
        
        # Create patterns
        if re.search(r'^(create|make|new)\s+', command_lower):
            if 'folder' in command_lower or 'directory' in command_lower:
                match = re.search(r'(?:create|make|new)\s+(?:folder|directory)\s+(.+)', command_lower, re.IGNORECASE)
                if match:
                    return {"action": "create_folder", "path": match.group(1).strip()}
            else:
                match = re.search(r'(?:create|make|new)\s+(?:file\s+)?(.+)', command_lower, re.IGNORECASE)
                if match:
                    return {"action": "create_file", "path": match.group(1).strip()}
        
        # List patterns
        if re.search(r'^(list|show|ls)\s+', command_lower):
            match = re.search(r'(?:list|show|ls)\s+(?:files\s+)?(?:in\s+)?(.+)?', command_lower, re.IGNORECASE)
            path = match.group(1).strip() if match and match.group(1) else "."
            return {"action": "list", "path": path}
        
        # Search patterns
        if re.search(r'^(search|find)\s+', command_lower):
            match = re.search(r'(?:search|find)\s+(?:for\s+)?(.+?)(?:\s+in\s+(.+))?$', command_lower, re.IGNORECASE)
            if match:
                return {
                    "action": "search",
                    "pattern": match.group(1).strip(),
                    "path": match.group(2).strip() if match.group(2) else "."
                }
        
        # Open folder patterns
        if re.search(r'^open\s+', command_lower):
            match = re.search(r'open\s+(?:folder\s+)?(.+)', command_lower, re.IGNORECASE)
            if match:
                return {"action": "open_folder", "path": match.group(1).strip()}
        
        # Keyboard shortcuts
        shortcuts = {
            "select all": "select_all",
            "copy": "copy",
            "cut": "cut", 
            "paste": "paste",
            "delete": "delete",
            "undo": "undo",
            "redo": "redo"
        }
        
        for phrase, action in shortcuts.items():
            if phrase in command_lower:
                return {"action": action, "type": "keyboard"}
        
        return {"action": "unknown", "original": command}
    
    def execute_command(self, command: str) -> Dict:
        """Parse and execute a natural language file command"""
        parsed = self.parse_command(command)
        action = parsed.get("action")
        
        if action == "copy":
            return self.copy_file(parsed["source"], parsed["destination"])
        elif action == "move":
            return self.move_file(parsed["source"], parsed["destination"])
        elif action == "delete":
            return self.delete_file(parsed["target"], parsed.get("permanent", False))
        elif action == "rename":
            return self.rename_file(parsed["source"], parsed["new_name"])
        elif action == "create_folder":
            return self.create_folder(parsed["path"])
        elif action == "create_file":
            return self.create_file(parsed["path"])
        elif action == "list":
            return self.list_files(parsed["path"])
        elif action == "search":
            return self.search_files(parsed["pattern"], parsed["path"])
        elif action == "open_folder":
            return self.open_folder(parsed["path"])
        elif action == "select_all":
            return self.select_all()
        elif action == "copy" and parsed.get("type") == "keyboard":
            return self.copy()
        elif action == "cut":
            return self.cut()
        elif action == "paste":
            return self.paste()
        elif action == "undo":
            return self.undo()
        elif action == "redo":
            return self.redo()
        else:
            return {"status": "error", "message": f"Unknown command: {command}"}
    
    # ==================== UTILITY METHODS ====================
    
    def _resolve_path(self, path: str) -> str:
        """Resolve path with alias support"""
        path = path.strip().strip('"\'')
        
        # Check for aliases
        path_lower = path.lower()
        for alias, real_path in self.FOLDER_ALIASES.items():
            if path_lower.startswith(alias):
                path = path.replace(alias, real_path, 1)
                break
        
        # Expand user home
        path = os.path.expanduser(path)
        
        # Make absolute
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        
        return path
    
    def _format_size(self, size: int) -> str:
        """Format file size to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
    
    def _is_text_file(self, filename: str) -> bool:
        """Check if file is likely a text file"""
        text_extensions = {'.txt', '.py', '.js', '.html', '.css', '.json', '.md', 
                         '.xml', '.csv', '.log', '.ini', '.cfg', '.yaml', '.yml'}
        return os.path.splitext(filename)[1].lower() in text_extensions
    
    def _add_history(self, action: str, source: str, destination: str = None, **kwargs):
        """Add operation to history"""
        self.operation_history.append({
            "action": action,
            "source": source,
            "destination": destination,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        })
        
        if len(self.operation_history) > self.max_history:
            self.operation_history = self.operation_history[-self.max_history:]
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """Get recent operation history"""
        return self.operation_history[-limit:]
    
    def clear_history(self):
        """Clear operation history"""
        self.operation_history = []


# Global instance
file_ops = AdvancedFileOperations()


# ==================== CONVENIENCE FUNCTIONS ====================

def execute(command: str) -> Dict:
    """Execute a natural language file command"""
    return file_ops.execute_command(command)

def select_all(): return file_ops.select_all()
def copy(): return file_ops.copy()
def cut(): return file_ops.cut()
def paste(): return file_ops.paste()
def delete(): return file_ops.delete()
def undo(): return file_ops.undo()
def redo(): return file_ops.redo()
def rename(): return file_ops.rename()
def new_folder(): return file_ops.new_folder()

def copy_file(source: str, dest: str): return file_ops.copy_file(source, dest)
def move_file(source: str, dest: str): return file_ops.move_file(source, dest)
def delete_file(path: str, permanent: bool = False): return file_ops.delete_file(path, permanent)
def rename_file(path: str, new_name: str): return file_ops.rename_file(path, new_name)
def create_folder(path: str): return file_ops.create_folder(path)
def create_file(path: str, content: str = ""): return file_ops.create_file(path, content)
def list_files(path: str = ".", pattern: str = "*"): return file_ops.list_files(path, pattern)
def search_files(pattern: str, path: str = "."): return file_ops.search_files(pattern, path)
def open_folder(path: str = "."): return file_ops.open_folder(path)


if __name__ == "__main__":
    print("🗂️ Testing Advanced File Operations v2.0\n")
    
    # Test natural language parsing
    test_commands = [
        "copy report.txt to Documents",
        "move *.jpg to Pictures",
        "delete old_folder permanently",
        "rename file.txt to newfile.txt",
        "create folder Projects",
        "list files in Downloads",
        "search for python in Documents",
        "select all"
    ]
    
    print("Natural Language Parsing:")
    for cmd in test_commands:
        result = file_ops.parse_command(cmd)
        print(f"  '{cmd}' -> {result}")
    
    print("\n✅ Advanced File Operations test complete!")
