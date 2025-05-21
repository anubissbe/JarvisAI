from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from services.assistant import AssistantService
from services.auth import get_current_user
from models.user import User
from models.assistant import AssistantResponse, Command

router = APIRouter()
assistant_service = AssistantService()

class AssistantRequest(BaseModel):
    query: str
    context: Optional[dict] = None

@router.post("/query", response_model=AssistantResponse)
async def process_query(
    request: AssistantRequest,
    current_user: User = Depends(get_current_user)
):
    """Process a user query and return the assistant's response"""
    try:
        response = await assistant_service.process_query(request.query, request.context, current_user)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@router.post("/execute-command", response_model=dict)
async def execute_command(
    command: Command,
    current_user: User = Depends(get_current_user)
):
    """Execute a specific command"""
    try:
        result = await assistant_service.execute_command(command, current_user)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing command: {str(e)}")