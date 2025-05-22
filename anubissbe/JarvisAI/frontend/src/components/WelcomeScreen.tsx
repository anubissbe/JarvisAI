import React from 'react';
import { Box, Typography, Paper, Button, Grid } from '@mui/material';
import { Chat, Settings, Info } from '@mui/icons-material';
import { motion } from 'framer-motion';

interface WelcomeScreenProps {
  onStartChat: () => void;
}

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onStartChat }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Paper
        elevation={3}
        sx={{
          p: 4,
          borderRadius: 2,
          textAlign: 'center',
          maxWidth: '800px',
          mx: 'auto',
          mt: 4,
        }}
      >
        <Box
          component={motion.div}
          initial={{ y: -20 }}
          animate={{ y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <Typography variant="h3" gutterBottom>
            Welcome to JarvisAI
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
            Your personal AI assistant
          </Typography>
        </Box>

        <Box
          component={motion.div}
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.4 }}
          sx={{ mb: 4 }}
        >
          <img
            src="/logo192.png"
            alt="JarvisAI Logo"
            style={{ width: '150px', height: '150px' }}
          />
        </Box>

        <Box
          component={motion.div}
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.6 }}
          sx={{ mb: 4 }}
        >
          <Typography variant="body1" paragraph>
            JarvisAI is your intelligent assistant powered by advanced AI. Ask questions, get information,
            control your digital life, and more - all through natural conversation.
          </Typography>
        </Box>

        <Grid
          container
          spacing={3}
          justifyContent="center"
          component={motion.div}
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.8 }}
        >
          <Grid item xs={12} sm={4}>
            <Paper
              elevation={2}
              sx={{
                p: 2,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                bgcolor: 'primary.dark',
              }}
            >
              <Chat sx={{ fontSize: 40, mb: 2, color: 'primary.light' }} />
              <Typography variant="h6" gutterBottom>
                Natural Conversation
              </Typography>
              <Typography variant="body2" align="center">
                Talk to JarvisAI just like you would with a human assistant
              </Typography>
            </Paper>
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <Paper
              elevation={2}
              sx={{
                p: 2,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                bgcolor: 'primary.dark',
              }}
            >
              <Settings sx={{ fontSize: 40, mb: 2, color: 'primary.light' }} />
              <Typography variant="h6" gutterBottom>
                Customizable
              </Typography>
              <Typography variant="body2" align="center">
                Personalize JarvisAI to fit your preferences and needs
              </Typography>
            </Paper>
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <Paper
              elevation={2}
              sx={{
                p: 2,
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                bgcolor: 'primary.dark',
              }}
            >
              <Info sx={{ fontSize: 40, mb: 2, color: 'primary.light' }} />
              <Typography variant="h6" gutterBottom>
                Intelligent
              </Typography>
              <Typography variant="body2" align="center">
                Powered by advanced AI to provide helpful and accurate responses
              </Typography>
            </Paper>
          </Grid>
        </Grid>

        <Box
          component={motion.div}
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5, delay: 1 }}
          sx={{ mt: 4 }}
        >
          <Button
            variant="contained"
            size="large"
            onClick={onStartChat}
            sx={{
              px: 4,
              py: 1.5,
              fontSize: '1.1rem',
              borderRadius: 8,
              background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
              boxShadow: '0 3px 5px 2px rgba(33, 203, 243, .3)',
            }}
          >
            Start Chatting
          </Button>
        </Box>
      </Paper>
    </motion.div>
  );
};

export default WelcomeScreen;