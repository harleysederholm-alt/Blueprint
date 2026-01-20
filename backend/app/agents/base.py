"""
Base Agent Class - Common functionality for AI agents
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, TypeVar, Generic
import json

import ollama
from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar("T", bound=BaseModel)


class BaseAgent(ABC, Generic[T]):
    """
    Base class for all AI agents.
    
    Provides:
    - Ollama integration
    - Structured JSON output
    - Error handling and retries
    - Logging
    """
    
    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.ollama_model
        self.client = ollama.Client(host=settings.ollama_base_url)
        
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """The system prompt for this agent."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name for logging."""
        pass
    
    async def generate(
        self,
        user_prompt: str,
        temperature: float = 0.3,
        max_retries: int = 2,
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            user_prompt: The user message/data to process
            temperature: Sampling temperature (lower = more deterministic)
            max_retries: Number of retries on failure
            
        Returns:
            The generated response text
        """
        import asyncio
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"[{self.name}] Generating response (attempt {attempt + 1})")
                
                # Run blocking ollama call in executor
                loop = asyncio.get_event_loop()
                
                def _call_ollama():
                    return self.client.chat(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        options={
                            "temperature": temperature,
                            "num_predict": 4096,  # Token limit
                        },
                    )
                
                # Apply timeout (5 minutes for large prompts)
                response = await asyncio.wait_for(
                    loop.run_in_executor(None, _call_ollama),
                    timeout=settings.ollama_timeout
                )
                
                content = response["message"]["content"]
                logger.info(f"[{self.name}] Generated {len(content)} characters")
                return content
                
            except asyncio.TimeoutError:
                logger.error(f"[{self.name}] Timeout on attempt {attempt + 1}")
                if attempt == max_retries:
                    raise RuntimeError(f"[{self.name}] LLM inference timed out after {settings.ollama_timeout}s")
            except Exception as e:
                logger.error(f"[{self.name}] Error on attempt {attempt + 1}: {e}")
                if attempt == max_retries:
                    raise
        
        raise RuntimeError(f"[{self.name}] Failed after {max_retries + 1} attempts")
    
    def parse_json_response(self, response: str) -> dict:
        """
        Extract and parse JSON from an LLM response.
        
        Handles common issues like markdown code blocks.
        """
        # Strip markdown code blocks if present
        content = response.strip()
        
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.warning(f"[{self.name}] JSON parse failed: {e}")
            
            # Try to find JSON object in response
            start = content.find("{")
            end = content.rfind("}") + 1
            
            if start >= 0 and end > start:
                try:
                    return json.loads(content[start:end])
                except json.JSONDecodeError:
                    pass
            
            # Return as raw content if parsing fails
            return {"raw_response": response, "parse_error": str(e)}
    
    async def generate_structured(
        self,
        user_prompt: str,
        temperature: float = 0.3,
    ) -> dict:
        """
        Generate a structured JSON response.
        
        Args:
            user_prompt: The user message/data to process
            temperature: Sampling temperature
            
        Returns:
            Parsed JSON dictionary
        """
        response = await self.generate(
            user_prompt=user_prompt,
            temperature=temperature,
        )
        return self.parse_json_response(response)
