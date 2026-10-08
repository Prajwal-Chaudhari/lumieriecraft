import os
import json
import httpx
from app.providers.llm.base import LLMProvider

class OllamaLLMProvider(LLMProvider):
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3")

    async def generate_json(self, prompt: str, schema: dict) -> dict:
        url = f"{self.base_url}/api/chat"
        
        system_instruction = (
            f"You are a master screenwriter. You MUST return ONLY valid JSON matching this JSON Schema:\n"
            f"{json.dumps(schema)}\n"
            f"Do not include ```json markdown blocks, just raw JSON."
        )

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_instruction
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "format": "json",
            "stream": False
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                content = data.get("message", {}).get("content", "")
                
                if not content:
                    raise Exception("Ollama returned an empty response.")
                    
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse JSON from Ollama response: {str(e)}\nRaw output: {content}")
            except Exception as e:
                raise Exception(f"Ollama API Error: {str(e)}")
