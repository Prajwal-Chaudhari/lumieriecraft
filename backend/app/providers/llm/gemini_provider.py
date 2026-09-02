import os
import json
from google import genai
from google.genai import types
from app.providers.llm.base import LLMProvider

class GeminiLLMProvider(LLMProvider):
    def __init__(self):
        # We assume GEMINI_API_KEY is configured in the environment
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    async def generate_json(self, prompt: str, schema: dict) -> dict:
        if not self.api_key or not self.client:
            raise Exception("Configuration Error: GEMINI_API_KEY environment variable is missing.")

        system_instruction = (
            f"You are a master screenwriter. You MUST return ONLY valid JSON matching this JSON Schema:\n"
            f"{json.dumps(schema)}\n"
            f"Do not include ```json markdown blocks, just raw JSON."
        )

        try:
            import asyncio
            import logging
            
            max_retries = 3
            base_delay = 2.0
            
            for attempt in range(max_retries):
                try:
                    response = await self.client.aio.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=schema,
                        ),
                    )
                    
                    content = response.text
                    if not content:
                        raise Exception("Gemini returned an empty response.")
                        
                    return json.loads(content)
                except Exception as e:
                    error_msg = str(e)
                    is_transient = any(code in error_msg for code in ["429", "500", "502", "503", "504"])
                    
                    if not is_transient or attempt == max_retries - 1:
                        # Re-raise if it's not transient or we're out of retries
                        raise e
                    
                    delay = base_delay * (2 ** attempt)
                    logging.warning(f"Transient LLM error. Retrying in {delay}s (Attempt {attempt+1}/{max_retries})...")
                    await asyncio.sleep(delay)
                    
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON from Gemini response: {str(e)}")
        except Exception as e:
            # We catch other API errors and surface them cleanly
            error_msg = str(e)
            if self.api_key and self.api_key in error_msg:
                error_msg = error_msg.replace(self.api_key, "***API_KEY_HIDDEN***")
            raise Exception(f"Gemini API Error: {error_msg}")
