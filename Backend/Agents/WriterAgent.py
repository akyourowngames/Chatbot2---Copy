"""
Writer Agent - Content Creation Specialist
==============================================
Creates high-quality written content: articles, reports, summaries, etc.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime

from Backend.Agents.BaseAgent import BaseAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """
    Specialist agent for content creation and writing.
    Creates articles, reports, summaries, and other written content.
    """
    
    def __init__(self):
        super().__init__(
            name="Writer Agent",
            specialty="Content creation, writing, summarization",
            description="I write high-quality content including articles, reports, summaries, and creative pieces."
        )
        
        self.writing_styles = {
            "professional": "formal, business-appropriate, clear and concise",
            "casual": "friendly, conversational, approachable",
            "academic": "scholarly, well-cited, analytical",
            "creative": "engaging, vivid, storytelling-focused",
            "technical": "precise, detailed, documentation-style"
        }
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute writing task with optional research context.
        """
        logger.info(f"[WriterAgent] Starting writing: {task[:50]}...")
        
        try:
            # Determine writing type and style
            writing_type = self._detect_writing_type(task)
            style = context.get("style", "professional") if context else "professional"
            
            # Get research context if provided
            research = context.get("research", "") if context else ""
            
            # Generate content
            content = self._write_content(task, writing_type, style, research)
            
            return {
                "status": "success",
                "agent": self.name,
                "output": content,
                "writing_type": writing_type,
                "style": style,
                "word_count": len(content.split()),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[WriterAgent] Error: {e}")
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _detect_writing_type(self, task: str) -> str:
        """Detect what type of content to write."""
        task_lower = task.lower()
        
        if any(word in task_lower for word in ["article", "blog", "post"]):
            return "article"
        elif any(word in task_lower for word in ["report", "analysis"]):
            return "report"
        elif any(word in task_lower for word in ["summary", "summarize"]):
            return "summary"
        elif any(word in task_lower for word in ["email", "letter"]):
            return "email"
        elif any(word in task_lower for word in ["story", "creative"]):
            return "creative"
        else:
            return "general"
    
    def _write_content(self, task: str, writing_type: str, style: str, research: str = "") -> str:
        """Generate written content based on parameters."""
        style_guide = self.writing_styles.get(style, self.writing_styles["professional"])
        
        prompt = f"""You are a professional writer creating {writing_type} content.

TASK: {task}

STYLE GUIDE: {style_guide}

{f'RESEARCH/CONTEXT TO USE:{chr(10)}{research}' if research else ''}

INSTRUCTIONS:
1. Create well-structured, engaging content
2. Follow the style guide
3. Include appropriate headings if needed
4. Make it comprehensive but not verbose
5. End with a strong conclusion

Write the content now:"""

        return self.think(prompt)
    
    def summarize(self, text: str, max_sentences: int = 5) -> str:
        """Summarize given text."""
        prompt = f"""Summarize the following text in {max_sentences} sentences or less.
Keep the key points and main ideas.

TEXT:
{text}

SUMMARY:"""
        return self.think(prompt)
    
    def rewrite(self, text: str, style: str = "professional") -> str:
        """Rewrite text in a different style."""
        style_guide = self.writing_styles.get(style, "clear and professional")
        prompt = f"""Rewrite the following text in a {style} style ({style_guide}).
Keep the meaning but change the tone and style.

ORIGINAL:
{text}

REWRITTEN:"""
        return self.think(prompt)
    
    def expand(self, text: str, target_words: int = 500) -> str:
        """Expand short text into longer content."""
        prompt = f"""Expand the following text into approximately {target_words} words.
Add more details, examples, and explanation while keeping the original meaning.

ORIGINAL:
{text}

EXPANDED VERSION:"""
        return self.think(prompt)


# Global instance
writer_agent = WriterAgent()
