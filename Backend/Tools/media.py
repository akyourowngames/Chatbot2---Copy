from typing import Dict, Any
from .base import Tool
from Backend.Automation import PlayYoutube
# Import dynamic handlers or use api_server globals if needed?
# Ideally we import the core logic. 
# Image Gen is likely in Backend.ImageGeneration or similar.
# Let's check api_server for extraction.
# It uses 'Backend.api.image_generation.py' or similar?
# api_server imports `from Backend.ImageGeneration import GenerateImages` (based on log)

import asyncio
# Lazy import to avoid circular or missing dependencies during init
import sys

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
                if not query: return "Please provide a description for the image."
                
                # Import here to be safe
                try:
                    from Backend.ImageGeneration import GenerateImages
                    # This function might print or return?
                    # In api_server: result = GenerateImages(query) -> Returns list of paths or string?
                    # Let's assume it returns paths or we capture output.
                    # Based on existing code, it seems to do filesystem ops.
                    # Let's assume it returns a list of files or single file path.
                    
                    # Correction: looking at logs "Generating image of..."
                    result = GenerateImages(query)
                    return f"Generated image: {result}"
                except ImportError:
                     return "Image Generation module not available."

            elif action == "play_video":
                if not query: return "What video should I play?"
                PlayYoutube(query)
                return f"Playing video for: {query}"
                
            elif action == "stop_video":
                # Automation didn't have a clear stop video command other than maybe key press
                import keyboard
                keyboard.press_and_release("k") # YouTube pause shortcut often works if focused, or media keys
                return "Sent pause command."
                
            return f"Unknown media action: {action}"
            
        except Exception as e:
            return f"Media Error: {str(e)}"
