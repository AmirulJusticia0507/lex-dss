import httpx
import json
import logging
from typing import Optional, List, Dict, Any, AsyncGenerator
from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.timeout = httpx.Timeout(settings.LLM_TIMEOUT_SECONDS)
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "LexDSS-Backend/1.0",
        }
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        format: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        system: Optional[str] = None,
    ) -> Dict[str, Any]:
        model = model or settings.OLLAMA_MODEL
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": settings.OLLAMA_TEMPERATURE,
                "top_p": settings.OLLAMA_TOP_P,
                "num_ctx": settings.OLLAMA_NUM_CTX,
                **(options or {}),
            },
        }
        if format:
            payload["format"] = format
        if system:
            payload["system"] = system
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        format: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        model = model or settings.OLLAMA_MODEL
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": settings.OLLAMA_TEMPERATURE,
                "top_p": settings.OLLAMA_TOP_P,
                "num_ctx": settings.OLLAMA_NUM_CTX,
                **(options or {}),
            },
        }
        if format:
            payload["format"] = format
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    
    async def embeddings(
        self,
        prompt: str,
        model: Optional[str] = None,
    ) -> List[float]:
        model = model or settings.OLLAMA_EMBED_MODEL
        payload = {
            "model": model,
            "prompt": prompt,
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                headers=self.headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])
    
    async def list_models(self) -> List[Dict[str, Any]]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/api/tags",
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json().get("models", [])
    
    async def pull_model(self, model: str) -> AsyncGenerator[Dict[str, Any], None]:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300)) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/pull",
                headers=self.headers,
                json={"model": model, "stream": True},
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        yield json.loads(line)


class GeminiClient:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.timeout = httpx.Timeout(settings.LLM_TIMEOUT_SECONDS)
    
    def has_key(self) -> bool:
        return bool(self.api_key)
    
    async def generate(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> Dict[str, Any]:
        if not self.has_key():
            raise ValueError("GEMINI_API_KEY not configured")
        
        model = model or settings.GEMINI_MODEL
        
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                continue
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}],
            })
        
        payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}],
            },
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
            },
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/models/{model}:generateContent?key={self.api_key}",
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            
            text = ""
            if data.get("candidates"):
                parts = data["candidates"][0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts).strip()
            
            return {"text": text, "model": model}


ollama_client = OllamaClient()
gemini_client = GeminiClient()