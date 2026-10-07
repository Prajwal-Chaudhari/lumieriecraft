import os
import json
from google import genai
from google.genai import types
from app.providers.llm.base import LLMProvider

class GeminiLLMProvider(LLMProvider):
    DEFAULT_MODEL = "gemini-3.5-flash-lite"
    FALLBACK_MODELS = [
        "gemini-3.5-flash-lite",
        "gemini-3.5-flash",
        "gemini-3.7-flash",
    ]

    def __init__(self):
        # We assume GEMINI_API_KEY is configured in the environment
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", self.DEFAULT_MODEL)
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    async def generate_json(self, prompt: str, schema: dict) -> dict:
        if not self.api_key or not self.client:
            raise Exception("Configuration Error: GEMINI_API_KEY environment variable is missing.")

        system_instruction = (
            f"You are a master screenwriter. You MUST return ONLY valid JSON that matches the requested schema.\n"
            f"Do not include ```json markdown blocks, just raw JSON."
        )

        import asyncio
        import logging

        models_to_try = [self.model] + [m for m in self.FALLBACK_MODELS if m != self.model]
        last_error = None

        for model in models_to_try:
            max_retries = 2
            base_delay = 1.5

            for attempt in range(max_retries):
                try:
                    response = await self.client.aio.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=schema,
                        ),
                    )
                    
                    content = response.text
                    if not content:
                        raise Exception(f"Gemini returned an empty response from {model}.")
                        
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    raise Exception(f"Failed to parse JSON from Gemini response: {str(e)}")
                except Exception as e:
                    error_msg = str(e)
                    last_error = error_msg
                    is_transient = any(code in error_msg for code in ["429", "500", "502", "503", "504"])
                    
                    if not is_transient or attempt == max_retries - 1:
                        logging.warning(f"Gemini model {model} failed: {error_msg}. Trying fallback model...")
                        break
                    
                    delay = base_delay * (2 ** attempt)
                    logging.warning(f"Transient error with {model}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)

        if self.api_key and last_error and self.api_key in last_error:
            last_error = last_error.replace(self.api_key, "***API_KEY_HIDDEN***")
        raise Exception(f"Gemini API Error: {last_error}")
