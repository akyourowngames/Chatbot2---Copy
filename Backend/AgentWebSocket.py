"""
Agent WebSocket Handler
=======================
Real-time WebSocket connection for Local Agent communication.
Replaces polling with instant task delivery.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional
import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger("AgentWebSocket")

# Connected agents: {device_id: websocket_connection}
_connected_agents: Dict[str, WebSocketServerProtocol] = {}

# Pending tasks for agents (fallback if not connected)
_pending_tasks: Dict[str, list] = {}

# Task results callback
_task_result_callbacks: Dict[str, callable] = {}


class AgentWebSocketServer:
    """WebSocket server for Local Agent connections."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8766):
        self.host = host
        self.port = port
        self.server = None
        
    async def handler(self, websocket: WebSocketServerProtocol):
        """Handle incoming WebSocket connections from agents."""
        device_id = None
        
        try:
            # Wait for authentication message
            auth_msg = await asyncio.wait_for(websocket.recv(), timeout=30)
            auth_data = json.loads(auth_msg)
            
            if auth_data.get("type") != "auth":
                await websocket.send(json.dumps({
                    "type": "error",
                    "message": "First message must be auth"
                }))
                return
                
            device_id = auth_data.get("device_id")
            auth_token = auth_data.get("auth_token")
            
            # Validate device credentials
            if not await self._validate_device(device_id, auth_token):
                await websocket.send(json.dumps({
                    "type": "auth_failed",
                    "message": "Invalid credentials"
                }))
                return
            
            # Register connection
            _connected_agents[device_id] = websocket
            logger.info(f"[WS-AGENT] ✅ Device connected: {device_id[:8]}...")
            
            # Send auth success
            await websocket.send(json.dumps({
                "type": "auth_success",
                "message": f"Connected as {device_id[:8]}...",
                "server_time": datetime.now().isoformat()
            }))
            
            # Send any pending tasks immediately
            await self._flush_pending_tasks(device_id, websocket)
            
            # Main message loop
            async for message in websocket:
                await self._handle_message(device_id, websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"[WS-AGENT] Device disconnected: {device_id[:8] if device_id else 'unknown'}...")
        except asyncio.TimeoutError:
            logger.warning("[WS-AGENT] Auth timeout - closing connection")
        except Exception as e:
            logger.error(f"[WS-AGENT] Handler error: {e}")
        finally:
            # Cleanup
            if device_id and device_id in _connected_agents:
                del _connected_agents[device_id]
                
    async def _validate_device(self, device_id: str, auth_token: str) -> bool:
        """Validate device credentials against LocalAgentAPI registry."""
        try:
            from Backend.LocalAgentAPI import _registered_devices, _get_firestore
            
            # Check memory cache first
            device = _registered_devices.get(device_id)
            
            # Fallback to Firestore
            if not device:
                db = _get_firestore()
                if db:
                    doc = db.collection('devices').document(device_id).get()
                    if doc.exists:
                        device = doc.to_dict()
                        _registered_devices[device_id] = device
            
            if device and device.get('auth_token') == auth_token:
                return True
                
        except Exception as e:
            logger.error(f"[WS-AGENT] Validation error: {e}")
            
        return False
        
    async def _flush_pending_tasks(self, device_id: str, websocket: WebSocketServerProtocol):
        """Send any pending tasks to the newly connected device."""
        try:
            from Backend.LocalAgentAPI import _pending_tasks as api_pending_tasks
            
            tasks = api_pending_tasks.get(device_id, [])
            for task in tasks[:]:  # Copy list to allow modification
                await websocket.send(json.dumps({
                    "type": "task",
                    "task_id": task['task_id'],
                    "command": task['command'],
                    "params": task['params']
                }))
                tasks.remove(task)
                logger.info(f"[WS-AGENT] Flushed pending task to {device_id[:8]}...")
                
        except Exception as e:
            logger.error(f"[WS-AGENT] Flush error: {e}")
            
    async def _handle_message(self, device_id: str, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming message from agent."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "heartbeat":
                # Update last seen
                from Backend.LocalAgentAPI import _registered_devices
                if device_id in _registered_devices:
                    _registered_devices[device_id]['last_seen'] = datetime.now().isoformat()
                await websocket.send(json.dumps({
                    "type": "heartbeat_ack",
                    "server_time": datetime.now().isoformat()
                }))
                
            elif msg_type == "result":
                # Task result from agent
                task_id = data.get("task_id")
                status = data.get("status", "unknown")
                result = data.get("result", {})
                
                # Store result
                from Backend.LocalAgentAPI import _task_results
                _task_results[task_id] = {
                    "device_id": device_id,
                    "status": status,
                    "result": result,
                    "reported_at": datetime.now().isoformat()
                }
                
                logger.info(f"[WS-AGENT] Task {task_id[:8]}... result: {status}")
                
                # Acknowledge
                await websocket.send(json.dumps({
                    "type": "result_ack",
                    "task_id": task_id
                }))
                
                # Call any registered callback
                if task_id in _task_result_callbacks:
                    callback = _task_result_callbacks.pop(task_id)
                    try:
                        callback(result)
                    except Exception:
                        pass
                        
            elif msg_type == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
                
        except json.JSONDecodeError:
            logger.warning(f"[WS-AGENT] Invalid JSON from {device_id[:8]}...")
        except Exception as e:
            logger.error(f"[WS-AGENT] Message handling error: {e}")
            
    async def start(self):
        """Start the WebSocket server."""
        self.server = await websockets.serve(
            self.handler,
            self.host,
            self.port
        )
        logger.info(f"[WS-AGENT] ✅ Agent WebSocket server started on ws://{self.host}:{self.port}")
        await self.server.wait_closed()
        
    def stop(self):
        """Stop the WebSocket server."""
        if self.server:
            self.server.close()


# ==================== PUBLIC API ====================

def get_connected_agents() -> Dict[str, WebSocketServerProtocol]:
    """Get all connected agent connections."""
    return _connected_agents.copy()


def is_agent_connected(device_id: str) -> bool:
    """Check if an agent is currently connected via WebSocket."""
    return device_id in _connected_agents


async def send_task_to_agent(device_id: str, task_id: str, command: str, params: dict) -> bool:
    """
    Send a task to a connected agent via WebSocket.
    
    Returns True if sent successfully, False if agent not connected.
    """
    websocket = _connected_agents.get(device_id)
    if not websocket:
        return False
        
    try:
        await websocket.send(json.dumps({
            "type": "task",
            "task_id": task_id,
            "command": command,
            "params": params
        }))
        logger.info(f"[WS-AGENT] Task {task_id[:8]}... sent to {device_id[:8]}...")
        return True
    except Exception as e:
        logger.error(f"[WS-AGENT] Failed to send task: {e}")
        # Remove dead connection
        if device_id in _connected_agents:
            del _connected_agents[device_id]
        return False


def send_task_sync(device_id: str, task_id: str, command: str, params: dict) -> bool:
    """Synchronous wrapper for send_task_to_agent."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Schedule as a task (non-blocking)
            asyncio.ensure_future(send_task_to_agent(device_id, task_id, command, params))
            return True
        else:
            return loop.run_until_complete(send_task_to_agent(device_id, task_id, command, params))
    except Exception:
        # Create new loop if needed
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(send_task_to_agent(device_id, task_id, command, params))


# ==================== SERVER STARTUP ====================

_server_instance: Optional[AgentWebSocketServer] = None


def start_agent_websocket_server(host: str = "0.0.0.0", port: int = 8766):
    """Start the agent WebSocket server in a background thread."""
    global _server_instance
    
    def run_server():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        _server_instance = AgentWebSocketServer(host, port)
        loop.run_until_complete(_server_instance.start())
        
    import threading
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    logger.info(f"[WS-AGENT] Server thread started")
    return server_thread
