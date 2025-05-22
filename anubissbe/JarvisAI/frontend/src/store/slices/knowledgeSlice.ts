import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import api from '../../services/api';

interface Document {
  id: string;
  title: string;
  file_type: string;
  original_filename: string;
  status: string;
  created_at: string;
}

interface KnowledgeState {
  documents: Document[];
  loading: boolean;
  error: string | null;
}

const initialState: KnowledgeState = {
  documents: [],
  loading: false,
  error: null,
};

export const fetchDocuments = createAsyncThunk(
  'knowledge/fetchDocuments',
  async (_, { rejectWithValue }) => {
    try {
      const response = await api.get('/api/documents');
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch documents');
    }
  }
);

export const uploadDocument = createAsyncThunk(
  'knowledge/uploadDocument',
  async (formData: FormData, { rejectWithValue }) => {
    try {
      const response = await api.post('/api/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to upload document');
    }
  }
);

export const deleteDocument = createAsyncThunk(
  'knowledge/deleteDocument',
  async (documentId: string, { rejectWithValue }) => {
    try {
      await api.delete(`/api/documents/${documentId}`);
      return documentId;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to delete document');
    }
  }
);

const knowledgeSlice = createSlice({
  name: 'knowledge',
  initialState,
  reducers: {
    clearKnowledgeError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch documents
    builder.addCase(fetchDocuments.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(fetchDocuments.fulfilled, (state, action: PayloadAction<Document[]>) => {
      state.loading = false;
      state.documents = action.payload;
    });
    builder.addCase(fetchDocuments.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });
    
    // Upload document
    builder.addCase(uploadDocument.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(uploadDocument.fulfilled, (state, action: PayloadAction<Document>) => {
      state.loading = false;
      state.documents.push(action.payload);
    });
    builder.addCase(uploadDocument.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });
    
    // Delete document
    builder.addCase(deleteDocument.pending, (state) => {
      state.loading = true;
      state.error = null;
    });
    builder.addCase(deleteDocument.fulfilled, (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.documents = state.documents.filter(doc => doc.id !== action.payload);
    });
    builder.addCase(deleteDocument.rejected, (state, action) => {
      state.loading = false;
      state.error = action.payload as string;
    });
  },
});

export const { clearKnowledgeError } = knowledgeSlice.actions;
export default knowledgeSlice.reducer;