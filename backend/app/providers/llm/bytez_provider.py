import os
import json
import logging
from typing import Optional
from bytez import Bytez

from .base import LLMProvider

class BytezLLMProvider(LLMProvider):
    def __init__(self):
        api_key = os.getenv("BYTEZ_API_KEY")
        if not api_key:
            raise ValueError("BYTEZ_API_KEY environment variable is not set")
        
        self.sdk = Bytez(api_key)
        self.model_id = os.getenv("BYTEZ_MODEL", "Qwen/Qwen3-4B")
        self.model = self.sdk.model(self.model_id)

    async def _call_model(self, system_prompt: str, prompt: str) -> dict:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # provide the model with params
        params = {
            "temperature": 0.3
        }

        result = self.model.run(messages, params)
        if result.error:
            raise Exception(f"Bytez API Error: {result.error}")
        
        if not result.output:
            raise Exception("Bytez returned an empty response.")
        
        # Strip markdown code blocks if the model wrapped the JSON
        content = result.output
        
        # If output is a list or dict, maybe it already parsed?
        if isinstance(content, (dict, list)):
            return content
            
        if isinstance(content, str):
            content = content.strip()
            if content.startswith("```json"):
                content = content[len("```json"):]
            elif content.startswith("```"):
                content = content[len("```"):]
                
            if content.endswith("```"):
                content = content[:-len("```")]
                
            content = content.strip()
            return json.loads(content)
            
        raise Exception(f"Unexpected output type from Bytez: {type(content)}")

    async def generate_json(self, prompt: str, schema: dict) -> dict:
        normalized_schema = self.normalize_schema(schema)
        system_prompt = f"You are a helpful assistant. Please return ONLY a valid JSON object matching the following schema. Do NOT wrap the JSON in Markdown formatting.\n\nSCHEMA:\n{json.dumps(normalized_schema)}"
        return await self._call_model(system_prompt, prompt)
