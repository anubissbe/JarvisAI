import aiohttp
import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

from .base import BaseIntegration

logger = logging.getLogger(__name__)

class WebIntegration(BaseIntegration):
    async def execute(self, action: str, parameters: Dict[str, Any], api_key: Optional[str] = None) -> Any:
        """Execute a web action"""
        action = action.lower()
        
        if action == "search":
            return await self._search(parameters.get("query", ""))
        elif action == "fetch_url":
            return await self._fetch_url(parameters.get("url", ""))
        else:
            raise ValueError(f"Unknown web action: {action}")
    
    async def _search(self, query: str) -> Dict[str, Any]:
        """Perform a web search"""
        # This is a simplified implementation
        # In a real application, you would use a search API like Google or Bing
        search_url = f"https://www.google.com/search?q={query}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        # Parse the HTML to extract search results
                        # This is a simplified example
                        soup = BeautifulSoup(html, 'html.parser')
                        results = []
                        
                        # Extract search results (this is a simplified example)
                        for result in soup.select('.g'):
                            title_elem = result.select_one('.LC20lb')
                            link_elem = result.select_one('.yuRUbf a')
                            snippet_elem = result.select_one('.VwiC3b')
                            
                            if title_elem and link_elem:
                                title = title_elem.get_text()
                                link = link_elem.get('href')
                                snippet = snippet_elem.get_text() if snippet_elem else ""
                                
                                results.append({
                                    "title": title,
                                    "link": link,
                                    "snippet": snippet
                                })
                        
                        return {
                            "query": query,
                            "results": results[:5]  # Return top 5 results
                        }
                    else:
                        return {"error": f"Failed to search: HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Error during web search: {str(e)}")
            return {"error": f"Search failed: {str(e)}"}
    
    async def _fetch_url(self, url: str) -> Dict[str, Any]:
        """Fetch content from a URL"""
        try: 
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Parse the HTML
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract title and main content
                        title = soup.title.string if soup.title else ""
                        
                        # Try to extract main content (simplified)
                        main_content = ""
                        for p in soup.find_all('p'):
                            main_content += p.get_text() + "\n"
                        
                        return {
                            "url": url,
                            "title": title,
                            "content": main_content[:1000]  # Limit content length
                        }
                    else:
                        return {"error": f"Failed to fetch URL: HTTP {response.status}"}
        except Exception as e:
            logger.error(f"Error fetching URL: {str(e)}")
            return {"error": f"URL fetch failed: {str(e)}"}