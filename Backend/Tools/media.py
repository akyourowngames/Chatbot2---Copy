"""
Media Tool - Web Version
========================
Image generation and media control for cloud deployment.
"""

from typing import Dict, Any
from .base import Tool


class MediaTool(Tool):
    def __init__(self):
        super().__init__(
            name="media_control",
            description="Generate images or play videos (YouTube).",
            domain="media_control",
            priority="MEDIUM",
            allowed_intents=["media_control", "conversation"]
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Action to perform",
                    "enum": ["generate_image", "play_video", "stop_video"]
                },
                "query": {
                    "type": "string",
                    "description": "Image prompt or Video search term"
                }
            },
            "required": ["action"]
        }

    def execute(self, action: str, query: str = "", **kwargs) -> str:
        try:
            if action == "generate_image":
                if not query:
                    return "Please provide a description for the image."
                
                # Try to use EnhancedImageGen (works on web)
                try:
                    from Backend.EnhancedImageGen import enhanced_image_gen
                    images = enhanced_image_gen.generate_with_style(query, style="realistic", num_images=1)
                    if images:
                        return f"✅ Generated image: {images[0]}"
                    return "Failed to generate image."
                except Exception as e:
                    return f"Image generation error: {e}"

            elif action == "play_video":
                if not query:
                    return "What video should I play?"
                # On web, return YouTube search URL instead of opening browser
                from urllib.parse import quote_plus
                search_query = quote_plus(query)
                youtube_url = f"https://www.youtube.com/results?search_query={search_query}"
                # Return structured tag for Frontend to render a card
                return f"PLAY_YOUTUBE:{query}|{youtube_url}"
                
            elif action == "stop_video":
                return "⚠️ Video control is not available on web deployment."
                
            return f"Unknown media action: {action}"
            
        except Exception as e:
            return f"Media Error: {str(e)}"
