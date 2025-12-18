import time
import pyautogui
import ctypes
from ctypes import wintypes
import subprocess
import threading
import sys
import os

class AutomationChain:
    """
    Handles stateful automation with feedback loops.
    Verifies window states, handles focus, and executes complex interaction chains.
    """
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
        # Define types for ctypes
        self.user32.GetForegroundWindow.restype = wintypes.HWND
        self.user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        self.user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        self.user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        self.user32.IsWindowVisible.argtypes = [wintypes.HWND]

    def _get_active_window_title(self):
        """Get title of currently focused window"""
        hwnd = self.user32.GetForegroundWindow()
        length = self.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        self.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value

    def find_window(self, keyword):
        """Find a window handle by keyword in title"""
        keyword = keyword.lower()
        found_hwnds = []
        
        def callback(hwnd, extra):
            if self.user32.IsWindowVisible(hwnd):
                length = self.user32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.lower()
                if keyword in title:
                    found_hwnds.append(hwnd)
            return True
            
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        self.user32.EnumWindows(WNDENUMPROC(callback), 0)
        
        return found_hwnds[0] if found_hwnds else None

    def verify_app_state(self, app_keyword, timeout=5):
        """
        Verify if an app is open and ready.
        Returns: (bool, str) -> (Success, Message)
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            title = self._get_active_window_title().lower()
            if app_keyword.lower() in title:
                return True, f"Verified: '{title}' is active."
            
            # If not active, try to find and focus
            hwnd = self.find_window(app_keyword)
            if hwnd:
                self.user32.ShowWindow(hwnd, 9) # SW_RESTORE
                self.user32.SetForegroundWindow(hwnd)
                time.sleep(0.5)
                # Check again
                if app_keyword.lower() in self._get_active_window_title().lower():
                    return True, f"Found and focused: '{app_keyword}'."
            
            time.sleep(0.5)
            
        return False, f"Could not verify '{app_keyword}' as active window."

    def open_and_verify(self, app_command, app_keyword):
        """
        Open an app and verify it loaded.
        """
        print(f"[CHAIN] Opening: {app_command}")
        subprocess.Popen(app_command, shell=True)
        
        # Wait up to 10 seconds for launch
        success, msg = self.verify_app_state(app_keyword, timeout=10)
        return success, msg

    def type_content(self, text, interval=0.005):
        """
        Type content into the active window.
        Assumes window is already focused.
        """
        try:
            # Safety check
            active = self._get_active_window_title()
            print(f"[CHAIN] Typing into: {active}")
            
            # Simple typing
            # For long text, pyperclip is faster and safer (paste), but typing looks cooler ("ghost")
            # User asked for "write a letter" -> Typing effect is nice.
            
            pyautogui.write(text, interval=interval)
            return True, "Typing complete."
        except Exception as e:
            return False, f"Typing failed: {e}"

    def save_file(self, filename):
        """
        Automate Save As dialog.
        Assumes standard Ctrl+S shortcut.
        """
        try:
            pyautogui.hotkey('ctrl', 's')
            time.sleep(1.0) # Wait for dialog
            
            # Check if dialog appeared? Hard. Just type.
            pyautogui.write(filename)
            time.sleep(0.5)
            pyautogui.press('enter')
            return True, f"Attempted to save as {filename}"
        except Exception as e:
            return False, f"Save failed: {e}"

    def prepare_typing(self, text):
        """
        Check active window and propose typing (requires confirmation).
        Returns: (bool, str, window_title)
        """
        active = self._get_active_window_title()
        if not active:
            return False, "No active window found.", None
            
        self.pending_text = text
        self.pending_window = active
        return True, f"I found '{active}'. Should I write it there?", active

    def confirm_typing(self):
        """Execute pending typing after user confirmation"""
        if not hasattr(self, 'pending_text') or not self.pending_text:
            return False, "Nothing pending to write."
            
        # Just type into current active window
        result = self.type_content(self.pending_text)
        
        # Clear pending
        self.pending_text = None
        self.pending_window = None
        
        return result

    def has_pending(self):
        """Check if there's pending content"""
        return hasattr(self, 'pending_text') and self.pending_text is not None

# Singleton instance
automation_chain = AutomationChain()
