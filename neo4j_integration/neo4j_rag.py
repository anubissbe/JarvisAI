from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Neo4j connection settings
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_secure_password_here")

class KnowledgeGraph:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        
    def close(self):
        self.driver.close()
        
    def find_related_documents(self, topic):
        """Find documents related to a specific topic"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Document)-[:COVERS]->(t:Topic {name: $topic})
                RETURN d.title, d.path, d.id
            """, topic=topic)
            return [record for record in result]
            
    def find_related_concepts(self, query):
        """Find concepts related to a query string"""
        # This is a simple implementation - in production you would use embeddings
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Concept)
                WHERE c.name CONTAINS $query OR c.description CONTAINS $query
                RETURN c.name, c.description
            """, query=query)
            return [record for record in result]
    
    def get_document_context(self, doc_id):
        """Get the full context of a document with its topics and concepts"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Document {id: $doc_id})
                OPTIONAL MATCH (d)-[:COVERS]->(t:Topic)
                OPTIONAL MATCH (c:Concept)-[:BELONGS_TO]->(t)
                RETURN d.title, collect(distinct t.name) as topics, 
                       collect(distinct {name: c.name, description: c.description}) as concepts
            """, doc_id=doc_id)
            return [record for record in result]

# Example usage
if __name__ == "__main__":
    kg = KnowledgeGraph()
    try:
        # Test queries
        print("Documents about Argparse:")
        for doc in kg.find_related_documents("Argparse"):
            print(f"- {doc['d.title']}")
            
        print("\nConcepts related to 'parser':")
        for concept in kg.find_related_concepts("parser"):
            print(f"- {concept['c.name']}: {concept['c.description']}")
            
        print("\nContext for argparse-optparse document:")
        for ctx in kg.get_document_context("argparse-optparse"):
            print(f"Document: {ctx['d.title']}")
            print(f"Topics: {', '.join(ctx['topics'])}")
            print(f"Related concepts:")
            for c in ctx['concepts']:
                if c['name'] is not None:  # Filter out None values
                    print(f"  - {c['name']}: {c['description']}")
    finally:
        kg.close()
