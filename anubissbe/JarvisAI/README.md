# ... existing code ...

## Features


## Important Clarification

JarvisAI is a standalone application that uses OpenAI's API directly. It is **not** built on top of OpenWebUI or Ollama. You don't need to configure anything in OpenWebUI or any other external system.

All configuration is done within the JarvisAI application itself through the Settings page after you create an account and log in.

### Required Configuration

After installation, you'll need to configure the following:

1. **OpenAI API Key**: Obtain an API key from [OpenAI](https://platform.openai.com/account/api-keys) and enter it in the Settings page.
2. **Voice Settings**: Choose your preferred voice from the list of available voices in the Settings page.
3. **AI Model**: Select the GPT model you want to use for generating responses (e.g., gpt-3.5-turbo, gpt-4).
4. **Appearance**: Customize the chat interface with your preferred colors and fonts.

### Knowledge Base

JarvisAI includes a knowledge base feature that allows you to upload documents (PDF, TXT, DOCX, CSV) that the AI can reference when answering your questions:

1. Navigate to the Knowledge Base page
2. Click "Upload Document" and select a file
3. Enter a title for the document
4. Upload and wait for processing to complete
5. Ask questions related to your documents in the chat

The AI will automatically search your documents for relevant information when answering your queries.

# ... existing code ...