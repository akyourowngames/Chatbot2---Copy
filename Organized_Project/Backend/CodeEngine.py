"""
Code Engine - Beast Mode
=========================
Advanced coding capabilities: Project generation, Execution, Code explanation, and Refactoring.
Features:
- Multi-language support (Python, JS, HTML/CSS, Flask, C++)
- Safe sandbox execution with timeouts
- Smart Project Scaffolding
- LLM-integrated Code Generation
"""

import os
import sys
import subprocess
import tempfile
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
try:
    from Backend.LLM import ChatCompletion
except ImportError:
     def ChatCompletion(messages, model, text_only): return "LLM Unavailable"

class CodeEngine:
    def __init__(self):
        self.workspace = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "Code")
        os.makedirs(self.workspace, exist_ok=True)
        self.logger = logging.getLogger("CodeEngine")

    def generate_code(self, prompt: str, language: str = "python") -> Dict[str, Any]:
        """
        Generate sophisticated code based on user prompt.
        """
        print(f"[CodeEngine] Generating {language} code for: {prompt}")
        
        system_prompt = f"""
        You are an expert Senior Software Engineer.
        Generate production-ready {language} code for the user request.
        Rules:
        1. Return ONLY the code. No markdown backticks, no explanation text.
        2. Include comments explaining complex logic.
        3. Handle edge cases and errors.
        4. If Python, include `if __name__ == "__main__":` block.
        """
        
        try:
            code = ChatCompletion(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                text_only=True,
                system_prompt=system_prompt
            )
            
            # Clean up potential markdown leakage
            code = code.replace("```python", "").replace("```javascript", "").replace("```", "").strip()

            # Save
            filename = f"gen_{datetime.now().strftime('%H%M%S')}.{self._get_ext(language)}"
            filepath = os.path.join(self.workspace, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)
                
            return {
                "status": "success",
                "code": code,
                "filepath": filepath,
                "language": language
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def execute_code(self, code: str = None, filepath: str = None, language: str = "python") -> Dict[str, Any]:
        """
        Execute code safely.
        """
        if filepath:
            full_path = filepath if os.path.isabs(filepath) else os.path.join(self.workspace, filepath)
            if not os.path.exists(full_path):
                return {"status": "error", "message": "File not found"}
        elif code:
            # write temp file
            ext = self._get_ext(language)
            with tempfile.NamedTemporaryFile(mode='w', suffix=f".{ext}", delete=False, dir=self.workspace) as f:
                f.write(code)
                full_path = f.name
        else:
            return {"status": "error", "message": "No code provided"}

        try:
            # Execution Logic per language
            cmd = []
            if language == "python":
                cmd = [sys.executable, full_path]
            elif language == "javascript":
                cmd = ["node", full_path] # Requires node installed
            # Add more languages here
            
            if not cmd:
                return {"status": "error", "message": f"Execution not supported for {language}"}

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, cwd=self.workspace)
            
            return {
                "status": "success" if result.returncode == 0 else "error",
                "output": result.stdout,
                "error": result.stderr,
                "return_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Execution Timed Out (10s limit)"}
        except Exception as e:
             return {"status": "error", "message": str(e)}
        finally:
            if code and 'full_path' in locals():
               try: os.unlink(full_path)
               except: pass

    def create_project(self, name: str, project_type: str = "python") -> str:
        """
        Create a full project folder with scaffolding.
        """
        project_path = os.path.join(self.workspace, name)
        os.makedirs(project_path, exist_ok=True)
        
        files = {}
        if project_type == "python":
            files = {
                "main.py": "def main():\n    print('Hello World')\n\nif __name__ == '__main__':\n    main()",
                "requirements.txt": "",
                "README.md": f"# {name}\nPython Project"
            }
        elif project_type == "flask":
            files = {
                "app.py": "from flask import Flask\napp = Flask(__name__)\n@app.route('/')\ndef home(): return 'Hello'\nif __name__ == '__main__': app.run(debug=True)",
                "requirements.txt": "flask",
                "templates/index.html": "<h1>Hello Flask</h1>"
            }
        elif project_type == "html":
             files = {
                "index.html": "<!DOCTYPE html><html><body><h1>Hello</h1><script src='script.js'></script></body></html>",
                "style.css": "body { background: #f0f0f0; }",
                "script.js": "console.log('Loaded');"
            }

        for path, content in files.items():
            full_path = os.path.join(project_path, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
                
        return f"Created {project_type} project at: {project_path}"

    def _get_ext(self, lang: str) -> str:
        return {
            "python": "py", "javascript": "js", "html": "html", "css": "css", "cpp": "cpp"
        }.get(lang, "txt")

# Global Instance
code_engine = CodeEngine()

