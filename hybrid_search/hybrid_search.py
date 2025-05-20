#!/usr/bin/env python3
import os
import re
import logging
try:
    from neo4j import GraphDatabase
except ImportError:  # pragma: no cover - optional dependency
    GraphDatabase = None

try:
    import numpy as np
except ImportError:  # pragma: no cover - optional dependency
    np = None

try:
    import requests
except ImportError:  # pragma: no cover - optional dependency
    requests = None

try:
    from pymilvus import connections, Collection, utility
except ImportError:  # pragma: no cover - optional dependency
    connections = Collection = utility = None
import json
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("HybridSearch")

class HybridSearch:
    def __init__(self, neo4j_uri, neo4j_user, neo4j_password, milvus_host, milvus_port, ollama_url):
        # Neo4j connection
        if GraphDatabase is not None:
            try:
                self.driver = GraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_user, neo4j_password)
                )
                logger.info(f"Connected to Neo4j at {neo4j_uri}")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {str(e)}")
                self.driver = None
        else:
            logger.warning("neo4j library not installed; graph features disabled")
            self.driver = None

        # Milvus connection
        if connections is not None:
            try:
                connections.connect(
                    alias="default",
                    host=milvus_host,
                    port=milvus_port
                )
                logger.info(f"Connected to Milvus at {milvus_host}:{milvus_port}")
            except Exception as e:
                logger.error(f"Failed to connect to Milvus: {str(e)}")
        else:
            logger.warning("pymilvus library not installed; vector search disabled")
        
        # Ollama connection for embeddings
        self.ollama_url = ollama_url
        self.model = "nomic-embed-text"

        # Cache for available knowledge bases
        self.kb_cache = {}
        self.refresh_kb_cache()

    def get_timestamp(self):
        """Return an ISO formatted timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def refresh_kb_cache(self):
        """Refresh the cache of available knowledge bases"""
        if GraphDatabase is None or not self.driver:
            logger.warning("Neo4j driver not available for KB cache refresh")
            return
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (d:Document)
                    WITH DISTINCT d.kb_id AS kb_id
                    WHERE kb_id IS NOT NULL
                    RETURN kb_id, count(kb_id) AS doc_count
                """)
                
                self.kb_cache = {record["kb_id"]: record["doc_count"] for record in result}
                logger.info(f"Refreshed KB cache. Found {len(self.kb_cache)} knowledge bases.")
                
        except Exception as e:
            logger.error(f"Error refreshing KB cache: {str(e)}")
            logger.error(traceback.format_exc())
    
    def get_available_knowledge_bases(self):
        """Get list of available knowledge bases"""
        # Refresh cache if empty
        if not self.kb_cache:
            self.refresh_kb_cache()
        
        return list(self.kb_cache.keys())
    
    def get_knowledge_base_info(self, kb_id=None):
        """Get information about knowledge bases"""
        # Refresh cache if empty
        if not self.kb_cache:
            self.refresh_kb_cache()
        
        if kb_id:
            # Return info for specific KB
            if kb_id in self.kb_cache:
                return {kb_id: self.kb_cache[kb_id]}
            return {}
        else:
            # Return info for all KBs
            return self.kb_cache
    
    def hybrid_search(self, query_text, knowledge_base_id, top_k=3):
        """Perform hybrid search using both Neo4j and Milvus"""
        results = []
        
        # Validate knowledge base ID
        if not knowledge_base_id:
            logger.error("No knowledge base ID provided for search")
            return results
        
        # Check if this KB exists in our cache
        if not self.kb_cache or knowledge_base_id not in self.kb_cache:
            self.refresh_kb_cache()
            if knowledge_base_id not in self.kb_cache:
                logger.warning(f"Knowledge base {knowledge_base_id} not found in cache")
                # Continue anyway as it might be a new KB
        
        # Extract key terms from the query for graph search
        query_terms = self._extract_query_terms(query_text)
        
        # Check if query might be about personal information
        is_personal_query = self._is_personal_query(query_text)
        
        # Perform graph-based search if appropriate terms found
        if query_terms or is_personal_query:
            logger.info(f"Performing graph search with terms: {query_terms} for KB: {knowledge_base_id}")
            graph_results = self._graph_search(query_terms, knowledge_base_id, top_k, is_personal_query)
            results.extend(graph_results)
        
        # If not enough results, perform vector search
        if len(results) < top_k:
            logger.info(f"Performing vector search for KB: {knowledge_base_id}")
            vector_results = self._vector_search(query_text, knowledge_base_id, top_k - len(results))
            
            # Merge results, avoiding duplicates
            for vr in vector_results:
                if not any(r.get('title') == vr.get('title') for r in results):
                    results.append(vr)
        
        return results
    
    def _extract_query_terms(self, query_text):
        """Extract key terms from the query text for graph searching"""
        # Extract potential keywords/concepts from the query
        # This is a simple implementation that could be enhanced with NLP
        words = re.findall(r'\b\w+\b', query_text.lower())
        
        # Filter out common stop words
        stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                      'in', 'on', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
                      'into', 'through', 'during', 'before', 'after', 'above', 'below',
                      'to', 'from', 'up', 'down', 'of', 'off', 'over', 'under', 'again',
                      'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
                      'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
                      'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
                      'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don',
                      'should', 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren',
                      'couldn', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'ma',
                     'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won',
                     'wouldn', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'who'}
        
        terms = [word for word in words if word not in stop_words and len(word) > 2]
        
        # Capitalize first letter to match potential topic/concept names
        terms = [term.capitalize() for term in terms]
        
        return terms
    
    def _is_personal_query(self, query_text):
        """Detect if a query is asking for personal information"""
        personal_indicators = [
            r'\b(?:my|your|their|his|her)\b',
            r'\b(?:I|me|myself|we|us|our)\b',
            r'\b(?:personal|private|own|individual|contact|information)\b',
            r'\b(?:family|friend|relative|relationship)\b',
            r'\b(?:appointment|meeting|schedule|calendar|reminder|event)\b',
            r'\b(?:health|medical|medication|condition|symptom)\b',
            r'\b(?:finance|money|budget|payment|transaction)\b',
            r'\b(?:education|school|university|degree|course|grade)\b', 
            r'\b(?:job|work|career|profession|company|employer)\b',
            r'\b(?:home|address|location|place|where)\b',
            r'\b(?:hobby|interest|like|enjoy|prefer)\b',
            r'\b(?:project|task|goal|objective|plan)\b',
            r'\b(?:note|thought|idea|remind)\b',
            r'\b(?:who|what|when|where|how|why)\b.*\b(?:I|me|my)\b'
        ]
        
        for pattern in personal_indicators:
            if re.search(pattern, query_text, re.IGNORECASE):
                return True
        
        return False
    
    def _graph_search(self, query_terms, knowledge_base_id, top_k=3, is_personal_query=False):
        """Search the knowledge graph for relevant information"""
        results = []

        if GraphDatabase is None or not self.driver:
            logger.warning("Graph search not available")
            return results
        
        try:
            with self.driver.session() as session:
                # Regular knowledge graph search (existing functionality)
                if query_terms:
                    # Search for concepts related to query terms
                    concept_query = """
                    MATCH (c:Concept)
                    WHERE c.name IN $query_terms OR c.name CONTAINS $query_text
                    MATCH (d:Document)-[:DEMONSTRATES_CONCEPT]->(c)
                    WHERE d.kb_id = $kb_id
                    RETURN d.title AS title, d.path AS path, 'document' AS source,
                           c.name AS concept, c.description AS concept_description,
                           c.example AS content
                    LIMIT $limit
                    """
                    
                    concept_results = session.run(
                        concept_query,
                        query_terms=query_terms,
                        query_text=" ".join(query_terms),
                        kb_id=knowledge_base_id,
                        limit=top_k
                    )
                    
                    for record in concept_results:
                        results.append(dict(record))
                    
                    # Search for topics related to query terms
                    topic_query = """
                    MATCH (t:Topic)
                    WHERE t.name IN $query_terms OR t.name CONTAINS $query_text
                    MATCH (d:Document)-[:CONTAINS_TOPIC]->(t)
                    WHERE d.kb_id = $kb_id
                    RETURN d.title AS title, d.path AS path, 'document' AS source,
                           t.name AS topic, 'Topic in document' AS content
                    LIMIT $limit
                    """
                    
                    topic_results = session.run(
                        topic_query,
                        query_terms=query_terms,
                        query_text=" ".join(query_terms),
                        kb_id=knowledge_base_id,
                        limit=top_k
                    )
                    
                    for record in topic_results:
                        results.append(dict(record))
                
                # Personal knowledge graph search (new functionality)
                if is_personal_query:
                    # Search for personal entities
                    personal_entity_query = """
                    MATCH (e:PersonalEntity)
                    WHERE (toLower(e.text) CONTAINS toLower($query_text)
                       OR e.type IN $query_terms
                       OR e.category IN $query_terms)
                       AND e.kb_id = $kb_id
                    MATCH (d:Document)-[:MENTIONS_ENTITY]->(e)
                    WHERE d.kb_id = $kb_id
                    RETURN d.title AS title, d.path AS path, 'personal' AS source,
                           e.type AS entity_type, e.category AS entity_category, 
                           e.text AS content
                    LIMIT $limit
                    """
                    
                    entity_results = session.run(
                        personal_entity_query,
                        query_terms=query_terms,
                        query_text=" ".join(query_terms),
                        kb_id=knowledge_base_id,
                        limit=top_k
                    )
                    
                    for record in entity_results:
                        results.append(dict(record))
                    
                    # Search for personal topics
                    personal_topic_query = """
                    MATCH (t:PersonalTopic)
                    WHERE (t.name IN $query_terms OR toLower(t.name) CONTAINS toLower($query_text))
                       AND t.kb_id = $kb_id
                    MATCH (d:Document)-[:CONTAINS_PERSONAL_TOPIC]->(t)
                    WHERE d.kb_id = $kb_id
                    OPTIONAL MATCH (e:PersonalEntity)-[:BELONGS_TO_TOPIC]->(t)
                    WHERE e.kb_id = $kb_id
                    WITH d, t, COLLECT(e.text) AS related_entities
                    RETURN d.title AS title, d.path AS path, 'personal' AS source,
                           t.name AS topic, 
                           CASE WHEN size(related_entities) > 0 
                                THEN 'Related to: ' + reduce(s = '', x IN related_entities | s + x + '; ') 
                                ELSE 'Personal topic in document' 
                           END AS content
                    LIMIT $limit
                    """
                    
                    personal_topic_results = session.run(
                        personal_topic_query,
                        query_terms=query_terms,
                        query_text=" ".join(query_terms),
                        kb_id=knowledge_base_id,
                        limit=top_k
                    )
                    
                    for record in personal_topic_results:
                        results.append(dict(record))
                
                # Limit results to top_k
                if len(results) > top_k:
                    results = results[:top_k]
                
                return results
                
        except Exception as e:
            logger.error(f"Error during graph search: {str(e)}")
            logger.error(traceback.format_exc())
            return []
    
    def _vector_search(self, query_text, knowledge_base_id, top_k=3):
        """Search for similar documents using vector similarity in Milvus"""
        results = []

        if connections is None or Collection is None or utility is None:
            logger.warning("Vector search libraries not available")
            return results

        try:
            # Generate embedding for the query
            query_embedding = self._get_embedding(query_text)
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return results
            
            # Search in Milvus
            collection_name = f"documents_{knowledge_base_id.replace('-', '_')}"
            
            # Check if collection exists
            if not utility.has_collection(collection_name):
                logger.error(f"Collection {collection_name} does not exist in Milvus")
                
                # Try to create collection or initialize it if it doesn't exist
                if self._initialize_vector_collection(knowledge_base_id):
                    logger.info(f"Initialized new collection for KB: {knowledge_base_id}")
                else:
                    logger.error(f"Failed to initialize collection for KB: {knowledge_base_id}")
                    return results
            
            # Load the collection
            collection = Collection(collection_name)
            collection.load()
            
            # Perform the search
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10},
            }
            
            # Check if collection has any entities
            if collection.num_entities == 0:
                logger.warning(f"Collection {collection_name} has no entities")
                collection.release()
                return results
            
            search_results = collection.search(
                data=[query_embedding],
                anns_field="embedding",
                param=search_params,
                limit=top_k,
                output_fields=["title", "path", "content"]
            )
            
            # Process results
            for hits in search_results:
                for hit in hits:
                    result = {
                        "title": hit.entity.get("title"),
                        "path": hit.entity.get("path"),
                        "source": "vector",
                        "content": hit.entity.get("content", "")[:500],  # Truncate long content
                        "score": hit.score
                    }
                    results.append(result)
            
            # Release the collection
            collection.release()
            
            return results
            
        except Exception as e:
            logger.error(f"Error during vector search: {str(e)}")
            logger.error(traceback.format_exc())
            return []
    
    def _initialize_vector_collection(self, knowledge_base_id):
        """Initialize a vector collection for a knowledge base if it doesn't exist"""
        if connections is None or Collection is None or utility is None:
            logger.warning("Vector search libraries not available")
            return False

        try:
            collection_name = f"documents_{knowledge_base_id.replace('-', '_')}"
            
            # Check if collection already exists
            if utility.has_collection(collection_name):
                logger.info(f"Collection {collection_name} already exists")
                return True
            
            # Define collection schema
            from pymilvus import CollectionSchema, FieldSchema, DataType
            
            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="path", dtype=DataType.VARCHAR, max_length=512),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="kb_id", dtype=DataType.VARCHAR, max_length=64),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768)  # Adjust dimension to match model
            ]
            
            schema = CollectionSchema(fields)
            
            # Create collection
            collection = Collection(name=collection_name, schema=schema)
            
            # Create index
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            
            collection.create_index(field_name="embedding", index_params=index_params)
            logger.info(f"Created new collection and index for KB: {knowledge_base_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing vector collection: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def _get_embedding(self, text):
        """Generate a text embedding using Ollama"""
        if requests is None:
            logger.warning("Requests library not available; cannot generate embeddings")
            return None

        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.model, "prompt": text}
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get("embedding", [])
                return embedding
            else:
                logger.error(f"Error from Ollama API: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return None
    
    def get_current_kb_context(self, session_id):
        """Get the current knowledge base context for a session"""
        # This would typically be retrieved from a database or cache
        # For now, we'll use a simple file-based approach
        context_file = f"/tmp/jarvis_kb_context_{session_id}.json"
        
        try:
            if os.path.exists(context_file):
                with open(context_file, 'r') as f:
                    context = json.load(f)
                    return context.get('kb_id')
            return None
        except Exception as e:
            logger.error(f"Error getting KB context: {str(e)}")
            return None
    
    def set_current_kb_context(self, session_id, kb_id):
        """Set the current knowledge base context for a session"""
        context_file = f"/tmp/jarvis_kb_context_{session_id}.json"
        
        try:
            with open(context_file, 'w') as f:
                json.dump({'kb_id': kb_id}, f)
            return True
        except Exception as e:
            logger.error(f"Error setting KB context: {str(e)}")
            return False
    
    def detect_kb_from_query(self, query_text):
        """Try to detect which knowledge base a query is referring to"""
        # Get available KBs
        if not self.kb_cache:
            self.refresh_kb_cache()
        
        # This is a placeholder for more sophisticated KB detection
        # In a real implementation, you might:
        # 1. Use NLP to extract potential KB names from the query
        # 2. Match against known KB names/descriptions
        # 3. Use context from recent queries
        
        # For now, we'll just return None, indicating no specific KB was detected
        return None
    
    def search_across_all_kbs(self, query_text, top_k=3):
        """Search across all knowledge bases"""
        all_results = []
        
        # Get available KBs
        kb_ids = self.get_available_knowledge_bases()
        
        # Search each KB
        for kb_id in kb_ids:
            kb_results = self.hybrid_search(query_text, kb_id, top_k)
            # Add KB ID to results
            for result in kb_results:
                result['kb_id'] = kb_id
            all_results.extend(kb_results)
        
        # Sort by relevance (if score is available)
        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Limit to top_k across all KBs
        return all_results[:top_k]

# For testing standalone
if __name__ == "__main__":
    # Example usage
    searcher = HybridSearch(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="your_password",
        milvus_host="localhost",
        milvus_port="19530",
        ollama_url="http://localhost:11434"
    )
    
    # Get available knowledge bases
    kb_ids = searcher.get_available_knowledge_bases()
    print(f"Available knowledge bases: {kb_ids}")
    
    # Search in a specific knowledge base
    if kb_ids:
        results = searcher.hybrid_search(
            query_text="How do I use argparse in Python?",
            knowledge_base_id=kb_ids[0],
            top_k=3
        )
        
        print(json.dumps(results, indent=2))
    else:
        print("No knowledge bases available")
