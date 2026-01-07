"""
Kai Local Agent - Close App Executor
=====================================
Executor for the 'close_app' command.
Closes predefined, whitelisted applications safely.

Security: No arbitrary process kill. Only mapped application names.
"""

import subprocess
import sys
import os
from typing import Dict, Any

from .base import BaseExecutor


# Application process names per platform
# Keys are the allowed app names, values are the process names to terminate
APP_PROCESSES = {
    "win32": {
        # Browsers
        "browser": ["chrome.exe", "msedge.exe", "firefox.exe"],
        "chrome": ["chrome.exe"],
        "firefox": ["firefox.exe"],
        "edge": ["msedge.exe"],
        "brave": ["brave.exe"],
        "opera": ["opera.exe"],
        "vivaldi": ["vivaldi.exe"],
        # Development
        "vscode": ["Code.exe"],
        "code": ["Code.exe"],
        "terminal": ["cmd.exe"],
        "cmd": ["cmd.exe"],
        "powershell": ["powershell.exe"],
        "postman": ["Postman.exe"],
        # Productivity
        "notepad": ["notepad.exe"],
        "word": ["WINWORD.EXE"],
        "excel": ["EXCEL.EXE"],
        "outlook": ["OUTLOOK.EXE"],
        "powerpoint": ["POWERPNT.EXE"],
        "onenote": ["onenote.exe"],
        "notion": ["Notion.exe"],
        "obsidian": ["Obsidian.exe"],
        # Communication
        "teams": ["Teams.exe", "ms-teams.exe"],
        "slack": ["slack.exe"],
        "discord": ["Discord.exe"],
        "zoom": ["Zoom.exe"],
        "skype": ["Skype.exe"],
        "telegram": ["Telegram.exe"],
        "whatsapp": ["WhatsApp.exe"],
        "signal": ["Signal.exe"],
        # Media
        "spotify": ["Spotify.exe"],
        "vlc": ["vlc.exe"],
        "itunes": ["iTunes.exe"],
        "winamp": ["winamp.exe"],
        "obs": ["obs64.exe", "obs32.exe"],
        "audacity": ["Audacity.exe"],
        # System (excluding critical)
        "calculator": ["CalculatorApp.exe", "calc.exe"],
        "paint": ["mspaint.exe"],
        "snipping": ["SnippingTool.exe"],
        "explorer": [],  # Don't close explorer
        # Games
        "steam": ["steam.exe"],
        "epicgames": ["EpicGamesLauncher.exe"],
        "origin": ["Origin.exe"],
        "ubisoft": ["upc.exe"],
        "gog": ["GalaxyClient.exe"],
    },
    "darwin": {  # macOS
        "browser": ["Google Chrome", "Safari", "Firefox"],
        "chrome": ["Google Chrome"],
        "firefox": ["Firefox"],
        "safari": ["Safari"],
        "vscode": ["Code"],
        "code": ["Code"],
        "notepad": ["TextEdit"],
        "terminal": ["Terminal"],
        "finder": [],  # Don't close Finder
        "spotify": ["Spotify"],
        "discord": ["Discord"],
    },
    "linux": {
        "browser": ["chrome", "firefox", "chromium"],
        "chrome": ["chrome", "chromium"],
        "firefox": ["firefox"],
        "vscode": ["code"],
        "code": ["code"],
        "notepad": ["gedit", "kate", "nano"],
        "terminal": [],  # Don't close terminal
        "spotify": ["spotify"],
        "discord": ["discord"],
    }
}


class CloseAppExecutor(BaseExecutor):
    """Executor for closing predefined applications."""
    
    @property
    def command_name(self) -> str:
        return "close_app"
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Close the specified application.
        
        Args:
            params: {"app": "browser" | "vscode" | "notepad" | etc.}
        
        Returns:
            Dict with status and message
        """
        app_name = params.get("app", "").lower()
        
        if not app_name:
            return {
                "status": "error",
                "message": "No app name specified"
            }
        
        # Get platform-specific process names
        platform = sys.platform
        if platform.startswith("linux"):
            platform = "linux"
        
        platform_apps = APP_PROCESSES.get(platform, {})
        
        if app_name not in platform_apps:
            return {
                "status": "error",
                "message": f"App '{app_name}' not available for closing on {platform}. Available: {list(platform_apps.keys())}"
            }
        
        process_names = platform_apps[app_name]
        
        if not process_names:
            return {
                "status": "error",
                "message": f"Cannot close '{app_name}' - it's a system-critical application"
            }
        
        try:
            closed_count = 0
            errors = []
            
            for process_name in process_names:
                try:
                    if platform == "win32":
                        # Windows: Use taskkill
                        result = subprocess.run(
                            ["taskkill", "/IM", process_name, "/F"],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            closed_count += 1
                        elif "not found" not in result.stderr.lower() and "no running" not in result.stderr.lower():
                            # Only log if it's not just "process not found"
                            if result.stderr:
                                errors.append(f"{process_name}: {result.stderr.strip()}")
                    
                    elif platform == "darwin":
                        # macOS: Use osascript to quit gracefully
                        result = subprocess.run(
                            ["osascript", "-e", f'tell application "{process_name}" to quit'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            closed_count += 1
                    
                    else:
                        # Linux: Use pkill
                        result = subprocess.run(
                            ["pkill", "-f", process_name],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            closed_count += 1
                
                except subprocess.TimeoutExpired:
                    errors.append(f"{process_name}: Timeout")
                except Exception as e:
                    errors.append(f"{process_name}: {str(e)}")
            
            if closed_count > 0:
                return {
                    "status": "success",
                    "message": f"Successfully closed {app_name}",
                    "data": {"closed_count": closed_count}
                }
            elif errors:
                return {
                    "status": "error",
                    "message": f"Failed to close {app_name}: {'; '.join(errors)}"
                }
            else:
                return {
                    "status": "success",
                    "message": f"{app_name} was not running"
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to close {app_name}: {str(e)}"
            }
