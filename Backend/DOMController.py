"""
DOMController.py - AI-Powered DOM Control System
=================================================
The brain behind KAI's "Operator Mode" - enables intelligent
understanding and control of any web page.

🎯 HACKATHON FEATURE: True System Operator Control
"""

import json
import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ActionType(Enum):
    FILL = "fill"
    CLICK = "click"
    SELECT = "select"
    CHECK = "check"
    UNCHECK = "uncheck"
    SCROLL = "scroll"
    FOCUS = "focus"
    CLEAR = "clear"


@dataclass
class DOMAction:
    """Represents a single action to execute on the page"""
    type: ActionType
    selector: str
    value: Optional[str] = None
    description: str = ""
    
    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "selector": self.selector,
            "value": self.value,
            "description": self.description
        }


class DOMController:
    """
    AI-Powered DOM Analysis and Control
    
    Flow:
    1. Receive DOM structure from Chrome extension
    2. Use AI to understand form context and fields
    3. Map user profile data to appropriate fields
    4. Return actionable commands with CSS selectors
    """
    
    def __init__(self):
        self.last_analysis = None
        self.action_history = []
        logger.info("[DOMController] 🖥️ Operator Mode Initialized")
    
    async def analyze_page(self, dom_structure: dict, user_profile: dict, user_query: str = "") -> dict:
        """
        Main entry point - Analyze page DOM and generate smart actions
        
        Args:
            dom_structure: Extracted DOM from extension
            user_profile: User's profile data for filling forms
            user_query: Optional user instruction (e.g., "fill this form")
            
        Returns:
            dict with actions, summary, and analysis
        """
        try:
            # Extract key information
            page_url = dom_structure.get("url", "")
            page_title = dom_structure.get("title", "")
            forms = dom_structure.get("forms", [])
            buttons = dom_structure.get("buttons", [])
            inputs = dom_structure.get("inputs", [])
            
            logger.info(f"[DOMController] Analyzing: {page_title}")
            logger.info(f"[DOMController] Found: {len(forms)} forms, {len(inputs)} inputs, {len(buttons)} buttons")
            
            # Generate AI analysis
            analysis = await self._ai_analyze_dom(dom_structure, user_profile, user_query)
            
            # Store for reference
            self.last_analysis = analysis
            
            return analysis
            
        except Exception as e:
            logger.error(f"[DOMController] Analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "actions": []
            }
    
    async def _ai_analyze_dom(self, dom: dict, profile: dict, query: str) -> dict:
        """Use AI to understand page and generate actions"""
        from Backend.LLM import ChatCompletion
        
        # Build context for AI
        dom_summary = self._create_dom_summary(dom)
        profile_summary = self._create_profile_summary(profile)
        
        system_prompt = """You are an AI DOM Analyzer for KAI's Operator Mode.

Your job is to analyze web page structure and generate precise actions to interact with it.

You will receive:
1. DOM structure (forms, inputs, buttons with their selectors and labels)
2. User profile data
3. Optional user instruction

OUTPUT FORMAT (STRICT JSON):
{
    "summary": "Brief description of what you found",
    "page_type": "form|checkout|login|search|article|other",
    "detected_fields": [
        {"label": "Field Name", "type": "text|email|phone|etc", "confidence": 0.9}
    ],
    "actions": [
        {
            "type": "fill|click|select|check|clear",
            "selector": "exact CSS selector from input",
            "value": "value to fill or null for clicks",
            "description": "what this action does"
        }
    ],
    "warnings": ["any issues or missing data"],
    "requires_human": false
}

RULES:
- ONLY use selectors provided in the DOM structure
- Match fields intelligently based on labels, placeholders, and context
- For ambiguous fields, use the best match from user profile
- If a required field has no matching profile data, add to warnings
- Set requires_human=true if human intervention is needed (captcha, file upload, etc.)"""

        user_message = f"""Analyze this page and generate fill actions:

PAGE INFO:
URL: {dom.get('url', 'unknown')}
Title: {dom.get('title', 'unknown')}

DOM STRUCTURE:
{dom_summary}

USER PROFILE:
{profile_summary}

USER REQUEST: {query if query else 'Fill this form with my profile data'}

Generate the actions JSON:"""

        try:
            response = ChatCompletion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                model="llama-3.3-70b-versatile",
                inject_memory=False
            )
            
            # Parse JSON from response
            result = self._extract_json(response)
            result["success"] = True
            result["raw_response"] = response
            
            logger.info(f"[DOMController] Generated {len(result.get('actions', []))} actions")
            
            return result
            
        except Exception as e:
            logger.error(f"[DOMController] AI analysis failed: {e}")
            # Fallback to rule-based matching
            return self._fallback_analysis(dom, profile)
    
    def _create_dom_summary(self, dom: dict) -> str:
        """Create a concise summary of DOM for AI"""
        lines = []
        
        # Forms
        for i, form in enumerate(dom.get("forms", [])):
            lines.append(f"\nFORM #{i+1}:")
            for field in form.get("fields", []):
                selector = field.get("selector", "")
                label = field.get("label", "")
                field_type = field.get("type", "text")
                placeholder = field.get("placeholder", "")
                required = "REQUIRED" if field.get("required") else ""
                lines.append(f"  - [{field_type}] '{label or placeholder}' selector='{selector}' {required}")
        
        # Standalone inputs
        for inp in dom.get("inputs", []):
            selector = inp.get("selector", "")
            label = inp.get("label", "")
            inp_type = inp.get("type", "text")
            lines.append(f"INPUT: [{inp_type}] '{label}' selector='{selector}'")
        
        # Buttons
        for btn in dom.get("buttons", []):
            selector = btn.get("selector", "")
            text = btn.get("text", "")
            lines.append(f"BUTTON: '{text}' selector='{selector}'")
        
        return "\n".join(lines) if lines else "No interactive elements found"
    
    def _create_profile_summary(self, profile: dict) -> str:
        """Create profile summary for AI"""
        if not profile:
            return "No profile data available"
        
        lines = []
        field_map = {
            "name": "Full Name",
            "firstName": "First Name",
            "lastName": "Last Name",
            "email": "Email",
            "phone": "Phone",
            "address": "Address",
            "city": "City",
            "state": "State",
            "zip": "ZIP Code",
            "country": "Country",
            "company": "Company",
            "title": "Job Title",
            "linkedin": "LinkedIn",
            "github": "GitHub",
            "website": "Website",
            "bio": "Bio/About",
            "education": "Education",
            "skills": "Skills"
        }
        
        for key, label in field_map.items():
            if key in profile and profile[key]:
                value = profile[key]
                # Truncate long values
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                lines.append(f"{label}: {value}")
        
        return "\n".join(lines) if lines else "Empty profile"
    
    def _extract_json(self, text: str) -> dict:
        """Extract JSON from AI response"""
        # Try to find JSON block
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Return empty structure if parsing fails
        return {
            "summary": "Could not parse AI response",
            "actions": [],
            "warnings": ["AI response parsing failed"]
        }
    
    def _fallback_analysis(self, dom: dict, profile: dict) -> dict:
        """Rule-based fallback when AI fails"""
        actions = []
        
        # Simple keyword matching
        field_mapping = {
            "email": ["email", "e-mail", "mail"],
            "name": ["name", "full name", "your name"],
            "firstName": ["first name", "given name", "first"],
            "lastName": ["last name", "family name", "surname", "last"],
            "phone": ["phone", "mobile", "tel", "telephone", "contact"],
            "address": ["address", "street", "location"],
            "city": ["city", "town"],
            "state": ["state", "province", "region"],
            "zip": ["zip", "postal", "postcode"],
            "company": ["company", "organization", "employer"],
            "title": ["title", "position", "job title", "role"]
        }
        
        # Process all inputs
        all_inputs = []
        for form in dom.get("forms", []):
            all_inputs.extend(form.get("fields", []))
        all_inputs.extend(dom.get("inputs", []))
        
        for inp in all_inputs:
            label = (inp.get("label", "") + " " + inp.get("placeholder", "")).lower()
            selector = inp.get("selector", "")
            
            if not selector:
                continue
            
            # Try to match with profile fields
            for profile_key, keywords in field_mapping.items():
                if any(kw in label for kw in keywords):
                    if profile_key in profile and profile[profile_key]:
                        actions.append({
                            "type": "fill",
                            "selector": selector,
                            "value": profile[profile_key],
                            "description": f"Fill {profile_key}"
                        })
                        break
        
        return {
            "success": True,
            "summary": f"Fallback analysis: found {len(actions)} fillable fields",
            "page_type": "form",
            "actions": actions,
            "warnings": ["Using fallback rule-based matching (AI unavailable)"],
            "requires_human": False
        }
    
    def get_quick_fill_actions(self, dom: dict, profile: dict) -> List[dict]:
        """
        Quick synchronous version for simple forms
        Uses rule-based matching without AI
        """
        result = self._fallback_analysis(dom, profile)
        return result.get("actions", [])
    
    async def execute_with_feedback(self, actions: List[dict], feedback_callback=None):
        """
        Process actions with real-time feedback
        
        This is called from the API endpoint and sends actions to the extension
        """
        results = []
        
        for i, action in enumerate(actions):
            result = {
                "index": i,
                "action": action,
                "status": "pending"
            }
            
            # Track for history
            self.action_history.append(result)
            results.append(result)
            
            if feedback_callback:
                await feedback_callback(f"Action {i+1}/{len(actions)}: {action.get('description', action.get('type'))}")
        
        return results
    
    def get_status(self) -> dict:
        """Get current controller status"""
        return {
            "initialized": True,
            "last_analysis": self.last_analysis is not None,
            "actions_executed": len(self.action_history),
            "mode": "operator"
        }


# Singleton instance
dom_controller = DOMController()


# ==================== UTILITY FUNCTIONS ====================

def generate_unique_selector(element_info: dict) -> str:
    """
    Generate a unique CSS selector for an element
    Priority: id > name > aria-label > data-testid > nth-child
    """
    if element_info.get("id"):
        return f"#{element_info['id']}"
    
    if element_info.get("name"):
        tag = element_info.get("tag", "input")
        return f"{tag}[name='{element_info['name']}']"
    
    if element_info.get("aria-label"):
        tag = element_info.get("tag", "input")
        return f"{tag}[aria-label='{element_info['aria-label']}']"
    
    if element_info.get("data-testid"):
        return f"[data-testid='{element_info['data-testid']}']"
    
    if element_info.get("placeholder"):
        tag = element_info.get("tag", "input")
        return f"{tag}[placeholder='{element_info['placeholder']}']"
    
    # Fallback to class + index
    if element_info.get("class"):
        return f".{element_info['class'].split()[0]}"
    
    return element_info.get("selector", "")


def extract_form_context(html_snippet: str) -> dict:
    """Extract contextual information from HTML around a form"""
    context = {
        "likely_purpose": "unknown",
        "fields_detected": [],
        "submit_button": None
    }
    
    # Simple heuristics
    html_lower = html_snippet.lower()
    
    if "sign up" in html_lower or "register" in html_lower:
        context["likely_purpose"] = "registration"
    elif "sign in" in html_lower or "log in" in html_lower:
        context["likely_purpose"] = "login"
    elif "contact" in html_lower:
        context["likely_purpose"] = "contact"
    elif "apply" in html_lower or "application" in html_lower:
        context["likely_purpose"] = "application"
    elif "checkout" in html_lower or "payment" in html_lower:
        context["likely_purpose"] = "checkout"
    elif "search" in html_lower:
        context["likely_purpose"] = "search"
    
    return context
