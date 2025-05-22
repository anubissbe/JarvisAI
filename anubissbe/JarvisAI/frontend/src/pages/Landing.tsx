import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Button,
  Container,
  Typography,
  Grid,
  Paper,
  AppBar,
  Toolbar,
} from '@mui/material';
import { motion } from 'framer-motion';

const Landing: React.FC = () => {
  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static" color="transparent" elevation={0}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            JarvisAI
          </Typography>
          <Button color="inherit" component={RouterLink} to="/login">
            Login
          </Button>
          <Button
            variant="contained"
            color="primary"
            component={RouterLink}
            to="/register"
            sx={{ ml: 2 }}
          >
            Sign Up
          </Button>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg">
        <Box
          sx={{
            mt: 8,
            mb: 12,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}
        >
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <Typography
              component="h1"
              variant="h2"
              align="center"
              color="text.primary"
              gutterBottom
            >
              Meet JarvisAI
            </Typography>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <Typography
              variant="h5"
              align="center"
              color="text.secondary"
              paragraph
              sx={{ maxWidth: 700 }}
            >
              Your personal AI assistant powered by advanced artificial intelligence.
              Get answers, complete tasks, and simplify your digital life through natural conversation.
            </Typography>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <Box sx={{ mt: 4, display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                size="large"
                component={RouterLink}
                to="/register"
                sx={{
                  px: 4,
                  py: 1.5,
                  borderRadius: 8,
                  background: 'linear-gradient(45deg, #2196F3 30%, #21CBF3 90%)',
                  boxShadow: '0 3px 5px 2px rgba(33, 203, 243, .3)',
                }}
              >
                Get Started
              </Button>
              <Button
                variant="outlined"
                size="large"
                component={RouterLink}
                to="/login"
                sx={{ px: 4, py: 1.5, borderRadius: 8 }}
              >
                Login
              </Button>
            </Box>
          </motion.div>
        </Box>

        <Grid container spacing={4}>
          <Grid item xs={12} md={4}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.6 }}
            >
              <Paper
                elevation={3}
                sx={{
                  p: 4,
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: 4,
                  bgcolor: 'background.paper',
                }}
              >
                <Typography variant="h5" component="h2" gutterBottom>
                  Natural Conversation
                </Typography>
                <Typography variant="body1" paragraph sx={{ flexGrow: 1 }}>
                  Interact with JarvisAI using natural language. Ask questions, give commands,
                  or just chat - JarvisAI understands and responds like a human assistant.
                </Typography>
              </Paper>
            </motion.div>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.8 }}
            >
              <Paper
                elevation={3}
                sx={{
                  p: 4,
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: 4,
                  bgcolor: 'background.paper',
                }}
              >
                <Typography variant="h5" component="h2" gutterBottom>
                  Voice Enabled
                </Typography>
                <Typography variant="body1" paragraph sx={{ flexGrow: 1 }}>
                  JarvisAI can listen to your voice commands and respond with a natural-sounding voice.
                  Enable hands-free operation when you need it.
                </Typography>
              </Paper>
            </motion.div>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 1 }}
            >
              <Paper
                elevation={3}
                sx={{
                  p: 4,
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: 4,
                  bgcolor: 'background.paper',
                }}
              >
                <Typography variant="h5" component="h2" gutterBottom>
                  Powerful Integrations
                </Typography>
                <Typography variant="body1" paragraph sx={{ flexGrow: 1 }}>
                  Connect JarvisAI to your favorite services and apps. Check the weather,
                  send emails, manage your calendar, play music, and more.
                </Typography>
              </Paper>
            </motion.div>
          </Grid>
        </Grid>

        <Box sx={{ mt: 8, mb: 4, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            © {new Date().getFullYear()} JarvisAI. All rights reserved.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Landing;