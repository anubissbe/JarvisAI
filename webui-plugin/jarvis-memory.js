// Jarvis Memory Integration Plugin for Open WebUI
class JarvisMemoryPlugin {
    constructor() {
        this.websocket = null;
        this.connectionAttempts = 0;
        this.maxRetries = 5;
        this.retryDelay = 5000; // 5 seconds
        this.heartbeatInterval = null;
        this.pendingMessages = new Map();
        this.messageCallbacks = new Map();
        this.conversationHandlers = new Set();
        this.connected = false;
        this.reconectTimer = null;

        // Bind methods
        this.init = this.init.bind(this);
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.handleMessage = this.handleMessage.bind(this);
        this.sendMessage = this.sendMessage.bind(this);
        this.startHeartbeat = this.startHeartbeat.bind(this);
        this.stopHeartbeat = this.stopHeartbeat.bind(this);
        this.reconnect = this.reconnect.bind(this);
        this.handleWebSocketError = this.handleWebSocketError.bind(this);
    }

    async init() {
        try {
            // Get WebSocket URL from environment or default
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsHost = window.location.hostname;
            const wsPort = '5000'; // Jarvis WebSocket port
            this.wsUrl = `${wsProtocol}//${wsHost}:${wsPort}/ws`;

            // Initialize WebSocket connection
            await this.connect();

            // Add chat interceptor to Open WebUI
            this.interceptChatMessages();

            // Add conversation sync button to UI
            this.addSyncButton();

            console.log('Jarvis Memory Plugin initialized');
        } catch (error) {
            console.error('Failed to initialize Jarvis Memory Plugin:', error);
        }
    }

    async connect() {
        try {
            this.websocket = new WebSocket(this.wsUrl);

            this.websocket.onopen = () => {
                console.log('Connected to Jarvis Memory System');
                this.connected = true;
                this.connectionAttempts = 0;
                this.startHeartbeat();
                this.syncConversations();
            };

            this.websocket.onmessage = (event) => {
                this.handleMessage(event.data);
            };

            this.websocket.onerror = (error) => {
                this.handleWebSocketError(error);
            };

            this.websocket.onclose = () => {
                this.connected = false;
                this.stopHeartbeat();
                this.handleDisconnect();
            };

        } catch (error) {
            console.error('WebSocket connection error:', error);
            this.handleWebSocketError(error);
        }
    }

    handleWebSocketError(error) {
        console.error('WebSocket error:', error);
        this.connected = false;
        this.stopHeartbeat();

        // Attempt reconnection if not max attempts
        if (this.connectionAttempts < this.maxRetries) {
            this.reconnect();
        } else {
            console.error('Max reconnection attempts reached');
        }
    }

    async reconnect() {
        this.connectionAttempts++;
        console.log(`Attempting to reconnect (${this.connectionAttempts}/${this.maxRetries})...`);

        // Clear any existing reconnect timer
        if (this.reconectTimer) {
            clearTimeout(this.reconectTimer);
        }

        // Wait before reconnecting
        this.reconectTimer = setTimeout(() => {
            this.connect();
        }, this.retryDelay * this.connectionAttempts);
    }

    handleDisconnect() {
        if (!this.connected && this.connectionAttempts < this.maxRetries) {
            this.reconnect();
        }
    }

    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.connected) {
                this.sendMessage({
                    type: 'heartbeat',
                    timestamp: new Date().toISOString()
                });
            }
        }, 30000); // Send heartbeat every 30 seconds
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    handleMessage(data) {
        try {
            const message = JSON.parse(data);
            
            switch (message.type) {
                case 'chat_received':
                    this.handleChatReceived(message);
                    break;
                case 'sync_response':
                    this.handleSyncResponse(message);
                    break;
                case 'error':
                    this.handleError(message);
                    break;
                case 'heartbeat':
                    // Heartbeat received, connection is alive
                    break;
                default:
                    console.warn('Unknown message type:', message.type);
            }

            // Handle any pending callbacks
            if (message.message_id && this.messageCallbacks.has(message.message_id)) {
                const callback = this.messageCallbacks.get(message.message_id);
                callback(message);
                this.messageCallbacks.delete(message.message_id);
            }

        } catch (error) {
            console.error('Error handling message:', error);
        }
    }

    async sendMessage(message) {
        if (!this.connected) {
            throw new Error('WebSocket not connected');
        }

        try {
            // Add message ID if not present
            if (!message.message_id) {
                message.message_id = this.generateMessageId();
            }

            // Store message in pending map
            this.pendingMessages.set(message.message_id, message);

            // Send the message
            this.websocket.send(JSON.stringify(message));

            return message.message_id;
        } catch (error) {
            console.error('Error sending message:', error);
            throw error;
        }
    }

    generateMessageId() {
        return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    // Chat message interception
    interceptChatMessages() {
        // Find the chat input form
        const chatForm = document.querySelector('#chat-input-form');
        if (chatForm) {
            const originalSubmit = chatForm.onsubmit;
            chatForm.onsubmit = async (event) => {
                // Get the message content
                const messageInput = chatForm.querySelector('input[type="text"], textarea');
                const message = messageInput.value;

                // Get conversation ID from URL or state
                const conversationId = this.getCurrentConversationId();

                // Send to Jarvis Memory System
                await this.sendMessage({
                    type: 'chat',
                    conversation_id: conversationId,
                    message: message,
                    timestamp: new Date().toISOString()
                });

                // Call original submit handler
                if (originalSubmit) {
                    originalSubmit.call(chatForm, event);
                }
            };
        }
    }

    getCurrentConversationId() {
        // Try to get from URL
        const urlParams = new URLSearchParams(window.location.search);
        let conversationId = urlParams.get('conversation');

        // If not in URL, try to get from page state
        if (!conversationId) {
            const conversationElement = document.querySelector('[data-conversation-id]');
            if (conversationElement) {
                conversationId = conversationElement.dataset.conversationId;
            }
        }

        // If still no ID, generate one
        if (!conversationId) {
            conversationId = `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        }

        return conversationId;
    }

    // UI Modifications
    addSyncButton() {
        // Create sync button
        const syncButton = document.createElement('button');
        syncButton.innerHTML = `
            <span class="icon">🔄</span>
            <span class="text">Sync Memory</span>
        `;
        syncButton.className = 'jarvis-sync-button';
        syncButton.onclick = () => this.syncConversations();

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .jarvis-sync-button {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 16px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background: #f5f5f5;
                cursor: pointer;
                transition: background 0.2s;
            }
            .jarvis-sync-button:hover {
                background: #e5e5e5;
            }
            .jarvis-sync-button .icon {
                font-size: 16px;
            }
        `;
        document.head.appendChild(style);

        // Find appropriate location to insert button
        const toolbar = document.querySelector('.chat-toolbar, .toolbar, header');
        if (toolbar) {
            toolbar.appendChild(syncButton);
        }
    }

    async syncConversations() {
        try {
            await this.sendMessage({
                type: 'system',
                command: 'sync_request',
                timestamp: new Date().toISOString()
            });
        } catch (error) {
            console.error('Error syncing conversations:', error);
        }
    }

    handleChatReceived(message) {
        // Notify any registered conversation handlers
        this.conversationHandlers.forEach(handler => {
            handler(message);
        });
    }

    handleSyncResponse(message) {
        // Update UI with synced conversations
        const conversations = message.conversations || [];
        this.updateConversationsList(conversations);
    }

    handleError(message) {
        console.error('Jarvis Memory System error:', message.error);
        // Show error in UI if appropriate
        this.showErrorNotification(message.error);
    }

    updateConversationsList(conversations) {
        // Find conversations list element
        const listElement = document.querySelector('.conversations-list');
        if (!listElement) return;

        // Update UI with conversation history
        conversations.forEach(conv => {
            const convElement = document.createElement('div');
            convElement.className = 'conversation-item';
            convElement.innerHTML = `
                <div class="conversation-title">${conv.title || 'Conversation'}</div>
                <div class="conversation-date">${new Date(conv.timestamp).toLocaleString()}</div>
            `;
            listElement.appendChild(convElement);
        });
    }

    showErrorNotification(error) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'jarvis-error-notification';
        notification.textContent = `Error: ${error}`;

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            .jarvis-error-notification {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 24px;
                background: #ff5555;
                color: white;
                border-radius: 4px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                z-index: 9999;
                animation: slideIn 0.3s ease-out;
            }
            @keyframes slideIn {
                from { transform: translateX(100%); }
                to { transform: translateX(0); }
            }
        `;
        document.head.appendChild(style);

        // Add to document
        document.body.appendChild(notification);

        // Remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // Public API
    onConversation(handler) {
        this.conversationHandlers.add(handler);
        return () => this.conversationHandlers.delete(handler);
    }

    async disconnect() {
        this.stopHeartbeat();
        if (this.websocket) {
            this.websocket.close();
        }
    }
}

// Initialize plugin when the page loads
window.addEventListener('load', () => {
    window.jarvisMemory = new JarvisMemoryPlugin();
    window.jarvisMemory.init();
});