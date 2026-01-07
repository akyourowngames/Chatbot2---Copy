"""
Kai Local Agent - Main Agent Module
=====================================
The core agent that:
- Registers with the Kai cloud API
- Polls for tasks
- Executes commands via whitelisted executors
- Reports results back

Run with: python -m LocalAgent.agent [--register TOKEN] [--api URL]
"""

import argparse
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
        print("\nYou can now run the agent with: python -m LocalAgent.agent")
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
    
    # Run the agent
    agent.run()


if __name__ == "__main__":
    main()
