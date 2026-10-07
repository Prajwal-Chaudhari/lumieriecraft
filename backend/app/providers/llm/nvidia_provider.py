import os
import json
from openai import AsyncOpenAI
from app.providers.llm.base import LLMProvider

class NvidiaLLMProvider(LLMProvider):
    def __init__(self):
        self.api_key = os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError("Configuration Error: NVIDIA_API_KEY environment variable is not set.")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://integrate.api.nvidia.com/v1"
        )
        self.model = os.getenv("NVIDIA_MODEL", "meta/llama3-70b-instruct")

    async def generate_json(self, prompt: str, schema: dict) -> dict:
        normalized_schema = self.normalize_schema(schema)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a master screenwriter. You MUST return ONLY valid JSON matching this JSON Schema:\n{json.dumps(normalized_schema)}\nDo not include ```json markdown blocks, just raw JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        if not content:
            raise Exception("NVIDIA API returned an empty response.")
            
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON from NVIDIA API response: {e}\nContent: {content}")
