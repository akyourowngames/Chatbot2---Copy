"""
File Upload & Analysis System - Like ChatGPT/Gemini
===================================================
Analyze uploaded files: PDFs, images, documents, code, etc.
"""

import os
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
import mimetypes
from datetime import datetime
import json

class FileAnalyzer:
    def __init__(self):
        self.upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "Uploads")
        os.makedirs(self.upload_dir, exist_ok=True)
        
        self.supported_types = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
            'video': ['.mp4', '.webm', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.3gp', '.mpeg', '.mpg'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.md'],
            'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.go', '.rs'],
            'data': ['.json', '.csv', '.xml', '.yaml', '.yml'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz']
        }
    
    def save_upload(self, file_data: bytes, filename: str) -> str:
        """Save uploaded file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(self.upload_dir, safe_filename)
        
        with open(filepath, 'wb') as f:
            f.write(file_data)
        
        return filepath
    
    def get_file_type(self, filename: str) -> str:
        """Determine file type"""
        ext = Path(filename).suffix.lower()
        
        for file_type, extensions in self.supported_types.items():
            if ext in extensions:
                return file_type
        
        return 'unknown'
    
    def analyze_with_vqa(self, filepath: str, question: str = "Describe this image in detail") -> Dict[str, Any]:
        """Analyze image using Vision service with custom question"""
        try:
            from Backend.VisionService import get_vision_service
            
            vision = get_vision_service()
            result = vision.analyze(filepath, question)
            
            return result
        except Exception as e:
            print(f"[Vision] Error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_smart_caption(self, filepath: str) -> str:
        """Get intelligent caption for image file"""
        try:
            # Check if analysis is cached
            cached = self.load_analysis(filepath)
            if cached and cached.get('caption'):
                return cached['caption']
            
            # Generate new caption with Vision API
            from Backend.VisionService import get_vision_service
            vision = get_vision_service()
            caption = vision.generate_caption(filepath)
            
            if caption:
                # Cache the caption
                self.save_analysis(filepath, {'caption': caption})
                return caption
            
            return "Image uploaded successfully"
        except Exception as e:
            print(f"[Caption] Error: {e}")
            return "Image uploaded successfully"
    
    def save_analysis(self, filepath: str, analysis: Dict[str, Any]) -> None:
        """Cache VQA analysis results"""
        try:
            cache_file = os.path.join(self.upload_dir, '.analysis_cache.json')
            
            # Load existing cache
            cache = {}
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
            
            # Add new analysis
            filename = os.path.basename(filepath)
            cache[filename] = {
                **analysis,
                'cached_at': datetime.now().isoformat()
            }
            
            # Save cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2)
        except Exception as e:
            print(f"[Cache] Save error: {e}")
    
    def load_analysis(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Load cached analysis if available"""
        try:
            cache_file = os.path.join(self.upload_dir, '.analysis_cache.json')
            
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            
            filename = os.path.basename(filepath)
            return cache.get(filename)
        except Exception as e:
            print(f"[Cache] Load error: {e}")
            return None

    
    def analyze_image(self, filepath: str) -> Dict[str, Any]:
        """Analyze image file with both technical details and AI description"""
        try:
            from PIL import Image
            from Backend.VisionService import get_vision_service
            
            img = Image.open(filepath)
            
            # Get technical details
            technical_info = {
                "type": "image",
                "format": img.format,
                "mode": img.mode,
                "size": img.size,
                "width": img.width,
                "height": img.height,
                "megapixels": round((img.width * img.height) / 1000000, 2),
                "file_size": os.path.getsize(filepath),
            }
            
            # Get AI description using Groq Vision (Llama 3.2 Vision)
            try:
                vision_service = get_vision_service()
                caption = vision_service.generate_caption(filepath)
                ai_description = f"🤖 AI Analysis: {caption}" if caption else "✅ Image uploaded successfully"
            except Exception as e:
                print(f"[Vision ERROR] {e}")
                ai_description = "✅ Image uploaded successfully"
            
            # Combine technical and AI analysis
            technical_info["ai_description"] = ai_description
            technical_info["analysis"] = f"📸 Technical: {img.width}x{img.height} pixels, {img.format} format\n\n{ai_description}"
            
            return technical_info
            
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_text(self, filepath: str) -> Dict[str, Any]:
        """Analyze text file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            words = content.split()
            
            return {
                "type": "text",
                "lines": len(lines),
                "words": len(words),
                "characters": len(content),
                "file_size": os.path.getsize(filepath),
                "preview": content[:500],
                "analysis": f"Text file: {len(lines)} lines, {len(words)} words"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_code(self, filepath: str) -> Dict[str, Any]:
        """Analyze code file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
            comments = [l for l in lines if l.strip().startswith('#')]
            
            ext = Path(filepath).suffix
            
            return {
                "type": "code",
                "language": ext[1:],
                "total_lines": len(lines),
                "code_lines": len(code_lines),
                "comment_lines": len(comments),
                "blank_lines": len(lines) - len(code_lines) - len(comments),
                "file_size": os.path.getsize(filepath),
                "preview": content[:500],
                "analysis": f"Code file ({ext[1:]}): {len(lines)} lines, {len(code_lines)} code lines"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_json(self, filepath: str) -> Dict[str, Any]:
        """Analyze JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            def count_keys(obj):
                if isinstance(obj, dict):
                    return sum(count_keys(v) for v in obj.values()) + len(obj)
                elif isinstance(obj, list):
                    return sum(count_keys(item) for item in obj)
                return 0
            
            return {
                "type": "json",
                "structure": type(data).__name__,
                "keys": count_keys(data) if isinstance(data, dict) else 0,
                "items": len(data) if isinstance(data, (list, dict)) else 0,
                "file_size": os.path.getsize(filepath),
                "preview": json.dumps(data, indent=2)[:500],
                "analysis": f"JSON file: {type(data).__name__} with {len(data) if isinstance(data, (list, dict)) else 0} items"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def analyze_pdf(self, filepath: str) -> Dict[str, Any]:
        """Analyze PDF file"""
        try:
            import PyPDF2
            
            with open(filepath, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)
                
                num_pages = len(pdf.pages)
                
                # Extract text from first page
                first_page_text = pdf.pages[0].extract_text() if num_pages > 0 else ""
                
                return {
                    "type": "pdf",
                    "pages": num_pages,
                    "file_size": os.path.getsize(filepath),
                    "preview": first_page_text[:500],
                    "analysis": f"PDF document: {num_pages} pages"
                }
        except Exception as e:
            return {"error": str(e), "note": "Install PyPDF2: pip install PyPDF2"}
    
    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """Analyze any file"""
        filename = os.path.basename(filepath)
        file_type = self.get_file_type(filename)
        
        base_info = {
            "filename": filename,
            "filepath": filepath,
            "file_type": file_type,
            "extension": Path(filename).suffix,
            "size_bytes": os.path.getsize(filepath),
            "size_mb": round(os.path.getsize(filepath) / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
            "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
        }
        
        # Type-specific analysis
        if file_type == 'image':
            analysis = self.analyze_image(filepath)
        elif file_type == 'code':
            analysis = self.analyze_code(filepath)
        elif file_type == 'data':
            if filepath.endswith('.json'):
                analysis = self.analyze_json(filepath)
            else:
                analysis = self.analyze_text(filepath)
        elif file_type == 'document':
            if filepath.endswith('.pdf'):
                analysis = self.analyze_pdf(filepath)
            else:
                analysis = self.analyze_text(filepath)
        else:
            analysis = {"type": "unknown", "analysis": "File type not specifically supported"}
        
        return {**base_info, **analysis}
    
    def list_uploads(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List uploaded files"""
        files = []
        
        if os.path.exists(self.upload_dir):
            for file in sorted(Path(self.upload_dir).iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
                files.append({
                    "filename": file.name,
                    "path": str(file),
                    "size": file.stat().st_size,
                    "uploaded": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
                    "type": self.get_file_type(file.name)
                })
        
        return files
    
    def delete_upload(self, filename: str) -> bool:
        """Delete an uploaded file"""
        try:
            filepath = os.path.join(self.upload_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                return True
            return False
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

# Global instance
file_analyzer = FileAnalyzer()

if __name__ == "__main__":
    print("File Analyzer ready!")
    print(f"Upload directory: {file_analyzer.upload_dir}")
    print(f"Supported types: {list(file_analyzer.supported_types.keys())}")
