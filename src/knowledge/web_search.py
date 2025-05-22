"""
Web search module for Jarvis AI Assistant.
This module handles searching the web for up-to-date information.
"""

import logging
import json
import os
import time
import re
import requests
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse

# Import web utilities
from ..utilities.web_utils import (
    is_valid_url, 
    extract_main_content, 
    get_webpage_title, 
    extract_metadata,
    sanitize_url,
    get_domain_from_url
)


class WebSearch:
    """Web search capability for Jarvis AI Assistant.
    
    This class handles:
    1. Searching the web for information
    2. Extracting relevant content from search results
    3. Caching results to minimize redundant requests
    4. Providing structured search results for knowledge augmentation
    """
    
    def __init__(self, cache_dir: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize the web search module.
        
        Args:
            cache_dir: Optional directory path for caching search results.
            config: Optional configuration dictionary.
        """
        self.logger = logging.getLogger("jarvis.web_search")
        self.config = config or {}
        
        # Set up cache directory
        self.cache_dir = cache_dir or os.path.expanduser("~/.jarvis/cache/web_search")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Default cache expiration time (2 hours in seconds)
        self.cache_expiration = self.config.get("web_search_cache_expiration", 7200)
        
        # Maximum search results to return
        self.max_results = self.config.get("web_search_max_results", 5)
        
        # User-agent for requests
        self.user_agent = self.config.get("web_search_user_agent", 
                                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Search engines and their base URLs
        self.search_engines = {
            "duckduckgo": "https://html.duckduckgo.com/html/?q=",
            "brave": "https://search.brave.com/search?q="
        }
        
        # Default search engine
        self.default_engine = self.config.get("web_search_default_engine", "duckduckgo")
        
        self.logger.info("Web search module initialized")
    
    def search(self, query: str, language: str = "en", 
              engine: Optional[str] = None, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search the web for information.
        
        Args:
            query: The search query.
            language: The language code (en/nl).
            engine: Optional search engine to use.
            max_results: Optional maximum number of results to return.
            
        Returns:
            A list of search result dictionaries.
        """
        # Use specified parameters or fall back to defaults
        engine = engine or self.default_engine
        max_results = max_results or self.max_results
        
        # Check if we have cached results
        cached_results = self._get_cached_results(query, language, engine)
        if cached_results:
            self.logger.info(f"Using cached results for query: {query}")
            return cached_results[:max_results]
        
        # No cached results, perform the search
        self.logger.info(f"Searching web for: {query} (engine: {engine}, language: {language})")
        
        # Add language constraint to the query if specified
        if language == "nl":
            query = f"{query} site:.nl OR site:.be"
        
        # Encode the query for URL
        encoded_query = quote_plus(query)
        
        # Get the search engine URL
        search_url = self.search_engines.get(engine)
        if not search_url:
            self.logger.warning(f"Unknown search engine: {engine}, falling back to {self.default_engine}")
            search_url = self.search_engines[self.default_engine]
        
        # Complete search URL
        url = f"{search_url}{encoded_query}"
        
        try:
            # Make the request
            headers = {
                "User-Agent": self.user_agent,
                "Accept-Language": "en-US,en;q=0.9" if language == "en" else "nl-NL,nl;q=0.9"
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parse the results based on the engine
                if engine == "duckduckgo":
                    results = self._parse_duckduckgo_results(response.text)
                elif engine == "brave":
                    results = self._parse_brave_results(response.text)
                else:
                    results = []
                
                # Cache the results
                self._cache_results(query, language, engine, results)
                
                # Return limited number of results
                return results[:max_results]
            else:
                self.logger.error(f"Search request failed with status code {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error during web search: {e}")
            return []
    
    def _parse_duckduckgo_results(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse search results from DuckDuckGo.
        
        Args:
            html_content: The HTML content of the search results page.
            
        Returns:
            A list of search result dictionaries.
        """
        results = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all result elements
            result_elements = soup.select('.result')
            
            for element in result_elements:
                try:
                    # Extract title
                    title_element = element.select_one('.result__title')
                    title = title_element.get_text().strip() if title_element else "No title"
                    
                    # Extract URL
                    url_element = element.select_one('.result__url')
                    url = url_element.get_text().strip() if url_element else ""
                    
                    # Fix URL if needed
                    if url and not url.startswith(('http://', 'https://')):
                        url = f"https://{url}"
                    
                    # Extract snippet
                    snippet_element = element.select_one('.result__snippet')
                    snippet = snippet_element.get_text().strip() if snippet_element else "No description"
                    
                    # Validate URL before adding
                    if url and is_valid_url(url):
                        # Sanitize the URL
                        clean_url = sanitize_url(url)
                        
                        # Create result dictionary
                        result = {
                            "title": title,
                            "url": clean_url,
                            "snippet": snippet,
                            "source": "DuckDuckGo",
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        results.append(result)
                except Exception as e:
                    self.logger.warning(f"Error parsing a DuckDuckGo result: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error parsing DuckDuckGo results: {e}")
        
        return results
    
    def _parse_brave_results(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse search results from Brave Search.
        
        Args:
            html_content: The HTML content of the search results page.
            
        Returns:
            A list of search result dictionaries.
        """
        results = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all result elements
            result_elements = soup.select('.snippet')
            
            for element in result_elements:
                try:
                    # Extract title
                    title_element = element.select_one('.snippet-title')
                    title = title_element.get_text().strip() if title_element else "No title"
                    
                    # Extract URL
                    url_element = element.select_one('a.h-url')
                    url = url_element['href'] if url_element and 'href' in url_element.attrs else ""
                    
                    # Extract snippet
                    snippet_element = element.select_one('.snippet-description')
                    snippet = snippet_element.get_text().strip() if snippet_element else "No description"
                    
                    # Create result dictionary
                    result = {
                        "title": title,
                        "url": url,
                        "snippet": snippet,
                        "source": "Brave Search",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    results.append(result)
                except Exception as e:
                    self.logger.warning(f"Error parsing a Brave Search result: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error parsing Brave Search results: {e}")
        
        return results
    
    def _get_cached_results(self, query: str, language: str, engine: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached search results if available and not expired.
        
        Args:
            query: The search query.
            language: The language code.
            engine: The search engine used.
            
        Returns:
            A list of search result dictionaries or None if no valid cache exists.
        """
        # Create a unique cache key
        cache_key = self._create_cache_key(query, language, engine)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        # Check if cache file exists
        if not os.path.exists(cache_file):
            return None
        
        try:
            # Load the cache file
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # Check if cache has expired
            cache_time = datetime.fromisoformat(cache_data.get("timestamp", "2000-01-01T00:00:00"))
            current_time = datetime.now()
            
            # Calculate seconds since cache
            cache_age = (current_time - cache_time).total_seconds()
            
            if cache_age > self.cache_expiration:
                self.logger.debug(f"Cache expired for query: {query}")
                return None
            
            # Return the cached results
            return cache_data.get("results", [])
            
        except Exception as e:
            self.logger.warning(f"Error reading cache file: {e}")
            return None
    
    def _cache_results(self, query: str, language: str, engine: str, results: List[Dict[str, Any]]) -> None:
        """Cache search results for future use.
        
        Args:
            query: The search query.
            language: The language code.
            engine: The search engine used.
            results: The search results to cache.
        """
        # Create a unique cache key
        cache_key = self._create_cache_key(query, language, engine)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            # Create cache data structure
            cache_data = {
                "query": query,
                "language": language,
                "engine": engine,
                "timestamp": datetime.now().isoformat(),
                "results": results
            }
            
            # Write to cache file
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
                
            self.logger.debug(f"Cached results for query: {query}")
            
        except Exception as e:
            self.logger.warning(f"Error writing cache file: {e}")
    
    def _create_cache_key(self, query: str, language: str, engine: str) -> str:
        """Create a unique cache key for a search query.
        
        Args:
            query: The search query.
            language: The language code.
            engine: The search engine used.
            
        Returns:
            A string key for the cache file.
        """
        # Normalize the query
        normalized_query = query.lower().strip()
        
        # Replace non-alphanumeric characters with underscores
        safe_query = re.sub(r'[^a-z0-9]+', '_', normalized_query)
        
        # Truncate if too long
        if len(safe_query) > 100:
            safe_query = safe_query[:100]
        
        # Combine with language and engine
        return f"{safe_query}_{language}_{engine}"
    
    def get_webpage_content(self, url: str) -> Tuple[str, Dict[str, Any]]:
        """Get the content of a webpage.
        
        Args:
            url: The URL of the webpage.
            
        Returns:
            A tuple containing the extracted text content and metadata.
        """
        metadata = {
            "url": url,
            "title": "",
            "timestamp": datetime.now().isoformat(),
            "success": False
        }
        
        try:
            # Make the request
            headers = {"User-Agent": self.user_agent}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Parse the HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract title
                title_tag = soup.find('title')
                if title_tag:
                    metadata["title"] = title_tag.get_text().strip()
                
                # Extract content
                # Remove script and style elements
                for script in soup(["script", "style", "header", "footer", "nav"]):
                    script.extract()
                
                # Get text
                text = soup.get_text()
                
                # Break into lines and remove leading and trailing space
                lines = (line.strip() for line in text.splitlines())
                
                # Break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                
                # Drop blank lines
                content = '\n'.join(chunk for chunk in chunks if chunk)
                
                metadata["success"] = True
                
                return content, metadata
            else:
                self.logger.warning(f"Failed to fetch webpage: {url} - Status code: {response.status_code}")
                return f"Failed to fetch content: HTTP {response.status_code}", metadata
                
        except Exception as e:
            self.logger.error(f"Error fetching webpage content: {e}")
            return f"Error fetching content: {str(e)}", metadata
    
    def get_domain(self, url: str) -> str:
        """Extract the domain from a URL.
        
        Args:
            url: The URL to process.
            
        Returns:
            The domain name.
        """
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # Remove www. prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]
                
            return domain
        except Exception:
            return url