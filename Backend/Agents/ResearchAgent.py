"""
Research Agent - Web Search & Fact Finding Specialist
======================================================
Gathers information from the web, searches for facts, and provides verified data.
"""

import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

from Backend.Agents.BaseAgent import BaseAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """
    Specialist agent for web research and fact-finding.
    Uses web scraping and search to gather real information.
    """
    
    def __init__(self):
        super().__init__(
            name="Research Agent",
            specialty="Web research, fact-finding, data gathering",
            description="I search the web, gather facts, and provide verified information from real sources."
        )
        self._search = None
    
    @property
    def search(self):
        """Lazy load search functionality."""
        if self._search is None:
            try:
                from Backend.RealtimeSearchEngine import realtime_search
                self._search = realtime_search
            except Exception as e:
                logger.warning(f"[ResearchAgent] Search not available: {e}")
        return self._search
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute research task: search web, gather facts, summarize.
        """
        logger.info(f"[ResearchAgent] Starting research: {task[:50]}...")
        
        try:
            # Step 1: Determine search queries
            search_queries = self._generate_search_queries(task)
            
            # Step 2: Search the web
            search_results = self._perform_searches(search_queries)
            
            # Step 3: Synthesize findings
            synthesis = self._synthesize_findings(task, search_results)
            
            return {
                "status": "success",
                "agent": self.name,
                "output": synthesis,
                "sources": search_results.get("sources", []),
                "queries_used": search_queries,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[ResearchAgent] Error: {e}")
            # Fallback to LLM-only response
            fallback = self.think(f"Research this topic (use your knowledge): {task}")
            return {
                "status": "partial",
                "agent": self.name,
                "output": fallback,
                "note": "Used AI knowledge (web search unavailable)",
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_search_queries(self, task: str) -> List[str]:
        """Generate optimal search queries for the task."""
        prompt = f"""Generate 2-3 search queries to research this topic. 
Return ONLY the queries, one per line, no numbering or explanation.

Topic: {task}"""

        response = self.think(prompt)
        queries = [q.strip() for q in response.strip().split('\n') if q.strip()]
        return queries[:3]  # Max 3 queries
    
    def _perform_searches(self, queries: List[str]) -> Dict[str, Any]:
        """Search the web using available search tools."""
        all_results = []
        sources = []
        
        for query in queries:
            try:
                if self.search:
                    # Use realtime search
                    result = self.search(query)
                    if result and isinstance(result, str):
                        all_results.append(f"Search: {query}\nResults: {result[:1000]}")
                        sources.append({"query": query, "source": "web_search"})
            except Exception as e:
                logger.warning(f"[ResearchAgent] Search failed for '{query}': {e}")
        
        return {
            "results": "\n\n".join(all_results) if all_results else "No web results available",
            "sources": sources
        }
    
    def _synthesize_findings(self, task: str, search_results: Dict) -> str:
        """Synthesize search results into a coherent research summary."""
        prompt = f"""Based on the following research, provide a comprehensive answer to the task.

TASK: {task}

RESEARCH FINDINGS:
{search_results.get('results', 'No specific findings')}

Instructions:
- Synthesize the information into a clear, organized response
- Cite sources when possible
- If information is missing, note what couldn't be verified
- Be factual and objective"""

        return self.think(prompt)
    
    def quick_search(self, query: str) -> str:
        """Perform a quick single-query search."""
        results = self._perform_searches([query])
        return results.get("results", "No results found")


# Global instance
research_agent = ResearchAgent()
