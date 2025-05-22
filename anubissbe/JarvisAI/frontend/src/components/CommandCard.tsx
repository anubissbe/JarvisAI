import React from 'react';
import { Card, CardContent, Typography, Box, IconButton, Chip } from '@mui/material';
import { Close, PlayArrow } from '@mui/icons-material';
import { motion } from 'framer-motion';

interface Command {
  type: string;
  action: string;
  parameters: Record<string, any>;
}

interface CommandCardProps {
  command: Command;
  onExecute: (command: Command) => void;
  onDismiss: (commandId: string) => void;
}

const CommandCard: React.FC<CommandCardProps> = ({ command, onExecute, onDismiss }) => {
  const getCommandIcon = () => {
    switch (command.type) {
      case 'system':
        return '💻';
      case 'web':
        return '🌐';
      case 'email':
        return '📧';
      case 'calendar':
        return '📅';
      case 'weather':
        return '🌤️';
      case 'music':
        return '🎵';
      default:
        return '🤖';
    }
  };
  
  const getCommandTitle = () => {
    return `${command.type.charAt(0).toUpperCase() + command.type.slice(1)}: ${command.action}`;
  };
  
  const getCommandDescription = () => {
    if (Object.keys(command.parameters).length === 0) {
      return 'No parameters';
    }
    
    return Object.entries(command.parameters)
      .map(([key, value]) => `${key}: ${typeof value === 'object' ? JSON.stringify(value) : value}`)
      .join(', ');
  };
  
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.3 }}
    >
      <Card
        sx={{
          mb: 2,
          borderRadius: 2,
          boxShadow: 3,
          bgcolor: 'background.paper',
          border: '1px solid',
          borderColor: 'primary.dark',
        }}
      >
        <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Typography variant="h6" component="span" sx={{ mr: 1 }}>
                {getCommandIcon()}
              </Typography>
              <Typography variant="h6" component="span">
                {getCommandTitle()}
              </Typography>
            </Box>
            <Box>
              <IconButton
                size="small"
                color="primary"
                onClick={() => onExecute(command)}
                sx={{ mr: 1 }}
              >
                <PlayArrow />
              </IconButton>
              <IconButton
                size="small"
                color="error"
                onClick={() => onDismiss(`${command.type}:${command.action}`)}
              >
                <Close />
              </IconButton>
            </Box>
          </Box>
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {getCommandDescription()}
          </Typography>
          
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            <Chip
              label={command.type}
              size="small"
              color="primary"
              variant="outlined"
            />
            <Chip
              label={command.action}
              size="small"
              color="secondary"
              variant="outlined"
            />
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default CommandCard;