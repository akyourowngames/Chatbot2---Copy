"""
Advanced Window Manager - Beast Mode
=====================================
God-level window layout, snap control, and workspace optimization.
Uses win32gui with ultra-strict filtering to remove background/fake windows.
"""

import pygetwindow as gw
import pyautogui
import win32gui
import win32con
import win32api
import time
from typing import List, Dict, Optional

class WindowManager:
    def __init__(self):
        self.screen_width, self.screen_height = pyautogui.size()

    def is_real_window(self, hwnd):
        """Ultra-strict win32 filtering for user-facing applications"""
        if not win32gui.IsWindowVisible(hwnd): return False
        title = win32gui.GetWindowText(hwnd)
        if not title: return False
        
        # Filter by style
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if ex_style & win32con.WS_EX_TOOLWINDOW: return False
        
        # Must have a system menu or be a top-level app window
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        if not (style & win32con.WS_CAPTION): return False
        
        # Blacklist common background junk
        junk = [
            'Microsoft Text Input', 'Program Manager', 'Settings', 
            'NVIDIA', 'Task Switching', 'KAI', 'Chatbot', 'Cortana', 
            'Media viewer', 'Calculators', 'Host Process', 'Experience'
        ]
        if any(j.lower() in title.lower() for j in junk): return False
        
        # Filter by dimensions (Ignore invisible 1x1 windows)
        rect = win32gui.GetWindowRect(hwnd)
        w = rect[2] - rect[0]
        h = rect[3] - rect[1]
        if w <= 10 or h <= 10: return False
        
        return True

    def get_windows(self, include_minimized=True) -> List[gw.Win32Window]:
        """Get only REAL application windows"""
        windows = []
        
        def callback(hwnd, extra):
            if self.is_real_window(hwnd):
                try:
                    win = gw.Win32Window(hwnd)
                    if include_minimized or not win.isMinimized:
                        windows.append(win)
                except: pass
        
        win32gui.EnumWindows(callback, None)
        # Final filter: remove duplicates (sometimes UWP apps show twice)
        seen_titles = set()
        unique_windows = []
        for w in windows:
            if w.title not in seen_titles:
                unique_windows.append(w)
                seen_titles.add(w.title)
        return unique_windows

    # ==================== LAYOUT ENGINE (BEAST) ====================

    def arrange_grid(self):
        """Arrange all visible windows into a perfect grid"""
        windows = self.get_windows(include_minimized=False)
        count = len(windows)
        if count == 0: return "No active windows to arrange"

        cols = int(count**0.5)
        if cols == 0: cols = 1
        rows = (count + cols - 1) // cols
        
        w = self.screen_width // cols
        h = (self.screen_height - 60) // rows # Safe margin for taskbar
        
        for i, win in enumerate(windows):
            r, c = i // cols, i % cols
            try:
                win.restore()
                win.resizeTo(w, h)
                win.moveTo(c * w, r * h)
            except: continue
        
        return f"Grid layout applied to: {', '.join([win.title for win in windows])}"

    def focus_mode(self, app_name: str):
        windows = self.get_windows()
        target = None
        for win in windows:
            if app_name.lower() in win.title.lower():
                target = win
            else:
                try: win.minimize()
                except: pass
        if target:
            try:
                target.restore()
                target.maximize()
                target.activate()
                return f"Focus Mode: {target.title}"
            except: return f"Found {app_name} but failed to focus"
        return f"App '{app_name}' not found"

    def list_open_titles(self):
        return [w.title for w in self.get_windows()]

    def minimize_all(self):
        pyautogui.hotkey('win', 'd')
        return "Desktop shown"

# Global instance
window_manager = WindowManager()

# Bridge Functions
def list_apps(): 
    titles = window_manager.list_open_titles()
    return "\n".join([f"- {t}" for t in titles]) if titles else "No active user windows found."
def grid_layout(): return window_manager.arrange_grid()
