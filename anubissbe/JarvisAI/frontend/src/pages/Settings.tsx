import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';
import { fetchSettings, updateSettings } from '../store/slices/settingsSlice';
import {
  Box,
  Typography,
  Paper,
  Divider,
  Grid,
  TextField,
  Switch,
  FormControlLabel,
  Button,
  Slider,
  MenuItem,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  IconButton,
  InputAdornment,
} from '@mui/material';
import {
  Save,
  Refresh,
  Visibility,
  VisibilityOff,
} from '@mui/icons-material';
import speechService from '../services/speechService';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

const Settings: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { settings, loading, error } = useSelector((state: RootState) => state.settings);
  
  const [tabValue, setTabValue] = useState(0);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [voiceId, setVoiceId] = useState('');
  const [voiceSpeed, setVoiceSpeed] = useState(1.0);
  const [voicePitch, setVoicePitch] = useState(0.0);
  const [model, setModel] = useState('');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(150);
  const [theme, setTheme] = useState('dark');
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [showApiKeys, setShowApiKeys] = useState<Record<string, boolean>>({});
  const [enabledIntegrations, setEnabledIntegrations] = useState<string[]>([]);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  const availableVoices = speechService.getVoices();
  
  useEffect(() => {
    dispatch(fetchSettings());
  }, [dispatch]);
  
  useEffect(() => {
    if (settings) {
      setVoiceEnabled(settings.voice.enabled);
      setVoiceId(settings.voice.voice_id);
      setVoiceSpeed(settings.voice.speed);
      setVoicePitch(settings.voice.pitch);
      setModel(settings.ai_model.model);
      setTemperature(settings.ai_model.temperature);
      setMaxTokens(settings.ai_model.max_tokens);
      setTheme(settings.theme);
      setApiKeys(settings.integrations.api_keys);
      setEnabledIntegrations(settings.integrations.enabled_integrations);
    }
  }, [settings]);
  
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  const handleSaveSettings = async () => {
    const updatedSettings = {
      voice: {
        enabled: voiceEnabled,
        voice_id: voiceId,
        speed: voiceSpeed,
        pitch: voicePitch,
      },
      ai_model: {
        model,
        temperature,
        max_tokens: maxTokens,
      },
      integrations: {
        enabled_integrations: enabledIntegrations,
        api_keys: apiKeys,
      },
      theme,
    };
    
    const result = await dispatch(updateSettings(updatedSettings));
    
    if (updateSettings.fulfilled.match(result)) {
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    }
  };
  
  const handleToggleApiKeyVisibility = (key: string) => {
    setShowApiKeys({
      ...showApiKeys,
      [key]: !showApiKeys[key],
    });
  };
  
  const handleApiKeyChange = (integration: string, value: string) => {
    setApiKeys({
      ...apiKeys,
      [integration]: value,
    });
  };
  
  const handleIntegrationToggle = (integration: string) => {
    if (enabledIntegrations.includes(integration)) {
      setEnabledIntegrations(enabledIntegrations.filter(i => i !== integration));
    } else {
      setEnabledIntegrations([...enabledIntegrations, integration]);
    }
  };
  
  const testVoice = () => {
    speechService.speak('Hello, this is a test of the voice settings.', {
      voice: voiceId,
      rate: voiceSpeed,
      pitch: voicePitch,
    });
  };
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      
      <Paper elevation={3} sx={{ borderRadius: 2, overflow: 'hidden' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="settings tabs">
            <Tab label="Voice" />
            <Tab label="AI Model" />
            <Tab label="Integrations" />
            <Tab label="Appearance" />
          </Tabs>
        </Box>
        
        {error && (
          <Alert severity="error" sx={{ m: 2 }}>
            {error}
          </Alert>
        )}
        
        {saveSuccess && (
          <Alert severity="success" sx={{ m: 2 }}>
            Settings saved successfully!
          </Alert>
        )}
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <TabPanel value={tabValue} index={0}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={voiceEnabled}
                        onChange={(e) => setVoiceEnabled(e.target.checked)}
                      />
                    }
                    label="Enable Voice"
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    select
                    fullWidth
                    label="Voice"
                    value={voiceId}
                    onChange={(e) => setVoiceId(e.target.value)}
                    disabled={!voiceEnabled}
                  >
                    {availableVoices.map((voice) => (
                      <MenuItem key={voice.name} value={voice.name}>
                        {voice.name} ({voice.lang})
                      </MenuItem>
                    ))}
                  </TextField>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Button
                    variant="outlined"
                    onClick={testVoice}
                    disabled={!voiceEnabled}
                  >
                    Test Voice
                  </Button>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Typography gutterBottom>Speed</Typography>
                  <Slider
                    value={voiceSpeed}
                    onChange={(e, value) => setVoiceSpeed(value as number)}
                    min={0.5}
                    max={2}
                    step={0.1}
                    marks
                    valueLabelDisplay="auto"
                    disabled={!voiceEnabled}
                  />
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <Typography gutterBottom>Pitch</Typography>
                  <Slider
                    value={voicePitch}
                    onChange={(e, value) => setVoicePitch(value as number)}
                    min={-1}
                    max={1}
                    step={0.1}
                    marks
                    valueLabelDisplay="auto"
                    disabled={!voiceEnabled}
                  />
                </Grid>
              </Grid>
            </TabPanel>
            
            <TabPanel value={tabValue} index={1}>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    select
                    fullWidth
                    label="AI Model"
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                  >
                    <MenuItem value="gpt-3.5-turbo">GPT-3.5 Turbo</MenuItem>
                    <MenuItem value="gpt-4">GPT-4</MenuItem>
                    <MenuItem value="gpt-4-turbo">GPT-4 Turbo</MenuItem>
                  </TextField>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Max Tokens"
                    type="number"
                    value={maxTokens}
                    onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                    InputProps={{ inputProps: { min: 50, max: 4000 } }}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <Typography gutterBottom>Temperature</Typography>
                  <Slider
                    value={temperature}
                    onChange={(e, value) => setTemperature(value as number)}
                    min={0}
                    max={1}
                    step={0.1}
                    marks
                    valueLabelDisplay="auto"
                  />
                  <Typography variant="body2" color="text.secondary">
                    Lower values make responses more focused and deterministic. Higher values make responses more creative and varied.
                  </Typography>
                </Grid>
              </Grid>
            </TabPanel>
            
            <TabPanel value={tabValue} index={2}>
              <Grid container spacing={3}>
                <Grid item xs={12}>
                  <Typography variant="h6" gutterBottom>
                    Available Integrations
                  </Typography>
                </Grid>
                
                {['weather', 'email', 'calendar', 'music', 'web'].map((integration) => (
                  <Grid item xs={12} key={integration}>
                    <Paper sx={{ p: 2, borderRadius: 2 }}>
                      <Grid container spacing={2} alignItems="center">
                        <Grid item xs={12} sm={4}>
                          <FormControlLabel
                            control={
                              <Switch
                                checked={enabledIntegrations.includes(integration)}
                                onChange={() => handleIntegrationToggle(integration)}
                              />
                            }
                            label={integration.charAt(0).toUpperCase() + integration.slice(1)}
                          />
                        </Grid>
                        
                        <Grid item xs={12} sm={8}>
                          <TextField
                            fullWidth
                            label={`${integration.charAt(0).toUpperCase() + integration.slice(1)} API Key`}
                            value={apiKeys[integration] || ''}
                            onChange={(e) => handleApiKeyChange(integration, e.target.value)}
                            disabled={!enabledIntegrations.includes(integration)}
                            type={showApiKeys[integration] ? 'text' : 'password'}
                            InputProps={{
                              endAdornment: (
                                <InputAdornment position="end">
                                  <IconButton
                                    onClick={() => handleToggleApiKeyVisibility(integration)}
                                    edge="end"
                                  >
                                    {showApiKeys[integration] ? <VisibilityOff /> : <Visibility />}
                                  </IconButton>
                                </InputAdornment>
                              ),
                            }}
                          />
                        </Grid>
                      </Grid>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </TabPanel>
            
            <TabPanel value={tabValue} index={3}>
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    select
                    fullWidth
                    label="Theme"
                    value={theme}
                    onChange={(e) => setTheme(e.target.value)}
                  >
                    <MenuItem value="dark">Dark</MenuItem>
                    <MenuItem value="light">Light</MenuItem>
                    <MenuItem value="system">System Default</MenuItem>
                  </TextField>
                </Grid>
              </Grid>
            </TabPanel>
          </>
        )}
        
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={() => dispatch(fetchSettings())}
            disabled={loading}
          >
            Reset
          </Button>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={handleSaveSettings}
            disabled={loading}
          >
            Save Settings
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default Settings;