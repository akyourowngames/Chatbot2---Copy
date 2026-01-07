"""
Kai Local Agent - Open App Executor
====================================
Executor for the 'open_app' command.
Opens predefined, whitelisted applications.

Security: No arbitrary commands. Only mapped application names.
"""

import subprocess
import sys
import os
from typing import Dict, Any

from .base import BaseExecutor


# Application mappings per platform
# Keys are the allowed app names, values are the commands to run
APP_COMMANDS = {
    "win32": {
        # Browsers
        "browser": ["cmd", "/c", "start", "chrome"],
        "chrome": ["cmd", "/c", "start", "chrome"],
        "firefox": ["cmd", "/c", "start", "firefox"],
        "edge": ["cmd", "/c", "start", "msedge"],
        "brave": ["cmd", "/c", "start", "brave"],
        "opera": ["cmd", "/c", "start", "opera"],
        "vivaldi": ["cmd", "/c", "start", "vivaldi"],
        # Development
        "vscode": ["cmd", "/c", "code"],
        "code": ["cmd", "/c", "code"],
        "terminal": ["cmd", "/c", "start", "cmd"],
        "cmd": ["cmd", "/c", "start", "cmd"],
        "powershell": ["powershell", "-Command", "Start-Process", "powershell"],
        "postman": ["cmd", "/c", "start", "postman:"],
        "docker": ["cmd", "/c", "start", "docker"],
        # Productivity
        "notepad": ["notepad.exe"],
        "word": ["cmd", "/c", "start", "winword"],
        "excel": ["cmd", "/c", "start", "excel"],
        "outlook": ["cmd", "/c", "start", "outlook"],
        "powerpoint": ["cmd", "/c", "start", "powerpnt"],
        "onenote": ["cmd", "/c", "start", "onenote:"],
        "notion": ["cmd", "/c", "start", "notion:"],
        "obsidian": ["cmd", "/c", "start", "obsidian:"],
        # Communication
        "teams": ["cmd", "/c", "start", "msteams:"],
        "slack": ["cmd", "/c", "start", "slack:"],
        "discord": ["cmd", "/c", "start", "discord:"],
        "zoom": ["cmd", "/c", "start", "zoommtg:"],
        "skype": ["cmd", "/c", "start", "skype:"],
        "telegram": ["cmd", "/c", "start", "tg:"],
        "whatsapp": ["cmd", "/c", "start", "whatsapp:"],
        "signal": ["cmd", "/c", "start", "signal:"],
        # Media
        "spotify": ["cmd", "/c", "start", "spotify:"],
        "vlc": ["cmd", "/c", "start", "vlc"],
        "itunes": ["cmd", "/c", "start", "itunes"],
        "winamp": ["cmd", "/c", "start", "winamp"],
        "obs": ["cmd", "/c", "start", "obs64"],
        "audacity": ["cmd", "/c", "start", "audacity"],
        # System
        "explorer": ["explorer.exe"],
        "calculator": ["calc.exe"],
        "paint": ["mspaint.exe"],
        "snipping": ["snippingtool.exe"],
        "settings": ["cmd", "/c", "start", "ms-settings:"],
        "task_manager": ["taskmgr.exe"],
        # Games
        "steam": ["cmd", "/c", "start", "steam:"],
        "epicgames": ["cmd", "/c", "start", "com.epicgames.launcher:"],
        "origin": ["cmd", "/c", "start", "origin:"],
        "ubisoft": ["cmd", "/c", "start", "uplay:"],
        "gog": ["cmd", "/c", "start", "goggalaxy:"],
    },
    "darwin": {  # macOS
        "browser": ["open", "-a", "Google Chrome"],
        "chrome": ["open", "-a", "Google Chrome"],
        "firefox": ["open", "-a", "Firefox"],
        "safari": ["open", "-a", "Safari"],
        "vscode": ["open", "-a", "Visual Studio Code"],
        "code": ["open", "-a", "Visual Studio Code"],
        "notepad": ["open", "-a", "TextEdit"],
        "terminal": ["open", "-a", "Terminal"],
        "finder": ["open", "-a", "Finder"],
        "explorer": ["open", "-a", "Finder"],
    },
    "linux": {
        "browser": ["xdg-open", "https://google.com"],
        "chrome": ["google-chrome"],
        "firefox": ["firefox"],
        "vscode": ["code"],
        "code": ["code"],
        "notepad": ["gedit"],
        "terminal": ["gnome-terminal"],
        "explorer": ["nautilus"],
    }
}


class OpenAppExecutor(BaseExecutor):
    """Executor for opening predefined applications."""
    
    @property
    def command_name(self) -> str:
        return "open_app"
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Open the specified application.
        
        Args:
            params: {"app": "browser" | "vscode" | etc.}
        
        Returns:
            Dict with status and message
        """
        app_name = params.get("app", "").lower()
        
        # Get platform-specific commands
        platform = sys.platform
        if platform.startswith("linux"):
            platform = "linux"
        
        platform_apps = APP_COMMANDS.get(platform, {})
        
        if app_name not in platform_apps:
            return {
                "status": "error",
                "message": f"App '{app_name}' not available on {platform}. Available: {list(platform_apps.keys())}"
            }
        
        command = platform_apps[app_name]
        
        try:
            # Use subprocess with shell=False for security
            if platform == "win32":
                # On Windows, use CREATE_NEW_CONSOLE to show the app
                subprocess.Popen(
                    command,
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                subprocess.Popen(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            return {
                "status": "success",
                "message": f"Successfully opened {app_name}"
            }
            
        except FileNotFoundError:
            return {
                "status": "error",
                "message": f"Application '{app_name}' not found on this system"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to open {app_name}: {str(e)}"
            }
