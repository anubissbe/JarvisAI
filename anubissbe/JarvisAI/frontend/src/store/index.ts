import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import chatReducer from './slices/chatSlice';
import settingsReducer from './slices/settingsSlice';
import knowledgeReducer from './slices/knowledgeSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    chat: chatReducer,
    settings: settingsReducer,
    knowledge: knowledgeReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;