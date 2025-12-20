"""
DocumentRAG - Chat with Documents Feature (NEXT LEVEL)
=======================================================
Upload PDFs, text files, URLs, or YouTube videos and chat with their content using AI.

NEXT-LEVEL Features:
- Multi-document chat (combine context from multiple docs)
- Auto-summary on upload
- YouTube transcript extraction
- Citation support (show source references)
- Improved chunk relevance scoring
- Conversation memory for follow-up questions
- Document comparison
- Suggested questions per document
"""

import os
import re
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import logging
import hashlib

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
    RAG (Retrieval-Augmented Generation) for documents - NEXT LEVEL.
    Allows users to upload documents and chat with their content using AI.
    """
    
    def __init__(self):
        self.temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "RAG")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # In-memory document cache for fast access
        self.document_cache: Dict[str, Dict[str, Any]] = {}
        
        # Active document(s) for chat context - supports multiple
        self.active_document_ids: List[str] = []
        
        # Conversation memory for follow-up questions
        self.conversation_history: List[Dict[str, str]] = []
        self.max_history = 5  # Keep last 5 exchanges
        
        logger.info("[RAG] DocumentRAG NEXT LEVEL initialized")
    
    # ==================== YOUTUBE TRANSCRIPT EXTRACTION ====================
    
    def extract_youtube_transcript(self, url: str) -> Dict[str, Any]:
        """
        Extract transcript from YouTube video.
        Uses YouTube's API or third-party services.
        """
        try:
            # Extract video ID from URL
            video_id = None
            patterns = [
                r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
                r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    video_id = match.group(1)
                    break
            
            if not video_id:
                return {"status": "error", "message": "Could not extract YouTube video ID"}
            
            # Try to get transcript via youtube-transcript-api (if installed)
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                
                # Combine transcript segments
                full_transcript = " ".join([segment['text'] for segment in transcript_list])
                
                # Get video title via simple request
                title = f"YouTube Video ({video_id})"
                try:
                    import requests
                    response = requests.get(f"https://www.youtube.com/watch?v={video_id}", timeout=10)
                    title_match = re.search(r'<title>(.+?) - YouTube</title>', response.text)
                    if title_match:
                        title = title_match.group(1)
                except:
                    pass
                
                return {
                    "status": "success",
                    "title": title,
                    "content": full_transcript,
                    "video_id": video_id,
                    "url": url,
                    "char_count": len(full_transcript)
                }
                
            except ImportError:
                # Fallback: Use web scraping to get basic info
                if pro_scraper:
                    result = pro_scraper.scrape_smart(url) if hasattr(pro_scraper, 'scrape_smart') else pro_scraper.scrape_url(url)
                    if result.get("status") == "success":
                        return {
                            "status": "success",
                            "title": result.get("title", f"YouTube Video ({video_id})"),
                            "content": result.get("content", "Transcript not available - install youtube-transcript-api for full transcript support"),
                            "video_id": video_id,
                            "url": url,
                            "char_count": len(result.get("content", ""))
                        }
                
                return {"status": "error", "message": "YouTube transcript extraction requires youtube-transcript-api package"}
                
        except Exception as e:
            logger.error(f"[RAG] YouTube extraction error: {e}")
            return {"status": "error", "message": str(e)}
    
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
    
    def download_and_extract_pdf(self, url: str) -> Dict[str, Any]:
        """
        Download PDF from URL (including Supabase Storage) and extract text.
        Solves the "cannot access external private assets" issue.
        """
        try:
            import requests
            import tempfile
            
            logger.info(f"[RAG] Downloading PDF from: {url[:80]}...")
            
            # Download PDF
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=60, stream=True)
            
            if response.status_code != 200:
                return {"status": "error", "message": f"Failed to download PDF: HTTP {response.status_code}"}
            
            # Check if it's actually a PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower() and not url.lower().endswith('.pdf'):
                return {"status": "error", "message": f"URL does not point to a PDF file"}
            
            # Save to temp file
            temp_path = os.path.join(self.temp_dir, f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"[RAG] Downloaded PDF to: {temp_path}")
            
            # Extract text
            content = self.extract_pdf_text(temp_path)
            
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
            
            if content.startswith("Error") or content.startswith("PDF extraction"):
                return {"status": "error", "message": content}
            
            # Extract title from URL
            title = url.split('/')[-1].replace('.pdf', '').replace('_', ' ').replace('%20', ' ')
            if len(title) > 50:
                title = title[:50] + "..."
            
            return {
                "status": "success",
                "title": title,
                "content": content,
                "url": url,
                "char_count": len(content),
                "doc_type": "pdf"
            }
            
        except Exception as e:
            logger.error(f"[RAG] PDF download error: {e}")
            return {"status": "error", "message": str(e)}
    
    def extract_url_content(self, url: str) -> Dict[str, Any]:
        """Extract content from a URL using web scraper."""
        # Check if it's a YouTube URL
        if 'youtube.com' in url or 'youtu.be' in url:
            return self.extract_youtube_transcript(url)
        
        # Check if it's a PDF URL (including Supabase Storage)
        if url.lower().endswith('.pdf') or 'supabase' in url.lower() and '.pdf' in url.lower():
            return self.download_and_extract_pdf(url)

        
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
    
    # ==================== AUTO-SUMMARY ====================
    
    def generate_auto_summary(self, content: str, title: str) -> Dict[str, Any]:
        """Generate automatic summary and suggested questions when document is uploaded."""
        if not ChatCompletion:
            return {"summary": None, "suggested_questions": []}
        
        try:
            # Use only first 4000 chars for summary to save tokens
            truncated = content[:4000] if len(content) > 4000 else content
            
            prompt = f"""Analyze this document and provide:
1. A 2-3 sentence summary
2. 3 specific questions someone might ask about this document

DOCUMENT TITLE: {title}

CONTENT:
{truncated}

Respond in this exact format:
SUMMARY: [your summary here]
QUESTIONS:
- [question 1]
- [question 2]
- [question 3]"""

            response = ChatCompletion(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                text_only=True
            )
            
            # Parse response
            summary = ""
            questions = []
            
            if "SUMMARY:" in response:
                summary_match = re.search(r'SUMMARY:\s*(.+?)(?=QUESTIONS:|$)', response, re.DOTALL)
                if summary_match:
                    summary = summary_match.group(1).strip()
            
            question_matches = re.findall(r'-\s*(.+?)(?=\n|$)', response)
            questions = [q.strip() for q in question_matches[:3]]
            
            return {
                "summary": summary,
                "suggested_questions": questions
            }
            
        except Exception as e:
            logger.warning(f"[RAG] Auto-summary failed: {e}")
            return {"summary": None, "suggested_questions": []}
    
    # ==================== TEXT CHUNKING WITH CITATIONS ====================
    
    def chunk_text_with_refs(self, text: str, max_chars: int = 3000) -> List[Dict[str, Any]]:
        """
        Split text into chunks with citation references.
        Each chunk has an ID for citation purposes.
        """
        if len(text) <= max_chars:
            return [{"id": "chunk_1", "content": text, "start": 0, "end": len(text)}]
        
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = ""
        current_start = 0
        chunk_num = 1
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append({
                        "id": f"chunk_{chunk_num}",
                        "content": current_chunk.strip(),
                        "start": current_start,
                        "end": current_start + len(current_chunk)
                    })
                    chunk_num += 1
                    current_start += len(current_chunk)
                
                if len(para) > max_chars:
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    current_chunk = ""
                    for sent in sentences:
                        if len(current_chunk) + len(sent) <= max_chars:
                            current_chunk += sent + " "
                        else:
                            if current_chunk:
                                chunks.append({
                                    "id": f"chunk_{chunk_num}",
                                    "content": current_chunk.strip(),
                                    "start": current_start,
                                    "end": current_start + len(current_chunk)
                                })
                                chunk_num += 1
                                current_start += len(current_chunk)
                            current_chunk = sent + " "
                else:
                    current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append({
                "id": f"chunk_{chunk_num}",
                "content": current_chunk.strip(),
                "start": current_start,
                "end": current_start + len(current_chunk)
            })
        
        logger.info(f"[RAG] Split text into {len(chunks)} chunks with references")
        return chunks
    
    def find_relevant_chunks_scored(self, chunks: List[Dict[str, Any]], query: str, max_chunks: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        """
        Find most relevant chunks with improved scoring.
        Returns chunks with their relevance scores.
        """
        query_words = set(query.lower().split())
        # Remove common words
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 'when', 'where', 'who', 'which', 'this', 'that', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'but'}
        query_words = query_words - stopwords
        
        scored_chunks = []
        for chunk in chunks:
            content = chunk["content"].lower()
            chunk_words = set(content.split()) - stopwords
            
            # Calculate multiple scoring factors
            word_overlap = len(query_words & chunk_words)
            
            # Bonus for exact phrase matches
            phrase_bonus = 0
            for word in query_words:
                if word in content:
                    phrase_bonus += 0.5
            
            # Bonus for query words appearing multiple times
            frequency_bonus = sum(content.count(word) for word in query_words) * 0.1
            
            total_score = word_overlap + phrase_bonus + frequency_bonus
            if total_score > 0:
                scored_chunks.append((chunk, total_score))
        
        # Sort by score and return top chunks
        scored_chunks.sort(reverse=True, key=lambda x: x[1])
        return scored_chunks[:max_chunks]
    
    # ==================== DOCUMENT STORAGE ====================
    
    def save_document(self, title: str, content: str, doc_type: str, source_url: str = None, auto_summarize: bool = True) -> Dict[str, Any]:
        """Save document with auto-summary to Supabase and cache."""
        try:
            doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:19]}"
            
            # Generate auto-summary and suggested questions
            summary_data = {"summary": None, "suggested_questions": []}
            if auto_summarize and ChatCompletion:
                summary_data = self.generate_auto_summary(content, title)
            
            # Create chunks with references
            chunks = self.chunk_text_with_refs(content)
            
            doc_data = {
                "id": doc_id,
                "title": title,
                "content": content,
                "doc_type": doc_type,
                "source_url": source_url,
                "char_count": len(content),
                "chunk_count": len(chunks),
                "chunks": chunks,
                "summary": summary_data.get("summary"),
                "suggested_questions": summary_data.get("suggested_questions", []),
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
                        "char_count": len(content),
                        "summary": summary_data.get("summary")
                    }).execute()
                    logger.info(f"[RAG] Saved document to Supabase: {title}")
                except Exception as db_err:
                    logger.warning(f"[RAG] Supabase save failed: {db_err}")
            
            # Cache locally
            self.document_cache[doc_id] = doc_data
            
            # Add to active documents
            if doc_id not in self.active_document_ids:
                self.active_document_ids.append(doc_id)
            
            return {
                "status": "success",
                "doc_id": doc_id,
                "title": title,
                "char_count": len(content),
                "chunk_count": len(chunks),
                "summary": summary_data.get("summary"),
                "suggested_questions": summary_data.get("suggested_questions", []),
                "message": f"✅ Document '{title}' uploaded ({len(content):,} chars, {len(chunks)} sections)"
            }
            
        except Exception as e:
            logger.error(f"[RAG] Save document error: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_document(self, doc_id: str = None) -> Optional[Dict[str, Any]]:
        """Get document from cache or Supabase."""
        if not doc_id:
            doc_id = self.active_document_ids[-1] if self.active_document_ids else None
        
        if not doc_id:
            return None
        
        if doc_id in self.document_cache:
            return self.document_cache[doc_id]
        
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
        
        for doc_id, doc in self.document_cache.items():
            docs.append({
                "id": doc_id,
                "title": doc.get("title", "Untitled"),
                "doc_type": doc.get("doc_type", "unknown"),
                "char_count": doc.get("char_count", 0),
                "summary": doc.get("summary"),
                "is_active": doc_id in self.active_document_ids,
                "created_at": doc.get("created_at")
            })
        
        if supabase_db:
            try:
                result = supabase_db.client.table('rag_documents').select('id, title, doc_type, char_count, summary, created_at').order('created_at', desc=True).limit(20).execute()
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
            if doc_id in self.document_cache:
                del self.document_cache[doc_id]
            
            if supabase_db:
                try:
                    supabase_db.client.table('rag_documents').delete().eq('id', doc_id).execute()
                except:
                    pass
            
            if doc_id in self.active_document_ids:
                self.active_document_ids.remove(doc_id)
            
            return {"status": "success", "message": f"Document {doc_id} deleted"}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def set_active_documents(self, doc_ids: List[str]) -> Dict[str, Any]:
        """Set multiple documents as active for multi-document chat."""
        self.active_document_ids = doc_ids
        return {"status": "success", "active_documents": doc_ids}
    
    # ==================== CHAT WITH DOCUMENT(S) ====================
    
    def chat_with_document(self, query: str, doc_id: str = None, include_citations: bool = True) -> Dict[str, Any]:
        """
        Chat with document(s) using RAG.
        Supports multi-document chat, citations, and conversation memory.
        """
        if not ChatCompletion:
            return {"status": "error", "message": "LLM not available"}
        
        # Determine which documents to use
        doc_ids = [doc_id] if doc_id else self.active_document_ids
        
        if not doc_ids:
            return {
                "status": "error", 
                "message": "No document found. Please upload a document first using 'add URL for chat: [url]' or upload a PDF."
            }
        
        # Gather context from all active documents
        all_context = []
        doc_titles = []
        all_citations = []
        
        for did in doc_ids:
            doc = self.get_document(did)
            if not doc:
                continue
            
            content = doc.get("content", "")
            title = doc.get("title", "Document")
            doc_titles.append(title)
            
            # Get chunks with references
            chunks = doc.get("chunks") or self.chunk_text_with_refs(content)
            relevant = self.find_relevant_chunks_scored(chunks, query, max_chunks=2)
            
            for chunk, score in relevant:
                all_context.append(f"[Source: {title}, Section {chunk['id']}]\n{chunk['content']}")
                all_citations.append({
                    "document": title,
                    "section": chunk['id'],
                    "relevance": round(score, 2)
                })
        
        if not all_context:
            return {"status": "error", "message": "No relevant content found in documents"}
        
        # Build conversation history context
        history_context = ""
        if self.conversation_history:
            history_context = "\n\nPREVIOUS CONVERSATION:\n"
            for exchange in self.conversation_history[-3:]:  # Last 3 exchanges
                history_context += f"User: {exchange['query']}\nAssistant: {exchange['response'][:200]}...\n"
        
        # Build RAG prompt with citations instruction
        combined_context = "\n\n---\n\n".join(all_context[:6])  # Max 6 sections
        
        system_prompt = f"""You are a helpful AI assistant. Answer the user's question based on the provided document content.

DOCUMENTS: {', '.join(doc_titles)}
{history_context}

RELEVANT DOCUMENT SECTIONS:
{combined_context}

INSTRUCTIONS:
- Answer based on the document content above
- {"Reference the source section when citing specific information (e.g., 'According to Section chunk_1...')" if include_citations else ""}
- If the answer is not in the document, say so
- Be concise but thorough
- Consider the conversation history for context"""

        try:
            response = ChatCompletion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                model="llama-3.3-70b-versatile",
                text_only=True
            )
            
            # Store in conversation history
            self.conversation_history.append({
                "query": query,
                "response": response
            })
            if len(self.conversation_history) > self.max_history:
                self.conversation_history.pop(0)
            
            result = {
                "status": "success",
                "response": response,
                "documents_used": doc_titles,
                "doc_count": len(doc_titles)
            }
            
            if include_citations:
                result["citations"] = all_citations
            
            return result
            
        except Exception as e:
            logger.error(f"[RAG] Chat error: {e}")
            return {"status": "error", "message": str(e)}
    
    def compare_documents(self, doc_id1: str, doc_id2: str, aspect: str = None) -> Dict[str, Any]:
        """Compare two documents."""
        if not ChatCompletion:
            return {"status": "error", "message": "LLM not available"}
        
        doc1 = self.get_document(doc_id1)
        doc2 = self.get_document(doc_id2)
        
        if not doc1 or not doc2:
            return {"status": "error", "message": "One or both documents not found"}
        
        prompt = f"""Compare these two documents{' focusing on: ' + aspect if aspect else ''}:

DOCUMENT 1: {doc1.get('title')}
{doc1.get('content', '')[:3000]}

DOCUMENT 2: {doc2.get('title')}
{doc2.get('content', '')[:3000]}

Provide a clear comparison highlighting:
1. Key similarities
2. Key differences
3. Summary of each document's main points"""

        try:
            response = ChatCompletion(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                text_only=True
            )
            
            return {
                "status": "success",
                "comparison": response,
                "documents": [doc1.get('title'), doc2.get('title')]
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def clear_conversation(self) -> Dict[str, Any]:
        """Clear conversation history for fresh start."""
        self.conversation_history = []
        return {"status": "success", "message": "Conversation history cleared"}
    
    # ==================== HIGH-LEVEL API ====================
    
    def upload_url(self, url: str) -> Dict[str, Any]:
        """Upload a URL for RAG (auto-detects YouTube)."""
        logger.info(f"[RAG] Uploading URL: {url}")
        
        result = self.extract_url_content(url)
        if result.get("status") != "success":
            return result
        
        doc_type = "youtube" if result.get("video_id") else "url"
        
        return self.save_document(
            title=result.get("title", "Web Page"),
            content=result.get("content", ""),
            doc_type=doc_type,
            source_url=url
        )
    
    def upload_pdf(self, file_path: str, title: str = None) -> Dict[str, Any]:
        """Upload a PDF for RAG."""
        logger.info(f"[RAG] Uploading PDF: {file_path}")
        
        if not os.path.exists(file_path):
            return {"status": "error", "message": "File not found"}
        
        content = self.extract_pdf_text(file_path)
        if content.startswith("Error") or content.startswith("PDF extraction"):
            return {"status": "error", "message": content}
        
        if not title:
            title = os.path.basename(file_path).replace('.pdf', '').replace('_', ' ').title()
        
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
    print("Testing DocumentRAG NEXT LEVEL...")
    
    # Test URL upload with auto-summary
    result = document_rag.upload_url("https://en.wikipedia.org/wiki/Python_(programming_language)")
    print(f"URL Upload: {result}")
    
    if result.get("status") == "success":
        print(f"\n📝 Summary: {result.get('summary')}")
        print(f"❓ Suggested Questions: {result.get('suggested_questions')}")
        
        # Test chat with citations
        chat_result = document_rag.chat_with_document("What is Python used for?")
        print(f"\n💬 Chat Result: {chat_result.get('response', '')[:500]}...")
        print(f"📚 Citations: {chat_result.get('citations', [])}")

