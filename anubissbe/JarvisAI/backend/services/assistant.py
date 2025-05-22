# ... existing code ...
from .document_processor import DocumentProcessor

# ... existing code ...

class AssistantService:
    def __init__(self):
        self.ai_service = AIService()
        self.integration_manager = IntegrationManager()
        self.document_processor = DocumentProcessor()
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]], user: User) -> AssistantResponse:
        """Process a user query and generate a response"""
        try:
            # Get user settings for AI model configuration
            user_settings = await self._get_user_settings(user.id)
            
            # Search for relevant documents
            document_results = await self.document_processor.search_documents(query, user.id, top_k=3)
            
            # Add document context if available
            if document_results:
                if not context:
                    context = {}
                
                context["documents"] = document_results
            
            # Process the query with AI
            ai_response = await self.ai_service.generate_response(
                query, 
                context, 
                user_settings.ai_model
            )
            
            # Extract any commands from the AI response
            commands = self._extract_commands(ai_response)
            
            # Format the final response
            response = AssistantResponse(
                text=ai_response.get("text", ""),
                commands=commands,
                data=ai_response.get("data")
            )
            
            return response
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise

# ... existing code ...