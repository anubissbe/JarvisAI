import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import api from '../../services/api';

interface VoiceSettings {
  enabled: boolean;
  voice_id: string;
  speed: number;
  pitch: number;
}

interface AIModelSettings {
  model: string;
  temperature: number;
  max_tokens: number;
}

interface IntegrationSettings {
  enabled_integrations: string[];
  api_keys: Record<string, string>;
}

interface Settings {
  user_id: string;
  voice: VoiceSettings;
  ai_model: AIModelSettings;
  integrations: IntegrationSettings;
  theme: string;
  custom_settings: Record<string, any>;
}

interface SettingsState {
  settings: Settings | null;
  loading: boolean;
  error: string | null;
}

const initialState: SettingsState = {
  settings: null,
  loading: false,
  error: null,
};

export const fetchSettings = createAsyncThunk(
  'settings/fetchSettings',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/api/settings');
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch settings');
    }
  }
);

export const updateSettings = createAsyncThunk(
  'settings/updateSettings',
  async (settingsData: Partial<Settings>, { rejectWithValue }) => {
    try {
      const response = await api.put('/api/settings', settingsData);
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to update settings');
    }
  }
);

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    clearSettingsError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch settings
    builder.addCase(fetchSettings.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchSettings.fulfilled, (state, action: PayloadAction<Settings>) => {
      state.loading = false;
      state.settings = action.payload;
    });
    builder.addCase(fetchSettings.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });
    
    // Update settings
    builder.addCase(updateSettings.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(updateSettings.fulfilled, (state, action: PayloadAction<Settings>) => {
      state.loading = false;
      state.settings = action.payload;
    });
    builder.addCase(updateSettings.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });
  },
});

export const { clearSettingsError } = settingsSlice.actions;
export default settingsSlice.reducer;