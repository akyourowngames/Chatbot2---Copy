"""
Kai Local Agent - System Control Executor
==========================================
Executor for safe system controls:
- Volume (set, up, down, mute, unmute)
- Brightness (set, up, down)
- Lock screen

Security: All actions are bounded and reversible.
No shutdown, restart, or destructive actions allowed.
"""

import sys
import ctypes
import time
from typing import Dict, Any

from .base import BaseExecutor

# Configure logging
import logging
logger = logging.getLogger("KaiLocalAgent")


class SystemControlExecutor(BaseExecutor):
    """Executor for safe system controls."""
    
    # Windows Virtual Key Codes
    VK_VOLUME_MUTE = 0xAD
    VK_VOLUME_DOWN = 0xAE
    VK_VOLUME_UP = 0xAF
    
    @property
    def command_name(self) -> str:
        return "system_control"
    
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a system control action."""
        action = params.get("action", "").lower()
        level = params.get("level")
        
        # Validate level if provided
        if level is not None:
            try:
                level = int(level)
                level = max(0, min(100, level))  # Clamp to 0-100
            except (ValueError, TypeError):
                return {"status": "error", "message": f"Invalid level '{level}'. Must be 0-100."}
        
        # Route to appropriate handler
        if action in ["set_volume", "volume_up", "volume_down"]:
            return self._handle_volume(action, level)
        elif action in ["mute", "unmute", "toggle_mute"]:
            return self._handle_mute(action)
        elif action in ["set_brightness", "brightness_up", "brightness_down"]:
            return self._handle_brightness(action, level)
        elif action == "lock_screen":
            return self._handle_lock()
        else:
            return {"status": "error", "message": f"Unknown action '{action}'"}
    
    def _press_key(self, vk_code: int, times: int = 1, delay: float = 0.01):
        """Press a virtual key multiple times."""
        for _ in range(times):
            ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)  # Key down
            ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)  # Key up
            time.sleep(delay)
    
    def _handle_volume(self, action: str, level: int = None) -> Dict[str, Any]:
        """Handle volume controls using keyboard media keys."""
        if sys.platform != "win32":
            return {"status": "error", "message": "Volume control only supported on Windows"}
        
        try:
            if action == "set_volume":
                if level is None:
                    return {"status": "error", "message": "Level required for set_volume"}
                
                # Set to 0 first, then increase to target
                # Each key press is approximately 2% volume
                self._press_key(self.VK_VOLUME_DOWN, times=50, delay=0.005)  # Get to 0
                presses_needed = level // 2
                self._press_key(self.VK_VOLUME_UP, times=presses_needed, delay=0.005)
                
                logger.info(f"[SYSTEM_CONTROL] Volume set to {level}%")
                return {
                    "status": "success",
                    "message": f"🔊 Volume set to {level}%",
                    "data": {"volume": level}
                }
            
            elif action == "volume_up":
                self._press_key(self.VK_VOLUME_UP, times=5)  # ~10%
                logger.info("[SYSTEM_CONTROL] Volume increased")
                return {"status": "success", "message": "🔊 Volume increased", "data": {"change": "+10%"}}
            
            elif action == "volume_down":
                self._press_key(self.VK_VOLUME_DOWN, times=5)  # ~10%
                logger.info("[SYSTEM_CONTROL] Volume decreased")
                return {"status": "success", "message": "🔉 Volume decreased", "data": {"change": "-10%"}}
                
        except Exception as e:
            logger.error(f"[SYSTEM_CONTROL] Volume error: {e}")
            return {"status": "error", "message": f"Volume control failed: {str(e)}"}
    
    def _handle_mute(self, action: str) -> Dict[str, Any]:
        """Handle mute/unmute using media key."""
        if sys.platform != "win32":
            return {"status": "error", "message": "Mute control only supported on Windows"}
        
        try:
            self._press_key(self.VK_VOLUME_MUTE)
            
            if action == "mute":
                logger.info("[SYSTEM_CONTROL] Audio muted")
                return {"status": "success", "message": "🔇 Audio muted", "data": {"muted": True}}
            elif action == "unmute":
                logger.info("[SYSTEM_CONTROL] Audio unmuted")
                return {"status": "success", "message": "🔊 Audio unmuted", "data": {"muted": False}}
            else:
                logger.info("[SYSTEM_CONTROL] Audio toggled")
                return {"status": "success", "message": "🔇 Audio toggled", "data": {"toggled": True}}
                
        except Exception as e:
            logger.error(f"[SYSTEM_CONTROL] Mute error: {e}")
            return {"status": "error", "message": f"Mute control failed: {str(e)}"}
    
    def _handle_brightness(self, action: str, level: int = None) -> Dict[str, Any]:
        """Handle brightness controls."""
        if sys.platform != "win32":
            return {"status": "error", "message": "Brightness control only supported on Windows"}
        
        try:
            import screen_brightness_control as sbc
            
            current = sbc.get_brightness()
            if isinstance(current, list):
                current = current[0]
            
            if action == "set_brightness":
                if level is None:
                    return {"status": "error", "message": "Level required for set_brightness"}
                sbc.set_brightness(level)
                logger.info(f"[SYSTEM_CONTROL] Brightness set to {level}%")
                return {"status": "success", "message": f"🔆 Brightness set to {level}%", "data": {"brightness": level}}
            
            elif action == "brightness_up":
                new_level = min(100, current + 10)
                sbc.set_brightness(new_level)
                logger.info(f"[SYSTEM_CONTROL] Brightness increased to {new_level}%")
                return {"status": "success", "message": f"🔆 Brightness increased to {new_level}%", "data": {"brightness": new_level}}
            
            elif action == "brightness_down":
                new_level = max(0, current - 10)
                sbc.set_brightness(new_level)
                logger.info(f"[SYSTEM_CONTROL] Brightness decreased to {new_level}%")
                return {"status": "success", "message": f"🔅 Brightness decreased to {new_level}%", "data": {"brightness": new_level}}
                
        except ImportError:
            return {"status": "error", "message": "Brightness control requires: pip install screen-brightness-control"}
        except Exception as e:
            logger.error(f"[SYSTEM_CONTROL] Brightness error: {e}")
            return {"status": "error", "message": f"Brightness control failed: {str(e)}"}
    
    def _handle_lock(self) -> Dict[str, Any]:
        """Lock the Windows workstation."""
        if sys.platform != "win32":
            return {"status": "error", "message": "Lock screen only supported on Windows"}
        
        try:
            logger.info("[SYSTEM_CONTROL] Locking screen...")
            result = ctypes.windll.user32.LockWorkStation()
            if result:
                return {"status": "success", "message": "🔒 Screen locked", "data": {"locked": True}}
            else:
                return {"status": "error", "message": "Failed to lock screen"}
        except Exception as e:
            logger.error(f"[SYSTEM_CONTROL] Lock error: {e}")
            return {"status": "error", "message": f"Lock screen failed: {str(e)}"}
