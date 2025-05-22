import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, Avatar } from '@mui/material';
import { SmartToy, Person } from '@mui/icons-material';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  isTyping?: boolean;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ role, content, isTyping }) => {
  const [displayedContent, setDisplayedContent] = useState('');
  const [charIndex, setCharIndex] = useState(0);
  
  // Typing effect for assistant messages
  useEffect(() => {
    if (role === 'assistant' && !isTyping) {
      if (charIndex < content.length) {
        const timer = setTimeout(() => {
          setDisplayedContent(content.substring(0, charIndex + 1));
          setCharIndex(charIndex + 1);
        }, 15); // Adjust speed as needed
        
        return () => clearTimeout(timer);
      }
    } else {
      setDisplayedContent(content);
      setCharIndex(content.length);
    }
  }, [role, content, charIndex, isTyping]);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Box
        sx={{
          display: 'flex',
          mb: 2,
          flexDirection: role === 'user' ? 'row-reverse' : 'row',
        }}
      >
        <Avatar
          sx={{
            bgcolor: role === 'user' ? 'secondary.main' : 'primary.main',
            mr: role === 'user' ? 0 : 2,
            ml: role === 'user' ? 2 : 0,
          }}
        >
          {role === 'user' ? <Person /> : <SmartToy />}
        </Avatar>
        <Paper
          elevation={1}
          sx={{
            p: 2,
            maxWidth: '70%',
            borderRadius: 2,
            bgcolor: role === 'user' ? 'secondary.dark' : 'primary.dark',
            position: 'relative',
          }}
        >
          {isTyping ? (
            <Box sx={{ display: 'flex', alignItems: 'center', height: '24px' }}>
              <Box
                component="span"
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: 'common.white',
                  mx: 0.5,
                  animation: 'pulse 1s infinite',
                  animationDelay: '0s',
                }}
              />
              <Box
                component="span"
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: 'common.white',
                  mx: 0.5,
                  animation: 'pulse 1s infinite',
                  animationDelay: '0.2s',
                }}
              />
              <Box
                component="span"
                sx={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  bgcolor: 'common.white',
                  mx: 0.5,
                  animation: 'pulse 1s infinite',
                  animationDelay: '0.4s',
                }}
              />
            </Box>
          ) : (
            <Typography component="div" variant="body1">
              <ReactMarkdown>{displayedContent}</ReactMarkdown>
            </Typography>
          )}
        </Paper>
      </Box>
    </motion.div>
  );
};

export default ChatMessage;