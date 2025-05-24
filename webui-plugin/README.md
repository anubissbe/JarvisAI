# Jarvis Memory Plugin for Open WebUI

This plugin integrates Jarvis's long-term memory system with Open WebUI, enabling persistent conversation history, context awareness, and intelligent memory management.

## Features

1. **Real-time Memory Integration**
   - Automatic conversation storage
   - Context preservation
   - Intelligent importance scoring
   - Long-term memory retention

2. **Seamless WebUI Integration**
   - Automatic chat message capture
   - Conversation synchronization
   - Memory access interface
   - Error handling and notifications

3. **Robust Connection Management**
   - Automatic reconnection
   - Heartbeat monitoring
   - Error recovery
   - Connection state management

## Installation

1. Add the plugin to your Open WebUI installation:

```bash
# Navigate to Open WebUI plugins directory
cd /app/backend/plugins

# Create directory for Jarvis plugin
mkdir jarvis-memory
cd jarvis-memory

# Copy plugin files
cp /path/to/jarvis-memory.js .
```

2. Enable the plugin in Open WebUI configuration:

```json
{
  "plugins": {
    "jarvis-memory": {
      "enabled": true,
      "script": "/plugins/jarvis-memory/jarvis-memory.js"
    }
  }
}
```

3. Restart Open WebUI to load the plugin.

## Usage

### Automatic Memory Integration

The plugin automatically:
- Captures all chat messages
- Stores conversation context
- Maintains conversation history
- Syncs with Jarvis's memory system

### Manual Sync

Use the "Sync Memory" button in the UI to:
- Force synchronization with memory system
- Retrieve historical conversations
- Update conversation context

### Accessing Memory

Memory integration is transparent:
1. Historical context is automatically included in conversations
2. Important information is preserved long-term
3. Related conversations are linked together

### Error Handling

The plugin provides:
- Visual error notifications
- Automatic reconnection
- Error logging
- Connection status indicators

## API Reference

### Global Object

The plugin creates a global `window.jarvisMemory` object with the following methods:

```javascript
// Add conversation handler
const unsubscribe = window.jarvisMemory.onConversation((message) => {
    console.log('New conversation:', message);
});

// Force sync
await window.jarvisMemory.syncConversations();

// Disconnect
await window.jarvisMemory.disconnect();
```

### Event Handling

Subscribe to memory events:

```javascript
window.jarvisMemory.onConversation((message) => {
    const {
        conversation_id,
        message: content,
        timestamp
    } = message;
    
    // Handle conversation update
});
```

## Troubleshooting

1. **Connection Issues**
   - Check Jarvis backend is running
   - Verify WebSocket port (5000) is accessible
   - Check browser console for errors

2. **Sync Problems**
   - Click "Sync Memory" button
   - Check network connectivity
   - Verify Jarvis memory system status

3. **UI Integration**
   - Ensure plugin is properly loaded
   - Check browser console for errors
   - Verify Open WebUI configuration

## Contributing

1. **Bug Reports**
   - Use GitHub Issues
   - Include browser console logs
   - Provide steps to reproduce

2. **Feature Requests**
   - Describe use case
   - Explain desired behavior
   - Provide example scenarios

3. **Code Contributions**
   - Fork repository
   - Create feature branch
   - Submit pull request

## License

This plugin is part of the JarvisAI project and is licensed under the MIT License.