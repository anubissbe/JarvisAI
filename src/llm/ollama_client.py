"""
Ollama LLM client for Jarvis AI Assistant.
This module handles interactions with the Ollama API.
"""

import json
import logging
import requests
import time
from typing import Dict, List, Any, Optional, Union, Tuple


class OllamaClient:
    """Client for interacting with the Ollama API.
    
    This class handles:
    1. Sending requests to the Ollama API
    2. Processing responses
    3. Managing conversation context
    4. Error handling and retries
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "jarvis"):
        """Initialize the Ollama client.
        
        Args:
            base_url: The base URL of the Ollama API.
            model: The name of the model to use.
        """
        self.logger = logging.getLogger("jarvis.llm")
        self.base_url = base_url
        self.model = model
        self.api_url = f"{base_url}/api"
        self.generate_url = f"{self.api_url}/generate"
        self.chat_url = f"{self.api_url}/chat"
        
        # Test connection to Ollama
        self._test_connection()
    
    def _test_connection(self) -> bool:
        """Test the connection to the Ollama API.
        
        Returns:
            True if the connection is successful, False otherwise.
        """
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Try to ping the Ollama API
                response = requests.get(f"{self.api_url}/health", timeout=5)
                if response.status_code == 200:
                    self.logger.info(f"Successfully connected to Ollama API at {self.base_url}")
                    return True
                
                self.logger.warning(f"Ollama API responded with status code {response.status_code} (Attempt {attempt+1}/{max_retries})")
                
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Connection refused to Ollama API at {self.base_url} (Attempt {attempt+1}/{max_retries})")
            except requests.exceptions.Timeout:
                self.logger.warning(f"Connection timeout to Ollama API at {self.base_url} (Attempt {attempt+1}/{max_retries})")
            except Exception as e:
                self.logger.error(f"Failed to connect to Ollama API: {e} (Attempt {attempt+1}/{max_retries})")
            
            # Retry with exponential backoff if this is not the last attempt
            if attempt < max_retries - 1:
                retry_seconds = retry_delay * (2 ** attempt)  # Exponential backoff
                self.logger.info(f"Retrying connection in {retry_seconds} seconds...")
                time.sleep(retry_seconds)
            
        self.logger.error(f"Failed to connect to Ollama API after {max_retries} attempts")
        return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                max_tokens: int = 2048, temperature: float = 0.7) -> Tuple[str, Dict[str, Any]]:
        """Generate a response from the model.
        
        Args:
            prompt: The user prompt.
            system_prompt: Optional system prompt to guide the model.
            max_tokens: Maximum number of tokens to generate.
            temperature: Temperature for sampling (0.0 to 1.0).
            
        Returns:
            A tuple containing the generated text and metadata.
        """
        # Prepare the request payload
        payload = {
            "model": self.model,
            "prompt": prompt,
            "raw": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        # Maximum number of retries
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Send the request to the Ollama API
                self.logger.debug(f"Sending generate request to Ollama (Attempt {attempt+1}/{max_retries})")
                response = requests.post(self.generate_url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    # Parse the response
                    response_data = response.json()
                    generated_text = response_data.get("response", "")
                    
                    # Extract metadata
                    metadata = {
                        "model": response_data.get("model", self.model),
                        "total_duration": response_data.get("total_duration", 0),
                        "prompt_eval_count": response_data.get("prompt_eval_count", 0),
                        "eval_count": response_data.get("eval_count", 0),
                    }
                    
                    return generated_text, metadata
                else:
                    self.logger.warning(
                        f"Ollama API responded with status code {response.status_code}: {response.text} "
                        f"(Attempt {attempt+1}/{max_retries}, prompt: '{prompt[:50]}...')"
                    )
            except requests.exceptions.ConnectionError as e:
                self.logger.error(
                    f"Connection error during generate request (Attempt {attempt+1}/{max_retries}): {e}"
                )
            except requests.exceptions.Timeout as e:
                self.logger.error(
                    f"Timeout during generate request (Attempt {attempt+1}/{max_retries}): {e}"
                )
            except Exception as e:
                self.logger.error(
                    f"Unexpected error during generate request (Attempt {attempt+1}/{max_retries}): {e}"
                )
            
            # Retry with exponential backoff
            if attempt < max_retries - 1:
                retry_delay *= 1.5  # Exponential backoff
                self.logger.info(f"Retrying in {retry_delay:.1f} seconds...")
                time.sleep(retry_delay)
        
        # If all retries failed, return an error message
        error_msg = "I'm sorry, I encountered an issue connecting to my reasoning engine. Please try again later."
        return error_msg, {"error": "Failed to connect to Ollama API after multiple attempts"}
    
    def chat(self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None,
            temperature: float = 0.7) -> Tuple[str, Dict[str, Any]]:
        """Send a chat request to the model.
        
        Args:
            messages: List of message dictionaries with "role" and "content" keys.
            system_prompt: Optional system prompt to guide the model.
            temperature: Temperature for sampling (0.0 to 1.0).
            
        Returns:
            A tuple containing the generated response and metadata.
        """
        # Prepare the request payload
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        # Maximum number of retries
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Send the request to the Ollama API
                self.logger.debug(f"Sending chat request to Ollama (Attempt {attempt+1}/{max_retries})")
                response = requests.post(self.chat_url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    # Parse the response
                    response_data = response.json()
                    
                    # Extract the assistant's response
                    message = response_data.get("message", {})
                    content = message.get("content", "")
                    
                    # Extract metadata
                    metadata = {
                        "model": response_data.get("model", self.model),
                        "total_duration": response_data.get("total_duration", 0),
                        "prompt_eval_count": response_data.get("prompt_eval_count", 0),
                        "eval_count": response_data.get("eval_count", 0),
                    }
                    
                    return content, metadata
                else:
                    self.logger.warning(f"Ollama API responded with status code {response.status_code}: {response.text}")
            except Exception as e:
                self.logger.error(f"Error during chat request (Attempt {attempt+1}): {e}")
            
            # Retry with exponential backoff
            if attempt < max_retries - 1:
                retry_delay *= 1.5  # Exponential backoff
                self.logger.info(f"Retrying in {retry_delay:.1f} seconds...")
                time.sleep(retry_delay)
        
        # If all retries failed, return an error message
        error_msg = "I'm sorry, I encountered an issue connecting to my reasoning engine. Please try again later."
        return error_msg, {"error": "Failed to connect to Ollama API after multiple attempts"}
    
    def get_available_models(self) -> List[str]:
        """Get a list of available models from the Ollama API.
        
        Returns:
            A list of model names.
        """
        try:
            # Send a request to the Ollama API to list models
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            
            if response.status_code == 200:
                models_data = response.json()
                models = [model.get("name", "") for model in models_data.get("models", [])]
                return models
            else:
                self.logger.warning(f"Failed to get models: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            self.logger.error(f"Error getting available models: {e}")
            return []
    
    def format_chat_history(self, conversation: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format conversation history for the Ollama chat API.
        
        Args:
            conversation: List of interaction dictionaries from memory manager.
            
        Returns:
            A list of message dictionaries suitable for the Ollama chat API.
        """
        formatted_messages = []
        
        for interaction in conversation:
            # Add user message
            formatted_messages.append({
                "role": "user",
                "content": interaction.get("user_input", "")
            })
            
            # Add assistant message
            formatted_messages.append({
                "role": "assistant",
                "content": interaction.get("response", "")
            })
        
        return formatted_messages