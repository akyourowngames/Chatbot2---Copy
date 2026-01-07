"""
Kai Local Agent - Write Notepad Executor
=========================================
Executor for the 'write_notepad' command.
Writes text into Windows Notepad in a controlled, auditable way.

Security:
- Only targets Windows Notepad (window title verification)
- No raw key codes or control characters
- Text length limit enforced
- No file save operations
"""

import subprocess
import sys
import time
import logging
from typing import Dict, Any

from .base import BaseExecutor


logger = logging.getLogger("KaiLocalAgent")


class WriteNotepadExecutor(BaseExecutor):
    """
    Executor for writing text into Windows Notepad.
    
    This is a controlled capability - not generic keyboard automation.
    """
    
    # Maximum text length (10KB)
    MAX_TEXT_LENGTH = 10000
    
    # Notepad window title patterns
    NOTEPAD_TITLES = ["Notepad", "Untitled - Notepad", "*Untitled - Notepad"]
    
    @property
    def command_name(self) -> str:
        return "write_notepad"
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write text into Windows Notepad.
        
        Args:
            params: {"text": "string to write"}
        
        Returns:
            Dict with status and message
        """
        # Only supported on Windows
        if sys.platform != "win32":
            return {
                "status": "error",
                "message": "write_notepad is only supported on Windows"
            }
        
        text = params.get("text", "")
        
        # Validate text
        if not text:
            return {
                "status": "error",
                "message": "Text cannot be empty"
            }
        
        if len(text) > self.MAX_TEXT_LENGTH:
            return {
                "status": "error",
                "message": f"Text too long ({len(text)} chars). Maximum: {self.MAX_TEXT_LENGTH}"
            }
        
        # Sanitize text - remove control characters except newline
        sanitized_text = "".join(
            c for c in text 
            if c == '\n' or c == '\r' or (ord(c) >= 32 and ord(c) < 127) or ord(c) > 127
        )
        
        try:
            # Import Windows-specific modules
            import pyautogui
            import pygetwindow as gw
            
            # Step 1: Check if Notepad is running, if not launch it
            notepad_window = self._find_notepad_window(gw)
            
            if not notepad_window:
                logger.info("[WRITE_NOTEPAD] Notepad not running, launching...")
                subprocess.Popen(["notepad.exe"])
                time.sleep(1.0)  # Wait for Notepad to open
                notepad_window = self._find_notepad_window(gw)
                
                if not notepad_window:
                    return {
                        "status": "error",
                        "message": "Failed to launch Notepad"
                    }
            
            # Step 2: Focus the Notepad window
            logger.info(f"[WRITE_NOTEPAD] Focusing window: {notepad_window.title}")
            
            # Try multiple methods to focus the window
            focus_success = False
            for attempt in range(3):
                try:
                    notepad_window.activate()
                    time.sleep(0.3)
                    focus_success = True
                    break
                except Exception:
                    try:
                        # Fallback: minimize and restore
                        notepad_window.minimize()
                        time.sleep(0.1)
                        notepad_window.restore()
                        time.sleep(0.3)
                        focus_success = True
                        break
                    except Exception:
                        time.sleep(0.2)
                        continue
            
            # Step 3: Verify Notepad is focused (security check)
            # Check multiple times in case of delay
            for verify_attempt in range(3):
                active_window = gw.getActiveWindow()
                if active_window and self._is_notepad_window(active_window.title):
                    break
                time.sleep(0.2)
            
            if not active_window or not self._is_notepad_window(active_window.title):
                # Last resort: try clicking on the notepad window
                try:
                    notepad_window.activate()
                    time.sleep(0.5)
                    active_window = gw.getActiveWindow()
                except:
                    pass
                    
                if not active_window or not self._is_notepad_window(active_window.title):
                    return {
                        "status": "error", 
                        "message": f"Could not focus Notepad window (security check failed). Active: {active_window.title if active_window else 'None'}"
                    }
            
            # Step 4: Type the text
            logger.info(f"[WRITE_NOTEPAD] Typing {len(sanitized_text)} characters...")
            
            # Use pyautogui with typewrite for ASCII, write for unicode
            # pyautogui.write() handles unicode better
            pyautogui.write(sanitized_text, interval=0.01)
            
            logger.info(f"[WRITE_NOTEPAD] Successfully wrote {len(sanitized_text)} chars to Notepad")
            
            return {
                "status": "success",
                "message": f"Successfully wrote {len(sanitized_text)} characters to Notepad",
                "data": {
                    "chars_written": len(sanitized_text)
                }
            }
            
        except ImportError as e:
            missing = str(e).split("'")[-2] if "'" in str(e) else "required module"
            return {
                "status": "error",
                "message": f"Missing dependency: {missing}. Install with: pip install pyautogui pygetwindow"
            }
        except Exception as e:
            logger.error(f"[WRITE_NOTEPAD] Error: {e}")
            return {
                "status": "error",
                "message": f"Failed to write to Notepad: {str(e)}"
            }
    
    def _find_notepad_window(self, gw):
        """Find an open Notepad window."""
        windows = gw.getAllWindows()
        for window in windows:
            if self._is_notepad_window(window.title):
                return window
        return None
    
    def _is_notepad_window(self, title: str) -> bool:
        """Check if a window title belongs to Notepad."""
        if not title:
            return False
        title_lower = title.lower()
        # Match "Notepad", "Untitled - Notepad", "filename.txt - Notepad"
        return "notepad" in title_lower
