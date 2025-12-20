"""
DocumentRAG - Chat with Documents Feature
==========================================
Upload PDFs, text files, or URLs and chat with their content using AI.

Features:
- PDF text extraction
- URL content extraction (via web scraper)
- Text chunking for large documents
- Context injection for LLM queries
- Supabase storage for documents
"""

import os
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import PDF libraries
try:
    import pdfplumber
    PDF_SUPPORT = True
    logger.info("[RAG] pdfplumber available for PDF extraction")
except ImportError:
    try:
        from PyPDF2 import PdfReader
        PDF_SUPPORT = True
        logger.info("[RAG] PyPDF2 available for PDF extraction")
    except ImportError:
        PDF_SUPPORT = False
        logger.warning("[RAG] No PDF library available. PDF upload will be limited.")

# Import existing modules
try:
    from Backend.ProWebScraper import pro_scraper
except ImportError:
    try:
        from Backend.EnhancedWebScraper import EnhancedWebScraper
        pro_scraper = EnhancedWebScraper()
    except ImportError:
        pro_scraper = None
        logger.warning("[RAG] Web scraper not available")

try:
    from Backend.LLM import ChatCompletion
except ImportError:
    ChatCompletion = None
    logger.warning("[RAG] LLM not available")

try:
    from Backend.SupabaseDB import supabase_db
except ImportError:
    supabase_db = None
    logger.warning("[RAG] Supabase not available")


class DocumentRAG:
    """
    RAG (Retrieval-Augmented Generation) for documents.
    Allows users to upload documents and chat with their content.
    """
    
    def __init__(self):
        self.temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "RAG")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # In-memory document cache for fast access
        self.document_cache: Dict[str, Dict[str, Any]] = {}
        
        # Active document for chat context
        self.active_document_id: Optional[str] = None
        
        logger.info("[RAG] DocumentRAG initialized")
    
    # ==================== DOCUMENT EXTRACTION ====================
    
    def extract_pdf_text(self, file_path: str) -> str:
        """Extract text content from a PDF file."""
        if not PDF_SUPPORT:
            return "PDF extraction not available. Please install pdfplumber or PyPDF2."
        
        try:
            text_content = []
            
            # Try pdfplumber first (better extraction)
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text_content.append(page_text)
                logger.info(f"[RAG] Extracted {len(text_content)} pages with pdfplumber")
            except:
                # Fallback to PyPDF2
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
                logger.info(f"[RAG] Extracted {len(text_content)} pages with PyPDF2")
            
            full_text = "\n\n".join(text_content)
            return full_text.strip()
            
        except Exception as e:
            logger.error(f"[RAG] PDF extraction error: {e}")
            return f"Error extracting PDF: {str(e)}"
    
    def extract_url_content(self, url: str) -> Dict[str, Any]:
        """Extract content from a URL using web scraper."""
        if not pro_scraper:
            return {"status": "error", "message": "Web scraper not available"}
        
        try:
            # Use existing scraper
            if hasattr(pro_scraper, 'scrape_smart'):
                result = pro_scraper.scrape_smart(url)
            else:
                result = pro_scraper.scrape_url(url)
            
            if result.get("status") == "success":
                content = result.get("content", "") or result.get("text", "")
                title = result.get("title", "Untitled")
                
                return {
                    "status": "success",
                    "title": title,
                    "content": content,
                    "url": url,
                    "char_count": len(content)
                }
            else:
                return {"status": "error", "message": result.get("message", "Scraping failed")}
                
        except Exception as e:
            logger.error(f"[RAG] URL extraction error: {e}")
            return {"status": "error", "message": str(e)}
    
    # ==================== TEXT CHUNKING ====================
    
    def chunk_text(self, text: str, max_chars: int = 4000, overlap: int = 200) -> List[str]:
        """
        Split text into chunks for processing.
        Uses paragraph boundaries when possible.
        """
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # If paragraph is too long, split by sentences
                if len(para) > max_chars:
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    current_chunk = ""
                    for sent in sentences:
                        if len(current_chunk) + len(sent) <= max_chars:
                            current_chunk += sent + " "
                        else:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sent + " "
                else:
                    current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        logger.info(f"[RAG] Split text into {len(chunks)} chunks")
        return chunks
    
    def find_relevant_chunks(self, chunks: List[str], query: str, max_chunks: int = 3) -> List[str]:
        """
        Find the most relevant chunks for a query using keyword matching.
        Simple but effective for most use cases.
        """
        query_words = set(query.lower().split())
        
        # Score each chunk by keyword overlap
        scored_chunks = []
        for chunk in chunks:
            chunk_words = set(chunk.lower().split())
            score = len(query_words & chunk_words)
            scored_chunks.append((score, chunk))
        
        # Sort by score and return top chunks
        scored_chunks.sort(reverse=True, key=lambda x: x[0])
        return [chunk for score, chunk in scored_chunks[:max_chunks]]
    
    # ==================== DOCUMENT STORAGE ====================
    
    def save_document(self, title: str, content: str, doc_type: str, source_url: str = None) -> Dict[str, Any]:
        """Save document to Supabase and cache."""
        try:
            doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            doc_data = {
                "id": doc_id,
                "title": title,
                "content": content,
                "doc_type": doc_type,
                "source_url": source_url,
                "char_count": len(content),
                "created_at": datetime.now().isoformat()
            }
            
            # Save to Supabase
            if supabase_db:
                try:
                    supabase_db.client.table('rag_documents').insert({
                        "title": title,
                        "content": content,
                        "doc_type": doc_type,
                        "source_url": source_url,
                        "char_count": len(content)
                    }).execute()
                    logger.info(f"[RAG] Saved document to Supabase: {title}")
                except Exception as db_err:
                    logger.warning(f"[RAG] Supabase save failed: {db_err}")
            
            # Cache locally
            self.document_cache[doc_id] = doc_data
            self.active_document_id = doc_id
            
            return {
                "status": "success",
                "doc_id": doc_id,
                "title": title,
                "char_count": len(content),
                "message": f"Document '{title}' uploaded successfully ({len(content):,} characters)"
            }
            
        except Exception as e:
            logger.error(f"[RAG] Save document error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_document(self, doc_id: str = None) -> Optional[Dict[str, Any]]:
        """Get document from cache or Supabase."""
        # Use active document if no ID provided
        if not doc_id:
            doc_id = self.active_document_id
        
        if not doc_id:
            return None
        
        # Check cache first
        if doc_id in self.document_cache:
            return self.document_cache[doc_id]
        
        # Try Supabase
        if supabase_db:
            try:
                result = supabase_db.client.table('rag_documents').select('*').eq('id', doc_id).execute()
                if result.data:
                    doc = result.data[0]
                    self.document_cache[doc_id] = doc
                    return doc
            except Exception as e:
                logger.error(f"[RAG] Get document error: {e}")
        
        return None
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """List all uploaded documents."""
        docs = []
        
        # Add cached documents
        for doc_id, doc in self.document_cache.items():
            docs.append({
                "id": doc_id,
                "title": doc.get("title", "Untitled"),
                "doc_type": doc.get("doc_type", "unknown"),
                "char_count": doc.get("char_count", 0),
                "created_at": doc.get("created_at")
            })
        
        # Add from Supabase if available
        if supabase_db:
            try:
                result = supabase_db.client.table('rag_documents').select('id, title, doc_type, char_count, created_at').order('created_at', desc=True).limit(20).execute()
                if result.data:
                    for doc in result.data:
                        if doc.get("id") not in self.document_cache:
                            docs.append(doc)
            except Exception as e:
                logger.warning(f"[RAG] List documents from Supabase failed: {e}")
        
        return docs
    
    def delete_document(self, doc_id: str) -> Dict[str, Any]:
        """Delete a document."""
        try:
            # Remove from cache
            if doc_id in self.document_cache:
                del self.document_cache[doc_id]
            
            # Remove from Supabase
            if supabase_db:
                try:
                    supabase_db.client.table('rag_documents').delete().eq('id', doc_id).execute()
                except:
                    pass
            
            if self.active_document_id == doc_id:
                self.active_document_id = None
            
            return {"status": "success", "message": f"Document {doc_id} deleted"}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    # ==================== CHAT WITH DOCUMENT ====================
    
    def chat_with_document(self, query: str, doc_id: str = None) -> Dict[str, Any]:
        """
        Chat with a document using RAG.
        Injects document context into LLM prompt.
        """
        if not ChatCompletion:
            return {"status": "error", "message": "LLM not available"}
        
        # Get document
        doc = self.get_document(doc_id)
        if not doc:
            return {
                "status": "error", 
                "message": "No document found. Please upload a document first using 'add URL for chat: [url]' or upload a PDF."
            }
        
        content = doc.get("content", "")
        title = doc.get("title", "Document")
        
        # For large documents, find relevant chunks
        if len(content) > 6000:
            chunks = self.chunk_text(content)
            relevant_chunks = self.find_relevant_chunks(chunks, query)
            context = "\n\n---\n\n".join(relevant_chunks)
            context_note = f"(Showing {len(relevant_chunks)} relevant sections from {len(chunks)} total)"
        else:
            context = content
            context_note = ""
        
        # Build RAG prompt
        system_prompt = f"""You are a helpful AI assistant. Answer the user's question based on the following document.

DOCUMENT TITLE: {title}
{context_note}

DOCUMENT CONTENT:
{context[:8000]}

INSTRUCTIONS:
- Answer based on the document content above
- If the answer is not in the document, say so
- Be concise but thorough
- Quote relevant parts when helpful"""

        try:
            response = ChatCompletion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                model="llama-3.3-70b-versatile",
                text_only=True
            )
            
            return {
                "status": "success",
                "response": response,
                "document_title": title,
                "doc_id": doc.get("id")
            }
            
        except Exception as e:
            logger.error(f"[RAG] Chat error: {e}")
            return {"status": "error", "message": str(e)}
    
    # ==================== HIGH-LEVEL API ====================
    
    def upload_url(self, url: str) -> Dict[str, Any]:
        """Upload a URL for RAG."""
        logger.info(f"[RAG] Uploading URL: {url}")
        
        # Extract content
        result = self.extract_url_content(url)
        if result.get("status") != "success":
            return result
        
        # Save document
        return self.save_document(
            title=result.get("title", "Web Page"),
            content=result.get("content", ""),
            doc_type="url",
            source_url=url
        )
    
    def upload_pdf(self, file_path: str, title: str = None) -> Dict[str, Any]:
        """Upload a PDF for RAG."""
        logger.info(f"[RAG] Uploading PDF: {file_path}")
        
        if not os.path.exists(file_path):
            return {"status": "error", "message": "File not found"}
        
        # Extract text
        content = self.extract_pdf_text(file_path)
        if content.startswith("Error") or content.startswith("PDF extraction"):
            return {"status": "error", "message": content}
        
        # Determine title
        if not title:
            title = os.path.basename(file_path).replace('.pdf', '').replace('_', ' ').title()
        
        # Save document
        return self.save_document(
            title=title,
            content=content,
            doc_type="pdf"
        )
    
    def upload_text(self, text: str, title: str = "Text Document") -> Dict[str, Any]:
        """Upload raw text for RAG."""
        logger.info(f"[RAG] Uploading text: {title}")
        
        if not text or len(text) < 10:
            return {"status": "error", "message": "Text is too short"}
        
        return self.save_document(
            title=title,
            content=text,
            doc_type="text"
        )


# Global instance
document_rag = DocumentRAG()


if __name__ == "__main__":
    # Test
    print("Testing DocumentRAG...")
    
    # Test URL upload
    result = document_rag.upload_url("https://en.wikipedia.org/wiki/Python_(programming_language)")
    print(f"URL Upload: {result}")
    
    if result.get("status") == "success":
        # Test chat
        chat_result = document_rag.chat_with_document("What is Python used for?")
        print(f"\nChat Result: {chat_result.get('response', chat_result)[:500]}...")
