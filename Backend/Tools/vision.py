from typing import Dict, Any
from .base import Tool
# We need to import the vision logic. 
# Currently 'VisionAnalysis' in 'api_server' is just a wrapper around 'vision_analyze' in 'Backend.vision.Vision'.
# Let's import the core logic directly if possible.
# Backend.vision.VisionAnalysis doesn't exist? 
# In api_server: from Backend.api.analyze import analyze_endpoint ...
# Actually, the user's previous 'VisionAnalysis' variable in 'api_server' seemed to be dynamically loaded.
# Let's assume we use the new 'florence_inference.py' directly for best results.
from Backend.vision.florence_inference import analyze_image_comprehensive
import pyautogui
import os
import time

class VisionTool(Tool):
    def __init__(self):
        super().__init__(
            name="vision_analysis",
            description="Analyze what is currently on the screen. Use this when the user asks 'what is on my screen' or 'look at this'.",
            domain="vision_analysis",
            priority="MEDIUM",
            allowed_intents=["vision_analysis", "conversation"]
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Specific question about the screen, or empty for general description"
                }
            }
        }

    def execute(self, prompt: str = "", **kwargs) -> str:
        try:
            # 1. Take screenshot
            temp_dir = "temp_vision"
            os.makedirs(temp_dir, exist_ok=True)
            screenshot_path = os.path.join(temp_dir, "current_screen.png")
            
            # Clean up old
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
                
            pyautogui.screenshot(screenshot_path)
            
            # 2. Analyze
            # If we have a prompt, we might want to pass it to VQA/Caption task?
            # analyze_image_comprehensive does a general caption + OCR. 
            # If the user has a specific question, we rely on the LLM to filter the comprehensive output 
            # OR we should add a specific VQA method to the tool. 
            # For now, let's stick to comprehensive as it's the "fast" robust baseline we just optimized.
            
            result = analyze_image_comprehensive(screenshot_path)
            
            description = result.get('friendly_response', '')
            if not description:
                description = result.get('description', '')
                
            return f"Screen Analysis Result:\n{description}"
            
        except Exception as e:
            return f"Vision analysis failed: {str(e)}"
