"""
Research Agent - Autonomous Web Researcher
==========================================
Uses the ReAct pattern to conduct deep web research.
Can formulate multiple queries, read pages, and synthesize information autonomously.
"""

from Backend.Agents.AutonomousAgent import AutonomousAgent, Tool
import logging

logger = logging.getLogger(__name__)

class ResearchAgent(AutonomousAgent):
    """
    Autonomous ReAct agent for web research.
    """
    def __init__(self):
        super().__init__(
            name="Research Agent",
            specialty="Web research, fact-finding, deep analysis",
            description="I search the web, read pages, and verify facts autonomously. I can refine my search if initial results are poor."
        )
        # Register tools
        self._register_research_tools()
        
    def _register_research_tools(self):
        """Register the specific tools for this agent."""
        
        # Tool 1: Search
        def search_tool(params: str):
            """Search the web. Params: query string"""
            # Clean up params
            query = params.strip('"').strip("'")
            if self.scraper:
                 # Use the simple search or scraper based on what's available
                 # For now, let's use the property scraper's capabilities or import specialized search
                 try:
                     # Accessing the lazy-loaded scraper
                     # Assuming scraper has a search method or we use RealtimeSearch
                     from Backend.RealtimeSearchEngine import realtime_search
                     return realtime_search(query)
                 except Exception as e:
                     return f"Search Error: {e}"
            return "Search unavailable"

        self.register_tool(
            name="search", 
            func=search_tool, 
            description="Search Google/Web for a query.",
            parameters="query: str"
        )
        
        # Tool 2: Read Page (Deep scrape)
        def read_page(params: str):
            """Reader a specific URL. Params: url string"""
            url = params.strip('"').strip("'")
            if self.scraper:
                try:
                    return self.scraper.scrape(url)
                except Exception as e:
                    return f"Scrape Error: {e}"
            return "Scraper unavailable"
            
        self.register_tool(
            name="read_page",
            func=read_page,
            description="Read the content of a specific URL found in search results.",
            parameters="url: str"
        )

# Global instance
research_agent = ResearchAgent()
