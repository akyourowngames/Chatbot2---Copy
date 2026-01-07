"""
Kai Local Agent - Screenshot Executor
=====================================
Takes screenshots of the current screen.
Saves to a designated folder and returns the path.
"""

import os
import sys
import time
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from .base import BaseExecutor

# Configure logging
import logging
logger = logging.getLogger("KaiLocalAgent")


class ScreenshotExecutor(BaseExecutor):
    """Executor for taking screenshots."""
    
    def __init__(self):
        """Initialize screenshot executor."""
        super().__init__()
        # Set up screenshots directory
        self.screenshots_dir = Path.home() / ".kai-agent" / "screenshots"
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def command_name(self) -> str:
        return "screenshot"
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Take a screenshot of the current screen.
        
        Args:
            params: Optional parameters
                - region: Optional region to capture (not implemented yet)
        
        Returns:
            Dict with status and screenshot path
        """
        if sys.platform != "win32":
            return {"status": "error", "message": "Screenshot only supported on Windows"}
        
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = self.screenshots_dir / filename
            
            # Method 1: Try using PIL/Pillow
            try:
                from PIL import ImageGrab
                
                # Capture the screen
                screenshot = ImageGrab.grab()
                screenshot.save(str(filepath))
                
                logger.info(f"[SCREENSHOT] Captured screenshot: {filepath}")
                return {
                    "status": "success",
                    "message": f"📸 Screenshot saved!",
                    "data": {
                        "path": str(filepath),
                        "filename": filename,
                        "timestamp": timestamp
                    }
                }
                
            except ImportError:
                logger.warning("[SCREENSHOT] PIL not available, trying pyautogui...")
            
            # Method 2: Try using pyautogui
            try:
                import pyautogui
                
                screenshot = pyautogui.screenshot()
                screenshot.save(str(filepath))
                
                logger.info(f"[SCREENSHOT] Captured screenshot with pyautogui: {filepath}")
                return {
                    "status": "success",
                    "message": f"📸 Screenshot saved!",
                    "data": {
                        "path": str(filepath),
                        "filename": filename,
                        "timestamp": timestamp
                    }
                }
                
            except ImportError:
                logger.warning("[SCREENSHOT] pyautogui not available, trying mss...")
            
            # Method 3: Try using mss (fastest option)
            try:
                import mss
                
                with mss.mss() as sct:
                    # Capture the primary monitor
                    sct.shot(output=str(filepath))
                
                logger.info(f"[SCREENSHOT] Captured screenshot with mss: {filepath}")
                return {
                    "status": "success",
                    "message": f"📸 Screenshot saved!",
                    "data": {
                        "path": str(filepath),
                        "filename": filename,
                        "timestamp": timestamp
                    }
                }
                
            except ImportError:
                pass
            
            # Method 4: Windows native (PowerShell)
            import subprocess
            
            ps_script = f'''
            Add-Type -AssemblyName System.Windows.Forms
            [System.Windows.Forms.Screen]::PrimaryScreen | ForEach-Object {{
                $bitmap = New-Object System.Drawing.Bitmap($_.Bounds.Width, $_.Bounds.Height)
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($_.Bounds.Location, [System.Drawing.Point]::Empty, $_.Bounds.Size)
                $bitmap.Save("{filepath}")
            }}
            '''
            
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and filepath.exists():
                logger.info(f"[SCREENSHOT] Captured screenshot with PowerShell: {filepath}")
                return {
                    "status": "success",
                    "message": f"📸 Screenshot saved!",
                    "data": {
                        "path": str(filepath),
                        "filename": filename,
                        "timestamp": timestamp
                    }
                }
            else:
                return {
                    "status": "error",
                    "message": f"Screenshot failed: {result.stderr}"
                }
                
        except Exception as e:
            logger.error(f"[SCREENSHOT] Error: {e}")
            return {
                "status": "error",
                "message": f"Screenshot failed: {str(e)}"
            }
