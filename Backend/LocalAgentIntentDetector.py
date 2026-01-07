"""
Kai Local Agent - AI Intent Detector
=====================================
LLM-based intent detection for natural language PC control commands.

Handles:
- Spelling mistakes ("notpad" → notepad)
- Natural language variations ("fire up chrome" → open browser)
- Any command format without explicit patterns
"""

import os
import json
import re
from typing import Dict, Any, Optional, Tuple
from difflib import get_close_matches

try:
    import google.generativeai as genai
    from dotenv import dotenv_values
    env_vars = dotenv_values(".env")
    
    # Configure Gemini
    api_key = os.environ.get("GEMINI_API_KEY") or env_vars.get("GeminiAPIKey", "") or env_vars.get("GEMINI_API_KEY", "")
    if api_key:
        genai.configure(api_key=api_key)
        GEMINI_AVAILABLE = True
    else:
        GEMINI_AVAILABLE = False
except ImportError:
    GEMINI_AVAILABLE = False

# ==================== APP ALIASES (Fuzzy Matching) ====================

APP_ALIASES = {
    "notepad": ["ntpd", "notpad", "notepadd", "notepd", "text editor", "txt editor", "note pad"],
    "chrome": ["chromium", "browser", "google", "web browser", "internet", "chrom", "crome"],
    "firefox": ["mozila", "mozilla", "fox", "ffox", "fire fox"],
    "edge": ["microsoft edge", "msedge", "ms edge", "egde"],
    "vscode": ["vs code", "visual studio code", "code", "vsc", "vs", "visual studio"],
    "terminal": ["cmd", "command prompt", "command line", "console", "shell", "powershell", "ps"],
    "explorer": ["file explorer", "files", "file manager", "my computer", "folders", "file browser"],
}

# Flatten aliases for quick lookup
ALIAS_TO_APP = {}
for app, aliases in APP_ALIASES.items():
    ALIAS_TO_APP[app] = app
    for alias in aliases:
        ALIAS_TO_APP[alias.lower()] = app

ALL_APPS = list(APP_ALIASES.keys())


# ==================== FUZZY MATCHING ====================

def fuzzy_match_app(query: str) -> Optional[str]:
    """
    Find the best matching app name using fuzzy matching.
    
    Args:
        query: User's app name (possibly misspelled)
    
    Returns:
        Canonical app name or None if no match
    """
    query_lower = query.lower().strip()
    
    # Direct match in aliases
    if query_lower in ALIAS_TO_APP:
        return ALIAS_TO_APP[query_lower]
    
    # Fuzzy match against all aliases
    all_aliases = list(ALIAS_TO_APP.keys())
    matches = get_close_matches(query_lower, all_aliases, n=1, cutoff=0.6)
    
    if matches:
        return ALIAS_TO_APP[matches[0]]
    
    # Try matching each word in the query
    for word in query_lower.split():
        if len(word) > 2:
            if word in ALIAS_TO_APP:
                return ALIAS_TO_APP[word]
            matches = get_close_matches(word, all_aliases, n=1, cutoff=0.7)
            if matches:
                return ALIAS_TO_APP[matches[0]]
    
    return None


# ==================== AI INTENT DETECTION ====================

SYSTEM_PROMPT = """You are an intent detector for a PC control assistant named Kai.
Given a user message, determine if they want to control their PC.

IMPORTANT: Return ONLY valid JSON, no markdown, no explanation.

Intents you can detect:
1. "open_app" - User wants to open an application
2. "system_status" - User asks about PC status, CPU, RAM, uptime, if PC is online
3. null - Not a PC control command (general chat)

For open_app, extract the target app. Map to one of: notepad, chrome, firefox, edge, vscode, terminal, explorer

Response format (JSON only):
{"intent": "open_app", "target": "notepad", "confidence": 0.95}
or
{"intent": "system_status", "target": null, "confidence": 0.9}
or
{"intent": null, "target": null, "confidence": 0.0}

Examples:
"opn ntpd" → {"intent": "open_app", "target": "notepad", "confidence": 0.9}
"fire up the browser" → {"intent": "open_app", "target": "chrome", "confidence": 0.95}
"is my pc running?" → {"intent": "system_status", "target": null, "confidence": 0.9}
"what's for lunch" → {"intent": null, "target": null, "confidence": 0.0}
"lanch vscode" → {"intent": "open_app", "target": "vscode", "confidence": 0.95}
"""


def detect_intent_ai(query: str) -> Dict[str, Any]:
    """
    Use LLM to detect PC control intent from natural language.
    
    Args:
        query: User's natural language query
    
    Returns:
        Dict with intent, target, and confidence
    """
    if not GEMINI_AVAILABLE:
        return {"intent": None, "target": None, "confidence": 0.0, "error": "Gemini not available"}
    
    try:
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            system_instruction=SYSTEM_PROMPT,
            generation_config={
                "temperature": 0.1,  # Low temp for consistent classification
                "max_output_tokens": 100
            }
        )
        
        response = model.generate_content(query)
        text = response.text.strip()
        
        # Clean up response (remove markdown if any)
        if text.startswith("```"):
            text = re.sub(r'^```json?\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
        
        # Parse JSON
        result = json.loads(text)
        
        # Validate and normalize
        intent = result.get("intent")
        target = result.get("target")
        confidence = float(result.get("confidence", 0.0))
        
        # If intent is open_app, validate/fuzzy-match the target
        if intent == "open_app" and target:
            matched_app = fuzzy_match_app(target)
            if matched_app:
                target = matched_app
            else:
                # LLM gave unknown app, try fuzzy on original query
                matched_app = fuzzy_match_app(query)
                if matched_app:
                    target = matched_app
        
        return {
            "intent": intent,
            "target": target,
            "confidence": confidence # Gemini often gives high confidence
        }
        
    except json.JSONDecodeError as e:
        print(f"[AI-INTENT] JSON parse error: {e}")
        return {"intent": None, "target": None, "confidence": 0.0, "error": "JSON parse error"}
    except Exception as e:
        print(f"[AI-INTENT] Detection error: {e}")
        return {"intent": None, "target": None, "confidence": 0.0, "error": str(e)}


# ==================== HYBRID DETECTION (Fast + AI) ====================

# Quick patterns for instant matching (before calling LLM)
# NOTE: Patterns require ACTION VERBS to avoid false positives
# e.g., "performance" alone won't trigger, but "check performance" will
QUICK_PATTERNS = {
    "open_app": [
        # Requires explicit open/launch/start verb at the beginning
        r"^(?:open|opn|opne|launch|lanch|start|strt|run|fire up)\s+(.+)",
        r"^(?:give me|show me|bring up)\s+(.+)",
    ],
    "system_status": [
        # Requires action verb + PC-related context
        r"^(?:check|show|get|view|tell me)\s+(?:my\s+)?(?:pc|computer|system|device)\s*(?:status|health|stats|performance|info)?",
        r"^(?:system|pc|computer|device)\s+status\b",
        r"^(?:check|show|get)\s+(?:my\s+)?(?:cpu|ram|memory|uptime|performance)",
        r"^(?:how|what)\s+(?:is|are)\s+(?:my\s+)?(?:pc|computer|system)\s+(?:doing|running|performing)",
        r"^is\s+(?:my\s+)?(?:pc|computer|device)\s+(?:online|running|ok|connected)",
        r"^(?:pc|system|computer)\s+(?:health|stats|info)\b",
    ]
}


def quick_detect(query: str) -> Tuple[Optional[str], Optional[str], float]:
    """
    Quick pattern-based detection before calling AI.
    
    Returns:
        (intent, target, confidence) or (None, None, 0.0)
    """
    query_lower = query.lower().strip()
    
    # Check system_status patterns first (no target needed)
    for pattern in QUICK_PATTERNS["system_status"]:
        if re.search(pattern, query_lower):
            return ("system_status", None, 0.9)
    
    # Check open_app patterns
    for pattern in QUICK_PATTERNS["open_app"]:
        match = re.search(pattern, query_lower)
        if match:
            app_query = match.group(1).strip()
            # Try fuzzy matching
            matched_app = fuzzy_match_app(app_query)
            if matched_app:
                return ("open_app", matched_app, 0.95)
    
    return (None, None, 0.0)


def detect_intent(query: str, use_ai: bool = True) -> Dict[str, Any]:
    """
    Hybrid intent detection: Quick patterns first, AI fallback.
    
    Args:
        query: User's natural language query
        use_ai: Whether to use AI if quick detection fails
    
    Returns:
        Dict with intent, target, confidence, and method used
    """
    # Step 1: Quick pattern detection
    intent, target, confidence = quick_detect(query)
    
    if intent and confidence >= 0.8:
        print(f"[AI-INTENT] Quick match: {intent} -> {target} ({confidence})")
        return {
            "intent": intent,
            "target": target,
            "confidence": confidence,
            "method": "quick"
        }
    
    # Step 2: AI detection (if enabled)
    if use_ai:
        print(f"[AI-INTENT] Using AI detection for: {query[:50]}...")
        ai_result = detect_intent_ai(query)
        
        if ai_result.get("intent") and ai_result.get("confidence", 0) >= 0.5:
            ai_result["method"] = "ai"
            print(f"[AI-INTENT] AI match: {ai_result['intent']} -> {ai_result.get('target')} ({ai_result.get('confidence')})")
            return ai_result
    
    # No match
    return {
        "intent": None,
        "target": None,
        "confidence": 0.0,
        "method": "none"
    }


# ==================== TEST ====================

if __name__ == "__main__":
    test_queries = [
        "open notepad",
        "opn ntpd",
        "fire up the browser",
        "lanch vscode",
        "is my pc online?",
        "check system status",
        "what's for lunch?",
        "start chromium",
        "run the text editor",
        "cpu usage please",
    ]
    
    print("=" * 60)
    print("AI Intent Detection Test")
    print("=" * 60)
    
    for q in test_queries:
        result = detect_intent(q)
        print(f"\nQuery: '{q}'")
        print(f"  Intent: {result.get('intent')}")
        print(f"  Target: {result.get('target')}")
        print(f"  Confidence: {result.get('confidence')}")
        print(f"  Method: {result.get('method')}")
