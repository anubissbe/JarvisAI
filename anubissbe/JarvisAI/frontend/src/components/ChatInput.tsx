import React, { useState, useEffect } from 'react';
import { Box, TextField, IconButton, Paper, Tooltip, CircularProgress } from '@mui/material';
import { Send, Mic, MicOff, Keyboard } from '@mui/icons-material';
import voiceRecognitionService from '../services/voiceRecognitionService';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
  const [message, setMessage] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isVoiceMode, setIsVoiceMode] = useState(false);
  
  // Initialize voice recognition
  useEffect(() => {
    voiceRecognitionService.onResult((text) => {
      setMessage((prev) => prev + ' ' + text);
    });
    
    voiceRecognitionService.onEnd(() => {
      setIsListening(false);
    });
    
    return () => {
      voiceRecognitionService.stop();
    };
  }, []);
  
  // Update listening state
  useEffect(() => {
    setIsListening(voiceRecognitionService.getListeningState());
  }, []);
  
  const handleSendMessage = () => {
    if (message.trim()) {
      onSendMessage(message.trim());
      setMessage('');
      
      // If in voice mode, start listening again after sending
      if (isVoiceMode && !disabled) {
        setTimeout(() => {
          toggleListening();
        }, 1000);
      }
    }
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  const toggleListening = () => {
    if (isListening) {
      voiceRecognitionService.stop();
      setIsListening(false);
    } else {
      const started = voiceRecognitionService.start();
      setIsListening(started);
    }
  };
  
  const toggleInputMode = () => {
    const newMode = !isVoiceMode;
    setIsVoiceMode(newMode);
    
    if (newMode) {
      // Switch to voice mode
      toggleListening();
    } else {
      // Switch to keyboard mode
      voiceRecognitionService.stop();
      setIsListening(false);
    }
  };
  
  const isVoiceSupported = voiceRecognitionService.isSupported();
  
  return (
    <Paper
      elevation={3}
      sx={{
        p: 2,
        borderRadius: 2,
        bgcolor: 'background.paper',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        {isVoiceMode ? (
          <Box 
            sx={{ 
              flexGrow: 1, 
              p: 2, 
              border: '1px solid',
              borderColor: isListening ? 'primary.main' : 'divider',
              borderRadius: 2,
              minHeight: '56px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              bgcolor: isListening ? 'rgba(33, 150, 243, 0.1)' : 'transparent',
            }}
          >
            {message ? (
              <Box sx={{ width: '100%' }}>{message}</Box>
            ) : (
              <Box sx={{ color: 'text.secondary' }}>
                {isListening ? 'Listening...' : 'Tap the microphone to speak'}
              </Box>
            )}
            
            {isListening && (
              <Box
                sx={{
                  position: 'absolute',
                  left: '50%',
                  top: '50%',
                  transform: 'translate(-50%, -50%)',
                  width: '100%',
                  height: '100%',
                  pointerEvents: 'none',
                }}
              >
                <Box
                  sx={{
                    position: 'absolute',
                    left: '50%',
                    top: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: '40px',
                    height: '40px',
                  }}
                >
                  <CircularProgress
                    size={40}
                    thickness={2}
                    sx={{ opacity: 0.3 }}
                  />
                </Box>
              </Box>
            )}
          </Box>
        ) : (
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Type your message..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={disabled}
            multiline
            maxRows={4}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
              },
            }}
          />
        )}
        
        {isVoiceSupported && (
          <Tooltip title={isVoiceMode ? "Switch to keyboard" : "Switch to voice"}>
            <IconButton
              color="primary"
              onClick={toggleInputMode}
              disabled={disabled}
              sx={{ ml: 1 }}
            >
              {isVoiceMode ? <Keyboard /> : <Mic />}
            </IconButton>
          </Tooltip>
        )}
        
        {isVoiceMode && isVoiceSupported && (
          <Tooltip title={isListening ? "Stop listening" : "Start listening"}>
            <IconButton
              color={isListening ? "secondary" : "primary"}
              onClick={toggleListening}
              disabled={disabled}
              sx={{ ml: 1 }}
            >
              {isListening ? <MicOff /> : <Mic />}
            </IconButton>
          </Tooltip>
        )}
        
        <Tooltip title="Send message">
          <IconButton
            color="primary"
            onClick={handleSendMessage}
            disabled={!message.trim() || disabled}
            sx={{ ml: 1 }}
          >
            <Send />
          </IconButton>
        </Tooltip>
      </Box>
    </Paper>
  );
};

export default ChatInput;