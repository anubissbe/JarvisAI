import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional, Any, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.connection_queues: Dict[str, asyncio.Queue] = {}
        self.broadcast_queue = asyncio.Queue()
        
    async def connect(self, websocket: WebSocket, client_id: Optional[str] = None) -> str:
        """
        Accept a new WebSocket connection
        Returns the connection ID
        """
        try:
            await websocket.accept()
            
            # Generate or use provided client ID
            connection_id = client_id or str(uuid.uuid4())
            
            # Store connection
            self.active_connections[connection_id] = websocket
            self.connection_metadata[connection_id] = {
                "connected_at": datetime.utcnow().isoformat(),
                "last_active": datetime.utcnow().isoformat(),
                "messages_received": 0,
                "messages_sent": 0
            }
            
            # Create message queue for this connection
            self.connection_queues[connection_id] = asyncio.Queue()
            
            logger.info(f"Client connected: {connection_id}")
            return connection_id
            
        except Exception as e:
            logger.error(f"Error accepting connection: {str(e)}")
            raise

    async def disconnect(self, connection_id: str):
        """Handle client disconnection"""
        try:
            if connection_id in self.active_connections:
                # Clean up connection resources
                websocket = self.active_connections[connection_id]
                try:
                    await websocket.close()
                except Exception as e:
                    logger.warning(f"Error closing websocket: {str(e)}")
                
                # Remove from tracking
                del self.active_connections[connection_id]
                del self.connection_metadata[connection_id]
                del self.connection_queues[connection_id]
                
                logger.info(f"Client disconnected: {connection_id}")
            
        except Exception as e:
            logger.error(f"Error during disconnect cleanup: {str(e)}")

    async def send_personal_message(self, message: Dict[str, Any], connection_id: str):
        """Send a message to a specific client"""
        try:
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                try:
                    await websocket.send_json(message)
                    self.connection_metadata[connection_id]["messages_sent"] += 1
                    self.connection_metadata[connection_id]["last_active"] = datetime.utcnow().isoformat()
                except WebSocketDisconnect:
                    await self.disconnect(connection_id)
                except Exception as e:
                    logger.error(f"Error sending message to {connection_id}: {str(e)}")
                    await self.disconnect(connection_id)
            
        except Exception as e:
            logger.error(f"Error in send_personal_message: {str(e)}")

    async def broadcast(self, message: Dict[str, Any], exclude: Optional[Set[str]] = None):
        """Broadcast a message to all connected clients except those in exclude set"""
        exclude = exclude or set()
        
        for connection_id in list(self.active_connections.keys()):
            if connection_id not in exclude:
                await self.send_personal_message(message, connection_id)

class JarvisWebSocket:
    """Main WebSocket handler for Jarvis"""
    
    def __init__(self, app: FastAPI, memory_manager: Any, knowledge_manager: Any):
        self.app = app
        self.memory_manager = memory_manager
        self.knowledge_manager = knowledge_manager
        self.connection_manager = ConnectionManager()
        
        # Register WebSocket endpoint
        self.app.websocket("/ws")(self.websocket_endpoint)
        
        # Start background tasks
        self.background_tasks = set()
        self.app.on_event("startup")(self.start_background_tasks)
        self.app.on_event("shutdown")(self.cleanup_background_tasks)
    
    async def websocket_endpoint(self, websocket: WebSocket):
        """Handle WebSocket connections"""
        connection_id = None
        
        try:
            # Accept connection
            connection_id = await self.connection_manager.connect(websocket)
            
            # Send welcome message
            await self.connection_manager.send_personal_message(
                {
                    "type": "system",
                    "message": "Connected to Jarvis WebSocket server",
                    "connection_id": connection_id
                },
                connection_id
            )
            
            # Handle messages
            while True:
                try:
                    # Receive message
                    message = await websocket.receive_json()
                    
                    # Update metadata
                    self.connection_manager.connection_metadata[connection_id]["messages_received"] += 1
                    self.connection_manager.connection_metadata[connection_id]["last_active"] = datetime.utcnow().isoformat()
                    
                    # Process message
                    await self.handle_message(message, connection_id)
                    
                except WebSocketDisconnect:
                    logger.info(f"Client disconnected normally: {connection_id}")
                    break
                except Exception as e:
                    logger.error(f"Error handling message: {str(e)}")
                    # Send error message to client
                    await self.connection_manager.send_personal_message(
                        {
                            "type": "error",
                            "message": f"Error processing message: {str(e)}"
                        },
                        connection_id
                    )
        
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
        
        finally:
            if connection_id:
                await self.connection_manager.disconnect(connection_id)

    async def handle_message(self, message: Dict[str, Any], connection_id: str):
        """Process incoming WebSocket messages"""
        try:
            message_type = message.get("type", "unknown")
            
            if message_type == "chat":
                await self.handle_chat_message(message, connection_id)
            elif message_type == "system":
                await self.handle_system_message(message, connection_id)
            elif message_type == "heartbeat":
                await self.handle_heartbeat(message, connection_id)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error in handle_message: {str(e)}")
            raise

    async def handle_chat_message(self, message: Dict[str, Any], connection_id: str):
        """Handle chat messages from Open WebUI"""
        try:
            # Extract conversation data
            conversation_id = message.get("conversation_id") or str(uuid.uuid4())
            user_message = message.get("message", "")
            context = message.get("context", {})
            
            # Store in memory system
            await self.memory_manager.store_interaction(
                conversation_id=conversation_id,
                user_message=user_message,
                ai_response=None,  # Will be updated when AI responds
                context=context,
                metadata={
                    "source": "webui",
                    "connection_id": connection_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Acknowledge receipt
            await self.connection_manager.send_personal_message(
                {
                    "type": "chat_received",
                    "conversation_id": conversation_id,
                    "message_id": message.get("message_id"),
                    "timestamp": datetime.utcnow().isoformat()
                },
                connection_id
            )
            
        except Exception as e:
            logger.error(f"Error handling chat message: {str(e)}")
            raise

    async def handle_system_message(self, message: Dict[str, Any], connection_id: str):
        """Handle system messages from Open WebUI"""
        try:
            command = message.get("command")
            
            if command == "sync_request":
                # Client requesting conversation sync
                await self.sync_conversations(connection_id)
            elif command == "clear_memory":
                # Client requesting memory clear
                conversation_id = message.get("conversation_id")
                if conversation_id:
                    await self.memory_manager.forget_conversation(conversation_id)
            
        except Exception as e:
            logger.error(f"Error handling system message: {str(e)}")
            raise

    async def handle_heartbeat(self, message: Dict[str, Any], connection_id: str):
        """Handle heartbeat messages to maintain connection"""
        try:
            await self.connection_manager.send_personal_message(
                {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                },
                connection_id
            )
        except Exception as e:
            logger.error(f"Error handling heartbeat: {str(e)}")
            raise

    async def sync_conversations(self, connection_id: str):
        """Synchronize conversations for a client"""
        try:
            # Get recent conversations
            recent_convs = await self.memory_manager.get_recent_conversations(limit=50)
            
            # Send sync data
            await self.connection_manager.send_personal_message(
                {
                    "type": "sync_response",
                    "conversations": recent_convs,
                    "timestamp": datetime.utcnow().isoformat()
                },
                connection_id
            )
            
        except Exception as e:
            logger.error(f"Error syncing conversations: {str(e)}")
            raise

    async def start_background_tasks(self):
        """Start background tasks"""
        try:
            # Start connection monitoring
            task = asyncio.create_task(self.monitor_connections())
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)
            
        except Exception as e:
            logger.error(f"Error starting background tasks: {str(e)}")
            raise

    async def cleanup_background_tasks(self):
        """Cleanup background tasks"""
        try:
            for task in self.background_tasks:
                task.cancel()
            
            # Wait for tasks to complete
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"Error cleaning up background tasks: {str(e)}")
            raise

    async def monitor_connections(self):
        """Monitor and cleanup inactive connections"""
        try:
            while True:
                current_time = datetime.utcnow()
                
                # Check each connection
                for connection_id in list(self.connection_manager.connection_metadata.keys()):
                    metadata = self.connection_manager.connection_metadata[connection_id]
                    last_active = datetime.fromisoformat(metadata["last_active"].replace('Z', '+00:00'))
                    
                    # If inactive for more than 5 minutes
                    if (current_time - last_active).total_seconds() > 300:
                        logger.info(f"Cleaning up inactive connection: {connection_id}")
                        await self.connection_manager.disconnect(connection_id)
                
                await asyncio.sleep(60)  # Check every minute
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in connection monitor: {str(e)}")
            raise