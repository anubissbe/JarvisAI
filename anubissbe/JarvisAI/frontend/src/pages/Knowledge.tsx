import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../store';
import { fetchDocuments, uploadDocument, deleteDocument } from '../store/slices/knowledgeSlice';
import {
  Box,
  Typography,
  Paper,
  Button,
  Grid,
  TextField,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  List,
  ListItem,
  ListItemText,
  ListItemSecondary,
  IconButton,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Description as DescriptionIcon,
  PictureAsPdf as PdfIcon,
  InsertDriveFile as FileIcon,
  TableChart as CsvIcon,
} from '@mui/icons-material';

const Knowledge: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { documents, loading, error } = useSelector((state: RootState) => state.knowledge);
  
  const [openUploadDialog, setOpenUploadDialog] = useState(false);
  const [title, setTitle] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState('');
  
  useEffect(() => {
    dispatch(fetchDocuments());
  }, [dispatch]);
  
  const handleOpenUploadDialog = () => {
    setOpenUploadDialog(true);
    setTitle('');
    setFile(null);
    setUploadError('');
  };
  
  const handleCloseUploadDialog = () => {
    setOpenUploadDialog(false);
  };
  
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      const selectedFile = event.target.files[0];
      const fileExtension = selectedFile.name.split('.').pop()?.toLowerCase();
      
      if (!fileExtension || !['pdf', 'txt', 'docx', 'csv'].includes(fileExtension)) {
        setUploadError('Unsupported file type. Please upload PDF, TXT, DOCX, or CSV files.');
        setFile(null);
        return;
      }
      
      setFile(selectedFile);
      setUploadError('');
      
      // Auto-fill title from filename if empty
      if (!title) {
        const fileName = selectedFile.name.split('.')[0];
        setTitle(fileName);
      }
    }
  };
  
  const handleUpload = async () => {
    if (!file) {
      setUploadError('Please select a file to upload.');
      return;
    }
    
    if (!title.trim()) {
      setUploadError('Please enter a title for the document.');
      return;
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    
    try {
      await dispatch(uploadDocument(formData));
      handleCloseUploadDialog();
    } catch (error) {
      setUploadError('Failed to upload document. Please try again.');
    }
  };
  
  const handleDeleteDocument = (documentId: string) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      dispatch(deleteDocument(documentId));
    }
  };
  
  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case 'pdf':
        return <PdfIcon color="error" />;
      case 'docx':
        return <DescriptionIcon color="primary" />;
      case 'csv':
        return <CsvIcon color="success" />;
      default:
        return <FileIcon />;
    }
  };
  
  const getStatusChip = (status: string) => {
    switch (status) {
      case 'pending':
        return <Chip size="small" label="Pending" color="default" />;
      case 'processing':
        return <Chip size="small" label="Processing" color="warning" />;
      case 'completed':
        return <Chip size="small" label="Completed" color="success" />;
      case 'failed':
        return <Chip size="small" label="Failed" color="error" />;
      default:
        return <Chip size="small" label={status} />;
    }
  };
  
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Knowledge Base</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleOpenUploadDialog}
        >
          Upload Document
        </Button>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      <Paper elevation={3} sx={{ borderRadius: 2, overflow: 'hidden' }}>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">Your Documents</Typography>
        </Box>
        
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : documents.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              No documents found. Upload documents to enhance Jarvis's knowledge.
            </Typography>
          </Box>
        ) : (
          <List>
            {documents.map((document) => (
              <ListItem
                key={document.id}
                secondaryAction={
                  <IconButton
                    edge="end"
                    aria-label="delete"
                    onClick={() => handleDeleteDocument(document.id)}
                  >
                    <DeleteIcon />
                  </IconButton>
                }
                sx={{ borderBottom: '1px solid', borderColor: 'divider' }}
              >
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      {getFileIcon(document.file_type)}
                      <Typography sx={{ ml: 1 }}>{document.title}</Typography>
                    </Box>
                  }
                  secondary={
                    <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                      <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
                        {document.original_filename}
                      </Typography>
                      {getStatusChip(document.status)}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </Paper>
      
      <Dialog open={openUploadDialog} onClose={handleCloseUploadDialog}>
        <DialogTitle>Upload Document</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Upload PDF, TXT, DOCX, or CSV files to enhance Jarvis's knowledge base.
            Jarvis will use this information when answering your questions.
          </DialogContentText>
          
          {uploadError && (
            <Alert severity="error" sx={{ mt: 2, mb: 1 }}>
              {uploadError}
            </Alert>
          )}
          
          <TextField
            margin="dense"
            label="Document Title"
            fullWidth
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            sx={{ mb: 2 }}
          />
          
          <Button
            variant="outlined"
            component="label"
            fullWidth
            sx={{ mt: 1, p: 1.5, borderStyle: 'dashed' }}
          >
            {file ? file.name : 'Select File'}
            <input
              type="file"
              hidden
              accept=".pdf,.txt,.docx,.csv"
              onChange={handleFileChange}
            />
          </Button>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseUploadDialog}>Cancel</Button>
          <Button
            onClick={handleUpload}
            variant="contained"
            disabled={!file || !title.trim()}
          >
            Upload
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Knowledge;