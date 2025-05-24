from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from ..models.memory import (
    ConversationMemory,
    KnowledgeMemory,
    MemoryStats,
    MemorySearchResult,
    MemoryConfig
)
from ..internal.memory import MemoryManager
from ..dependencies import get_memory_manager, get_current_user
from ..models.users import User

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])

@router.get("/stats", response_model=MemoryStats)
async def get_memory_stats(
    memory_manager: MemoryManager = Depends(get_memory_manager),
    current_user: User = Depends(get_current_user)
):
    """Get memory system statistics"""
    try:
        return await memory_manager.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}", response_model=List[ConversationMemory])
async def get_conversation_memories(
    conversation_id: str,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    memory_manager: MemoryManager = Depends(get_memory_manager),
    current_user: User = Depends(get_current_user)
):
    """Get memories for a specific conversation"""
    try:
        return await memory_manager.get_conversation_memories(
            conversation_id=conversation_id,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversations/{conversation_id}", response_model=ConversationMemory)
async def store_conversation_memory(
    conversation_id: str,
    memory: ConversationMemory,
    memory_manager: MemoryManager = Depends(get_memory_manager),
    current_user: User = Depends(get_current_user)
):
    """Store a new conversation memory"""
    try:
        return await memory_manager.store_conversation_memory(
            conversation_id=conversation_id,
            memory=memory
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=MemorySearchResult)
async def search_memories(
    query: str,
    limit: int = Query(default=10, ge=1, le=100),
    memory_type: Optional[str] = None,
    min_relevance: float = Query(default=0.5, ge=0.0, le=1.0),
    memory_manager: MemoryManager = Depends(get_memory_manager),
    current_user: User = Depends(get_current_user)
):
    """Search through memories"""
    try:
        return await memory_manager.search_memories(
            query=query,
            limit=limit,
            memory_type=memory_type,
            min_relevance=min_relevance
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def cleanup_memories(
    memory_manager: MemoryManager = Depends(get_memory_manager),
    current_user: User = Depends(get_current_user)
):
    """Trigger memory cleanup"""
    try:
        stats = await memory_manager.cleanup_memories()
        return {
            "status": "success",
            "message": "Memory cleanup completed",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config", response_model=MemoryConfig)
async def get_memory_config(
    memory_manager: MemoryManager = Depends(get_memory_manager),
    current_user: User = Depends(get_current_user)
):
    """Get memory system configuration"""
    try:
        return await memory_manager.get_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config")
async def update_memory_config(
    config: MemoryConfig,
    memory_manager: MemoryManager = Depends(get_memory_manager),
    current_user: User = Depends(get_current_user)
):
    """Update memory system configuration"""
    try:
        await memory_manager.update_config(config)
        return {
            "status": "success",
            "message": "Configuration updated",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/conversations/{conversation_id}")
async def delete_conversation_memories(
    conversation_id: str,
    memory_manager: MemoryManager = Depends(get_memory_manager),
    current_user: User = Depends(get_current_user)
):
    """Delete all memories for a conversation"""
    try:
        await memory_manager.delete_conversation_memories(conversation_id)
        return {
            "status": "success",
            "message": f"Memories for conversation {conversation_id} deleted",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/important", response_model=List[ConversationMemory])
async def get_important_memories(
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    memory_manager: MemoryManager = Depends(get_memory_manager),
    current_user: User = Depends(get_current_user)
):
    """Get important memories"""
    try:
        return await memory_manager.get_important_memories(
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/related/{conversation_id}", response_model=List[ConversationMemory])
async def get_related_memories(
    conversation_id: str,
    limit: int = Query(default=10, ge=1, le=100),
    memory_manager: MemoryManager = Depends(get_memory_manager),
    current_user: User = Depends(get_current_user)
):
    """Get memories related to a conversation"""
    try:
        return await memory_manager.get_related_memories(
            conversation_id=conversation_id,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_memories(
    format: str = Query(default="json", regex="^(json|csv)$"),
    memory_manager: MemoryManager = Depends(get_memory_manager),
    current_user: User = Depends(get_current_user)
):
    """Export memories in specified format"""
    try:
        export_data = await memory_manager.export_memories(format)
        return {
            "status": "success",
            "data": export_data,
            "format": format,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import")
async def import_memories(
    data: dict,
    format: str = Query(default="json", regex="^(json|csv)$"),
    memory_manager: MemoryManager = Depends(get_memory_manager),
    current_user: User = Depends(get_current_user)
):
    """Import memories from specified format"""
    try:
        stats = await memory_manager.import_memories(data, format)
        return {
            "status": "success",
            "message": "Memories imported successfully",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))