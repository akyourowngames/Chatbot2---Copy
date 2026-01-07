"""
Analyst Agent - Review, Analysis & Quality Control Specialist
==============================================================
Reviews content, provides feedback, and ensures quality.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

from Backend.Agents.BaseAgent import BaseAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """
    Specialist agent for analysis, review, and quality control.
    Reviews work from other agents and provides improvements.
    """
    
    def __init__(self):
        super().__init__(
            name="Analyst Agent",
            specialty="Analysis, review, quality control, fact-checking",
            description="I analyze content, review for quality, check facts, and suggest improvements."
        )
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute analysis task: review content and provide feedback.
        """
        logger.info(f"[AnalystAgent] Starting analysis: {task[:50]}...")
        
        try:
            content_to_review = context.get("content", "") if context else ""
            
            if content_to_review:
                # Review provided content
                analysis = self._review_content(content_to_review, task)
            else:
                # General analysis task
                analysis = self._analyze_topic(task)
            
            return {
                "status": "success",
                "agent": self.name,
                "output": analysis,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[AnalystAgent] Error: {e}")
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _review_content(self, content: str, task: str) -> str:
        """Review content and provide feedback."""
        prompt = f"""You are a quality analyst reviewing content.

TASK: {task}

CONTENT TO REVIEW:
{content[:3000]}

Provide a thorough review including:
1. STRENGTHS: What's good about this content
2. WEAKNESSES: What could be improved
3. ACCURACY: Any potential factual issues or claims to verify
4. SUGGESTIONS: Specific improvements
5. REVISED VERSION: If applicable, provide an improved version

Be constructive and specific in your feedback."""

        return self.think(prompt)
    
    def _analyze_topic(self, topic: str) -> str:
        """Provide analysis on a topic."""
        prompt = f"""Provide a thorough analysis of: {topic}

Include:
1. KEY POINTS: Main aspects to consider
2. PROS AND CONS: Advantages and disadvantages
3. TRENDS: Current developments
4. RECOMMENDATIONS: What actions to take
5. CONCLUSION: Summary of findings

Be analytical and objective."""

        return self.think(prompt)
    
    def fact_check(self, claims: str) -> str:
        """Fact-check claims in content."""
        prompt = f"""Fact-check the following claims. For each claim:
- Mark as LIKELY TRUE, NEEDS VERIFICATION, or LIKELY FALSE
- Explain your reasoning
- Note if you're uncertain

CLAIMS TO CHECK:
{claims}

FACT-CHECK RESULTS:"""
        return self.think(prompt)
    
    def improve(self, content: str) -> str:
        """Improve given content."""
        prompt = f"""Improve the following content. Make it:
- Clearer and more concise
- Better structured
- More engaging
- More accurate

ORIGINAL:
{content}

IMPROVED VERSION:"""
        return self.think(prompt)
    
    def compare(self, item1: str, item2: str, criteria: str = "") -> str:
        """Compare two items."""
        prompt = f"""Compare these two items{f' based on: {criteria}' if criteria else ''}:

ITEM 1:
{item1}

ITEM 2:
{item2}

Provide a detailed comparison including:
1. Similarities
2. Differences
3. Strengths of each
4. Which is better for what purpose
5. Recommendation"""
        return self.think(prompt)


# Global instance
analyst_agent = AnalystAgent()
