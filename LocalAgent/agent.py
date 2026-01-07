"""
Kai Local Agent - Main Agent Module
=====================================
The core agent that:
- Registers with the Kai cloud API
- Connects via WebSocket (preferred) or polls for tasks (fallback)
- Executes commands via whitelisted executors
- Reports results back

Run with: python -m LocalAgent.agent [--register TOKEN] [--api URL] [--ws]
"""

import argparse
import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

import requests

from .config import (
    load_config, save_config, is_registered, 
    get_credentials, get_config_path
)
from .schemas import validate_command, get_allowed_commands
from .executors.open_app import OpenAppExecutor
from .executors.close_app import CloseAppExecutor
from .executors.system_control import SystemControlExecutor
from .executors.system_status import SystemStatusExecutor
from .executors.write_notepad import WriteNotepadExecutor
from .executors.file_manager import FileManagerExecutor


# ==================== LOGGING SETUP ====================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("KaiLocalAgent")


# ==================== AGENT CLASS ====================

class KaiLocalAgent:
    """
    Main Kai Local Agent class.
    Handles registration, polling, command execution, and reporting.
    """
    
    def __init__(self, api_url: Optional[str] = None):
        """
        Initialize the agent.
        
        Args:
            api_url: Override the API URL from config
        """
        self.config = load_config()
        self.api_url = api_url or self.config.get("api_url")
        self.poll_interval = self.config.get("poll_interval", 5)
        self.heartbeat_interval = self.config.get("heartbeat_interval", 30)
        
        # Initialize executors
        self.executors = {
            "open_app": OpenAppExecutor(),
            "close_app": CloseAppExecutor(),
            "system_control": SystemControlExecutor(),
            "system_status": SystemStatusExecutor(),
            "write_notepad": WriteNotepadExecutor(),
            "file_manager": FileManagerExecutor(),
        }
        
        # Running state
        self.running = False
        self.last_heartbeat = 0
        
        logger.info(f"Agent initialized. API: {self.api_url}")
        logger.info(f"Registered: {is_registered()}")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        creds = get_credentials()
        if creds:
            device_id, auth_token = creds
            return {"Authorization": f"Bearer {auth_token}"}
        return {}
    
    def _get_device_id(self) -> Optional[str]:
        """Get the registered device ID."""
        creds = get_credentials()
        return creds[0] if creds else None
    
    def register(self, pairing_token: str, device_name: Optional[str] = None) -> bool:
        """
        Register this device with the Kai cloud.
        
        Args:
            pairing_token: User-provided pairing token
            device_name: Optional device name (defaults to hostname)
        
        Returns:
            True if registration successful
        """
        import socket
        
        if not device_name:
            device_name = socket.gethostname()
        
        url = f"{self.api_url}/agent/register"
        payload = {
            "device_name": device_name,
            "pairing_token": pairing_token
        }
        
        logger.info(f"Registering device '{device_name}' with Kai cloud...")
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            data = response.json()
            
            if response.status_code == 200 and data.get("success"):
                # Save credentials to config
                self.config["device_id"] = data["device_id"]
                self.config["auth_token"] = data["auth_token"]
                self.config["device_name"] = device_name
                self.config["registered_at"] = datetime.now().isoformat()
                save_config(self.config)
                
                logger.info(f"✓ Registration successful! Device ID: {data['device_id'][:8]}...")
                logger.info(f"  Credentials saved to: {get_config_path()}")
                return True
            else:
                logger.error(f"Registration failed: {data.get('error', 'Unknown error')}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Registration request failed: {e}")
            return False
    
    def poll(self) -> Optional[Dict[str, Any]]:
        """
        Poll the API for pending tasks.
        
        Returns:
            Task dict if available, None otherwise
        """
        device_id = self._get_device_id()
        if not device_id:
            logger.error("Cannot poll: device not registered")
            return None
        
        url = f"{self.api_url}/agent/poll"
        params = {"device_id": device_id}
        headers = self._get_auth_headers()
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            data = response.json()
            
            if response.status_code == 200:
                if data.get("task_id"):
                    logger.info(f"Received task: {data.get('command')} (ID: {data['task_id'][:8]}...)")
                    return data
                # No task available (normal case)
                return None
            elif response.status_code == 401:
                logger.error("Authentication failed - may need to re-register")
                return None
            else:
                logger.warning(f"Poll returned {response.status_code}: {data.get('error', 'Unknown')}")
                return None
                
        except requests.RequestException as e:
            logger.warning(f"Poll request failed: {e}")
            return None
    
    def report(self, task_id: str, status: str, result: Dict[str, Any]) -> bool:
        """
        Report task execution result to the API.
        
        Args:
            task_id: The task ID from poll
            status: "success" or "error"
            result: Result data from executor
        
        Returns:
            True if report was sent successfully
        """
        device_id = self._get_device_id()
        if not device_id:
            logger.error("Cannot report: device not registered")
            return False
        
        url = f"{self.api_url}/agent/report"
        headers = self._get_auth_headers()
        payload = {
            "device_id": device_id,
            "task_id": task_id,
            "status": status,
            "result": result
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            data = response.json()
            
            if response.status_code == 200 and data.get("success"):
                logger.info(f"✓ Reported task {task_id[:8]}... status: {status}")
                return True
            else:
                logger.warning(f"Report failed: {data.get('error', 'Unknown')}")
                return False
                
        except requests.RequestException as e:
            logger.warning(f"Report request failed: {e}")
            return False
    
    def heartbeat(self) -> bool:
        """Send heartbeat to keep device marked online."""
        device_id = self._get_device_id()
        if not device_id:
            return False
        
        url = f"{self.api_url}/agent/heartbeat"
        headers = self._get_auth_headers()
        payload = {"device_id": device_id}
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def execute_command(self, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and execute a command.
        
        Args:
            command: Command name
            params: Command parameters
        
        Returns:
            Result dict with status and message
        """
        # First, validate against schema
        is_valid, error_msg = validate_command(command, params)
        if not is_valid:
            logger.warning(f"Command rejected: {error_msg}")
            return {
                "status": "error",
                "message": f"Command rejected: {error_msg}"
            }
        
        # Get executor for command
        executor = self.executors.get(command)
        if not executor:
            logger.warning(f"No executor for command: {command}")
            return {
                "status": "error",
                "message": f"Command '{command}' has no executor implemented"
            }
        
        # Execute
        logger.info(f"Executing: {command} with params {params}")
        result = executor.execute(params)
        logger.info(f"Result: {result['status']} - {result['message']}")
        
        return result
    
    def run(self):
        """
        Main agent loop: poll for tasks, execute, report.
        Runs until interrupted.
        """
        if not is_registered():
            logger.error("Device not registered. Run with --register TOKEN first.")
            return
        
        self.running = True
        logger.info("=" * 50)
        logger.info("Kai Local Agent started")
        logger.info(f"Device: {self.config.get('device_name')}")
        logger.info(f"Polling every {self.poll_interval}s")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 50)
        
        # Send initial heartbeat
        self.heartbeat()
        self.last_heartbeat = time.time()
        
        while self.running:
            try:
                # Poll for task
                task = self.poll()
                
                if task:
                    # Execute the command
                    result = self.execute_command(
                        task.get("command", ""),
                        task.get("params", {})
                    )
                    
                    # Report result
                    self.report(
                        task["task_id"],
                        result.get("status", "error"),
                        result
                    )
                
                # Send heartbeat if needed
                if time.time() - self.last_heartbeat > self.heartbeat_interval:
                    if self.heartbeat():
                        self.last_heartbeat = time.time()
                
                # Wait before next poll
                time.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                logger.info("\nShutdown requested...")
                self.running = False
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(self.poll_interval)
        
        logger.info("Agent stopped.")
    
    def run_websocket(self, ws_url: Optional[str] = None):
        """
        Run agent in WebSocket mode (preferred, real-time).
        Falls back to polling if WebSocket fails.
        """
        if not is_registered():
            logger.error("Device not registered. Run with --register TOKEN first.")
            return
        
        # Derive WebSocket URL from API URL
        if not ws_url:
            # Convert http(s)://host:port/api/v1 -> ws(s)://host:8766
            api_url = self.api_url
            if api_url.startswith("https://"):
                ws_host = api_url.replace("https://", "").split("/")[0].split(":")[0]
                ws_url = f"wss://{ws_host}:8766"
            elif api_url.startswith("http://"):
                ws_host = api_url.replace("http://", "").split("/")[0].split(":")[0]
                ws_url = f"ws://{ws_host}:8766"
            else:
                ws_url = "ws://localhost:8766"
        
        self.running = True
        logger.info("=" * 50)
        logger.info("Kai Local Agent started (WebSocket Mode)")
        logger.info(f"Device: {self.config.get('device_name')}")
        logger.info(f"WebSocket URL: {ws_url}")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 50)
        
        asyncio.run(self._websocket_loop(ws_url))
        
    async def _websocket_loop(self, ws_url: str):
        """Main WebSocket connection loop with auto-reconnect."""
        import websockets
        
        reconnect_delay = 1  # Start with 1 second
        max_reconnect_delay = 30  # Max 30 seconds between retries
        
        while self.running:
            try:
                logger.info(f"Connecting to {ws_url}...")
                async with websockets.connect(ws_url) as websocket:
                    # Send auth message
                    creds = get_credentials()
                    if not creds:
                        logger.error("No credentials found!")
                        return
                        
                    device_id, auth_token = creds
                    await websocket.send(json.dumps({
                        "type": "auth",
                        "device_id": device_id,
                        "auth_token": auth_token
                    }))
                    
                    # Wait for auth response
                    response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    resp_data = json.loads(response)
                    
                    if resp_data.get("type") == "auth_success":
                        logger.info(f"✅ Connected: {resp_data.get('message')}")
                        reconnect_delay = 1  # Reset delay on success
                    else:
                        logger.error(f"Auth failed: {resp_data.get('message')}")
                        return
                    
                    # Start heartbeat task
                    heartbeat_task = asyncio.create_task(self._heartbeat_loop(websocket))
                    
                    try:
                        # Main message loop
                        async for message in websocket:
                            await self._handle_ws_message(websocket, message)
                    finally:
                        heartbeat_task.cancel()
                        
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"Connection closed: {e}")
            except asyncio.TimeoutError:
                logger.warning("Connection timeout")
            except ConnectionRefusedError:
                logger.warning(f"Connection refused - server may be offline")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
            
            if self.running:
                logger.info(f"Reconnecting in {reconnect_delay}s...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
        
        logger.info("WebSocket agent stopped.")
    
    async def _heartbeat_loop(self, websocket):
        """Send periodic heartbeat to keep connection alive."""
        while True:
            try:
                await asyncio.sleep(30)
                await websocket.send(json.dumps({"type": "heartbeat"}))
            except asyncio.CancelledError:
                break
            except Exception:
                break
    
    async def _handle_ws_message(self, websocket, message: str):
        """Handle incoming WebSocket message (task from server)."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "task":
                task_id = data.get("task_id")
                command = data.get("command")
                params = data.get("params", {})
                
                logger.info(f"📥 Task received: {command} ({task_id[:8]}...)")
                
                # Execute command
                result = self.execute_command(command, params)
                
                # Send result back via WebSocket
                await websocket.send(json.dumps({
                    "type": "result",
                    "task_id": task_id,
                    "status": result.get("status", "error"),
                    "result": result
                }))
                logger.info(f"📤 Result sent: {result.get('status')}")
                
            elif msg_type == "heartbeat_ack":
                pass  # Heartbeat acknowledged
                
            elif msg_type == "pong":
                pass  # Ping response
                
            elif msg_type == "result_ack":
                logger.info(f"✓ Result acknowledged: {data.get('task_id', '')[:8]}...")
                
        except json.JSONDecodeError:
            logger.warning("Invalid JSON message received")
        except Exception as e:
            logger.error(f"Message handling error: {e}")
    
    def stop(self):
        """Stop the agent loop."""
        self.running = False


# ==================== CLI ENTRY POINT ====================

def main():
    parser = argparse.ArgumentParser(
        description="Kai Local Agent - Secure remote automation for your PC"
    )
    parser.add_argument(
        "--register",
        metavar="TOKEN",
        help="Register this device with a pairing token"
    )
    parser.add_argument(
        "--name",
        metavar="NAME",
        help="Device name for registration (default: hostname)"
    )
    parser.add_argument(
        "--api",
        metavar="URL",
        help="Override API URL (default: from config)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show registration status and exit"
    )
    parser.add_argument(
        "--ws",
        action="store_true",
        help="Use WebSocket mode (real-time, preferred)"
    )
    
    args = parser.parse_args()
    
    # Create agent
    agent = KaiLocalAgent(api_url=args.api)
    
    # Handle --status
    if args.status:
        if is_registered():
            config = load_config()
            print(f"Status: Registered")
            print(f"Device ID: {config.get('device_id', 'N/A')[:8]}...")
            print(f"Device Name: {config.get('device_name', 'N/A')}")
            print(f"API URL: {config.get('api_url', 'N/A')}")
            print(f"Registered: {config.get('registered_at', 'N/A')}")
        else:
            print("Status: Not registered")
            print("Run with --register TOKEN to register this device")
        return
    
    # Handle --register
    if args.register:
        success = agent.register(args.register, args.name)
        if not success:
            sys.exit(1)
        print("\nYou can now run the agent with: python -m LocalAgent.agent --ws")
        return
    
    # Default: run the agent
    if not is_registered():
        print("Device not registered.")
        print("Run with --register TOKEN to register first.")
        print("Example: python -m LocalAgent.agent --register mytoken123")
        sys.exit(1)
    
    # Set up signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        agent.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the agent (WebSocket or polling mode)
    if args.ws:
        try:
            agent.run_websocket()
        except ImportError:
            print("WebSocket mode requires 'websockets' package.")
            print("Install with: pip install websockets")
            print("Falling back to polling mode...")
            agent.run()
    else:
        agent.run()


if __name__ == "__main__":
    main()
