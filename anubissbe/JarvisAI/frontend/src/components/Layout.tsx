// ... existing code ...

import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Settings as SettingsIcon,
  ExitToApp as LogoutIcon,
  AccountCircle,
  Book as KnowledgeIcon,
} from '@mui/icons-material';

// ... existing code ...

<List>
  <ListItem
    button
    selected={location.pathname === '/dashboard'}
    onClick={() => navigate('/dashboard')}
  >
    <ListItemIcon>
      <DashboardIcon />
    </ListItemIcon>
    <ListItemText primary="Dashboard" />
  </ListItem>
  <ListItem
    button
    selected={location.pathname === '/knowledge'}
    onClick={() => navigate('/knowledge')}
  >
    <ListItemIcon>
      <KnowledgeIcon />
    </ListItemIcon>
    <ListItemText primary="Knowledge Base" />
  </ListItem>
  <ListItem
    button
    selected={location.pathname === '/settings'}
    onClick={() => navigate('/settings')}
  >
    <ListItemIcon>
      <SettingsIcon />
    </ListItemIcon>
    <ListItemText primary="Settings" />
  </ListItem>
</List>

// ... existing code ...