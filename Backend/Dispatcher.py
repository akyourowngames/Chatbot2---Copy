import json
import logging
from typing import Dict, List, Any, Optional
from Backend.LLM import ChatCompletion
from Backend.Tools.base import Tool
from Backend.Tools.system import SystemTool
from Backend.Tools.app import AppTool
from Backend.Tools.web import WebSearchTool
from Backend.Tools.vision import VisionTool
from Backend.Tools.files import FileTool
from Backend.Tools.media import MediaTool
from Backend.Tools.social import SocialTool
from Backend.Tools.workflow import WorkflowTool
from Backend.Tools.document import DocumentTool
from Backend.Tools.code import CodeTool
from Backend.Tools.reminder import ReminderTool
from Backend.Tools.translator import TranslatorTool
from Backend.Tools.math import MathTool
from Backend.IntentClassifier import IntentClassifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.schemas: List[Dict[str, Any]] = []

    def register(self, tool: Tool):
        self.tools[tool.name] = tool
        self.schemas.append(tool.to_schema())
        logger.info(f"Registered tool: {tool.name} (Domain: {tool.domain})")

    def get_tool(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)

    def get_tools_for_intent(self, intent: str) -> List[Dict[str, Any]]:
        """
        Returns schemas of tools allowed for the given intent.
        Strict filtering: Only tools matching the domain or explicitly allowed.
        """
        if intent == "multi_step":
            # For multi-step, we allow almost everything, but maybe prioritizing 'high' value tools?
            # Creating a plan usually involves search, apps, system.
            return self.schemas # Allow all for complex planning

        allowed_schemas = []
        for tool in self.tools.values():
            if tool.domain == intent or intent in tool.allowed_intents:
                allowed_schemas.append(tool.to_schema())
        
        return allowed_schemas

class Dispatcher:
    def __init__(self):
        self.registry = ToolRegistry()
        self.classifier = IntentClassifier()
        self._register_default_tools()
        
    def _register_default_tools(self):
        self.registry.register(SystemTool())
        self.registry.register(AppTool())
        self.registry.register(WebSearchTool())
        self.registry.register(VisionTool())
        self.registry.register(FileTool())
        self.registry.register(MediaTool())
        self.registry.register(SocialTool())
        self.registry.register(WorkflowTool())
        self.registry.register(DocumentTool())
        self.registry.register(CodeTool())
        self.registry.register(ReminderTool())
        self.registry.register(TranslatorTool())
        self.registry.register(MathTool())
        
    def process_query(self, user_query: str, history: List[Dict[str, str]], system_prompt: str) -> str:
        """
        Smart Dispatcher Loop:
        1. Classify Intent
        2. Filter Tools
        3. Execute (Plan -> Act)
        """
        # 1. Intent Classification
        intent = self.classifier.classify(user_query, history)
        logger.info(f"User Query: '{user_query}' | Detected Intent: {intent}")
        
        # 2. Tool Selection
        active_tools = self.registry.get_tools_for_intent(intent)
        tool_definitions = json.dumps(active_tools, indent=2)
        
        # 3. Mode Selection
        current_messages = history.copy()
        current_messages.append({"role": "user", "content": user_query})
        
        # Specialized System Prompts based on Intent
        mode_instruction = ""
        if intent == "multi_step":
            mode_instruction = """
### MULTI-STEP PLANNING MODE
The user request requires multiple actions.
1. First, think step-by-step about what needs to be done.
2. Execute tools one by one.
3. Verify the output of each tool before proceeding.
"""
        elif intent == "conversation":
            mode_instruction = "You are in CONVERSATION mode. Do NOT use tools unless explicitly necessary."
        else:
            mode_instruction = f"You are in {intent.upper()} mode. ONLY use tools relevant to this domain."

        enhanced_system = f"""{system_prompt}

{mode_instruction}

### AVAILABLE TOOLS (STRICT USAGE)
You have access ONLY to these tools:
{tool_definitions}

### CRITICAL RULES
1. **NO GUESSING**: If you don't know the parameter, ask the user.
2. **STRICT FORMAT**: To use a tool, return JSON ONLY:
{{
  "tool": "tool_name",
  "parameters": {{ "arg": "value" }}
}}
3. **PLANNING**: If the request is complex, you can output a text thought before the JSON.
4. If no tool is needed, just reply with text.

### RESPONSE STYLE
- Be friendly, concise, and helpful.
- Avoid robotic phrases like "I will now proceed to..."
- Instead say: "Sure, opening that for you.", "I found this.", "Done."
- Keep text confirmation short when taking actions.
"""

        # Execution Loop
        MAX_TURNS = 6
        turn_count = 0
        
        while turn_count < MAX_TURNS:
            turn_count += 1
            
            response = ChatCompletion(
                messages=current_messages,
                system_prompt=enhanced_system,
                model="llama-3.1-8b-instant" 
            )
            
            response = response.strip()
            
            # Clean Markdown
            if response.startswith("```json"): response = response[7:]
            if response.startswith("```"): response = response[3:]
            if response.endswith("```"): response = response[:-3]
            response = response.strip()

            # Attempt to find JSON tool call
            tool_call = None
            try:
                # Basic parsing for embedded JSON or pure JSON
                if "{" in response and "}" in response:
                    # heuristic to extract json block if mixed with text
                    start = response.find("{")
                    end = response.rfind("}") + 1
                    json_str = response[start:end]
                    parsed = json.loads(json_str)
                    if "tool" in parsed:
                        tool_call = parsed
                        # Logic to handle "Thought" before tool call?
                        # The text before 'start' is the thought.
                        thought = response[:start].strip()
                        if thought:
                           logger.info(f"LLM Thought: {thought}")
            except:
                pass
                
            if tool_call:
                tool_name = tool_call.get("tool")
                params = tool_call.get("parameters", {})
                
                tool = self.registry.get_tool(tool_name)
                if tool:
                    # Strict Domain Check (Double Safety)
                    if intent != "multi_step" and tool.domain != intent and intent not in tool.allowed_intents:
                         # Soft deny or allow if it's a "conversation" helper?
                         # Let's enforce strictness for now.
                         logger.warning(f"Blocked tool {tool_name} for intent {intent}")
                         return f"I cannot use {tool_name} in {intent} mode. Please clarify."

                    logger.info(f"Executing tool: {tool_name} params: {params}")
                    try:
                        result = tool.execute(**params)
                    except Exception as e:
                        result = f"Error: {e}"
                        
                    current_messages.append({"role": "assistant", "content": json.dumps(tool_call)})
                    current_messages.append({"role": "tool", "content": f"Result: {result}"})
                else:
                    return f"Error: Unknown tool '{tool_name}'"
            else:
                # No tool call found - implies final answer or just text
                return response
                
        return "I completed the steps but hit the interaction limit."

# Global
dispatcher = Dispatcher()
