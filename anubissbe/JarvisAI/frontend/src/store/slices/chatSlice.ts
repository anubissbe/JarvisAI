// ... existing code ...

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
      state.error = null;
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
  // ... existing extraReducers ...
});

export const { 
  addUserMessage, 
  startAssistantTyping, 
  clearChat,
  addCommand,
  removeCommand
} = chatSlice.actions;
export default chatSlice.reducer;