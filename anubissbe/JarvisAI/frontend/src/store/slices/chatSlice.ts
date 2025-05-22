import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import api from '../../services/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  isTyping?: boolean;
}

interface Command {
  type: string;
  action: string;
  parameters: Record<string, any>;
}

interface ChatState {
  messages: Message[];
  loading: boolean;
  error: string | null;
  activeCommands: Command[];
}

const initialState: ChatState = {
  messages: [],
  loading: false,
  error: null,
  activeCommands: [],
};

export const sendMessage = createAsyncThunk(
  'chat/sendMessage',
  async (message: string, { getState, rejectWithValue }) => {
    try {
      // Get chat history for context
      const { chat } = getState() as { chat: ChatState };
      const history = chat.messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));
      
      const response = await api.post('/api/assistant/query', {
        query: message,
        context: { history }
      });
      
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to send message');
    }
  }
);

export const executeCommand = createAsyncThunk(
  'chat/executeCommand',
  async (command: Command, { rejectWithValue }) => {
    try {
      const response = await api.post('/api/assistant/execute-command', command);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to execute command');
    }
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addUserMessage: (state, action: PayloadAction<string>) => {
      state.messages.push({
        id: Date.now().toString(),
        role: 'user',
        content: action.payload,
        timestamp: Date.now(),
      });
    },
    startAssistantTyping: (state) => {
      state.messages.push({
        id: `typing-${Date.now()}`,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
        isTyping: true,
      });
    },
    clearChat: (state) => {
      state.messages = [];
      state.activeCommands = [];
    },
    addCommand: (state, action: PayloadAction<Command>) => {
      state.activeCommands.push(action.payload);
    },
    removeCommand: (state, action: PayloadAction<string>) => {
      state.activeCommands = state.activeCommands.filter(cmd => 
        !(cmd.type === action.payload || `${cmd.type}:${cmd.action}` === action.payload)
      );
    },
  },
  extraReducers: (builder) => {
    // Send message
    builder.addCase(sendMessage.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(sendMessage.fulfilled, (state, action) => {
      state.loading = false;
      
      // Remove typing indicator
      state.messages = state.messages.filter(msg => !msg.isTyping);
      
      // Add assistant response
      state.messages.push({
        id: Date.now().toString(),
        role: 'assistant',
        content: action.payload.text,
        timestamp: Date.now(),
      });
      
      // Add commands if any
      if (action.payload.commands && action.payload.commands.length > 0) {
        state.activeCommands = [
          ...state.activeCommands,
          ...action.payload.commands
        ];
      }
    });
    builder.addCase(sendMessage.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
      
      // Remove typing indicator
      state.messages = state.messages.filter(msg => !msg.isTyping);
      
      // Add error message
      state.messages.push({
        id: Date.now().toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${action.payload}`,
        timestamp: Date.now(),
      });
    });
    
    // Execute command
    builder.addCase(executeCommand.fulfilled, (state, action) => {
      // Add command result as assistant message if it has a message
      if (action.payload.message) {
        state.messages.push({
          id: Date.now().toString(),
          role: 'assistant',
          content: action.payload.message,
          timestamp: Date.now(),
        });
      }
    });
  },
});

export const { 
  addUserMessage, 
  startAssistantTyping, 
  clearChat,
  addCommand,
  removeCommand
} = chatSlice.actions;
export default chatSlice.reducer;