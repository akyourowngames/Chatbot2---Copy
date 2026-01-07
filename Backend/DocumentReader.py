"""
Document Reader - Extract text from PDFs and documents
=======================================================
Supports: PDF, DOCX, TXT files
"""

import os
from typing import Dict, Optional

class DocumentReader:
    """Extract text content from various document formats"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.txt', '.md']
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check which extraction libraries are available"""
        self.has_pypdf = False
        self.has_docx = False
        
        try:
            import PyPDF2
            self.has_pypdf = True
        except ImportError:
            try:
                import pdfplumber
                self.has_pdfplumber = True
            except ImportError:
                print("[DocumentReader] Warning: No PDF library (PyPDF2/pdfplumber)")
        
        try:
            import docx
            self.has_docx = True
        except ImportError:
            print("[DocumentReader] Warning: python-docx not installed")
    
    def read_document(self, file_path: str) -> Dict:
        """
        Extract text from a document file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dict with status, text content, and metadata
        """
        if not os.path.exists(file_path):
            return {"status": "error", "message": "File not found"}
        
        ext = os.path.splitext(file_path)[1].lower()
        filename = os.path.basename(file_path)
        
        if ext not in self.supported_formats:
            return {"status": "error", "message": f"Unsupported format: {ext}"}
        
        try:
            if ext == '.pdf':
                text = self._read_pdf(file_path)
            elif ext == '.docx':
                text = self._read_docx(file_path)
            elif ext in ['.txt', '.md']:
                text = self._read_text(file_path)
            else:
                return {"status": "error", "message": "Unknown format"}
            
            # Calculate stats
            word_count = len(text.split())
            char_count = len(text)
            
            return {
                "status": "success",
                "filename": filename,
                "text": text,
                "word_count": word_count,
                "char_count": char_count,
                "preview": text[:500] + "..." if len(text) > 500 else text
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Failed to read: {str(e)}"}
    
    def _read_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text_parts = []
        
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except ImportError:
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
            except ImportError:
                raise Exception("No PDF library available")
        
        return "\n\n".join(text_parts)
    
    def _read_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        try:
            import docx
            doc = docx.Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except ImportError:
            raise Exception("python-docx not installed")
    
    def _read_text(self, file_path: str) -> str:
        """Read plain text file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    def summarize_for_context(self, file_path: str, max_chars: int = 4000) -> str:
        """
        Read document and prepare for AI context injection.
        Truncates to max_chars to fit in prompt.
        """
        result = self.read_document(file_path)
        
        if result['status'] != 'success':
            return f"[Document Error: {result.get('message', 'Unknown')}]"
        
        text = result['text']
        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n[...truncated, {result['word_count']} total words]"
        
        return f"📄 **{result['filename']}** ({result['word_count']} words)\n\n{text}"


# Global instance
document_reader = DocumentReader()


if __name__ == "__main__":
    # Test
    print("Document Reader initialized")
    print(f"PDF support: {document_reader.has_pypdf}")
    print(f"DOCX support: {document_reader.has_docx}")
