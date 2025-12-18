from typing import Dict, Any
from .base import Tool
import keyboard
from Backend.UltimatePCControl import ultimate_pc
import pyautogui
import os

class SystemTool(Tool):
    def __init__(self):
        super().__init__(
            name="system_control",
            description="Control system volume, brightness, power, and desktop visibility.",
            domain="system_control",
            priority="HIGH",
            allowed_intents=["system_control", "conversation"]
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The action to perform",
                    "enum": [
                        "volume_up", "volume_down", "mute", "unmute",
                        "brightness_up", "brightness_down", 
                        "lock_screen", "show_desktop", "take_screenshot",
                        "shutdown", "restart", "sleep", "hibernate",
                        "battery_status"
                    ]
                }
            },
            "required": ["action"]
        }

    def execute(self, action: str, **kwargs) -> str:
        try:
            if action == "volume_up":
                keyboard.press_and_release("volume up")
                return "Increased volume"
            elif action == "volume_down":
                keyboard.press_and_release("volume down")
                return "Decreased volume"
            elif action == "mute":
                keyboard.press_and_release("volume mute")
                return "Muted system audio"
            elif action == "unmute":
                keyboard.press_and_release("volume mute")
                return "Unmuted system audio"
            elif action == "brightness_up":
                keyboard.press_and_release("brightness up") # Hardware dependent
                return "Increased brightness"
            elif action == "brightness_down":
                keyboard.press_and_release("brightness down")
                return "Decreased brightness"
            elif action == "lock_screen":
                keyboard.press_and_release("win+l")
                return "Locked screen"
            elif action == "show_desktop":
                keyboard.press_and_release("win+d")
                return "Toggled desktop visibility"
            elif action == "take_screenshot":
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
                pyautogui.screenshot(filename)
                return f"Screenshot saved as {filename}"
            elif action == "shutdown":
                ultimate_pc.shutdown(60)
                return "Shutting down system in 60 seconds"
            elif action == "restart":
                ultimate_pc.restart(60)
                return "Restarting system in 60 seconds"
            elif action == "sleep":
                ultimate_pc.sleep()
                return "System going to sleep"
            elif action == "hibernate":
                ultimate_pc.hibernate()
                return "System hibernating"
            elif action == "battery_status":
                stats = ultimate_pc.get_system_stats()
                batt = stats.get('battery', {})
                return f"Battery: {batt.get('percent', 'Unknown')}% (Plugged: {batt.get('plugged', 'Unknown')})"
            else:
                return f"Unknown system action: {action}"
        except Exception as e:
            return f"Error executing {action}: {str(e)}"
