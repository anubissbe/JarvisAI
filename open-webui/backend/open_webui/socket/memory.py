from fastapi import WebSocket
from typing import Dict, Any, Set, Optional
import asyncio
import json
import logging
from datetime import datetime

from ..models.memory import ConversationMemory
from ..internal.memory import MemoryManager

logger = logging.getLogger(__name__)

class MemoryWebSocketManager:
    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.conversation_subscribers: Dict[str, Set[str]] = {}
        self.broadcast_queue = asyncio.Queue()
        
        # Start background tasks
        self.background_tasks = set()
        self.start_background_tasks()

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection"""
        try:
            await websocket.accept()
            self.active_connections[client_id] = websocket
            self.connection_metadata[client_id] = {
                "connected_at": datetime.utcnow().isoformat(),
                "last_active": datetime.utcnow().isoformat(),
                "messages_received": 0,
                "messages_sent": 0
            }
            
            # Send welcome message
            await self.send_personal_message(
                client_id,
                {
                    "type": "system",
                    "message": "Connected to memory system",
                    "client_id": client_id
                }
            )
            
            logger.info(f"Client connected: {client_id}")
            
        except Exception as e:
            logger.error(f"Error accepting connection: {str(e)}")
            raise

    async def disconnect(self, client_id: str):
        """Handle client disconnection"""
        try:
            # Remove from all conversation subscriptions
            for subscribers in self.conversation_subscribers.values():
                subscribers.discard(client_id)
            
            # Clean up connection data
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            if client_id in self.connection_metadata:
                del self.connection_metadata[client_id]
                
            logger.info(f"Client disconnected: {client_id}")
            
        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")

    async def send_personal_message(self, client_id: str, message: Dict[str, Any]):
        """Send a message to a specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message)
                
                # Update metadata
                self.connection_metadata[client_id]["messages_sent"] += 1
                self.connection_metadata[client_id]["last_active"] = datetime.utcnow().isoformat()
                
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {str(e)}")
                await self.disconnect(client_id)

    async def broadcast_to_conversation(self, conversation_id: str, message: Dict[str, Any]):
        """Broadcast a message to all clients subscribed to a conversation"""
        if conversation_id in self.conversation_subscribers:
            for client_id in self.conversation_subscribers[conversation_id]:
                await self.send_personal_message(client_id, message)

    async def handle_message(self, client_id: str, message: Dict[str, Any]):
        """Process incoming WebSocket messages"""
        try:
            # Update metadata
            self.connection_metadata[client_id]["messages_received"] += 1
            self.connection_metadata[client_id]["last_active"] = datetime.utcnow().isoformat()
            
            message_type = message.get("type", "unknown")
            
            if message_type == "subscribe":
                await self.handle_subscribe(client_id, message)
            elif message_type == "unsubscribe":
                await self.handle_unsubscribe(client_id, message)
            elif message_type == "chat":
                await self.handle_chat_message(client_id, message)
            elif message_type == "sync":
                await self.handle_sync_request(client_id, message)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await self.send_personal_message(
                client_id,
                {
                    "type": "error",
                    "message": f"Error processing message: {str(e)}"
                }
            )

    async def handle_subscribe(self, client_id: str, message: Dict[str, Any]):
        """Handle conversation subscription requests"""
        conversation_id = message.get("conversation_id")
        if conversation_id:
            if conversation_id not in self.conversation_subscribers:
                self.conversation_subscribers[conversation_id] = set()
            self.conversation_subscribers[conversation_id].add(client_id)
            
            # Send recent memories
            memories = await self.memory_manager.get_conversation_memories(
                conversation_id=conversation_id,
                limit=50
            )
            
            await self.send_personal_message(
                client_id,
                {
                    "type": "memories",
                    "conversation_id": conversation_id,
                    "memories": [memory.dict() for memory in memories]
                }
            )

    async def handle_unsubscribe(self, client_id: str, message: Dict[str, Any]):
        """Handle conversation unsubscribe requests"""
        conversation_id = message.get("conversation_id")
        if conversation_id and conversation_id in self.conversation_subscribers:
            self.conversation_subscribers[conversation_id].discard(client_id)

    async def handle_chat_message(self, client_id: str, message: Dict[str, Any]):
        """Handle chat messages"""
        try:
            conversation_id = message.get("conversation_id")
            if not conversation_id:
                raise ValueError("conversation_id is required")
            
            # Create memory entry
            memory = ConversationMemory(
                id=f"mem_{datetime.utcnow().timestamp()}",
                conversation_id=conversation_id,
                user_message=message.get("message", ""),
                assistant_message=message.get("response", ""),
                context=message.get("context", {}),
                metadata={
                    "client_id": client_id,
                    "source": "chat"
                }
            )
            
            # Store memory
            stored_memory = await self.memory_manager.store_conversation_memory(
                conversation_id=conversation_id,
                memory=memory
            )
            
            # Notify subscribers
            await self.broadcast_to_conversation(
                conversation_id,
                {
                    "type": "memory_update",
                    "conversation_id": conversation_id,
                    "memory": stored_memory.dict()
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling chat message: {str(e)}")
            raise

    async def handle_sync_request(self, client_id: str, message: Dict[str, Any]):
        """Handle conversation sync requests"""
        try:
            conversation_id = message.get("conversation_id")
            if not conversation_id:
                raise ValueError("conversation_id is required")
            
            # Get memories
            memories = await self.memory_manager.get_conversation_memories(
                conversation_id=conversation_id,
                limit=message.get("limit", 50),
                offset=message.get("offset", 0)
            )
            
            # Send response
            await self.send_personal_message(
                client_id,
                {
                    "type": "sync_response",
                    "conversation_id": conversation_id,
                    "memories": [memory.dict() for memory in memories],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling sync request: {str(e)}")
            raise

    def start_background_tasks(self):
        """Start background tasks"""
        task = asyncio.create_task(self.monitor_connections())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

    async def monitor_connections(self):
        """Monitor and cleanup inactive connections"""
        try:
            while True:
                current_time = datetime.utcnow()
                
                # Check each connection
                for client_id in list(self.connection_metadata.keys()):
                    metadata = self.connection_metadata[client_id]
                    last_active = datetime.fromisoformat(
                        metadata["last_active"].replace('Z', '+00:00')
                    )
                    
                    # If inactive for more than 5 minutes
                    if (current_time - last_active).total_seconds() > 300:
                        logger.info(f"Cleaning up inactive connection: {client_id}")
                        await self.disconnect(client_id)
                
                await asyncio.sleep(60)  # Check every minute
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in connection monitor: {str(e)}")
            raise

    async def cleanup(self):
        """Cleanup tasks on shutdown"""
        # Cancel all background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        # Close all connections
        for client_id in list(self.active_connections.keys()):
            await self.disconnect(client_id)