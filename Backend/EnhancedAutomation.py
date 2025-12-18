"""
Enhanced System Automation - Complete System Control
====================================================
All automation functions including screenshots, volume, brightness, etc.
"""

import pyautogui
import subprocess
import os
import platform
from datetime import datetime
from typing import Optional
import json

class EnhancedAutomation:
    def __init__(self):
        self.screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Data", "Screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)
        self.system = platform.system()
    
    def take_screenshot(self, filename: Optional[str] = None) -> str:
        """Take a screenshot and save it"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
        
        filepath = os.path.join(self.screenshots_dir, filename)
        screenshot = pyautogui.screenshot()
        screenshot.save(filepath)
        
        print(f"✅ Screenshot saved: {filepath}")
        return filepath
    
    def increase_volume(self, amount: int = 10) -> str:
        """Increase system volume"""
        try:
            if self.system == "Windows":
                # Use nircmd or powershell
                for _ in range(amount // 2):
                    pyautogui.press('volumeup')
                return f"✅ Volume increased by {amount}%"
            else:
                return "⚠️ Volume control not supported on this OS"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def decrease_volume(self, amount: int = 10) -> str:
        """Decrease system volume"""
        try:
            if self.system == "Windows":
                for _ in range(amount // 2):
                    pyautogui.press('volumedown')
                return f"✅ Volume decreased by {amount}%"
            else:
                return "⚠️ Volume control not supported on this OS"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def mute_volume(self) -> str:
        """Mute/unmute system volume"""
        try:
            pyautogui.press('volumemute')
            return "✅ Volume toggled"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def increase_brightness(self, amount: int = 10) -> str:
        """Increase screen brightness"""
        try:
            if self.system == "Windows":
                # Use powershell to adjust brightness
                script = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{min(100, amount)})"
                subprocess.run(["powershell", "-Command", script], capture_output=True)
                return f"✅ Brightness increased"
            else:
                return "⚠️ Brightness control not supported on this OS"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def decrease_brightness(self, amount: int = 10) -> str:
        """Decrease screen brightness"""
        try:
            if self.system == "Windows":
                script = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1,{max(0, amount)})"
                subprocess.run(["powershell", "-Command", script], capture_output=True)
                return f"✅ Brightness decreased"
            else:
                return "⚠️ Brightness control not supported on this OS"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def lock_screen(self) -> str:
        """Lock the screen"""
        try:
            if self.system == "Windows":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
                return "✅ Screen locked"
            elif self.system == "Darwin":  # macOS
                subprocess.run(["/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession", "-suspend"])
                return "✅ Screen locked"
            else:
                subprocess.run(["gnome-screensaver-command", "-l"])
                return "✅ Screen locked"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def shutdown(self, delay: int = 0) -> str:
        """Shutdown the computer"""
        try:
            if self.system == "Windows":
                subprocess.run(["shutdown", "/s", "/t", str(delay)])
                return f"✅ Shutdown scheduled in {delay} seconds"
            else:
                subprocess.run(["shutdown", "-h", f"+{delay//60}"])
                return f"✅ Shutdown scheduled"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def restart(self, delay: int = 0) -> str:
        """Restart the computer"""
        try:
            if self.system == "Windows":
                subprocess.run(["shutdown", "/r", "/t", str(delay)])
                return f"✅ Restart scheduled in {delay} seconds"
            else:
                subprocess.run(["shutdown", "-r", f"+{delay//60}"])
                return f"✅ Restart scheduled"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def sleep(self) -> str:
        """Put computer to sleep"""
        try:
            if self.system == "Windows":
                subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
                return "✅ Computer going to sleep"
            elif self.system == "Darwin":
                subprocess.run(["pmset", "sleepnow"])
                return "✅ Computer going to sleep"
            else:
                subprocess.run(["systemctl", "suspend"])
                return "✅ Computer going to sleep"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def hibernate(self) -> str:
        """Hibernate the computer"""
        try:
            if self.system == "Windows":
                subprocess.run(["shutdown", "/h"])
                return "✅ Computer hibernating"
            else:
                return "⚠️ Hibernate not supported on this OS"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def open_app(self, app_name: str) -> str:
        """Open an application"""
        try:
            if self.system == "Windows":
                subprocess.Popen(app_name, shell=True)
                return f"✅ Opening {app_name}"
            else:
                subprocess.Popen(["open", "-a", app_name])
                return f"✅ Opening {app_name}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def close_app(self, app_name: str) -> str:
        """Close an application"""
        try:
            if self.system == "Windows":
                subprocess.run(["taskkill", "/IM", f"{app_name}.exe", "/F"], capture_output=True)
                return f"✅ Closed {app_name}"
            else:
                subprocess.run(["killall", app_name])
                return f"✅ Closed {app_name}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def type_text(self, text: str) -> str:
        """Type text using keyboard"""
        try:
            pyautogui.write(text, interval=0.05)
            return f"✅ Typed: {text[:50]}..."
        except Exception as e:
            return f"❌ Error: {e}"
    
    def press_key(self, key: str) -> str:
        """Press a keyboard key"""
        try:
            pyautogui.press(key)
            return f"✅ Pressed {key}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def hotkey(self, *keys) -> str:
        """Press a hotkey combination"""
        try:
            pyautogui.hotkey(*keys)
            return f"✅ Pressed {'+'.join(keys)}"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def get_battery_status(self) -> dict:
        """Get battery status"""
        try:
            import psutil
            battery = psutil.sensors_battery()
            if battery:
                return {
                    "percent": battery.percent,
                    "plugged": battery.power_plugged,
                    "time_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Charging"
                }
            else:
                return {"error": "No battery found"}
        except Exception as e:
            return {"error": str(e)}
    
    def copy_to_clipboard(self, text: str) -> str:
        """Copy text to clipboard"""
        try:
            import pyperclip
            pyperclip.copy(text)
            return f"✅ Copied to clipboard: {text[:50]}..."
        except Exception as e:
            return f"❌ Error: {e}"
    
    def paste_from_clipboard(self) -> str:
        """Get text from clipboard"""
        try:
            import pyperclip
            text = pyperclip.paste()
            return text
        except Exception as e:
            return f"❌ Error: {e}"
    
    def minimize_all_windows(self) -> str:
        """Minimize all windows (show desktop)"""
        try:
            if self.system == "Windows":
                pyautogui.hotkey('win', 'd')
                return "✅ All windows minimized"
            else:
                return "⚠️ Not supported on this OS"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def maximize_window(self) -> str:
        """Maximize current window"""
        try:
            if self.system == "Windows":
                pyautogui.hotkey('win', 'up')
                return "✅ Window maximized"
            else:
                return "⚠️ Not supported on this OS"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def switch_window(self) -> str:
        """Switch between windows (Alt+Tab)"""
        try:
            pyautogui.hotkey('alt', 'tab')
            return "✅ Switched window"
        except Exception as e:
            return f"❌ Error: {e}"
    
    def execute_command(self, command: str) -> str:
        """Execute a system command based on natural language"""
        command_lower = command.lower()
        
        # Screenshot commands
        if any(word in command_lower for word in ["screenshot", "screen shot", "capture screen", "take screenshot"]):
            return self.take_screenshot()
        
        # Volume commands
        elif any(word in command_lower for word in ["increase volume", "volume up", "louder", "raise volume"]):
            return self.increase_volume()
        elif any(word in command_lower for word in ["decrease volume", "volume down", "quieter", "lower volume"]):
            return self.decrease_volume()
        elif "mute" in command_lower or "unmute" in command_lower:
            return self.mute_volume()
        
        # Brightness commands
        elif any(word in command_lower for word in ["increase brightness", "brightness up", "brighter"]):
            return self.increase_brightness()
        elif any(word in command_lower for word in ["decrease brightness", "brightness down", "dimmer"]):
            return self.decrease_brightness()
        
        # Power commands
        elif "lock" in command_lower and ("screen" in command_lower or "computer" in command_lower):
            return self.lock_screen()
        elif "shutdown" in command_lower or "shut down" in command_lower or "power off" in command_lower:
            # Check for delay
            if "in" in command_lower:
                try:
                    import re
                    match = re.search(r'in (\d+)', command_lower)
                    if match:
                        delay = int(match.group(1)) * 60  # Convert minutes to seconds
                        return self.shutdown(delay)
                except:
                    pass
            return self.shutdown()
        elif "restart" in command_lower or "reboot" in command_lower:
            return self.restart()
        elif "sleep" in command_lower:
            return self.sleep()
        elif "hibernate" in command_lower:
            return self.hibernate()
        
        # Window management
        elif any(word in command_lower for word in ["minimize all", "show desktop", "hide all"]):
            return self.minimize_all_windows()
        elif "maximize" in command_lower:
            return self.maximize_window()
        elif any(word in command_lower for word in ["switch window", "alt tab", "next window"]):
            return self.switch_window()
        
        # Clipboard commands
        elif "copy" in command_lower and "clipboard" in command_lower:
            text = command_lower.replace("copy", "").replace("to clipboard", "").strip()
            return self.copy_to_clipboard(text)
        elif "paste" in command_lower or "clipboard" in command_lower:
            return self.paste_from_clipboard()
        
        # App commands
        elif "open" in command_lower:
            app = command_lower.replace("open", "").strip()
            # Common app mappings
            app_mappings = {
                "notepad": "notepad",
                "calculator": "calc",
                "chrome": "chrome",
                "firefox": "firefox",
                "edge": "msedge",
                "explorer": "explorer",
                "cmd": "cmd",
                "terminal": "cmd",
                "powershell": "powershell",
                "word": "winword",
                "excel": "excel",
                "powerpoint": "powerpnt"
            }
            for key, value in app_mappings.items():
                if key in app:
                    app = value
                    break
            return self.open_app(app)
        elif "close" in command_lower:
            app = command_lower.replace("close", "").strip()
            return self.close_app(app)
        
        # Battery status
        elif "battery" in command_lower:
            status = self.get_battery_status()
            if "error" in status:
                return f"❌ {status['error']}"
            return f"🔋 Battery: {status['percent']}% {'(Charging)' if status['plugged'] else '(Not Charging)'}"
        
        else:
            return f"⚠️ Command not recognized: {command}"

# Global instance
enhanced_automation = EnhancedAutomation()

if __name__ == "__main__":
    # Test
    print("Testing Enhanced Automation...")
    print(enhanced_automation.take_screenshot())
    print(enhanced_automation.get_battery_status())
