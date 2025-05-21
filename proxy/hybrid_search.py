import os
import sys
import requests
try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None
    print("Warning: neo4j driver not installed; graph features disabled", file=sys.stderr)
from datetime import datetime

class HybridSearch:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, milvus_host, milvus_port, ollama_url, openwebui_url):
        # Neo4j connection
        self.driver = None
        if GraphDatabase is not None:
            try:
                self.driver = GraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_user, neo4j_password)
                )
                with self.driver.session() as session:
                    session.run("RETURN 1")
                print("Successfully connected to Neo4j")
            except Exception as e:
                print(f"Neo4j connection error: {str(e)}")
                self.driver = None
        else:
            print("Neo4j library not installed; graph features disabled", file=sys.stderr)
        
        # Milvus configuration (used through OpenWebUI's API)
        self.milvus_host = milvus_host
        self.milvus_port = milvus_port
        
        # Ollama API for embeddings
        self.ollama_url = ollama_url

        # OpenWebUI API base URL
        self.openwebui_url = openwebui_url
    
    def get_timestamp(self):
        """Get current timestamp for status check"""
        return datetime.now().isoformat()
    
    def get_embedding(self, text):
        """Get embedding vector for text using Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
        except requests.RequestException as e:
            print(f"Embedding request error: {str(e)}")
        except ValueError as e:
            print(f"Embedding parse error: {str(e)}")
        except Exception as e:
            print(f"Embedding error: {str(e)}")
        return []
    
    def search_neo4j(self, query_text):
        """Search Neo4j knowledge graph for relevant documents"""
        if self.driver is None:
            print("Neo4j is not available, skipping graph search")
            return []
        
        # Extract keywords from query (simplified approach)
        keywords = [word for word in query_text.lower().split() if len(word) > 3]
        print(f"Extracted keywords: {keywords}")
        
        results = []
        with self.driver.session() as session:
            try:
                # Search for matching topics
                print("Searching for matching topics...")
                topic_result = session.run("""
                    MATCH (t:Topic)
                    WHERE any(keyword IN $keywords WHERE toLower(t.name) CONTAINS toLower(keyword))
                    MATCH (d:Document)-[:CONTAINS_TOPIC]->(t)
                    RETURN d.path AS id, d.title AS title, d.path AS path,
                           collect(distinct t.name) AS topics,
                           count(t) AS relevance
                    ORDER BY relevance DESC
                    LIMIT 5
                """, keywords=keywords)
                
                topic_records = list(topic_result)
                print(f"Found {len(topic_records)} topic matches")
                
                for record in topic_records:
                    results.append({
                        "id": record["id"],
                        "title": record["title"],
                        "path": record["path"],
                        "topics": record["topics"],
                        "relevance_score": record.get("relevance", 0) * 0.2,
                        "source": "graph_topic"
                    })
            except Exception as e:
                print(f"Topic search error: {str(e)}")
            
            try:
                # Search for matching concepts
                print("Searching for matching concepts...")
                concept_result = session.run("""
                    MATCH (c:Concept)
                    WHERE any(keyword IN $keywords WHERE
                              toLower(c.name) CONTAINS toLower(keyword) OR
                              toLower(c.description) CONTAINS toLower(keyword))
                    MATCH (d:Document)-[:DEMONSTRATES_CONCEPT]->(c)
                    OPTIONAL MATCH (t:Topic)-[:RELATED_TO]->(c)
                    WITH d, c, collect(distinct t.name) AS topics
                    RETURN d.path AS id, d.title AS title, d.path AS path,
                           c.name AS concept, c.description AS concept_description,
                           topics
                    LIMIT 5
                """, keywords=keywords)
                
                concept_records = list(concept_result)
                print(f"Found {len(concept_records)} concept matches")
                
                for record in concept_records:
                    results.append({
                        "id": record["id"],
                        "title": record["title"],
                        "path": record["path"],
                        "topics": record.get("topics", []),
                        "concept": record.get("concept"),
                        "concept_description": record.get("concept_description"),
                        "relevance_score": 0.8,
                        "source": "graph_concept"
                    })
            except Exception as e:
                print(f"Concept search error: {str(e)}")
        
        print(f"Neo4j search returned {len(results)} total results")
        return results
    
    def search_milvus_via_openwebui(self, query_text, knowledge_base_id, top_k=5):
        """Search Milvus through OpenWebUI's API"""
        print(f"Searching OpenWebUI with knowledge base ID: {knowledge_base_id}")
        
        # This assumes you have access to OpenWebUI's API
        api_url = f"{self.openwebui_url}/api/v1/knowledge/query"
        
        try:
            response = requests.post(
                api_url,
                json={
                    "query": query_text,
                    "knowledge_id": knowledge_base_id,
                    "top_k": top_k
                },
                headers={"Content-Type": "application/json"},
                timeout=60  # Add timeout
            )
            
            # Check if request was successful
            response.raise_for_status()
            
            data = response.json()
            print(f"OpenWebUI API response status: {response.status_code}")
            
            # Transform results to a consistent format
            results = []
            for item in data.get("results", []):
                results.append({
                    "id": item.get("document_id", "unknown"),
                    "content": item.get("content", ""),
                    "relevance_score": item.get("score", 0.5),
                    "source": "vector"
                })
            
            print(f"Transformed {len(results)} vector search results")
            return results
        
        except requests.exceptions.RequestException as e:
            print(f"OpenWebUI API request error: {str(e)}")
            return []
        except ValueError as e:
            print(f"JSON parsing error: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error in Milvus search: {str(e)}")
            return []
    
    def hybrid_search(self, query_text, knowledge_base_id, top_k=5):
        """Perform hybrid search combining Neo4j and Milvus results"""
        # Get results from both sources
        print(f"Searching for: {query_text}")
        
        try:
            print("Performing Neo4j graph search...")
            graph_results = self.search_neo4j(query_text)
            print(f"Neo4j returned {len(graph_results)} results")
        except Exception as e:
            print(f"Neo4j search error: {str(e)}")
            graph_results = []
        
        try:
            print("Performing Milvus vector search...")
            vector_results = self.search_milvus_via_openwebui(query_text, knowledge_base_id, top_k)
            print(f"Milvus returned {len(vector_results)} results")
        except Exception as e:
            print(f"Milvus search error: {str(e)}")
            vector_results = []
        
        # If both searches returned no results, return an empty list
        if not graph_results and not vector_results:
            print("No results found from either search method")
            return []
        
        # Combine results
        print("Combining results...")
        combined_results = {}
        
        # Process graph results
        for item in graph_results:
            doc_id = item["id"]
            combined_results[doc_id] = item
        
        # Process vector results and merge
        for item in vector_results:
            doc_id = item["id"]
            if doc_id in combined_results:
                # Item exists in both searches - boost score and merge info
                combined_results[doc_id]["relevance_score"] += item["relevance_score"]
                combined_results[doc_id]["content"] = item["content"]
                combined_results[doc_id]["source"] = "hybrid"
            else:
                combined_results[doc_id] = item
        
        # Convert to list and sort by relevance score
        results_list = list(combined_results.values())
        results_list.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        print(f"Returning {len(results_list)} combined results")
        return results_list[:top_k]

    def close(self):
        """Close all connections"""
        if self.driver:
            self.driver.close()

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python hybrid_search.py 'your search query'")
        sys.exit(1)
    
    query = sys.argv[1]
    # Configure via environment variables
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'VerySecurePassword')
    milvus_host = os.environ.get('MILVUS_HOST', 'localhost')
    milvus_port = os.environ.get('MILVUS_PORT', '19530')
    ollama_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
    openwebui_url = os.environ.get('OPENWEBUI_API_BASE_URL', 'http://open-webui:8080')
    searcher = HybridSearch(
        neo4j_uri,
        neo4j_user,
        neo4j_password,
        milvus_host,
        milvus_port,
        ollama_url,
        openwebui_url
    )
    
    try:
        results = searcher.hybrid_search(
            query_text=query,
            knowledge_base_id="96c3b9a4-10c1-400c-9d22-3e71cb8ed7fb",
            top_k=5
        )
        
        print("\nSearch Results:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result.get('title', 'Document')} (Source: {result.get('source')})")
            print(f"   Score: {result.get('relevance_score', 0)}")
            if "topics" in result:
                print(f"   Topics: {', '.join(result['topics'])}")
            if "concept" in result:
                print(f"   Concept: {result['concept']}")
                print(f"   Description: {result['concept_description']}")
            if "content" in result:
                content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
                print(f"   Content: {content_preview}")
    finally:
        searcher.close()
