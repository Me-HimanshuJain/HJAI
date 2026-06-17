import os
import httpx
import json

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = "llama3"

class LLMService:
    @staticmethod
    async def generate_response(prompt: str, model: str = DEFAULT_MODEL, system: str = None):
        """Generates a non-streaming response from Ollama."""
        url = f"{OLLAMA_HOST}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "")

    @staticmethod
    async def generate_response_stream(prompt: str, model: str = DEFAULT_MODEL, system: str = None):
        """Generates a streaming response from Ollama."""
        url = f"{OLLAMA_HOST}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }
        if system:
            payload["system"] = system

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        yield data.get("response", "")
                        if data.get("done"):
                            break

    @staticmethod
    async def chat(messages: list, model: str = DEFAULT_MODEL):
        """Generates a non-streaming chat response."""
        url = f"{OLLAMA_HOST}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("message", {}).get("content", "")

    @staticmethod
    async def chat_stream(messages: list, model: str = DEFAULT_MODEL):
        """Generates a streaming chat response."""
        url = f"{OLLAMA_HOST}/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        yield data.get("message", {}).get("content", "")
                        if data.get("done"):
                            break
