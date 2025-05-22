"""
Web utilities for Jarvis AI Assistant.
This module provides utility functions for web scraping and URL handling.
"""

import re
import logging
import requests
from typing import Optional, Tuple, List, Dict, Any
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# Set up logging
logger = logging.getLogger("jarvis.utilities.web")

# Default user agent for requests
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"


def is_valid_url(url: str) -> bool:
    """Check if a URL is valid.
    
    Args:
        url: The URL to check.
        
    Returns:
        True if the URL is valid, False otherwise.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception as e:
        logger.error(f"Error validating URL {url}: {e}")
        return False


def get_webpage_title(url: str, user_agent: Optional[str] = None) -> Optional[str]:
    """Get the title of a webpage.
    
    Args:
        url: The URL of the webpage.
        user_agent: Optional user agent string for the request.
        
    Returns:
        The title of the webpage, or None if it couldn't be retrieved.
    """
    if not is_valid_url(url):
        logger.error(f"Invalid URL: {url}")
        return None
    
    headers = {"User-Agent": user_agent or DEFAULT_USER_AGENT}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('title')
        
        if title_tag:
            return title_tag.get_text().strip()
        return None
    
    except Exception as e:
        logger.error(f"Error getting webpage title: {e}")
        return None


def extract_main_content(html_content: str, selector: Optional[str] = None) -> str:
    """Extract the main content from an HTML page.
    
    Args:
        html_content: The HTML content to process.
        selector: Optional CSS selector to target the main content.
        
    Returns:
        The extracted main content as plain text.
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script, style, header, footer, and nav elements
        for element in soup(['script', 'style', 'header', 'footer', 'nav', 'aside', 'iframe', 'noscript']):
            element.extract()
        
        # Common content selectors by priority
        content_selectors = [
            'main', 
            'article', 
            '#content', 
            '.content', 
            '#main', 
            '.main', 
            '.post', 
            '.entry',
            '.article',
            '.blog-post',
            '.post-content',
            '[role="main"]'
        ]
        
        # If a specific selector is provided, use it first
        if selector:
            content_selectors.insert(0, selector)
        
        # Try each selector in order
        for css_selector in content_selectors:
            if isinstance(css_selector, str) and css_selector.startswith(('#', '.')):
                # It's a CSS selector
                elements = soup.select(css_selector)
            else:
                # It's a tag name or attribute selector
                elements = soup.find_all(css_selector)
            
            if elements:
                # Found content with this selector
                content_html = ' '.join(str(element) for element in elements)
                content_soup = BeautifulSoup(content_html, 'html.parser')
                
                # Extract text
                text = content_soup.get_text(separator=' ', strip=True)
                if len(text) > 100:  # Ensure we got meaningful content
                    break
        else:
            # If no selector matched with substantial content, use the body
            body = soup.find('body')
            text = body.get_text(separator=' ', strip=True) if body else soup.get_text(separator=' ', strip=True)
        
        # Clean up the text
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Split into paragraphs
        paragraphs = re.split(r'\n{2,}', text)
        cleaned_paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        # Join paragraphs with proper spacing
        return '\n\n'.join(cleaned_paragraphs)
    
    except Exception as e:
        logger.error(f"Error extracting main content: {e}")
        return ""


def extract_metadata(html_content: str, url: str) -> Dict[str, Any]:
    """Extract metadata from an HTML page.
    
    Args:
        html_content: The HTML content to process.
        url: The URL of the page.
        
    Returns:
        A dictionary containing the extracted metadata.
    """
    metadata = {
        "url": url,
        "title": "",
        "description": "",
        "keywords": [],
        "author": "",
        "publish_date": "",
        "image": ""
    }
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata["title"] = title_tag.get_text().strip()
        
        # Extract meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            # Description
            if tag.get('name') == 'description' or tag.get('property') == 'og:description':
                metadata["description"] = tag.get('content', '').strip()
            
            # Keywords
            elif tag.get('name') == 'keywords':
                keywords = tag.get('content', '')
                metadata["keywords"] = [k.strip() for k in keywords.split(',') if k.strip()]
            
            # Author
            elif tag.get('name') == 'author':
                metadata["author"] = tag.get('content', '').strip()
            
            # Publication date
            elif tag.get('name') == 'article:published_time' or tag.get('property') == 'article:published_time':
                metadata["publish_date"] = tag.get('content', '').strip()
            
            # Image
            elif tag.get('property') == 'og:image':
                image_url = tag.get('content', '')
                if image_url and not is_valid_url(image_url):
                    # Convert relative URL to absolute
                    image_url = urljoin(url, image_url)
                metadata["image"] = image_url
        
        return metadata
    
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        return metadata


def sanitize_url(url: str) -> str:
    """Sanitize a URL by removing tracking parameters and fragments.
    
    Args:
        url: The URL to sanitize.
        
    Returns:
        The sanitized URL.
    """
    try:
        # Parse the URL
        parsed = urlparse(url)
        
        # List of tracking parameters to remove
        tracking_params = [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'ocid', 'ncid', 'ref', 'source', 'mc_cid', 'mc_eid'
        ]
        
        # Get the query parameters
        if parsed.query:
            params = [param.split('=') for param in parsed.query.split('&')]
            # Filter out tracking parameters
            filtered_params = [f"{k}={v}" for k, v in params if k.lower() not in tracking_params]
            # Reconstruct the query string
            query = '&'.join(filtered_params)
        else:
            query = ''
        
        # Reconstruct the URL without fragment and with filtered query
        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if query:
            clean_url += f"?{query}"
        
        return clean_url
    
    except Exception as e:
        logger.error(f"Error sanitizing URL {url}: {e}")
        return url


def get_domain_from_url(url: str) -> str:
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
    except Exception as e:
        logger.error(f"Error extracting domain from URL {url}: {e}")
        return ""


def detect_content_language(text: str) -> str:
    """Detect the language of text content.
    
    Args:
        text: The text to analyze.
        
    Returns:
        The language code ('en' for English, 'nl' for Dutch, etc.).
    """
    try:
        from langdetect import detect
        return detect(text)
    except:
        # Simple fallback - check if Dutch common words appear more than English
        dutch_words = ["de", "het", "een", "in", "van", "is", "op", "te", "en", "dat", "ik", "je", "niet"]
        english_words = ["the", "and", "is", "in", "to", "of", "a", "for", "that", "you", "it", "not", "on"]
        
        text_lower = text.lower()
        dutch_count = sum(1 for word in dutch_words if f" {word} " in f" {text_lower} ")
        english_count = sum(1 for word in english_words if f" {word} " in f" {text_lower} ")
        
        return "nl" if dutch_count > english_count else "en"


def extract_links(html_content: str, base_url: str) -> List[Dict[str, str]]:
    """Extract links from an HTML page.
    
    Args:
        html_content: The HTML content to process.
        base_url: The base URL for resolving relative links.
        
    Returns:
        A list of dictionaries containing link URL and text.
    """
    links = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Skip empty links, javascript, and mailto links
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:')):
                continue
            
            # Resolve relative URLs
            if not is_valid_url(href):
                href = urljoin(base_url, href)
            
            # Get link text
            text = link.get_text().strip()
            
            # Add to list of links
            links.append({
                "url": href,
                "text": text
            })
        
        return links
    
    except Exception as e:
        logger.error(f"Error extracting links: {e}")
        return links