import React, { useState, useEffect } from 'react';
import { Box, TextField, IconButton, Paper } from '@mui/material';
import { Send, Mic, MicOff } from '@mui/icons-material';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
  const [message, setMessage] = useState('');
  const [isListening, setIsListening] = useState(false);
  
  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition
  } = useSpeechRecognition();
  
  // Update message with transcript when speech recognition is active
  useEffect(() => {
    if (isListening && transcript) {
      setMessage(transcript);
    }
  }, [transcript, isListening]);
  
  // Update listening state based on SpeechRecognition state
  useEffect(() => {
    setIsListening(listening);
  }, [listening]);
  
  const handleSendMessage = () => {
    if (message.trim()) {
      onSendMessage(message.trim());
      setMessage('');
      resetTranscript();
    }
  };
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  const toggleListening = () => {
    if (listening) {
      SpeechRecognition.stopListening();
    } else {
      resetTranscript();
      SpeechRecognition.startListening({ continuous: true });
    }
  };
  
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
        {browserSupportsSpeechRecognition && (
          <IconButton
            color={isListening ? 'secondary' : 'primary'}
            onClick={toggleListening}
            disabled={disabled}
            sx={{ ml: 1 }}
          >
            {isListening ? <MicOff /> : <Mic />}
          </IconButton>
        )}
        <IconButton
          color="primary"
          onClick={handleSendMessage}
          disabled={!message.trim() || disabled}
          sx={{ ml: 1 }}
        >
          <Send />
        </IconButton>
      </Box>
    </Paper>
  );
};

export default ChatInput;