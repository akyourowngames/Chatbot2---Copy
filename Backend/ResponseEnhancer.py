"""
Response Enhancer - Quality Post-Processing
============================================
Enhances AI responses for better quality:
- Format with markdown
- Remove filler/redundancy
- Add structure
- Ensure completeness
"""

import re
from typing import Dict, Any, Optional


class ResponseEnhancer:
    """
    Post-process AI responses to improve quality and readability.
    """
    
    # Filler patterns to remove
    FILLER_PATTERNS = [
        r"^(Sure,?\s*|Of course,?\s*|Certainly,?\s*|Absolutely,?\s*)",
        r"^(I'd be happy to\s*|I'd love to\s*|Let me\s*)",
        r"^(Here's|Here is)\s*(the\s*)?(answer|response|information)[:\s]*",
        r"\bif you have any (more\s*)?(questions|queries)\b.*$",
        r"\bfeel free to ask\b.*$",
        r"\bhope (this|that) helps\b.*$",
        r"\blet me know if you need\b.*$",
    ]
    
    # Redundant phrases
    REDUNDANT_PHRASES = [
        "As an AI language model,",
        "As a large language model,",
        "I don't have personal opinions, but",
        "I cannot provide personal advice, however",
        "It's important to note that",
        "It's worth mentioning that",
        "In conclusion,",
        "To summarize,",
        "In summary,",
    ]
    
    def __init__(self):
        self.stats = {
            "enhanced": 0,
            "unchanged": 0
        }
        print("[ENHANCER] Response Enhancer initialized")
    
    def enhance(self, response: str, query: str = "", add_structure: bool = True) -> str:
        """
        Enhance a response for better quality.
        
        Args:
            response: The AI's raw response
            query: Original query (for context)
            add_structure: Whether to add markdown formatting
            
        Returns:
            Enhanced response string
        """
        if not response or len(response.strip()) < 10:
            return response
        
        original = response
        
        # Step 1: Remove filler at start
        for pattern in self.FILLER_PATTERNS:
            response = re.sub(pattern, "", response, flags=re.IGNORECASE | re.MULTILINE)
        
        # Step 2: Remove redundant phrases
        for phrase in self.REDUNDANT_PHRASES:
            response = response.replace(phrase, "")
            response = response.replace(phrase.lower(), "")
        
        # Step 3: Clean up whitespace
        response = re.sub(r'\n{3,}', '\n\n', response)  # Max 2 newlines
        response = re.sub(r'[ \t]+', ' ', response)  # Single spaces
        response = response.strip()
        
        # Step 4: Ensure proper capitalization after cleaning
        if response and response[0].islower():
            response = response[0].upper() + response[1:]
        
        # Step 5: Add structure if beneficial
        if add_structure:
            response = self._add_structure(response, query)
        
        # Track stats
        if response != original:
            self.stats["enhanced"] += 1
        else:
            self.stats["unchanged"] += 1
        
        return response
    
    def _add_structure(self, response: str, query: str) -> str:
        """Add markdown structure where beneficial"""
        
        # If response has numbered items without markdown, format them
        if re.search(r'^\d+[\.\)]\s', response, re.MULTILINE):
            # Already has numbered list - ensure proper formatting
            response = re.sub(r'^(\d+)[\.\)]\s', r'\1. ', response, flags=re.MULTILINE)
        
        # If response has bullet-like items, format them
        if re.search(r'^[-•*]\s', response, re.MULTILINE):
            response = re.sub(r'^[-•]\s', '- ', response, flags=re.MULTILINE)
        
        # Bold important terms in definitions
        if any(word in query.lower() for word in ["what is", "define", "explain"]):
            # Bold the first occurrence of key terms
            words = query.lower().replace("what is", "").replace("define", "").replace("explain", "").strip().split()
            for word in words[:2]:  # Only first 2 key words
                if len(word) > 3:
                    pattern = re.compile(r'\b(' + re.escape(word) + r')\b', re.IGNORECASE)
                    response = pattern.sub(r'**\1**', response, count=1)
        
        return response
    
    def format_code_blocks(self, response: str) -> str:
        """Ensure code is properly formatted in markdown blocks"""
        
        # If there's inline code that should be a block
        if '`' in response and '```' not in response:
            # Check if there's multi-line code in single backticks
            inline_code = re.findall(r'`([^`]+)`', response)
            for code in inline_code:
                if '\n' in code or len(code) > 80:
                    # This should be a code block
                    lang = self._detect_language(code)
                    response = response.replace(f'`{code}`', f'```{lang}\n{code}\n```')
        
        return response
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language from code"""
        code_lower = code.lower()
        
        if 'def ' in code_lower or 'import ' in code_lower or 'class ' in code_lower:
            return 'python'
        if 'function ' in code_lower or 'const ' in code_lower or 'let ' in code_lower:
            return 'javascript'
        if '<html' in code_lower or '<div' in code_lower:
            return 'html'
        if '{' in code and '}' in code and ';' in code:
            return 'javascript'
        
        return ''
    
    def score_quality(self, response: str) -> Dict[str, Any]:
        """
        Score response quality on various dimensions.
        
        Returns:
            Dict with quality scores and suggestions
        """
        scores = {
            "length": 0,
            "structure": 0,
            "clarity": 0,
            "completeness": 0,
            "overall": 0
        }
        suggestions = []
        
        word_count = len(response.split())
        
        # Length score
        if 10 <= word_count <= 500:
            scores["length"] = 100
        elif word_count < 10:
            scores["length"] = 50
            suggestions.append("Response may be too brief")
        else:
            scores["length"] = 70
            suggestions.append("Response may be verbose")
        
        # Structure score
        has_lists = bool(re.search(r'^[\d\-•*]\s', response, re.MULTILINE))
        has_paragraphs = '\n\n' in response
        has_code = '```' in response
        
        structure_points = sum([has_lists, has_paragraphs, has_code])
        if word_count > 100:
            scores["structure"] = min(100, 40 + structure_points * 20)
        else:
            scores["structure"] = 80  # Short responses don't need structure
        
        # Clarity score (penalize filler words)
        filler_count = sum(1 for p in self.FILLER_PATTERNS if re.search(p, response, re.IGNORECASE))
        scores["clarity"] = max(0, 100 - filler_count * 15)
        
        # Completeness (check for trailing incomplete sentences)
        if response.strip()[-1] not in '.!?:"\')':
            scores["completeness"] = 70
            suggestions.append("Response may be incomplete")
        else:
            scores["completeness"] = 100
        
        # Overall
        scores["overall"] = sum(scores.values()) // len(scores)
        
        return {
            "scores": scores,
            "suggestions": suggestions,
            "word_count": word_count
        }
    
    def get_stats(self) -> Dict[str, int]:
        return self.stats.copy()


# Global instance
response_enhancer = ResponseEnhancer()


def enhance_response(response: str, query: str = "") -> str:
    """Convenience function"""
    return response_enhancer.enhance(response, query)


def score_response(response: str) -> Dict[str, Any]:
    """Convenience function"""
    return response_enhancer.score_quality(response)


if __name__ == "__main__":
    # Test
    test_responses = [
        "Sure, I'd be happy to help! Here's the answer: Python is a programming language. Hope this helps!",
        "As an AI language model, I can explain that machine learning is...",
        "1) First step 2) Second step 3) Third step",
    ]
    
    for resp in test_responses:
        print(f"\nOriginal: {resp[:60]}...")
        enhanced = enhance_response(resp)
        print(f"Enhanced: {enhanced[:60]}...")
        quality = score_response(enhanced)
        print(f"Quality: {quality['scores']['overall']}/100")
