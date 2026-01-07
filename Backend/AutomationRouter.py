"""
Automation Router - Routes Automation Payloads to Local Agent
==============================================================
Handles the routing of automation commands from Kai (brain) to
the Local Agent (hands) via WebSocket.

Responsibilities:
- Send automation payloads to the correct device
- Wait for execution results
- Handle failures with fallback logic
- Report results back to the cognitive pipeline
"""

import uuid
import time
from datetime import datetime
from typing import Dict, Optional, Tuple, Callable


class AutomationRouter:
    """
    Routes automation payloads to local agent and handles results.
    
    Uses LocalAgentAPI for task queuing and AgentWebSocket for real-time delivery.
    """
    
    def __init__(self):
        """Initialize the automation router."""
        self.default_timeout = 30  # seconds
        self.retry_limit = 0  # No blind retries as per spec
        
        # Result callbacks for async notification
        self._result_callbacks: Dict[str, Callable] = {}
    
    def route(self, payload: Dict, user_id: str = None, device_id: str = None) -> Dict:
        """
        Route an automation payload to the local agent.
        
        Args:
            payload: Automation payload from AutomationIntentClassifier
            user_id: User ID for device lookup
            device_id: Specific device ID (optional, uses first online if not provided)
            
        Returns:
            Dict with routing result:
                - success: bool
                - task_id: str (if queued)
                - delivery: "websocket" | "polling"
                - error: str (if failed)
        """
        # Import here to avoid circular imports
        from Backend.LocalAgentAPI import (
            get_first_online_device, 
            get_user_devices,
            _pending_tasks,
            _registered_devices
        )
        
        try:
            # Get target device
            if not device_id:
                device_id, device_info = get_first_online_device(user_id)
            else:
                device_info = _registered_devices.get(device_id)
            
            if not device_id or not device_info:
                return {
                    "success": False,
                    "error": "No device available. Please ensure your local agent is running.",
                    "fallback": payload.get("fallback", "")
                }
            
            # Route each step as a task
            results = []
            for step in payload.get("steps", []):
                task_result = self._send_step(device_id, step, user_id)
                results.append(task_result)
                
                # If any step fails, stop execution
                if not task_result.get("success"):
                    return {
                        "success": False,
                        "error": f"Step failed: {step.get('action')} - {task_result.get('error')}",
                        "completed_steps": len([r for r in results if r.get("success")]),
                        "total_steps": len(payload.get("steps", [])),
                        "fallback": payload.get("fallback", "")
                    }
            
            return {
                "success": True,
                "task_ids": [r.get("task_id") for r in results],
                "delivery": results[0].get("delivery", "unknown") if results else "none",
                "device_id": device_id,
                "device_name": device_info.get("name", "Unknown"),
                "steps_sent": len(results)
            }
            
        except Exception as e:
            print(f"[AUTOMATION-ROUTER] Route error: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback": payload.get("fallback", "")
            }
    
    def _send_step(self, device_id: str, step: Dict, user_id: str = None) -> Dict:
        """
        Send a single automation step to the device.
        
        Args:
            device_id: Target device
            step: Single automation step {action, target, parameters}
            user_id: User ID for audit
            
        Returns:
            Dict with task result
        """
        from Backend.LocalAgentAPI import _pending_tasks, _registered_devices, log_command
        
        # Convert step to command format expected by LocalAgent
        command = step.get("action")
        params = {
            "target": step.get("target"),
            **step.get("parameters", {})
        }
        
        # Special handling for certain commands
        if command == "open_app":
            params = {"app": self._normalize_app_name(step.get("target", ""))}
        elif command == "close_app":
            params = {"app": self._normalize_app_name(step.get("target", ""))}
        elif command == "system_control":
            # Map LLM output to valid executor actions
            params = self._normalize_system_control_params(step)
        elif command == "write_notepad":
            params = {"text": step.get("parameters", {}).get("text", "")}
        elif command == "type":
            # Convert "type" to write_notepad if target is notepad
            if "notepad" in str(step.get("target", "")).lower():
                command = "write_notepad"
                params = {"text": step.get("parameters", {}).get("text", "")}
        
        # Create task
        task_id = str(uuid.uuid4())
        task = {
            "task_id": task_id,
            "command": command,
            "params": params,
            "user_id": user_id or "automation_router",
            "created_at": datetime.now().isoformat()
        }
        
        # Try WebSocket first (instant)
        ws_sent = False
        try:
            from Backend.AgentWebSocket import is_agent_connected, send_task_sync
            if is_agent_connected(device_id):
                ws_sent = send_task_sync(device_id, task_id, command, params)
                if ws_sent:
                    print(f"[AUTOMATION-ROUTER] ⚡ Step sent via WebSocket: {command} with params {params}")
        except Exception as ws_err:
            print(f"[AUTOMATION-ROUTER] WebSocket send failed: {ws_err}")
        
        # Fallback to polling queue
        if not ws_sent:
            if device_id not in _pending_tasks:
                _pending_tasks[device_id] = []
            _pending_tasks[device_id].append(task)
            print(f"[AUTOMATION-ROUTER] 📋 Step queued for polling: {command}")
        
        # Log the command
        if user_id:
            log_command(user_id, device_id, command, params, "sent_ws" if ws_sent else "queued")
        
        return {
            "success": True,
            "task_id": task_id,
            "command": command,
            "delivery": "websocket" if ws_sent else "polling"
        }
    
    def _normalize_app_name(self, app: str) -> str:
        """Normalize app name to match executor's allowed values."""
        app_lower = app.lower().strip()
        
        # Common aliases
        aliases = {
            "chrome": "chrome",
            "google chrome": "chrome",
            "google": "chrome",
            "firefox": "firefox",
            "mozilla": "firefox",
            "notepad": "notepad",
            "vs code": "vscode",
            "visual studio code": "vscode",
            "code": "vscode",
            "terminal": "terminal",
            "command prompt": "cmd",
            "cmd": "cmd",
            "spotify": "spotify",
            "discord": "discord",
            "slack": "slack",
            "word": "word",
            "excel": "excel",
            "calculator": "calculator",
            "calc": "calculator",
            "file explorer": "explorer",
            "explorer": "explorer",
            "files": "explorer",
            "steam": "steam",
            "edge": "edge",
            "microsoft edge": "edge",
            "vlc": "vlc",
            "teams": "teams",
            "microsoft teams": "teams",
            "zoom": "zoom",
        }
        
        return aliases.get(app_lower, app_lower)
    
    def _normalize_system_control_params(self, step: Dict) -> Dict:
        """
        Normalize system_control parameters to match executor's allowed actions.
        
        Allowed actions: set_volume, volume_up, volume_down, mute, unmute,
                        toggle_mute, set_brightness, brightness_up, brightness_down, lock_screen
        """
        target = str(step.get("target", "")).lower()
        params = step.get("parameters", {})
        
        # Extract action and level from various formats
        raw_action = params.get("action", "").lower() if params.get("action") else target
        level = params.get("level") or params.get("value")
        
        # Try to extract level from various parameter names
        if level is None:
            for key in ["volume", "brightness", "percent", "amount"]:
                if key in params:
                    try:
                        level = int(str(params[key]).replace("%", ""))
                    except:
                        pass
        
        # Normalize action based on keywords
        action = None
        
        # Volume actions
        if any(kw in raw_action for kw in ["volume up", "increase volume", "louder", "vol up", "higher volume"]):
            action = "volume_up"
        elif any(kw in raw_action for kw in ["volume down", "decrease volume", "quieter", "vol down", "lower volume", "reduce volume"]):
            action = "volume_down"
        elif any(kw in raw_action for kw in ["set volume", "volume to", "volume at"]) or ("volume" in raw_action and level is not None):
            action = "set_volume"
        elif raw_action in ["mute", "silence", "quiet"]:
            action = "mute"
        elif raw_action in ["unmute", "unsilence"]:
            action = "unmute"
        elif "toggle" in raw_action and "mute" in raw_action:
            action = "toggle_mute"
        
        # Brightness actions
        elif any(kw in raw_action for kw in ["brightness up", "increase brightness", "brighter", "bright up"]):
            action = "brightness_up"
        elif any(kw in raw_action for kw in ["brightness down", "decrease brightness", "dimmer", "dim", "darker"]):
            action = "brightness_down"
        elif any(kw in raw_action for kw in ["set brightness", "brightness to"]) or ("brightness" in raw_action and level is not None):
            action = "set_brightness"
        
        # Lock screen
        elif any(kw in raw_action for kw in ["lock", "lock screen", "lockscreen"]):
            action = "lock_screen"
        
        # Fallback: try to detect from just keywords
        if action is None:
            if "volume" in raw_action:
                if any(kw in raw_action for kw in ["up", "increase", "higher", "more", "louder"]):
                    action = "volume_up"
                elif any(kw in raw_action for kw in ["down", "decrease", "lower", "less", "quieter", "reduce"]):
                    action = "volume_down"
                elif level is not None:
                    action = "set_volume"
                else:
                    action = "volume_up"  # Default to up
            elif "bright" in raw_action:
                if any(kw in raw_action for kw in ["up", "increase", "higher", "more"]):
                    action = "brightness_up"
                elif any(kw in raw_action for kw in ["down", "decrease", "lower", "less", "dim"]):
                    action = "brightness_down"
                elif level is not None:
                    action = "set_brightness"
                else:
                    action = "brightness_up"  # Default to up
            elif "mute" in raw_action:
                action = "mute"
        
        # Build final params
        result = {"action": action} if action else {"action": "volume_up"}  # Safe default
        
        if level is not None and action in ["set_volume", "set_brightness"]:
            result["level"] = max(0, min(100, int(level)))
        
        print(f"[AUTOMATION-ROUTER] Normalized system_control: {raw_action} → {result}")
        return result

    
    def await_result(self, task_id: str, timeout: float = None) -> Dict:
        """
        Wait for a task result (blocking).
        
        Args:
            task_id: Task ID to wait for
            timeout: Max seconds to wait
            
        Returns:
            Task result dict
        """
        from Backend.LocalAgentAPI import _task_results
        
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            result = _task_results.get(task_id)
            if result:
                return {
                    "success": result.get("status") == "success",
                    "status": result.get("status"),
                    "result": result.get("result", {}),
                    "device_id": result.get("device_id")
                }
            time.sleep(0.5)
        
        return {
            "success": False,
            "status": "timeout",
            "error": f"No response within {timeout}s"
        }
    
    def handle_failure(self, task_id: str, error: Dict, payload: Dict) -> Dict:
        """
        Handle automation failure according to spec.
        
        Per spec:
        - Do NOT retry blindly
        - Do NOT hallucinate success
        - Downgrade confidence
        - Choose: replan, ask user, or stop safely
        
        Args:
            task_id: Failed task ID
            error: Error information
            payload: Original automation payload
            
        Returns:
            Failure handling response
        """
        print(f"[AUTOMATION-ROUTER] ❌ Task {task_id[:8]}... failed: {error}")
        
        fallback = payload.get("fallback", "")
        goal = payload.get("goal", "the requested action")
        
        # Build user-friendly error message
        error_msg = error.get("message", str(error))
        
        return {
            "success": False,
            "action": "report_failure",
            "message": f"I wasn't able to {goal}. {error_msg}",
            "fallback_suggestion": fallback,
            "options": [
                {"label": "Try again", "action": "retry"},
                {"label": "Do it manually", "action": "manual"},
                {"label": "Cancel", "action": "cancel"}
            ],
            # Downgraded confidence for similar future requests
            "confidence_adjustment": -0.2
        }
    
    def get_device_status(self, user_id: str = None) -> Dict:
        """
        Get status of available devices for automation.
        
        Returns:
            Dict with device availability info
        """
        from Backend.LocalAgentAPI import get_user_devices, _registered_devices
        from datetime import datetime
        
        devices = get_user_devices(user_id) if user_id else _registered_devices
        now = datetime.now()
        
        online_devices = []
        offline_devices = []
        
        for device_id, info in devices.items():
            last_seen = datetime.fromisoformat(info.get('last_seen', '2000-01-01'))
            is_online = (now - last_seen).total_seconds() < 60
            
            device_info = {
                "device_id": device_id,
                "name": info.get("name", "Unknown"),
                "last_seen": info.get("last_seen")
            }
            
            if is_online:
                online_devices.append(device_info)
            else:
                offline_devices.append(device_info)
        
        return {
            "has_online_device": len(online_devices) > 0,
            "online_count": len(online_devices),
            "offline_count": len(offline_devices),
            "online_devices": online_devices,
            "offline_devices": offline_devices
        }


# Global instance
automation_router = AutomationRouter()


# ==================== CONVENIENCE FUNCTIONS ====================

def route_automation(payload: Dict, user_id: str = None) -> Dict:
    """Quick helper to route an automation payload."""
    return automation_router.route(payload, user_id)


def can_automate(user_id: str = None) -> bool:
    """Check if automation is possible (device available)."""
    status = automation_router.get_device_status(user_id)
    return status.get("has_online_device", False)


# ==================== TEST ====================

if __name__ == "__main__":
    print("Testing Automation Router")
    print("=" * 70)
    
    # Check device status
    status = automation_router.get_device_status()
    print(f"Device Status: {status}")
    
    if status.get("has_online_device"):
        # Test routing
        test_payload = {
            "route": "local_agent",
            "type": "automation",
            "goal": "Open Notepad",
            "confidence": 0.9,
            "safety_level": "low",
            "steps": [
                {"action": "open_app", "target": "notepad", "parameters": {}}
            ],
            "fallback": "Please open Notepad manually"
        }
        
        result = automation_router.route(test_payload)
        print(f"\nRoute Result: {result}")
    else:
        print("\n⚠️ No online devices - cannot test routing")
        print("Start the local agent with: python -m LocalAgent.agent --ws")
