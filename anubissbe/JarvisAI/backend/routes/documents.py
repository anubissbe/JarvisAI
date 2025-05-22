from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from typing import List, Optional
import os
import uuid
import tempfile
import shutil

from services.auth import get_current_user
from services.document_processor import DocumentProcessor
from models.user import User
from models.db.document import DocumentDB

router = APIRouter()
document_processor = DocumentProcessor()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Upload a document"""
    try:
        # Check file type
        filename = file.filename
        file_extension = filename.split(".")[-1].lower()
        
        if file_extension not in ["pdf", "txt", "docx", "csv"]:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Save file to temp location
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        try:
            contents = await file.read()
            with open(temp_file.name, "wb") as f:
                f.write(contents)
            
            # Extract text
            text = await document_processor.extract_text_from_file(temp_file.name, file_extension)
            
            # Create document in database
            document = DocumentDB(
                user_id=current_user.id,
                title=title,
                content=text,
                file_type=file_extension,
                original_filename=filename
            )
            await document.save()
            
            # Process document in background
            # In a production app, this would be a background task
            await document_processor.process_document(str(document.id))
            
            return {
                "id": str(document.id),
                "title": document.title,
                "file_type": document.file_type,
                "original_filename": document.original_filename,
                "status": document.embedding_status
            }
        finally:
            os.unlink(temp_file.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@router.get("/")
async def get_documents(current_user: User = Depends(get_current_user)):
    """Get all documents for a user"""
    documents = await DocumentDB.find({"user_id": current_user.id}).to_list()
    return [
        {
            "id": str(doc.id),
            "title": doc.title,
            "file_type": doc.file_type,
            "original_filename": doc.original_filename,
            "status": doc.embedding_status,
            "created_at": doc.created_at
        }
        for doc in documents
    ]

@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a document"""
    document = await DocumentDB.get(document_id)
    if not document or document.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "id": str(document.id),
        "title": document.title,
        "content": document.content,
        "file_type": document.file_type,
        "original_filename": document.original_filename,
        "status": document.embedding_status,
        "created_at": document.created_at
    }

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a document"""
    document = await DocumentDB.get(document_id)
    if not document or document.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")
    
    await document.delete()
    return {"status": "success"}