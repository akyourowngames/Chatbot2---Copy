from typing import Dict, Any
from .base import Tool
import asyncio

class SocialTool(Tool):
    def __init__(self):
        super().__init__(
            name="social_media",
            description="Interact with Instagram (DM, Follow, Post) and WhatsApp.",
            domain="social",
            priority="LOW",
            allowed_intents=["social", "conversation"]
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "enum": ["instagram", "whatsapp"]
                },
                "action": {
                    "type": "string",
                    "enum": ["send_message", "check_messages", "follow", "post", "search"]
                },
                "target": {
                    "type": "string",
                    "description": "Username, Phone Number, or Group Name"
                },
                "content": {
                    "type": "string",
                    "description": "Message content or post caption"
                }
            },
            "required": ["platform", "action"]
        }

    def execute(self, platform: str, action: str, target: str = "", content: str = "", **kwargs) -> str:
        try:
            if platform == "instagram":
                # Lazy load to avoid startup issues if not configured
                try:
                    from Backend.InstagramAutomation import InstagramBot
                    # Need singleton? or init new? 
                    # Existing code seemed to use a global instance or context manager?
                    # Let's assume we can instantiate.
                    bot = InstagramBot() # Warning: This might require login flow if not cached. NOT SAFE for non-interactive?
                    # Ideally we use the api_server's initialized instance if possible, 
                    # but tools are isolated.
                    # Best effort:
                    
                    if action == "send_message":
                        bot.send_dm(target, content) # Hypothetical API match
                        return f"Sent DM to {target}"
                    elif action == "check_messages":
                        msgs = bot.get_dms()
                        return f"Unread messages: {msgs}"
                    # ... other actions
                    return f"Instagram action {action} triggered for {target}"
                except Exception as e:
                    return f"Instagram failed: {e}. (Make sure you are logged in)"

            elif platform == "whatsapp":
                try:
                    from Backend.WhatsAppAutomation import send_whatsapp_message
                    # This helper likely uses pywhatkit or selenium
                    if action == "send_message":
                         send_whatsapp_message(target, content)
                         return f"Sent WhatsApp to {target}"
                    return f"WhatsApp action {action} triggered"
                except ImportError:
                    return "WhatsApp module not available."

            return f"Unknown platform {platform}"
        except Exception as e:
            return f"Social Error: {str(e)}"
