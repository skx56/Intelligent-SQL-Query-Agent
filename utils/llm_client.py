"""
LLM Client for Ollama integration
"""

import json
import re
from typing import Any, Dict, List, Optional
import requests
from rich.console import Console

from config.config import OLLAMA_BASE_URL, OLLAMA_MODEL, SQL_TEMPERATURE

console = Console()


class OllamaClient:
    """
    Client for interacting with Ollama local LLM.
    """
    
    def __init__(
        self, 
        base_url: str = OLLAMA_BASE_URL,
        model: str = OLLAMA_MODEL
    ):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama server URL
            model: Model name to use
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._verify_connection()
    
    def _verify_connection(self):
        """Verify Ollama server is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                console.print("[yellow]Warning: Ollama server may not be running properly[/yellow]")
        except requests.exceptions.ConnectionError:
            console.print(f"[red]Error: Cannot connect to Ollama at {self.base_url}[/red]")
            console.print("[dim]Make sure Ollama is running: ollama serve[/dim]")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = SQL_TEMPERATURE,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> str:
        """
        Generate text using Ollama.
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream response
            
        Returns:
            Generated text response
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama API error: {e}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = SQL_TEMPERATURE,
        max_tokens: int = 2048
    ) -> str:
        """
        Chat completion using Ollama.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Assistant response
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("message", {}).get("content", "")
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama API error: {e}")
    
    def extract_sql(self, response: str) -> str:
        """
        Extract SQL query from LLM response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Extracted SQL query
        """
        # Try to find SQL in code blocks
        sql_pattern = r"```(?:sql)?\s*([\s\S]*?)```"
        matches = re.findall(sql_pattern, response, re.IGNORECASE)
        
        if matches:
            return matches[0].strip()
        
        # Try to find SELECT/INSERT/UPDATE/DELETE statements
        sql_keywords = r"(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\s+[\s\S]*?(?:;|$)"
        matches = re.findall(sql_keywords, response, re.IGNORECASE)
        
        if matches:
            # Find the full statement
            for keyword in ["SELECT", "INSERT", "UPDATE", "DELETE"]:
                if keyword in response.upper():
                    start = response.upper().find(keyword)
                    end = response.find(";", start)
                    if end == -1:
                        end = len(response)
                    return response[start:end+1].strip()
        
        # Return cleaned response as fallback
        return response.strip()
    
    def extract_json(self, response: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed JSON dictionary
        """
        # Try to find JSON in code blocks
        json_pattern = r"```(?:json)?\s*([\s\S]*?)```"
        matches = re.findall(json_pattern, response, re.IGNORECASE)
        
        if matches:
            try:
                return json.loads(matches[0].strip())
            except json.JSONDecodeError:
                pass
        
        # Try to parse entire response as JSON
        try:
            # Find JSON object boundaries
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        
        return {}
    
    def list_models(self) -> List[str]:
        """
        List available models in Ollama.
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return [m["name"] for m in result.get("models", [])]
            
        except requests.exceptions.RequestException:
            return []

