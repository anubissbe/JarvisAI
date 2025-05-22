"""
Knowledge base for Jarvis AI Assistant.
Handles information retrieval and verification from various sources.
"""

import logging
import json
import os
import time
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Import ChromaDB
import chromadb
from chromadb.config import Settings

# Import web search functionality
from .web_search import WebSearch
from ..utilities.web_utils import get_domain_from_url

class KnowledgeBase:
    """Knowledge base for the Jarvis AI Assistant.
    
    This class handles:
    1. Retrieving information from various sources
    2. Verifying information using the internet
    3. Storing and indexing verified information
    4. Integration with ChromaDB for vector storage
    """
    
    def __init__(self, knowledge_dir: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize the knowledge base.
        
        Args:
            knowledge_dir: Optional directory path for storing knowledge files.
            config: Optional configuration dictionary.
        """
        self.logger = logging.getLogger("jarvis.knowledge")
        self.config = config or {}
        
        # Set up knowledge storage directory
        self.knowledge_dir = knowledge_dir or os.path.expanduser("~/.jarvis/knowledge")
        os.makedirs(self.knowledge_dir, exist_ok=True)
        
        # Set up cache directory
        cache_dir = os.path.join(self.knowledge_dir, "cache")
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load base knowledge
        self.base_knowledge = self._load_json_file("base_knowledge.json", default={})
        self.verified_facts = self._load_json_file("verified_facts.json", default=[])
        
        # Load domain-specific knowledge bases
        self.domains = {
            "technology": self._load_json_file("domain_technology.json", default={}),
            "science": self._load_json_file("domain_science.json", default={}),
            "humanities": self._load_json_file("domain_humanities.json", default={}),
            "daily": self._load_json_file("domain_daily.json", default={}),
            "local": self._load_json_file("domain_local.json", default={})
        }
        
        # Initialize ChromaDB connection
        self._init_vector_db()
        
        # Initialize web search
        self.web_search = WebSearch(cache_dir=os.path.join(cache_dir, "web_search"), config=self.config)
        
        # Flag to enable/disable web search
        self.enable_web_search = self.config.get("enable_web_search", True)
        
        self.logger.info("Knowledge base initialized.")
    
    def _init_vector_db(self):
        """Initialize connection to ChromaDB for vector storage."""
        # Initialize as None first
        self.chroma_client = None
        self.collection = None
        
        # Get ChromaDB URL from config
        chroma_url = self.config.get("chroma_url", "http://chroma-db:8000")
        
        # Parse the URL more safely
        try:
            import urllib.parse
            parsed_url = urllib.parse.urlparse(chroma_url)
            host = parsed_url.hostname or "localhost"
            port = parsed_url.port or 8000
            
            # Maximum number of retries
            max_retries = 3
            retry_delay = 2  # seconds
            
            for attempt in range(max_retries):
                try:
                    # Try to connect to ChromaDB service
                    self.logger.info(f"Connecting to ChromaDB at {host}:{port} (Attempt {attempt+1}/{max_retries})")
                    self.chroma_client = chromadb.HttpClient(host=host, port=port)
                    
                    # Test the connection with a simple operation
                    self.chroma_client.heartbeat()
                    
                    # Create or get the default collection
                    self.collection = self._get_or_create_collection("jarvis_knowledge")
                    self.logger.info("Successfully connected to ChromaDB vector database")
                    break
                except Exception as e:
                    self.logger.warning(f"Attempt {attempt+1} to connect to ChromaDB failed: {e}")
                    if attempt < max_retries - 1:
                        import time
                        self.logger.info(f"Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 1.5  # Exponential backoff
                    else:
                        self.logger.error(f"Failed to connect to ChromaDB after {max_retries} attempts")
                        self.logger.warning("Falling back to local knowledge only")
        except Exception as e:
            self.logger.error(f"Error parsing ChromaDB URL or setting up connection: {e}")
            self.logger.warning("Falling back to local knowledge only")
    
    def _get_or_create_collection(self, collection_name: str):
        """Get or create a ChromaDB collection.
        
        Args:
            collection_name: The name of the collection.
            
        Returns:
            The ChromaDB collection.
        """
        try:
            # Try to get the collection
            return self.chroma_client.get_collection(collection_name)
        except ValueError:
            # Collection doesn't exist, create it
            return self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "Jarvis AI knowledge base"}
            )
    
    def _load_json_file(self, filename: str, default: Any = None) -> Any:
        """Load data from a JSON file.
        
        Args:
            filename: The name of the file to load.
            default: The default value to return if the file doesn't exist.
            
        Returns:
            The loaded data or the default value.
        """
        filepath = os.path.join(self.knowledge_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading {filename}: {e}")
                return default
        return default
    
    def _save_json_file(self, filename: str, data: Any) -> bool:
        """Save data to a JSON file.
        
        Args:
            filename: The name of the file to save.
            data: The data to save.
            
        Returns:
            True if successful, False otherwise.
        """
        filepath = os.path.join(self.knowledge_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error saving {filename}: {e}")
            return False
    
    def query(self, intent: str, entities: Dict[str, Any], language: str, force_web_search: bool = False) -> Optional[Dict[str, Any]]:
        """Query the knowledge base for information.
        
        Args:
            intent: The identified intent.
            entities: The extracted entities.
            language: The detected language code.
            force_web_search: Whether to force a web search even if other results are found.
            
        Returns:
            A dictionary with the retrieved information, or None if no relevant info is found.
        """
        # Create a query string from intent and entities
        query_text = self._construct_query_text(intent, entities, language)
        
        # Determine if this is likely a time-sensitive query that needs fresh data
        is_time_sensitive = self._is_time_sensitive_query(query_text, intent, entities)
        
        # If it's time-sensitive or web search is forced, go straight to web verification
        if (is_time_sensitive or force_web_search) and self.enable_web_search:
            self.logger.info(f"Performing web search for time-sensitive query: {query_text}")
            verified_info = self.verify_information(query_text, language)
            if verified_info[0]:  # If verified information was found
                return {
                    "content": verified_info[0],
                    "sources": verified_info[1],
                    "verified": True,
                    "from_web": True
                }
        
        # First try to get information from the vector database
        vector_results = self._query_vector_db(query_text, language)
        if vector_results:
            # If not time-sensitive, return vector results
            if not is_time_sensitive:
                return vector_results
            # Otherwise, add a note about potentially outdated information
            vector_results["content"] = (
                "Note: This information may not be current. " + vector_results["content"] 
                if language == "en" else 
                "Opmerking: Deze informatie is mogelijk niet actueel. " + vector_results["content"]
            )
        
        # Determine the appropriate knowledge domain based on intent and entities
        domain = self._determine_domain(intent, entities)
        
        # Try to get information from the domain-specific knowledge
        domain_info = self._query_domain(domain, intent, entities, language)
        if domain_info and not is_time_sensitive:
            return domain_info
        
        # If no domain-specific info is found, try to get it from the base knowledge
        base_info = self._query_base_knowledge(intent, entities, language)
        if base_info and not is_time_sensitive:
            return base_info
        
        # If still nothing or if time-sensitive, try to verify the information online
        if intent == "question" or is_time_sensitive:
            verified_info = self.verify_information(query_text, language)
            if verified_info[0]:  # If verified information was found
                return {
                    "content": verified_info[0],
                    "sources": verified_info[1],
                    "verified": True,
                    "from_web": True
                }
        
        # Return vector results if we have them, even for time-sensitive queries
        if vector_results:
            return vector_results
        
        # Return None if no information is found
        return None
    
    def _is_time_sensitive_query(self, query: str, intent: str, entities: Dict[str, Any]) -> bool:
        """Determine if a query is time-sensitive and needs fresh data.
        
        Args:
            query: The query string.
            intent: The identified intent.
            entities: The extracted entities.
            
        Returns:
            True if the query is time-sensitive, False otherwise.
        """
        # List of keywords that suggest time sensitivity
        time_sensitive_keywords = [
            "news", "current", "latest", "recent", "today", "now", "update",
            "weather", "forecast", "price", "stock", "market", "election",
            "score", "result", "live", "happening", "trending",
            "nieuws", "actueel", "laatste", "recent", "vandaag", "nu", "update",
            "weer", "voorspelling", "prijs", "beurs", "markt", "verkiezing",
            "score", "resultaat", "live", "gebeurt", "trending"
        ]
        
        # Check if any time-sensitive keywords are in the query
        query_lower = query.lower()
        for keyword in time_sensitive_keywords:
            if keyword in query_lower:
                return True
        
        # Check if the query asks about a specific date or time
        date_keywords = ["today", "tomorrow", "yesterday", "this week", "this month", "this year",
                       "vandaag", "morgen", "gisteren", "deze week", "deze maand", "dit jaar"]
        
        for keyword in date_keywords:
            if keyword in query_lower:
                return True
        
        # Check if entities contain date/time information
        for entity_key, entity_value in entities.items():
            if entity_key in ["date", "time", "datetime"]:
                return True
        
        return False
    
    def _query_vector_db(self, query: str, language: str) -> Optional[Dict[str, Any]]:
        """Query the vector database for relevant information.
        
        Args:
            query: The query string.
            language: The language code.
            
        Returns:
            A dictionary with the retrieved information, or None if no relevant info is found.
        """
        if not self.collection:
            return None
        
        try:
            # Filter by language if specified
            where_filter = None
            if language in ["en", "nl"]:
                where_filter = {"language": language}
            
            # Query the vector database
            results = self.collection.query(
                query_texts=[query],
                n_results=5,  # Get more results for better synthesis
                include=["documents", "metadatas", "distances"],
                where=where_filter
            )
            
            if not results["documents"][0]:
                return None
                
            # Process the results
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0]
            
            # Check if the results are relevant (low distance)
            relevance_threshold = 0.7  # Threshold for relevance
            relevant_results = []
            
            for i, distance in enumerate(distances):
                if distance <= relevance_threshold:
                    relevant_results.append({
                        "document": documents[i],
                        "metadata": metadatas[i],
                        "distance": distance
                    })
            
            if not relevant_results:
                return None
            
            # If we have multiple relevant results, synthesize them
            if len(relevant_results) > 1:
                content = self._synthesize_vector_results(relevant_results, query, language)
            else:
                # Just use the top result
                content = relevant_results[0]["document"]
            
            # Collect sources
            sources = []
            for result in relevant_results:
                source = result["metadata"].get("source", "Knowledge Base")
                if source and source not in sources:
                    sources.append(source)
            
            # Add timestamp information if available
            timestamps = [result["metadata"].get("timestamp") for result in relevant_results 
                         if "timestamp" in result["metadata"]]
            
            latest_update = max(timestamps) if timestamps else None
            
            result_data = {
                "content": content,
                "sources": sources,
                "from_vector_db": True
            }
            
            if latest_update:
                result_data["timestamp"] = latest_update
            
            return result_data
            
        except Exception as e:
            self.logger.error(f"Error querying vector database: {e}")
            return None
    
    def _synthesize_vector_results(self, results: List[Dict[str, Any]], query: str, language: str) -> str:
        """Synthesize multiple vector search results into a coherent response.
        
        Args:
            results: List of relevant results.
            query: The original query.
            language: The language code.
            
        Returns:
            A synthesized response string.
        """
        # Simple approach: concatenate results with headers
        synthesized = ""
        
        # Sort results by relevance (lowest distance first)
        sorted_results = sorted(results, key=lambda x: x["distance"])
        
        # First, check if we have results that directly answer the query
        # (those with very low distance)
        highly_relevant = [r for r in sorted_results if r["distance"] < 0.3]
        
        if highly_relevant:
            # Start with the most relevant information
            synthesized = highly_relevant[0]["document"]
            
            # If there are multiple highly relevant results, add complementary info
            if len(highly_relevant) > 1:
                for i, result in enumerate(highly_relevant[1:3]):  # Limit to next 2 results
                    # Add a separator and the additional information
                    if language == "en":
                        synthesized += f"\n\nAdditional information: {result['document']}"
                    else:  # Dutch
                        synthesized += f"\n\nAanvullende informatie: {result['document']}"
            
            return synthesized
        
        # If no highly relevant results, combine the top results
        if language == "en":
            synthesized = "Based on several sources:\n\n"
        else:  # Dutch
            synthesized = "Gebaseerd op verschillende bronnen:\n\n"
        
        # Add the top 3 results
        for i, result in enumerate(sorted_results[:3]):
            # Add a bullet point and the result
            synthesized += f"• {result['document']}\n\n"
        
        return synthesized
    
    def add_to_vector_db(self, text: str, metadata: Dict[str, Any]) -> bool:
        """Add a document to the vector database.
        
        Args:
            text: The document text.
            metadata: The document metadata.
            
        Returns:
            True if successful, False otherwise.
        """
        if not self.collection:
            return False
            
        try:
            # Generate a unique ID
            import uuid
            doc_id = str(uuid.uuid4())
            
            # Add the document to the collection
            self.collection.add(
                documents=[text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Error adding to vector database: {e}")
            return False
    
    def _determine_domain(self, intent: str, entities: Dict[str, Any]) -> str:
        """Determine the appropriate knowledge domain for a query.
        
        Args:
            intent: The identified intent.
            entities: The extracted entities.
            
        Returns:
            The name of the most relevant knowledge domain.
        """
        # In a real implementation, this would use more sophisticated classification
        # Here's a simplified approach based on keywords
        
        # Extract all text from entities for keyword matching
        entity_text = " ".join(str(v) for v in entities.values())
        combined_text = f"{intent} {entity_text}".lower()
        
        # Technology domain keywords
        tech_keywords = ["programming", "code", "software", "hardware", "computer", 
                       "algorithm", "database", "network", "cybersecurity", "ai", 
                       "machine learning", "python", "java", "javascript"]
        
        # Science domain keywords
        science_keywords = ["physics", "chemistry", "biology", "astronomy", "math", 
                          "equation", "scientific", "experiment", "theory", "hypothesis", 
                          "molecule", "atom", "cell", "organism"]
        
        # Humanities domain keywords
        humanities_keywords = ["history", "literature", "philosophy", "art", "music", 
                             "culture", "language", "religion", "politics", "society", 
                             "economics", "psychology", "ethics"]
        
        # Daily tasks domain keywords
        daily_keywords = ["recipe", "cooking", "exercise", "health", "nutrition", 
                        "weather", "schedule", "reminder", "appointment", "task", 
                        "shopping", "travel", "transportation"]
        
        # Local knowledge domain keywords
        local_keywords = ["belgium", "dutch", "flemish", "netherlands", "amsterdam", 
                        "brussels", "antwerp", "rotterdam", "local", "nearby", "event", 
                        "restaurant", "attraction"]
        
        # Count matches for each domain
        domain_scores = {
            "technology": sum(1 for kw in tech_keywords if kw in combined_text),
            "science": sum(1 for kw in science_keywords if kw in combined_text),
            "humanities": sum(1 for kw in humanities_keywords if kw in combined_text),
            "daily": sum(1 for kw in daily_keywords if kw in combined_text),
            "local": sum(1 for kw in local_keywords if kw in combined_text)
        }
        
        # Return the domain with the highest score, defaulting to "daily" if all scores are 0
        max_domain = max(domain_scores.items(), key=lambda x: x[1])
        if max_domain[1] > 0:
            return max_domain[0]
        return "daily"  # Default domain
    
    def _query_domain(self, domain: str, intent: str, entities: Dict[str, Any], 
                     language: str) -> Optional[Dict[str, Any]]:
        """Query a specific knowledge domain.
        
        Args:
            domain: The knowledge domain to query.
            intent: The identified intent.
            entities: The extracted entities.
            language: The detected language code.
            
        Returns:
            A dictionary with the retrieved information, or None if no relevant info is found.
        """
        # In a real implementation, this would use more sophisticated retrieval
        # Like vector similarity search on embeddings
        
        # Get the domain knowledge
        domain_knowledge = self.domains.get(domain, {})
        
        # Construct a query key from intent and entities
        query_key = self._construct_query_key(intent, entities)
        
        # Try to find a direct match in the domain knowledge
        if query_key in domain_knowledge:
            info = domain_knowledge[query_key]
            # Return the content in the appropriate language
            return {
                "content": info.get(language, info.get("en", "")),
                "domain": domain,
                "sources": info.get("sources", [])
            }
        
        # No direct match found
        return None
    
    def _query_base_knowledge(self, intent: str, entities: Dict[str, Any], 
                             language: str) -> Optional[Dict[str, Any]]:
        """Query the base knowledge.
        
        Args:
            intent: The identified intent.
            entities: The extracted entities.
            language: The detected language code.
            
        Returns:
            A dictionary with the retrieved information, or None if no relevant info is found.
        """
        # Similar to _query_domain, but for the base knowledge
        
        # Construct a query key from intent and entities
        query_key = self._construct_query_key(intent, entities)
        
        # Try to find a direct match in the base knowledge
        if query_key in self.base_knowledge:
            info = self.base_knowledge[query_key]
            # Return the content in the appropriate language
            return {
                "content": info.get(language, info.get("en", "")),
                "domain": "base",
                "sources": info.get("sources", [])
            }
        
        # No direct match found
        return None
    
    def _construct_query_key(self, intent: str, entities: Dict[str, Any]) -> str:
        """Construct a query key from intent and entities.
        
        Args:
            intent: The identified intent.
            entities: The extracted entities.
            
        Returns:
            A string key for knowledge lookup.
        """
        # In a real implementation, this would be more sophisticated
        # Here's a simple approach
        
        # Start with the intent
        key_parts = [intent]
        
        # Add entities, sorted by key for consistency
        for entity_key, entity_value in sorted(entities.items()):
            key_parts.append(f"{entity_key}:{entity_value}")
        
        # Join with a separator
        return "|".join(key_parts)
    
    def _construct_query_text(self, intent: str, entities: Dict[str, Any], language: str) -> str:
        """Construct a natural language query text from intent and entities.
        
        Args:
            intent: The identified intent.
            entities: The extracted entities.
            language: The detected language code.
            
        Returns:
            A natural language query string.
        """
        # In a real implementation, this would be more sophisticated
        
        # Basic templates for question intents
        if intent == "question":
            if language == "en":
                # English question template
                if not entities:
                    return "general information"
                
                entity_parts = []
                for entity_key, entity_value in entities.items():
                    entity_parts.append(f"{entity_key} {entity_value}")
                
                return " ".join(entity_parts)
            else:  # Dutch
                # Dutch question template
                if not entities:
                    return "algemene informatie"
                
                entity_parts = []
                for entity_key, entity_value in entities.items():
                    entity_parts.append(f"{entity_key} {entity_value}")
                
                return " ".join(entity_parts)
        
        # For other intents, just combine the intent and entities
        entity_str = " ".join(f"{k} {v}" for k, v in entities.items())
        return f"{intent} {entity_str}"
    
    def verify_information(self, query: str, language: str) -> Tuple[str, List[str]]:
        """Verify information using internet sources.
        
        Args:
            query: The information to verify.
            language: The language code (en/nl).
            
        Returns:
            A tuple containing the verified information and source citations.
        """
        self.logger.info(f"Verifying information: {query}")
        
        # Check if this information has been verified before
        for fact in self.verified_facts:
            if query.lower() in fact.get("query", "").lower():
                # Check if the fact is still fresh (less than 24 hours old)
                try:
                    fact_time = datetime.fromisoformat(fact.get("timestamp", "2000-01-01T00:00:00"))
                    current_time = datetime.now()
                    fact_age = (current_time - fact_time).total_seconds()
                    
                    # If fact is less than 24 hours old, use it
                    if fact_age < 86400:  # 24 hours in seconds
                        self.logger.info(f"Using cached verified fact for: {query}")
                        return fact.get("content", ""), fact.get("sources", [])
                except Exception:
                    # If there's an error parsing the timestamp, ignore this check
                    pass
        
        # If web search is disabled, return a generic response
        if not self.enable_web_search:
            if language == "en":
                return f"I don't have up-to-date information about {query}.", []
            else:  # Dutch
                return f"Ik heb geen actuele informatie over {query}.", []
        
        # Use web search to find information
        verified_info = ""
        sources = []
        
        try:
            # Search the web
            search_results = self.web_search.search(query, language=language)
            
            if not search_results:
                # No results found
                if language == "en":
                    return f"I couldn't find verified information about {query}.", []
                else:  # Dutch
                    return f"Ik kon geen geverifieerde informatie vinden over {query}.", []
            
            # Process the top 2-3 results to extract relevant information
            processed_results = []
            
            for i, result in enumerate(search_results[:3]):
                # Skip if no URL
                if not result.get("url"):
                    continue
                
                # Get content from the webpage
                try:
                    content, metadata = self.web_search.get_webpage_content(result["url"])
                    
                    # Skip if content retrieval failed
                    if not metadata.get("success"):
                        continue
                    
                    # Extract a relevant excerpt (first 1000 characters for simplicity)
                    excerpt = content[:1000].strip()
                    
                    # Add to processed results
                    processed_results.append({
                        "title": metadata.get("title", result.get("title", "")),
                        "url": result["url"],
                        "domain": self.web_search.get_domain(result["url"]),
                        "excerpt": excerpt
                    })
                    
                    # Add to sources
                    sources.append(result["url"])
                    
                except Exception as e:
                    self.logger.warning(f"Error processing search result: {e}")
                    continue
            
            # Combine information from processed results
            if processed_results:
                # Simple approach: use the first result's excerpt
                verified_info = processed_results[0]["excerpt"]
                
                # Add a prefix indicating the source
                domain = get_domain_from_url(processed_results[0]["url"])
                if language == "en":
                    verified_info = f"According to {domain}, {verified_info}"
                else:  # Dutch
                    verified_info = f"Volgens {domain}, {verified_info}"
            else:
                # No processed results
                if language == "en":
                    verified_info = f"I found search results for {query}, but couldn't extract useful information."
                else:  # Dutch
                    verified_info = f"Ik vond zoekresultaten voor {query}, maar kon geen bruikbare informatie extraheren."
                
        except Exception as e:
            self.logger.error(f"Error in web search verification: {e}")
            # Fallback response
            if language == "en":
                verified_info = f"I encountered an error while trying to verify information about {query}."
            else:  # Dutch
                verified_info = f"Ik ben een fout tegengekomen bij het verifiëren van informatie over {query}."
        
        # Store the verified information for future use
        if verified_info and sources:
            new_fact = {
                "query": query,
                "content": verified_info,
                "sources": sources,
                "language": language,
                "timestamp": datetime.now().isoformat()
            }
            self.verified_facts.append(new_fact)
            self._save_json_file("verified_facts.json", self.verified_facts)
            
            # Also add to vector database for future retrieval
            if self.collection:
                self.add_to_vector_db(
                    text=verified_info,
                    metadata={
                        "query": query,
                        "language": language,
                        "source": ", ".join(sources),
                        "timestamp": datetime.now().isoformat()
                    }
                )
        
        return verified_info, sources
    
    def add_to_knowledge_base(self, domain: str, query_key: str, 
                              content: Dict[str, str], sources: List[str]) -> bool:
        """Add verified information to the knowledge base.
        
        Args:
            domain: The knowledge domain.
            query_key: The query key for lookup.
            content: A dictionary mapping language codes to content.
            sources: A list of source URLs.
            
        Returns:
            True if successful, False otherwise.
        """
        # Validate input
        if domain not in self.domains:
            self.logger.error(f"Invalid domain: {domain}")
            return False
        
        if not content:
            self.logger.error("Content cannot be empty")
            return False
        
        # Add the information to the domain
        self.domains[domain][query_key] = {
            **content,
            "sources": sources,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to vector database for each language
        for lang, text in content.items():
            if self.collection and lang in ["en", "nl"]:
                self.add_to_vector_db(
                    text=text,
                    metadata={
                        "domain": domain,
                        "query_key": query_key,
                        "language": lang,
                        "source": ", ".join(sources),
                        "timestamp": datetime.now().isoformat()
                    }
                )
        
        # Save the updated domain knowledge
        return self._save_json_file(f"domain_{domain}.json", self.domains[domain])