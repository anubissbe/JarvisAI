import requests
from neo4j import GraphDatabase
from pymilvus import connections, Collection
import json
import time
import re
import os

class HybridSearch:
    def __init__(self, 
               neo4j_uri="bolt://neo4j:7687", 
               neo4j_user="neo4j", 
               neo4j_password="password",
               milvus_host="milvus-standalone", 
               milvus_port="19530",
               ollama_url="http://ollama:11434",
               openwebui_url="http://open-webui:8080"):
        # Neo4j setup
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        # Milvus setup
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        
        # Ollama setup
        self.ollama_url = ollama_url
        
        # OpenWebUI setup
        self.openwebui_url = openwebui_url
        
        print("Initializing HybridSearch with Neo4j connection...")
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 'Connected!' as message")
                print("Successfully connected to Neo4j")
        except Exception as e:
            print(f"Error connecting to Neo4j: {str(e)}")
        
        print("HybridSearch initialized successfully")
    
    # Rest of your implementation...
    
    def hybrid_search(self, query_text, knowledge_base_id, top_k=5):
        # Your hybrid search implementation
        # Make sure all API calls have the proper format:
        # requests.get(url, params, timeout=30)  # NOT requests.get(timeout=30, url, params)
        
        # Example of correct API call with timeout
        try:
            response = requests.get(
                f"{self.openwebui_url}/api/v1/knowledge/query",
                params={"query": query_text, "kb_id": knowledge_base_id},
                timeout=30  # Timeout placed at the end as a keyword argument
            )
        except Exception as e:
            print(f"Error in API call: {str(e)}")
            return []
            
        # Process and return the results
        return []
