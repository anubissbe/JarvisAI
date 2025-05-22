# ... existing code ...
@router.post("/upload", response_model=schemas.Document)
async def upload_document(
    file: UploadFile = File(...),
    collection_id: str = Form(...),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
):
    # ... existing code ...
    
    # Add logging to track progress
    logger.info(f"Starting to process document: {file.filename}, size: {file_size} bytes")
    
    # ... existing code ...
    
    # Add more logging throughout the process
    logger.info(f"Document parsed, extracting content")
    
    # ... existing code ...
    
    logger.info(f"Content extracted, creating document record")
    
    # ... existing code ...
    
    logger.info(f"Document record created, processing chunks")
    
    # ... existing code ...
    
    logger.info(f"Document processing completed: {file.filename}")
    
    # ... existing code ...