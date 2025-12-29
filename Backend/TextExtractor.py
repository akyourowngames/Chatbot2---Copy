"""
TextExtractor - Extract text from various file formats
=======================================================
Supports: PDF, DOCX, XLSX, TXT, CSV, JSON
"""

import os
import io
import json
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_text_from_file(file_data: bytes, file_type: str) -> str:
    """
    Extract text content from various file formats.
    
    Args:
        file_data: Binary file content
        file_type: File extension (pdf, docx, xlsx, txt, etc.)
        
    Returns:
        Extracted text as string
    """
    file_type = file_type.lower().strip('.')
    
    try:
        if file_type == 'txt':
            return extract_txt(file_data)
        elif file_type == 'pdf':
            return extract_pdf(file_data)
        elif file_type == 'docx':
            return extract_docx(file_data)
        elif file_type == 'xlsx':
            return extract_xlsx(file_data)
        elif file_type == 'csv':
            return extract_csv(file_data)
        elif file_type == 'json':
            return extract_json(file_data)
        else:
            logger.warning(f"[TextExtractor] Unsupported file type: {file_type}")
            return f"[Unsupported file type: {file_type}]"
    except Exception as e:
        logger.error(f"[TextExtractor] Extraction failed: {e}")
        return f"[Error extracting text: {str(e)}]"


def extract_txt(file_data: bytes) -> str:
    """Extract text from plain text file."""
    try:
        return file_data.decode('utf-8')
    except UnicodeDecodeError:
        return file_data.decode('latin-1')


def extract_pdf(file_data: bytes) -> str:
    """Extract text from PDF file."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_data)) as pdf:
            text_parts = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return '\n'.join(text_parts)
    except ImportError:
        logger.warning("[TextExtractor] pdfplumber not installed, trying PyPDF2")
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_data))
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())
            return '\n'.join(text_parts)
        except ImportError:
            return "[PDF extraction requires pdfplumber or pypdf]"
    except Exception as e:
        return f"[PDF extraction error: {str(e)}]"


def extract_docx(file_data: bytes) -> str:
    """Extract text from Word document."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_data))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return '\n'.join(paragraphs)
    except ImportError:
        try:
            # Fallback: extract raw text from XML
            import zipfile
            from xml.etree import ElementTree
            with zipfile.ZipFile(io.BytesIO(file_data)) as zf:
                xml_content = zf.read('word/document.xml')
                tree = ElementTree.fromstring(xml_content)
                ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                texts = tree.findall('.//w:t', ns)
                return ' '.join([t.text for t in texts if t.text])
        except Exception as e:
            return f"[DOCX extraction error: {str(e)}]"
    except Exception as e:
        return f"[DOCX extraction error: {str(e)}]"


def extract_xlsx(file_data: bytes) -> str:
    """Extract text from Excel spreadsheet."""
    try:
        import pandas as pd
        excel_file = pd.ExcelFile(io.BytesIO(file_data))
        all_text = []
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            all_text.append(f"=== Sheet: {sheet_name} ===")
            all_text.append(df.to_string())
        return '\n'.join(all_text)
    except ImportError:
        return "[Excel extraction requires pandas and openpyxl]"
    except Exception as e:
        return f"[Excel extraction error: {str(e)}]"


def extract_csv(file_data: bytes) -> str:
    """Extract text from CSV file."""
    try:
        import pandas as pd
        df = pd.read_csv(io.BytesIO(file_data))
        return df.to_string()
    except ImportError:
        # Fallback to raw text
        return extract_txt(file_data)
    except Exception as e:
        return f"[CSV extraction error: {str(e)}]"


def extract_json(file_data: bytes) -> str:
    """Extract text from JSON file."""
    try:
        data = json.loads(file_data.decode('utf-8'))
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"[JSON extraction error: {str(e)}]"


if __name__ == "__main__":
    print("TextExtractor Test\n" + "=" * 50)
    
    # Test TXT extraction
    sample_txt = b"Hello, this is a test file.\nWith multiple lines."
    result = extract_text_from_file(sample_txt, "txt")
    print(f"TXT: {result[:50]}...")
    
    # Test JSON extraction
    sample_json = b'{"name": "test", "value": 123}'
    result = extract_text_from_file(sample_json, "json")
    print(f"JSON: {result[:50]}...")
    
    print("\n✅ TextExtractor ready!")
