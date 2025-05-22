#!/usr/bin/env python3
"""
Test script for Document Processor service
"""

import os
import sys
import unittest
import json
import tempfile
import shutil
import threading
import time
import random
import string
import numpy as np
from unittest.mock import patch, MagicMock, mock_open

# Add parent directory to path to import module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the document processor module
try:
    from document_processor.processor import (
        DocumentChunk, extract_text_from_document, chunk_text,
        get_embedding, process_document, connect_to_neo4j,
        EXT_TO_TYPE
    )
except ImportError:
    print("Error: Cannot import document_processor module. Make sure you're running from the project root.")
    # Continue anyway to allow individual test execution
    pass


class TestDocumentProcessor(unittest.TestCase):
    """Tests for the Document Processor service"""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests"""
        # Create temporary directories for testing
        cls.temp_dir = tempfile.mkdtemp()
        cls.upload_dir = os.path.join(cls.temp_dir, 'uploads')
        cls.processed_dir = os.path.join(cls.temp_dir, 'processed')
        
        os.makedirs(cls.upload_dir, exist_ok=True)
        os.makedirs(cls.processed_dir, exist_ok=True)
        
        # Set environment variables
        os.environ['UPLOAD_DIR'] = cls.upload_dir
        os.environ['PROCESSED_DIR'] = cls.processed_dir
        
        # Create sample files for testing
        cls._create_sample_files()

    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        # Remove temporary directories
        shutil.rmtree(cls.temp_dir)

    @classmethod
    def _create_sample_files(cls):
        """Create sample files for testing"""
        # Create a sample text file
        with open(os.path.join(cls.upload_dir, 'sample.txt'), 'w') as f:
            f.write("This is a sample text file.\nIt has multiple lines.\nThis is for testing the document processor.")
        
        # Create a sample HTML file
        with open(os.path.join(cls.upload_dir, 'sample.html'), 'w') as f:
            f.write("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sample HTML</title>
            </head>
            <body>
                <h1>Sample HTML Document</h1>
                <p>This is a paragraph in an HTML document.</p>
                <p>It's used for testing the document processor.</p>
            </body>
            </html>
            """)
        
        # Create a sample code file
        with open(os.path.join(cls.upload_dir, 'sample.py'), 'w') as f:
            f.write("""
            # Sample Python file
            def hello_world():
                print("Hello, World!")
                
            if __name__ == "__main__":
                hello_world()
            """)

    def test_document_chunk_class(self):
        """Test the DocumentChunk class"""
        # Create a document chunk
        chunk = DocumentChunk(
            text="Sample text",
            doc_id="doc123",
            chunk_id="chunk456",
            page_num=1,
            section="Introduction",
            metadata={"author": "Test"}
        )
        
        # Test conversion to dictionary
        chunk_dict = chunk.to_dict()
        self.assertEqual(chunk_dict['text'], "Sample text")
        self.assertEqual(chunk_dict['doc_id'], "doc123")
        self.assertEqual(chunk_dict['chunk_id'], "chunk456")
        self.assertEqual(chunk_dict['page_num'], 1)
        self.assertEqual(chunk_dict['section'], "Introduction")
        self.assertEqual(chunk_dict['metadata']['author'], "Test")
        
        # Test creation from dictionary
        new_chunk = DocumentChunk.from_dict(chunk_dict)
        self.assertEqual(new_chunk.text, chunk.text)
        self.assertEqual(new_chunk.doc_id, chunk.doc_id)
        self.assertEqual(new_chunk.chunk_id, chunk.chunk_id)
        self.assertEqual(new_chunk.page_num, chunk.page_num)
        self.assertEqual(new_chunk.section, chunk.section)
        self.assertEqual(new_chunk.metadata, chunk.metadata)

    def test_chunk_text(self):
        """Test text chunking functionality"""
        # Test with short text (should be one chunk)
        short_text = "This is a short text that should fit in one chunk."
        chunks = chunk_text(short_text, chunk_size=100, overlap=20)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], short_text)
        
        # Test with longer text (should be multiple chunks)
        long_text = " ".join(["Sentence number {}. ".format(i) for i in range(50)])
        chunks = chunk_text(long_text, chunk_size=100, overlap=20)
        self.assertGreater(len(chunks), 1)
        
        # Test with empty text
        empty_text = ""
        chunks = chunk_text(empty_text)
        self.assertEqual(len(chunks), 0)
        
        # Test with None
        none_text = None
        with self.assertRaises(TypeError):
            chunk_text(none_text)
        
        # Test overlap (chunks should share some content)
        text_with_repeated_phrase = "The quick brown fox. " * 20
        chunks = chunk_text(text_with_repeated_phrase, chunk_size=100, overlap=50)
        if len(chunks) > 1:
            # Find some content from the end of first chunk
            end_of_first = chunks[0][-40:]
            # It should appear at the beginning of the second chunk
            self.assertTrue(chunks[1].startswith(end_of_first) or 
                           any(phrase in chunks[1][:100] for phrase in end_of_first.split()))

    @patch('requests.post')
    def test_get_embedding(self, mock_post):
        """Test getting embeddings from Ollama API"""
        # Mock the response from Ollama API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5]
        }
        mock_post.return_value = mock_response
        
        # Call the function
        embedding = get_embedding("Test text")
        
        # Check that the function called the API correctly
        mock_post.assert_called_once()
        self.assertEqual(embedding, [0.1, 0.2, 0.3, 0.4, 0.5])
        
        # Test error handling
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        embedding = get_embedding("Test text")
        self.assertIsNone(embedding)
        
        # Test exception handling
        mock_post.side_effect = Exception("Connection error")
        embedding = get_embedding("Test text")
        self.assertIsNone(embedding)

    def test_extract_text_from_text_file(self):
        """Test extracting text from a text file"""
        from document_processor.processor import extract_text_from_text_file
        
        # Get the path to the sample text file
        file_path = os.path.join(self.upload_dir, 'sample.txt')
        
        # Extract text
        text = extract_text_from_text_file(file_path)
        
        # Check that text was extracted correctly
        self.assertIn("This is a sample text file.", text)
        self.assertIn("It has multiple lines.", text)
        self.assertIn("This is for testing the document processor.", text)

    def test_extract_text_from_html(self):
        """Test extracting text from an HTML file"""
        from document_processor.processor import extract_text_from_html
        
        # Get the path to the sample HTML file
        file_path = os.path.join(self.upload_dir, 'sample.html')
        
        # Extract text
        text = extract_text_from_html(file_path)
        
        # Check that text was extracted correctly
        self.assertIn("Sample HTML Document", text)
        self.assertIn("This is a paragraph in an HTML document.", text)
        self.assertIn("It's used for testing the document processor.", text)
        
        # Check that HTML tags were removed
        self.assertNotIn("<html>", text)
        self.assertNotIn("<body>", text)
        self.assertNotIn("<p>", text)

    def test_extract_text_from_document_error_handling(self):
        """Test error handling in extract_text_from_document"""
        # Test with a non-existent file
        result = extract_text_from_document("nonexistent_file.txt")
        self.assertEqual(result, [])
        
        # Test with an unsupported file type
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as tmp:
            tmp.write(b"test content")
            file_path = tmp.name
        
        result = extract_text_from_document(file_path)
        self.assertEqual(result, [])
        
        # Clean up
        os.unlink(file_path)

    @patch('document_processor.processor.get_embedding')
    @patch('document_processor.processor.extract_text_from_document')
    @patch('document_processor.processor.neo4j_driver')
    def test_process_document(self, mock_neo4j_driver, mock_extract_text, mock_get_embedding):
        """Test the document processing pipeline"""
        # Mock the text extraction
        mock_extract_text.return_value = [(1, "This is page 1."), (2, "This is page 2.")]
        
        # Mock the embedding generation
        mock_get_embedding.return_value = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        # Mock Neo4j session
        mock_session = MagicMock()
        mock_neo4j_driver.session.return_value.__enter__.return_value = mock_session
        mock_session.run.return_value.single.return_value = None
        
        # Create a test file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"test content")
            file_path = tmp.name
        
        # Process the document
        doc_id = process_document(file_path)
        
        # Check that a document ID was returned
        self.assertIsNotNone(doc_id)
        self.assertTrue(doc_id.startswith("doc_"))
        
        # Check that Neo4j was called
        mock_session.run.assert_called()
        
        # Check that the file was processed
        mock_extract_text.assert_called_once_with(file_path)
        
        # Clean up
        os.unlink(file_path)
    
    def test_supported_file_extensions(self):
        """Test that the processor supports all advertised file extensions"""
        # Check that each extension in FILE_TYPES maps to a valid file type in EXT_TO_TYPE
        from document_processor.processor import FILE_TYPES, EXT_TO_TYPE
        
        for file_type, extensions in FILE_TYPES.items():
            for ext in extensions:
                self.assertIn(ext, EXT_TO_TYPE)
                self.assertEqual(EXT_TO_TYPE[ext], file_type)


class TestDocumentProcessorIntegration(unittest.TestCase):
    """Integration tests for the Document Processor"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures before running tests"""
        # Check if we can connect to Neo4j
        cls.neo4j_available = False
        
        try:
            from neo4j import GraphDatabase
            uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
            user = os.environ.get('NEO4J_USER', 'neo4j')
            password = os.environ.get('NEO4J_PASSWORD', 'password')
            
            driver = GraphDatabase.driver(uri, auth=(user, password))
            with driver.session() as session:
                result = session.run("RETURN 1 as num")
                if result.single()["num"] == 1:
                    cls.neo4j_available = True
            driver.close()
        except:
            print("Warning: Neo4j not available. Integration tests will be skipped.")
    
    @unittest.skipIf(not hasattr(TestDocumentProcessorIntegration, 'neo4j_available') or 
                    not TestDocumentProcessorIntegration.neo4j_available, 
                    "Neo4j not available")
    def test_neo4j_connection(self):
        """Test connection to Neo4j"""
        result = connect_to_neo4j()
        self.assertIsNotNone(result)
        result.close()


def generate_random_document(file_path, size_kb=10):
    """Generate a random document for testing"""
    # Generate random text
    chars_per_kb = 1024
    text = ''.join(random.choice(string.ascii_letters + string.digits + ' \n.,:;!?') 
                  for _ in range(size_kb * chars_per_kb))
    
    # Write to file
    with open(file_path, 'w') as f:
        f.write(text)
    
    return text


if __name__ == '__main__':
    # Run unit tests
    unittest.main()