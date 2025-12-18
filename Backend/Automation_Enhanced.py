"""
Enhanced Automation System
===========================
Significantly upgraded automation capabilities with:
- Smart app launching
- File operations
- System control
- Browser automation
- Keyboard/mouse control
- Screenshot & clipboard
- Process management
- And much more!
"""

import os
import subprocess
import webbrowser
import keyboard
import pyautogui
import psutil
import shutil
import time
from pathlib import Path
from typing import List, Dict, Optional
from AppOpener import close, open as appopen
from pywhatkit import search, playonyt

class EnhancedAutomation:
    """Enhanced automation with smart capabilities"""
    
    def __init__(self):
        self.common_apps = {
            # Browsers
            "chrome": "chrome.exe",
            "firefox": "firefox.exe",
            "edge": "msedge.exe",
            "brave": "brave.exe",
            
            # Communication
            "discord": "Discord.exe",
            "slack": "slack.exe",
            "teams": "Teams.exe",
            "zoom": "Zoom.exe",
            "skype": "Skype.exe",
            
            # Development
            "vscode": "Code.exe",
            "pycharm": "pycharm64.exe",
            "sublime": "sublime_text.exe",
            "atom": "atom.exe",
            
            # Office
            "word": "WINWORD.EXE",
            "excel": "EXCEL.EXE",
            "powerpoint": "POWERPNT.EXE",
            "notepad": "notepad.exe",
            "notepad++": "notepad++.exe",
            
            # Media
            "spotify": "Spotify.exe",
            "vlc": "vlc.exe",
            "itunes": "iTunes.exe",
            
            # Others
            "calculator": "calc.exe",
            "paint": "mspaint.exe",
            "cmd": "cmd.exe",
            "powershell": "powershell.exe",
        }
        
        self.common_websites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "gmail": "https://mail.google.com",
            "github": "https://github.com",
            "stackoverflow": "https://stackoverflow.com",
            "reddit": "https://www.reddit.com",
            "twitter": "https://twitter.com",
            "facebook": "https://www.facebook.com",
            "instagram": "https://www.instagram.com",
            "linkedin": "https://www.linkedin.com",
            "amazon": "https://www.amazon.com",
            "netflix": "https://www.netflix.com",
        }
    
    # ==================== APP MANAGEMENT ====================
    
    def open_app(self, app_name: str) -> bool:
        """Smart app opening with multiple fallback methods"""
        app_name = app_name.lower().strip()
        
        try:
            # Method 1: Try AppOpener
            appopen(app_name, match_closest=True, output=False)
            print(f"Opened {app_name} via AppOpener")
            return True
        except:
            pass
        
        try:
            # Method 2: Try common apps dictionary
            if app_name in self.common_apps:
                subprocess.Popen(self.common_apps[app_name])
                print(f"Opened {app_name} via subprocess")
                return True
        except:
            pass
        
        try:
            # Method 3: Try as executable
            subprocess.Popen(app_name)
            print(f"Opened {app_name} as executable")
            return True
        except:
            pass
        
        print(f"Could not open {app_name}")
        return False
    
    def close_app(self, app_name: str) -> bool:
        """Smart app closing"""
        app_name = app_name.lower().strip()
        
        try:
            # Method 1: Try AppOpener
            close(app_name, match_closest=True, output=False)
            print(f"Closed {app_name}")
            return True
        except:
            pass
        
        try:
            # Method 2: Kill process by name
            for proc in psutil.process_iter(['name']):
                if app_name in proc.info['name'].lower():
                    proc.kill()
                    print(f"Killed {app_name}")
                    return True
        except:
            pass
        
        print(f"Could not close {app_name}")
        return False
    
    def is_app_running(self, app_name: str) -> bool:
        """Check if app is running"""
        app_name = app_name.lower()
        for proc in psutil.process_iter(['name']):
            if app_name in proc.info['name'].lower():
                return True
        return False
    
    # ==================== BROWSER & WEB ====================
    
    def open_website(self, url_or_name: str) -> bool:
        """Open website by URL or name"""
        url_or_name = url_or_name.lower().strip()
        
        # Check if it's a known website
        if url_or_name in self.common_websites:
            url = self.common_websites[url_or_name]
        elif not url_or_name.startswith('http'):
            url = f"https://{url_or_name}"
        else:
            url = url_or_name
        
        try:
            webbrowser.open(url)
            print(f"Opened {url}")
            return True
        except Exception as e:
            print(f"Could not open {url}: {e}")
            return False
    
    def google_search(self, query: str) -> bool:
        """Search on Google"""
        try:
            search(query)
            print(f"Searched Google for: {query}")
            return True
        except Exception as e:
            print(f"Google search failed: {e}")
            return False
    
    def youtube_search(self, query: str) -> bool:
        """Search on YouTube"""
        try:
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            webbrowser.open(url)
            print(f"Searched YouTube for: {query}")
            return True
        except Exception as e:
            print(f"YouTube search failed: {e}")
            return False
    
    def play_youtube(self, query: str) -> bool:
        """Play video on YouTube"""
        try:
            playonyt(query)
            print(f"Playing on YouTube: {query}")
            return True
        except Exception as e:
            print(f"YouTube play failed: {e}")
            return False
    
    # ==================== SYSTEM CONTROL ====================
    
    def volume_up(self, steps: int = 2) -> bool:
        """Increase volume"""
        try:
            for _ in range(steps):
                keyboard.press_and_release('volume up')
            print(f"Volume increased")
            return True
        except Exception as e:
            print(f"Volume up failed: {e}")
            return False
    
    def volume_down(self, steps: int = 2) -> bool:
        """Decrease volume"""
        try:
            for _ in range(steps):
                keyboard.press_and_release('volume down')
            print(f"Volume decreased")
            return True
        except Exception as e:
            print(f"Volume down failed: {e}")
            return False
    
    def mute(self) -> bool:
        """Mute system"""
        try:
            keyboard.press_and_release('volume mute')
            print(f"System muted")
            return True
        except Exception as e:
            print(f"Mute failed: {e}")
            return False
    
    def unmute(self) -> bool:
        """Unmute system"""
        try:
            keyboard.press_and_release('volume mute')
            print(f"System unmuted")
            return True
        except Exception as e:
            print(f"Unmute failed: {e}")
            return False
    
    def brightness_up(self) -> bool:
        """Increase brightness"""
        try:
            keyboard.press_and_release('brightness up')
            print(f"Brightness increased")
            return True
        except:
            print(f"Brightness control not supported")
            return False
    
    def brightness_down(self) -> bool:
        """Decrease brightness"""
        try:
            keyboard.press_and_release('brightness down')
            print(f"Brightness decreased")
            return True
        except:
            print(f"Brightness control not supported")
            return False
    
    # ==================== FILE OPERATIONS ====================
    
    def create_file(self, filename: str, content: str = "") -> bool:
        """Create a new file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created file: {filename}")
            return True
        except Exception as e:
            print(f"File creation failed: {e}")
            return False
    
    def delete_file(self, filename: str) -> bool:
        """Delete a file"""
        try:
            os.remove(filename)
            print(f"Deleted file: {filename}")
            return True
        except Exception as e:
            print(f"File deletion failed: {e}")
            return False
    
    def create_folder(self, foldername: str) -> bool:
        """Create a new folder"""
        try:
            os.makedirs(foldername, exist_ok=True)
            print(f"Created folder: {foldername}")
            return True
        except Exception as e:
            print(f"Folder creation failed: {e}")
            return False
    
    def delete_folder(self, foldername: str) -> bool:
        """Delete a folder"""
        try:
            shutil.rmtree(foldername)
            print(f"Deleted folder: {foldername}")
            return True
        except Exception as e:
            print(f"Folder deletion failed: {e}")
            return False
    
    # ==================== SCREENSHOT & CLIPBOARD ====================
    
    def take_screenshot(self, filename: str = None) -> bool:
        """Take a screenshot"""
        try:
            if filename is None:
                filename = f"screenshot_{int(time.time())}.png"
            
            screenshot = pyautogui.screenshot()
            screenshot.save(filename)
            print(f"Screenshot saved: {filename}")
            return True
        except Exception as e:
            print(f"Screenshot failed: {e}")
            return False
    
    def copy_to_clipboard(self, text: str) -> bool:
        """Copy text to clipboard"""
        try:
            import pyperclip
            pyperclip.copy(text)
            print(f"Copied to clipboard")
            return True
        except ImportError:
            print(f"pyperclip not installed")
            return False
        except Exception as e:
            print(f"Clipboard copy failed: {e}")
            return False
    
    def paste_from_clipboard(self) -> Optional[str]:
        """Get text from clipboard"""
        try:
            import pyperclip
            text = pyperclip.paste()
            print(f"Pasted from clipboard")
            return text
        except ImportError:
            print(f"pyperclip not installed")
            return None
        except Exception as e:
            print(f"Clipboard paste failed: {e}")
            return None
    
    # ==================== KEYBOARD & MOUSE ====================
    
    def type_text(self, text: str, interval: float = 0.05) -> bool:
        """Type text using keyboard"""
        try:
            pyautogui.write(text, interval=interval)
            print(f"Typed text")
            return True
        except Exception as e:
            print(f"Typing failed: {e}")
            return False
    
    def press_key(self, key: str) -> bool:
        """Press a keyboard key"""
        try:
            keyboard.press_and_release(key)
            print(f"Pressed key: {key}")
            return True
        except Exception as e:
            print(f"Key press failed: {e}")
            return False
    
    def hotkey(self, *keys) -> bool:
        """Press a hotkey combination"""
        try:
            keyboard.press_and_release('+'.join(keys))
            print(f"Pressed hotkey: {'+'.join(keys)}")
            return True
        except Exception as e:
            print(f"Hotkey failed: {e}")
            return False
    
    # ==================== PROCESS MANAGEMENT ====================
    
    def list_running_apps(self) -> List[str]:
        """List all running applications"""
        apps = []
        for proc in psutil.process_iter(['name']):
            try:
                apps.append(proc.info['name'])
            except:
                pass
        return list(set(apps))
    
    def kill_process(self, process_name: str) -> bool:
        """Kill a process by name"""
        try:
            for proc in psutil.process_iter(['name']):
                if process_name.lower() in proc.info['name'].lower():
                    proc.kill()
                    print(f"Killed process: {process_name}")
                    return True
            print(f"Process not found: {process_name}")
            return False
        except Exception as e:
            print(f"Kill process failed: {e}")
            return False
    
    # ==================== SMART AUTOMATION ====================
    
    def execute_command(self, command: str, params: str = "") -> bool:
        """
        Execute automation command intelligently
        
        Args:
            command: Command type (open, close, search, etc.)
            params: Command parameters
        
        Returns:
            True if successful
        """
        command = command.lower().strip()
        params = params.strip()
        
        # App operations
        if command == "open":
            if params in self.common_websites:
                return self.open_website(params)
            else:
                return self.open_app(params)
        
        elif command == "close":
            return self.close_app(params)
        
        # Web operations
        elif command == "search" or command == "google":
            return self.google_search(params)
        
        elif command == "youtube":
            return self.youtube_search(params)
        
        elif command == "play":
            return self.play_youtube(params)
        
        # System operations
        elif command == "volume up":
            return self.volume_up()
        
        elif command == "volume down":
            return self.volume_down()
        
        elif command == "mute":
            return self.mute()
        
        elif command == "unmute":
            return self.unmute()
        
        elif command == "screenshot":
            return self.take_screenshot(params if params else None)
        
        # File operations
        elif command == "create file":
            return self.create_file(params)
        
        elif command == "delete file":
            return self.delete_file(params)
        
        elif command == "create folder":
            return self.create_folder(params)
        
        else:
            print(f"Unknown command: {command}")
            return False

# Global instance
_automation = None

def get_automation() -> EnhancedAutomation:
    """Get global automation instance"""
    global _automation
    if _automation is None:
        _automation = EnhancedAutomation()
    return _automation

# Convenience functions for backward compatibility
def OpenApp(app: str) -> bool:
    return get_automation().open_app(app)

def CloseApp(app: str) -> bool:
    return get_automation().close_app(app)

def GoogleSearch(query: str) -> bool:
    return get_automation().google_search(query)

def YouTubeSearch(query: str) -> bool:
    return get_automation().youtube_search(query)

def PlayYoutube(query: str) -> bool:
    return get_automation().play_youtube(query)

if __name__ == "__main__":
    # Test automation
    auto = EnhancedAutomation()
    
    print("\nTesting Enhanced Automation\n" + "="*50)
    
    # Test app opening
    print("\n1. Opening Chrome...")
    auto.open_app("chrome")
    time.sleep(2)
    
    # Test website
    print("\n2. Opening Google...")
    auto.open_website("google")
    time.sleep(2)
    
    # Test volume
    print("\n3. Testing volume...")
    auto.volume_up()
    time.sleep(1)
    auto.volume_down()
    
    print("\nAutomation test complete!")
