# ... existing code ...

def __init__(self):
    self.text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    # Use environment variable for OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        raise ValueError("OPENAI_API_KEY environment variable not set")
    self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    self.vector_store = None
    self._load_vector_store()

# ... existing code ...