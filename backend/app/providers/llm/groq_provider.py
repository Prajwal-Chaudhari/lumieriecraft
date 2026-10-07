import os
import json
import logging
from openai import AsyncOpenAI
from app.providers.llm.base import LLMProvider

class GroqLLMProvider(LLMProvider):
    """
    LLM Provider for Groq.
    Groq exposes an OpenAI-compatible API, so we use the AsyncOpenAI client
    pointed at Groq's base URL.
    """

    DEFAULT_MODEL = "llama-3.3-70b-versatile"

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", self.DEFAULT_MODEL)

        if not self.api_key:
            raise ValueError("Configuration Error: GROQ_API_KEY environment variable is not set.")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    async def _call_model(self, model: str, system_prompt: str, prompt: str) -> dict:
        """Make a single API call to a specific model."""
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            raise Exception(f"Groq returned an empty response from {model}.")

        # Strip markdown code blocks if the model wrapped the JSON
        content = content.strip()
        if content.startswith("```json"):
            content = content[len("```json"):]
        elif content.startswith("```"):
            content = content[len("```"):]
            
        if content.endswith("```"):
            content = content[:-len("```")]
            
        content = content.strip()

        return json.loads(content)

    async def generate_json(self, prompt: str, schema: dict) -> dict:
        normalized_schema = self.normalize_schema(schema)
        system_prompt = (
            f"You are a master screenwriter and production expert. "
            f"You MUST return ONLY valid JSON matching this JSON Schema:\n"
            f"{json.dumps(normalized_schema)}\n"
            f"Do not include ```json markdown blocks, just raw JSON."
        )

        try:
            logging.info(f"Trying Groq model: {self.model}")
            result = await self._call_model(self.model, system_prompt, prompt)
            return result
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON from Groq response: {e}")
        except Exception as e:
            error_msg = str(e)
            if self.api_key and self.api_key in error_msg:
                error_msg = error_msg.replace(self.api_key, "***API_KEY_HIDDEN***")
            raise Exception(f"Groq API Error: {error_msg}")
