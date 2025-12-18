from typing import Dict, Any
from .base import Tool
import os

class FileTool(Tool):
    def __init__(self):
        super().__init__(
            name="file_system",
            description="Create, read, or delete files. Use this for 'create file', 'delete file' commands.",
            domain="file_operation",
            priority="MEDIUM",
            allowed_intents=["file_operation"]
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "delete", "read", "list"]
                },
                "filename": {
                    "type": "string",
                    "description": "Name of the file (relative to Data folder preferred for safety)"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write (for create action)"
                }
            },
            "required": ["action"]
        }

    def execute(self, action: str, filename: str = "", content: str = "", **kwargs) -> str:
        try:
            # Safety: Default to Data/ directory if no path given?
            # Or allow full paths but careful?
            # User likely says "create file test.txt" -> implies CWD or Data.
            # Let's enforce a safe sandbox for now if possible, or just be careful.
            
            # Simple wrapper around standard OS
            if action == "create":
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"Created file: {filename}"
                
            elif action == "delete":
                if os.path.exists(filename):
                    os.remove(filename)
                    return f"Deleted file: {filename}"
                return f"File not found: {filename}"
                
            elif action == "read":
                if os.path.exists(filename):
                    with open(filename, "r", encoding="utf-8") as f:
                        return f.read()[:2000] # Limit output
                return f"File not found: {filename}"
            
            elif action == "list":
                 # List current directory
                 files = os.listdir(filename if filename else ".")
                 return f"Files: {', '.join(files[:50])}"

            elif action == "analyze":
                try:
                    from Backend.FileAnalyzer import FileAnalyzer
                    analyzer = FileAnalyzer()
                    result = analyzer.analyze_file(filename)
                    return f"Analysis of {filename}:\n{result}"
                except ImportError:
                    return "File Analyzer module not found."
                except Exception as e:
                    return f"Analysis Failed: {str(e)}"

            return f"Unknown file action: {action}"
            
        except Exception as e:
            return f"File Error: {str(e)}"
