import os
import logging
import tempfile
from typing import List, Dict, Any, Optional
import PyPDF2
import docx
import csv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
import numpy as np

from models.db.document import DocumentDB

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = None
        self._load_vector_store()
    
    def _load_vector_store(self):
        """Load or create the vector store"""
        try:
            if os.path.exists("faiss_index"):
                self.vector_store = FAISS.load_local("faiss_index", self.embeddings)
                logger.info("Loaded existing vector store")
            else:
                self.vector_store = FAISS.from_texts(["JarvisAI initialization"], self.embeddings)
                self.vector_store.save_local("faiss_index")
                logger.info("Created new vector store")
        except Exception as e:
            logger.error(f"Error loading vector store: {str(e)}")
            # Create empty vector store
            self.vector_store = FAISS.from_texts(["JarvisAI initialization"], self.embeddings)
    
    async def process_document(self, document_id: str) -> bool:
        """Process a document and create embeddings"""
        try:
            # Get document from database
            document = await DocumentDB.get(document_id)
            if not document:
                logger.error(f"Document not found: {document_id}")
                return False
            
            # Update status
            document.embedding_status = "processing"
            await document.save()
            
            # Extract text from content
            chunks = self.text_splitter.split_text(document.content)
            document.chunks = chunks
            
            # Create embeddings and add to vector store
            self.vector_store.add_texts(chunks, metadatas=[{"document_id": document_id, "chunk_id": i} for i in range(len(chunks))])
            self.vector_store.save_local("faiss_index")
            
            # Update status
            document.embedding_status = "completed"
            await document.save()
            
            return True
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            if document:
                document.embedding_status = "failed"
                await document.save()
            return False
    
    async def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """Extract text from a file"""
        try:
            if file_type == "pdf":
                return self._extract_text_from_pdf(file_path)
            elif file_type == "docx":
                return self._extract_text_from_docx(file_path)
            elif file_type == "txt":
                return self._extract_text_from_txt(file_path)
            elif file_type == "csv":
                return self._extract_text_from_csv(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error extracting text from file: {str(e)}")
            raise
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file"""
        text = ""
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from a DOCX file"""
        doc = docx.Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    
    def _extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from a TXT file"""
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    
    def _extract_text_from_csv(self, file_path: str) -> str:
        """Extract text from a CSV file"""
        text = ""
        with open(file_path, "r", encoding="utf-8") as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                text += " | ".join(row) + "\n"
        return text
    
    async def search_documents(self, query: str, user_id: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for documents relevant to a query"""
        try:
            if not self.vector_store:
                return []
            
            # Get documents for this user
            user_documents = await DocumentDB.find({"user_id": user_id}).to_list()
            user_document_ids = [str(doc.id) for doc in user_documents]
            
            if not user_document_ids:
                return []
            
            # Search vector store
            results = self.vector_store.similarity_search_with_score(query, k=top_k * 2)
            
            # Filter results to only include user's documents
            filtered_results = []
            for doc, score in results:
                if "document_id" in doc.metadata and doc.metadata["document_id"] in user_document_ids:
                    # Find the document
                    for user_doc in user_documents:
                        if str(user_doc.id) == doc.metadata["document_id"]:
                            filtered_results.append({
                                "document_id": doc.metadata["document_id"],
                                "chunk_id": doc.metadata.get("chunk_id", 0),
                                "title": user_doc.title,
                                "content": doc.page_content,
                                "score": float(score),
                            })
                            break
            
            # Sort by score and limit to top_k
            filtered_results.sort(key=lambda x: x["score"])
            return filtered_results[:top_k]
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []