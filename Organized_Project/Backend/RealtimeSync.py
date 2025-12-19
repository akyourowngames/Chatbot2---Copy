"""
Real-time Sync System - Firebase Listeners & WebSocket Server
==============================================================
Provides real-time updates for dashboard and client applications
"""

import asyncio
import websockets
import json
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
from firebase_admin import firestore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealtimeSync:
    """Real-time synchronization using Firestore listeners and WebSockets"""
    
    def __init__(self, db: firestore.Client, websocket_port: int = 8765):
        """
        Initialize real-time sync system
        
        Args:
            db: Firestore database client
            websocket_port: Port for WebSocket server
        """
        self.db = db
        self.websocket_port = websocket_port
        self.connected_clients: Dict[str, Set[websockets.WebSocketServerProtocol]] = {}
        self.firestore_listeners = {}
        self.websocket_server = None
        
        logger.info(f"[REALTIME] Real-time sync initialized on port {websocket_port}")
    
    # ==================== FIRESTORE LISTENERS ====================
    
    def start_user_listener(self, user_id: str, collection: str, callback=None):
        """
        Start listening to changes in a user's collection
        
        Args:
            user_id: User ID to listen for
            collection: Collection name (conversations, memory, workflows, etc.)
            callback: Optional callback function for changes
        """
        try:
            listener_key = f"{user_id}:{collection}"
            
            # Don't create duplicate listeners
            if listener_key in self.firestore_listeners:
                logger.debug(f"[REALTIME] Listener already exists for {listener_key}")
                return
            
            # Create collection reference
            col_ref = self.db.collection(collection).document(user_id).collection(collection)
            
            # Define callback for snapshot changes
            is_first_snapshot = True
            
            def on_snapshot(col_snapshot, changes, read_time):
                nonlocal is_first_snapshot
                
                # Skip the huge initial dump of existing data
                if is_first_snapshot:
                    is_first_snapshot = False
                    # logger.info(f"[REALTIME] Skipping initial snapshot for {collection}")
                    return

                for change in changes:
                    if change.type.name == 'ADDED':
                        logger.info(f"[REALTIME] New {collection}: {change.document.id}")
                        self._broadcast_to_user(user_id, {
                            "type": "added",
                            "collection": collection,
                            "document_id": change.document.id,
                            "data": change.document.to_dict()
                        })
                    
                    elif change.type.name == 'MODIFIED':
                        logger.info(f"[REALTIME] Modified {collection}: {change.document.id}")
                        self._broadcast_to_user(user_id, {
                            "type": "modified",
                            "collection": collection,
                            "document_id": change.document.id,
                            "data": change.document.to_dict()
                        })
                    
                    elif change.type.name == 'REMOVED':
                        logger.info(f"[REALTIME] Removed {collection}: {change.document.id}")
                        
                        # Special handling for deleted conversations
                        event_type = "chat_deleted" if collection == "conversations" else "removed"
                        
                        self._broadcast_to_user(user_id, {
                            "type": event_type,
                            "collection": collection,
                            "document_id": change.document.id
                        })
                
                # Call custom callback if provided
                if callback:
                    callback(changes)
            
            # Start listening
            listener = col_ref.on_snapshot(on_snapshot)
            self.firestore_listeners[listener_key] = listener
            
            logger.info(f"[REALTIME] Started listener for {listener_key}")
            
        except Exception as e:
            logger.error(f"[REALTIME] Error starting listener: {e}")
    
    def stop_user_listener(self, user_id: str, collection: str):
        """Stop listening to a user's collection"""
        listener_key = f"{user_id}:{collection}"
        
        if listener_key in self.firestore_listeners:
            self.firestore_listeners[listener_key].unsubscribe()
            del self.firestore_listeners[listener_key]
            logger.info(f"[REALTIME] Stopped listener for {listener_key}")
    
    def stop_all_listeners(self):
        """Stop all Firestore listeners"""
        for listener_key, listener in self.firestore_listeners.items():
            listener.unsubscribe()
            logger.info(f"[REALTIME] Stopped listener for {listener_key}")
        
        self.firestore_listeners.clear()
    
    # ==================== WEBSOCKET SERVER ====================
    
    async def handle_client(self, websocket, path=None):
        """Handle WebSocket client connection"""
        user_id = None
        
        try:
            # Wait for authentication message
            auth_message = await websocket.recv()
            auth_data = json.loads(auth_message)
            
            # Verify JWT token
            from Backend.SecurityManager import extract_user_from_token
            token = auth_data.get('token')
            
            if not token:
                await websocket.send(json.dumps({
                    "error": "Authentication token required"
                }))
                return
            
            user_info = extract_user_from_token(token)
            if not user_info:
                await websocket.send(json.dumps({
                    "error": "Invalid or expired token"
                }))
                return
            
            user_id = user_info['user_id']
            
            # Add client to connected clients
            if user_id not in self.connected_clients:
                self.connected_clients[user_id] = set()
            
            self.connected_clients[user_id].add(websocket)
            
            logger.info(f"[REALTIME] Client connected: {user_id}")
            
            # Send connection confirmation
            await websocket.send(json.dumps({
                "type": "connected",
                "user_id": user_id,
                "message": "Real-time sync active"
            }))
            
            # Start Firestore listeners for this user
            collections = ['conversations', 'memory', 'workflows', 'messages']
            for collection in collections:
                self.start_user_listener(user_id, collection)
            
            # Keep connection alive and handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    # Handle ping/pong for keep-alive
                    if data.get('type') == 'ping':
                        await websocket.send(json.dumps({"type": "pong"}))
                    
                    # Handle other message types as needed
                    
                except json.JSONDecodeError:
                    logger.warning(f"[REALTIME] Invalid JSON from client: {user_id}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"[REALTIME] Client disconnected: {user_id}")
        
        except Exception as e:
            logger.error(f"[REALTIME] Error handling client: {e}")
        
        finally:
            # Clean up on disconnect
            if user_id and user_id in self.connected_clients:
                self.connected_clients[user_id].discard(websocket)
                
                # Remove user entry if no more connections
                if not self.connected_clients[user_id]:
                    del self.connected_clients[user_id]
                    
                    # Stop listeners for this user
                    collections = ['conversations', 'memory', 'workflows', 'messages']
                    for collection in collections:
                        self.stop_user_listener(user_id, collection)
    
    async def start_websocket_server(self):
        """Start the WebSocket server"""
        try:
            self.websocket_server = await websockets.serve(
                self.handle_client,
                "localhost",
                self.websocket_port
            )
            
            logger.info(f"[REALTIME] WebSocket server started on ws://localhost:{self.websocket_port}")
            
            # Keep server running
            await asyncio.Future()  # Run forever
            
        except Exception as e:
            logger.error(f"[REALTIME] WebSocket server error: {e}")
    
    # ==================== JSON SERIALIZATION HELPER ====================
    def json_serial(self, obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime, datetime.date)):
            return obj.isoformat()
        # Handle Firestore DatetimeWithNanoseconds if present
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        if hasattr(obj, '__str__'):
            return str(obj)
        raise TypeError(f"Type {type(obj)} not serializable")

    def _broadcast_to_user(self, user_id: str, data: Dict[str, Any]):
        """Broadcast data to all connected clients for a user"""
        if user_id not in self.connected_clients:
            return
        
        try:
            message_data = {
                **data,
                "timestamp": datetime.utcnow().isoformat()
            }
            # Use custom default for json.dumps
            message = json.dumps(message_data, default=self.json_serial)
        except Exception as e:
            logger.error(f"[REALTIME] Serialization error: {e}")
            return
        
        # Send to all connected clients for this user
        disconnected = set()
        for websocket in self.connected_clients[user_id]:
            try:
                # Use ensure_future or create_task appropriately
                loop = asyncio.get_event_loop_policy().get_event_loop()
                # Check if loop is running to avoid runtime errors
                if loop.is_running():
                     asyncio.create_task(websocket.send(message))
            except Exception as e:
                logger.warning(f"[REALTIME] Failed to send to client: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.connected_clients[user_id].discard(websocket)
    
    # ==================== OFFLINE QUEUE ====================
    
    def queue_offline_update(self, user_id: str, update_data: Dict):
        """
        Queue an update for offline users (to be synced when they reconnect)
        
        Args:
            user_id: User ID
            update_data: Update data to queue
        """
        # Store in Firestore for offline sync
        try:
            offline_queue_ref = self.db.collection('offline_queue').document(user_id)
            
            # Get existing queue
            queue_doc = offline_queue_ref.get()
            if queue_doc.exists:
                queue = queue_doc.to_dict().get('updates', [])
            else:
                queue = []
            
            # Add new update
            queue.append({
                **update_data,
                "queued_at": datetime.utcnow()
            })
            
            # Save queue (keep last 100 updates)
            offline_queue_ref.set({
                "updates": queue[-100:]
            })
            
            logger.info(f"[REALTIME] Queued offline update for user {user_id}")
            
        except Exception as e:
            logger.error(f"[REALTIME] Error queuing offline update: {e}")
    
    def get_offline_queue(self, user_id: str) -> list:
        """Get queued updates for a user"""
        try:
            offline_queue_ref = self.db.collection('offline_queue').document(user_id)
            queue_doc = offline_queue_ref.get()
            
            if queue_doc.exists:
                return queue_doc.to_dict().get('updates', [])
            
            return []
            
        except Exception as e:
            logger.error(f"[REALTIME] Error getting offline queue: {e}")
            return []
    
    def clear_offline_queue(self, user_id: str):
        """Clear offline queue for a user"""
        try:
            offline_queue_ref = self.db.collection('offline_queue').document(user_id)
            offline_queue_ref.delete()
            logger.info(f"[REALTIME] Cleared offline queue for user {user_id}")
        except Exception as e:
            logger.error(f"[REALTIME] Error clearing offline queue: {e}")


# ==================== GLOBAL INSTANCE ====================

realtime_sync = None


def initialize_realtime_sync(db: firestore.Client, port: int = 8765):
    """Initialize the global real-time sync instance"""
    global realtime_sync
    realtime_sync = RealtimeSync(db, port)
    return realtime_sync


def get_realtime_sync() -> Optional[RealtimeSync]:
    """Get the global real-time sync instance"""
    return realtime_sync


# ==================== TESTING ====================

if __name__ == "__main__":
    print("🔄 Testing Real-time Sync System\n")
    
    # Note: This requires Firebase to be initialized
    print("Real-time sync requires Firebase connection.")
    print("Use initialize_realtime_sync(db) to start the system.")
    print("\nFeatures:")
    print("  ✅ Firestore snapshot listeners")
    print("  ✅ WebSocket server for real-time updates")
    print("  ✅ Offline queue for disconnected users")
    print("  ✅ JWT authentication for WebSocket connections")
    print("  ✅ Automatic listener management")
    
    print("\n✅ Real-time sync module ready!")
