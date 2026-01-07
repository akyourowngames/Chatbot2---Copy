"""
Document Analysis Agent - Deep PDF/DOCX Analysis
================================================
Analyzes documents beyond simple text extraction - structure, entities, insights.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import re

from Backend.Agents.BaseAgent import BaseAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentAnalysisAgent(BaseAgent):
    """
    Agent specialized in deep document analysis.
    Goes beyond text extraction to analyze structure, extract entities, and summarize.
    """
    
    def __init__(self):
        super().__init__(
            name="DocAnalyst",
            specialty="Document analysis and insight extraction",
            description="I analyze PDFs and DOCX files to extract structure, entities, and key insights"
        )
        self._doc_rag = None
        self._doc_reader = None
        logger.info("[DOC-AGENT] Initialized")
    
    @property
    def doc_rag(self):
        """Lazy load DocumentRAG."""
        if self._doc_rag is None:
            try:
                from Backend.DocumentRAG import DocumentRAG
                self._doc_rag = DocumentRAG()
            except Exception as e:
                logger.error(f"[DOC-AGENT] Failed to load DocumentRAG: {e}")
        return self._doc_rag
    
    @property
    def doc_reader(self):
        """Lazy load DocumentReader."""
        if self._doc_reader is None:
            try:
                from Backend.DocumentReader import DocumentReader
                self._doc_reader = DocumentReader()
            except Exception as e:
                logger.error(f"[DOC-AGENT] Failed to load DocumentReader: {e}")
        return self._doc_reader
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute document analysis task.
        
        Args:
            task: What to analyze (includes file path or analysis type)
            context: Optional context with file_path, analysis_type, etc.
            
        Returns:
            Analysis results
        """
        try:
            logger.info(f"[DOC-AGENT] Analyzing: {task[:50]}...")
            
            # Extract file path and analysis type
            file_path = self._extract_file_path(task, context)
            analysis_type = self._determine_analysis_type(task, context)
            
            if not file_path:
                return {
                    "status": "error",
                    "agent": self.name,
                    "error": "No file path provided",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Perform analysis based on type
            if analysis_type == "structure":
                result = self._analyze_structure(file_path, task)
            elif analysis_type == "entities":
                result = self._extract_entities(file_path, task)
            elif analysis_type == "summary":
                result = self._summarize_document(file_path, task)
            elif analysis_type == "qa":
                question = context.get("question", task)
                result = self._answer_question(file_path, question)
            elif analysis_type == "compare":
                file_path2 = context.get("file_path2")
                result = self._compare_documents(file_path, file_path2, task)
            else:
                # Full analysis
                result = self._full_analysis(file_path, task)
            
            return {
                "status": "success",
                "agent": self.name,
                "task": task,
                "file_path": file_path,
                "analysis_type": analysis_type,
                "output": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[DOC-AGENT] Analysis error: {e}")
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _extract_file_path(self, task: str, context: Dict[str, Any]) -> Optional[str]:
        """Extract file path from task or context."""
        if context and "file_path" in context:
            return context["file_path"]
        
        # Try to find file path in task
        import re
        # Match common file patterns
        patterns = [
            r'[\w\-\\\/:.]+\.pdf',
            r'[\w\-\\\/:.]+\.docx?',
            r'[\w\-\\\/:.]+\.txt'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                return match.group()
        
        return None
    
    def _determine_analysis_type(self, task: str, context: Dict[str, Any]) -> str:
        """Determine what type of analysis to perform."""
        if context and "analysis_type" in context:
            return context["analysis_type"]
        
        task_lower = task.lower()
        
        if any(word in task_lower for word in ["structure", "sections", "headings", "outline"]):
            return "structure"
        elif any(word in task_lower for word in ["entities", "extract", "names", "dates"]):
            return "entities"
        elif any(word in task_lower for word in ["summary", "summarize", "overview"]):
            return "summary"
        elif any(word in task_lower for word in ["question", "what", "how", "why", "when", "where"]):
            return "qa"
        elif any(word in task_lower for word in ["compare", "difference", "versus", "vs"]):
            return "compare"
        else:
            return "full"
    
    def _analyze_structure(self, file_path: str, task: str) -> str:
        """Analyze document structure."""
        if not self.doc_reader:
            return "DocumentReader not available"
        
        try:
            # Read document
            content = self.doc_reader.read(file_path)
            
            # Analyze structure with AI
            if self.llm:
                prompt = f"""Analyze the structure of this document and provide:
1. Main sections/headings
2. Document type (contract, report, article, etc.)
3. Key structural elements (tables, lists, etc.)
4. Organization pattern

DOCUMENT SAMPLE (first 3000 chars):
{content[:3000]}

Provide a structured analysis:"""
                
                analysis = self.llm(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    inject_memory=False
                )
                return analysis.strip()
            else:
                # Basic structure detection
                lines = content.split('\n')
                return f"Document has {len(lines)} lines and approximately {len(content.split())} words."
                
        except Exception as e:
            return f"Structure analysis failed: {e}"
    
    def _extract_entities(self, file_path: str, task: str) -> str:
        """Extract named entities from document."""
        if not self.doc_reader:
            return "DocumentReader not available"
        
        try:
            content = self.doc_reader.read(file_path)
            
            if self.llm:
                prompt = f"""Extract key entities from this document:
- People names
- Organizations
- Locations
- Dates
- Numbers/amounts
- Key terms

DOCUMENT:
{content[:4000]}

List the extracted entities by category:"""
                
                entities = self.llm(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    inject_memory=False
                )
                return entities.strip()
            else:
                # Simple regex-based extraction
                dates = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', content)
                emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
                return f"Found {len(dates)} dates and {len(emails)} emails."
                
        except Exception as e:
            return f"Entity extraction failed: {e}"
    
    def _summarize_document(self, file_path: str, task: str) -> str:
        """Summarize document content."""
        if not self.doc_reader:
            return "DocumentReader not available"
        
        try:
            content = self.doc_reader.read(file_path)
            
            if self.llm:
                prompt = f"""Provide a concise summary of this document.

DOCUMENT:
{content[:5000]}

Summary (3-5 key points):"""
                
                summary = self.llm(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    inject_memory=False
                )
                return summary.strip()
            else:
                return f"Document contains {len(content.split())} words."
                
        except Exception as e:
            return f"Summarization failed: {e}"
    
    def _answer_question(self, file_path: str, question: str) -> str:
        """Answer questions about the document."""
        if not self.doc_rag:
            # Fallback to simple Q&A
            if not self.doc_reader:
                return "Document analysis tools not available"
            
            content = self.doc_reader.read(file_path)
            
            if self.llm:
                prompt = f"""Answer this question based on the document:

QUESTION: {question}

DOCUMENT:
{content[:4000]}

Answer:"""
                
                answer = self.llm(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    inject_memory=False
                )
                return answer.strip()
            return "LLM not available"
        
        try:
            # Use DocumentRAG for better Q&A
            result = self.doc_rag.query(question, file_path)
            return result.get("answer", "Could not find answer")
        except Exception as e:
            return f"Q&A failed: {e}"
    
    def _compare_documents(self, file_path1: str, file_path2: str, task: str) -> str:
        """Compare two documents."""
        if not self.doc_reader:
            return "DocumentReader not available"
        
        try:
            content1 = self.doc_reader.read(file_path1)[:3000]
            content2 = self.doc_reader.read(file_path2)[:3000] if file_path2 else ""
            
            if not file_path2:
                return "Second document path not provided"
            
            if self.llm:
                prompt = f"""Compare these two documents and identify:
1. Key similarities
2. Main differences
3. Which document is more comprehensive

DOCUMENT 1:
{content1}

DOCUMENT 2:
{content2}

Comparison:"""
                
                comparison = self.llm(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    inject_memory=False
                )
                return comparison.strip()
            else:
                return f"Doc1: {len(content1.split())} words, Doc2: {len(content2.split())} words"
                
        except Exception as e:
            return f"Comparison failed: {e}"
    
    def _full_analysis(self, file_path: str, task: str) -> str:
        """Perform comprehensive document analysis."""
        results = []
        
        # Run all analyses
        results.append("=" * 50)
        results.append("FULL DOCUMENT ANALYSIS")
        results.append("=" * 50)
        
        results.append("\n📋 STRUCTURE ANALYSIS:")
        results.append(self._analyze_structure(file_path, task))
        
        results.append("\n\n🏷️ ENTITY EXTRACTION:")
        results.append(self._extract_entities(file_path, task))
        
        results.append("\n\n📝 SUMMARY:")
        results.append(self._summarize_document(file_path, task))
        
        return "\n".join(results)


# Global instance
document_analysis_agent = DocumentAnalysisAgent()


# Convenience function
def analyze_document(file_path: str, analysis_type: str = "full", question: str = None) -> Dict[str, Any]:
    """Analyze a document."""
    context = {
        "file_path": file_path,
        "analysis_type": analysis_type
    }
    if question:
        context["question"] = question
    
    task = f"Analyze {file_path}"
    if analysis_type != "full":
        task = f"{analysis_type.title()} analysis of {file_path}"
    
    return document_analysis_agent.execute(task, context)


# Test
if __name__ == "__main__":
    print("📄 Testing Document Analysis Agent\n")
    print("Note: Requires a test document file to fully test")
    print("Available analysis types: structure, entities, summary, qa, compare, full")
