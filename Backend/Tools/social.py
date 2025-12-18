"""
Social Media Tools - Web Version
================================
These features require local PC access and are not available on web deployment.
"""

from typing import Dict, Any
from .base import Tool


class SocialTool(Tool):
    def __init__(self):
        super().__init__(
            name="social_media",
            description="Social media features (not available on web deployment)",
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
        """Social media automation is not available on web deployment."""
        return (
            f"⚠️ {platform.title()} automation is not available on web deployment. "
            "This feature requires local PC access. "
            "Please use the desktop version of KAI for social media automation."
        )
