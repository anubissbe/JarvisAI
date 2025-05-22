# ... existing code ...

def _prepare_messages(self, query: str, context: Optional[Dict[str, Any]]) -> list:
    """Prepare the messages for the AI model"""
    system_message = "You are Jarvis, an advanced AI assistant. You can help with various tasks and provide information."
    
    # Add document context if available
    if context and "documents" in context and context["documents"]:
        document_context = "I have access to the following information from your documents:\n\n"
        for i, doc in enumerate(context["documents"]):
            document_context += f"Document {i+1}: {doc['title']}\n"
            document_context += f"Content: {doc['content']}\n\n"
        
        system_message += f"\n\n{document_context}"
        system_message += "\nWhen answering questions, use this document information when relevant."
    
    messages = [
        {"role": "system", "content": system_message}
    ]
    
    # Add context if provided
    if context and "history" in context and isinstance(context["history"], list):
        for msg in context["history"]:
            if "role" in msg and "content" in msg:
                messages.append({"role": msg["role"], "content": msg["content"]})
    
    # Add the current query
    messages.append({"role": "user", "content": query})
    
    return messages

# ... existing code ...