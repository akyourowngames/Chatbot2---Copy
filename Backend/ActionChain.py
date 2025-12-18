"""
Action Chain Executor - Multi-Step Automation
==============================================
Execute complex multi-step commands like form filling
"""

import pyautogui
import keyboard
import time
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Configure pyautogui for safety
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

@dataclass
class Action:
    type: str  # click, type, press, wait, scroll
    params: dict


class ActionChainExecutor:
    """
    Execute multi-step automation chains.
    Examples:
    - "Fill this form with my details"
    - "Open notepad, type hello, and save"
    - "Take screenshot and paste in paint"
    """
    
    def __init__(self):
        self.default_delay = 0.5
        self.user_data = {
            "name": "User",
            "email": "user@example.com",
            "phone": "",
            "address": ""
        }
    
    def set_user_data(self, data: Dict[str, str]):
        """Set user data for form filling"""
        self.user_data.update(data)
    
    def parse_and_execute(self, command: str) -> Dict[str, Any]:
        """
        Parse natural language command and execute actions.
        """
        command_lower = command.lower()
        
        results = []
        
        # Form filling
        if any(k in command_lower for k in ["fill", "form", "fill form", "fill this"]):
            return self.fill_current_form()
        
        # Type text
        if "type" in command_lower:
            text_match = re.search(r"type\s+['\"]?(.+?)['\"]?\s*(?:and|$)", command, re.IGNORECASE)
            if text_match:
                text = text_match.group(1).strip()
                self.type_text(text)
                results.append(f"Typed: {text[:50]}...")
        
        # Click
        if "click" in command_lower:
            if "right click" in command_lower:
                pyautogui.rightClick()
                results.append("Right clicked")
            else:
                pyautogui.click()
                results.append("Clicked")
        
        # Keyboard shortcuts
        if "save" in command_lower and "save as" not in command_lower:
            self.press_keys("ctrl", "s")
            results.append("Saved (Ctrl+S)")
        
        if "save as" in command_lower:
            self.press_keys("ctrl", "shift", "s")
            results.append("Save As dialog (Ctrl+Shift+S)")
        
        if "copy" in command_lower:
            self.press_keys("ctrl", "c")
            results.append("Copied")
        
        if "paste" in command_lower:
            self.press_keys("ctrl", "v")
            results.append("Pasted")
        
        if "select all" in command_lower:
            self.press_keys("ctrl", "a")
            results.append("Selected all")
        
        if "undo" in command_lower:
            self.press_keys("ctrl", "z")
            results.append("Undone")
        
        if "redo" in command_lower:
            self.press_keys("ctrl", "y")
            results.append("Redone")
        
        # Tab navigation
        if "next field" in command_lower or "tab" in command_lower:
            pyautogui.press("tab")
            results.append("Moved to next field")
        
        if "previous field" in command_lower or "shift tab" in command_lower:
            self.press_keys("shift", "tab")
            results.append("Moved to previous field")
        
        # Enter/Submit
        if "submit" in command_lower or "enter" in command_lower:
            pyautogui.press("enter")
            results.append("Pressed Enter")
        
        # Scroll
        if "scroll down" in command_lower:
            pyautogui.scroll(-3)
            results.append("Scrolled down")
        
        if "scroll up" in command_lower:
            pyautogui.scroll(3)
            results.append("Scrolled up")
        
        # New line
        if "new line" in command_lower:
            pyautogui.press("enter")
            results.append("New line")
        
        # Delete
        if "delete" in command_lower and "file" not in command_lower:
            pyautogui.press("delete")
            results.append("Deleted")
        
        if "backspace" in command_lower:
            pyautogui.press("backspace")
            results.append("Backspace")
        
        if results:
            return {
                "status": "success",
                "message": f"✅ Executed: {', '.join(results)}",
                "actions": results
            }
        
        return {
            "status": "error",
            "message": "Could not parse command. Try: 'type hello', 'click', 'save', 'fill form'"
        }
    
    def fill_current_form(self) -> Dict[str, Any]:
        """
        Fill the currently focused form field by field.
        Uses Tab to move between fields.
        """
        try:
            filled = []
            
            # Common form fields order: name, email, phone, message
            fields = ["name", "email", "phone", "address"]
            
            for field in fields:
                if self.user_data.get(field):
                    self.type_text(self.user_data[field])
                    filled.append(field)
                    time.sleep(0.3)
                    pyautogui.press("tab")
                    time.sleep(0.3)
            
            return {
                "status": "success",
                "message": f"📝 Filled form fields: {', '.join(filled)}",
                "fields": filled
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Form fill error: {str(e)}"}
    
    def type_text(self, text: str, interval: float = 0.02):
        """Type text with optional interval between keys"""
        pyautogui.typewrite(text, interval=interval) if text.isascii() else pyautogui.write(text)
    
    def press_keys(self, *keys):
        """Press key combination"""
        pyautogui.hotkey(*keys)
    
    def execute_chain(self, actions: List[Action]) -> Dict[str, Any]:
        """Execute a chain of actions"""
        results = []
        
        for action in actions:
            try:
                if action.type == "type":
                    self.type_text(action.params.get("text", ""))
                    results.append(f"Typed: {action.params.get('text', '')[:20]}")
                
                elif action.type == "click":
                    x = action.params.get("x")
                    y = action.params.get("y")
                    if x and y:
                        pyautogui.click(x, y)
                    else:
                        pyautogui.click()
                    results.append("Clicked")
                
                elif action.type == "press":
                    keys = action.params.get("keys", [])
                    if keys:
                        pyautogui.hotkey(*keys)
                        results.append(f"Pressed: {'+'.join(keys)}")
                
                elif action.type == "wait":
                    seconds = action.params.get("seconds", 1)
                    time.sleep(seconds)
                    results.append(f"Waited {seconds}s")
                
                elif action.type == "scroll":
                    amount = action.params.get("amount", -3)
                    pyautogui.scroll(amount)
                    results.append(f"Scrolled {amount}")
                
                time.sleep(self.default_delay)
                
            except Exception as e:
                results.append(f"Error: {e}")
        
        return {
            "status": "success",
            "message": f"Executed {len(actions)} actions",
            "results": results
        }
    
    def get_mouse_position(self) -> Dict[str, int]:
        """Get current mouse position"""
        x, y = pyautogui.position()
        return {"x": x, "y": y}
    
    def move_mouse(self, x: int, y: int, duration: float = 0.3):
        """Move mouse to position"""
        pyautogui.moveTo(x, y, duration=duration)


# Global instance
action_chain = ActionChainExecutor()


if __name__ == "__main__":
    print("Action Chain Executor ready!")
    print("Current mouse position:", action_chain.get_mouse_position())
