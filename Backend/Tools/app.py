from typing import Dict, Any
from .base import Tool
import webbrowser
from Backend.ChromeAutomation import chrome_open, chrome_close_tab
import asyncio

class AppTool(Tool):
    def __init__(self):
        super().__init__(
            name="app_control",
            description="Open or close applications and websites.",
            domain="app_control",
            priority="HIGH",
            allowed_intents=["app_control", "conversation"]
        )

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "Whether to open or close",
                    "enum": ["open", "close"]
                },
                "target": {
                    "type": "string",
                    "description": "Name of the application or website (e.g., 'notepad', 'google.com', 'spotify')"
                }
            },
            "required": ["action", "target"]
        }

    def execute(self, action: str, target: str, **kwargs) -> str:
        try:
            target = target.lower().strip()
            
            if action == "open":
                # Check for URLs first
                if "." in target and " " not in target: # simple check for domain
                     if not target.startswith("http"):
                         target = "https://" + target
                     chrome_open(target)
                     return f"Opened website: {target}"
                
            # Check for "chrome" special handling to open a new window/tab?
                # AppOpener handles 'google chrome' well usually.
                
                try:
                    from AppOpener import close, open as appopen
                    appopen(target, match_closest=True, output=True, throw_error=True)
                    return f"Opened application: {target}"
                except ImportError:
                    return "AppOpener not installed or crashed."
                except Exception as e:
                    # Fallback to web search if app not found? Or just try web open?
                    # Let's try basic web open if app fails, or report error.
                    # Actually, better to be explicit.
                    return f"Could not find install application: {target} (Error: {e})"

            elif action == "close":
                try:
                    from AppOpener import close, open as appopen
                    close(target, match_closest=True, output=True, throw_error=True)
                    return f"Closed application: {target}"
                except:
                    return f"Could not close application: {target}"
            
            return "Invalid action"
            
        except Exception as e:
            return f"Error controlling app {target}: {str(e)}"
