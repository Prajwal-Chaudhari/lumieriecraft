import os
import json
from openai import AsyncOpenAI
from app.providers.llm.base import LLMProvider

class OllamaLLMProvider(LLMProvider):
    def __init__(self):
        self.model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
        
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        if not base_url.endswith("/v1") and not base_url.endswith("/api"):
            base_url = f"{base_url.rstrip('/')}/v1"
            
        self.base_url = base_url
        
        # Ollama's OpenAI compatibility endpoint doesn't require an API key, 
        # but the OpenAI client requires the argument to be present.
        self.client = AsyncOpenAI(
            api_key="ollama",
            base_url=self.base_url
        )
        
        self.temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.6"))
        self.max_tokens = int(os.getenv("OLLAMA_MAX_TOKENS", "4096"))
        self.disable_thinking = os.getenv("OLLAMA_DISABLE_THINKING", "true").lower() == "true"

    async def generate_json(self, prompt: str, schema: dict) -> dict:
        normalized_schema = self.normalize_schema(schema)
        try:
            extra_body = {}
            if self.disable_thinking:
                extra_body["options"] = {"thinking": False}

            system_instruction = (
                "You are an expert AI assistant that strictly follows instructions.\n"
                "Your ONLY task is to generate valid JSON data that perfectly matches the provided JSON Schema.\n"
                "DO NOT output the JSON Schema itself. Output an object that CONFORMS to the schema.\n"
                f"JSON Schema:\n{json.dumps(normalized_schema)}\n"
                "Do not include markdown code blocks, just the raw JSON object."
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=self.temperature,
                max_completion_tokens=self.max_tokens,
                extra_body=extra_body if extra_body else None
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "connect" in error_msg or "all connection attempts failed" in error_msg:
                raise Exception(f"The local Ollama service could not be reached at {self.base_url}. Please ensure Ollama is running.") from e
            raise

        
        content = response.choices[0].message.content
        if not content:
            raise Exception("Ollama returned an empty response.")
            
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON from Ollama API response: {e}\nContent: {content}")
