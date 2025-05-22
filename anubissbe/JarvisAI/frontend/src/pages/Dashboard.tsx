import React, { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';
import { 
  addUserMessage, 
  startAssistantTyping, 
  sendMessage, 
  executeCommand,
  removeCommand
} from '../store/slices/chatSlice';
import { fetchSettings } from '../store/slices/settingsSlice';
import {
  Box,
  Typography,
  Paper,
  Divider,
  Grid,
  useTheme,
  Fade,
} from '@mui/material';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import CommandCard from '../components/CommandCard';
import speechService from '../services/speechService';

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const dispatch = useDispatch<AppDispatch>();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);
  
  const { messages, loading, activeCommands } = useSelector((state: RootState) => state.chat);
  const { settings } = useSelector((state: RootState) => state.settings);
  
  // Fetch user settings on component mount
  useEffect(() => {
    dispatch(fetchSettings());
  }, [dispatch]);
  
  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  // Text-to-speech for assistant messages
  useEffect(() => {
    if (settings?.voice?.enabled && messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.role === 'assistant' && !lastMessage.isTyping && !isSpeaking) {
        setIsSpeaking(true);
        
        speechService.speak(lastMessage.content, {
          voice: settings.voice.voice_id,
          rate: settings.voice.speed,
          pitch: settings.voice.pitch,
        });
        
        speechService.synth.onend = () => {
          setIsSpeaking(false);
        };
      }
    }
    
    return () => {
      speechService.stop();
    };
  }, [messages, settings, isSpeaking]);
  
  const handleSendMessage = async (message: string) => {
    // Add user message to chat
    dispatch(addUserMessage(message));
    
    // Show typing indicator
    dispatch(startAssistantTyping());
    
    // Send message to API
    await dispatch(sendMessage(message));
  };
  
  const handleExecuteCommand = (command: any) => {
    dispatch(executeCommand(command));
  };
  
  const handleDismissCommand = (commandId: string) => {
    dispatch(removeCommand(commandId));
  };
  
  return (
    <Box sx={{ height: 'calc(100vh - 100px)' }}>
      <Grid container spacing={2} sx={{ height: '100%' }}>
        <Grid item xs={12} md={8} lg={9} sx={{ height: '100%' }}>
          <Paper
            elevation={3}
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              borderRadius: 2,
              overflow: 'hidden',
              bgcolor: 'background.paper',
            }}
          >
            <Box
              sx={{
                p: 2,
                borderBottom: 1,
                borderColor: 'divider',
                bgcolor: 'background.paper',
              }}
            >
              <Typography variant="h6">Chat with Jarvis</Typography>
            </Box>
            
            <Box
              sx={{
                p: 2,
                flexGrow: 1,
                overflow: 'auto',
                bgcolor: theme.palette.background.default,
              }}
            >
              {messages.length === 0 ? (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    opacity: 0.7,
                  }}
                >
                  <Typography variant="h5" gutterBottom>
                    Welcome to JarvisAI
                  </Typography>
                  <Typography variant="body1" align="center">
                    How can I assist you today?
                  </Typography>
                </Box>
              ) : (
                messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    role={message.role}
                    content={message.content}
                    isTyping={message.isTyping}
                  />
                ))
              )}
              <div ref={messagesEndRef} />
            </Box>
            
            <Box sx={{ p: 2, bgcolor: 'background.paper' }}>
              <ChatInput onSendMessage={handleSendMessage} disabled={loading || isSpeaking} />
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4} lg={3} sx={{ height: '100%' }}>
          <Paper
            elevation={3}
            sx={{
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              borderRadius: 2,
              overflow: 'hidden',
              bgcolor: 'background.paper',
            }}
          >
            <Box
              sx={{
                p: 2,
                borderBottom: 1,
                borderColor: 'divider',
              }}
            >
              <Typography variant="h6">Available Commands</Typography>
            </Box>
            
            <Box
              sx={{
                p: 2,
                flexGrow: 1,
                overflow: 'auto',
              }}
            >
              {activeCommands.length === 0 ? (
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    opacity: 0.7,
                  }}
                >
                  <Typography variant="body1" align="center">
                    No commands available yet. Ask Jarvis to perform a task.
                  </Typography>
                </Box>
              ) : (
                activeCommands.map((command, index) => (
                  <CommandCard
                    key={`${command.type}-${command.action}-${index}`}
                    command={command}
                    onExecute={handleExecuteCommand}
                    onDismiss={handleDismissCommand}
                  />
                ))
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;