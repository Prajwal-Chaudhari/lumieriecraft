import os
import json
from google import genai
from google.genai import types
from app.providers.llm.base import LLMProvider

class GeminiLLMProvider(LLMProvider):
    def __init__(self):
        # We assume GEMINI_API_KEY is configured in the environment
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    async def generate_json(self, prompt: str, schema: dict) -> dict:
        if not os.getenv("GEMINI_API_KEY"):
            raise Exception("GEMINI_API_KEY environment variable is missing.")

        system_instruction = (
            f"You are a master screenwriter. You MUST return ONLY valid JSON matching this JSON Schema:\n"
            f"{json.dumps(schema)}\n"
            f"Do not include ```json markdown blocks, just raw JSON."
        )

        try:
            # Note: the google-genai SDK's generate_content_async is awaitable
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                ),
            )
            
            content = response.text
            if not content:
                raise Exception("Gemini returned an empty response.")
                
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON from Gemini response: {str(e)}")
        except Exception as e:
            # We catch other API errors and surface them cleanly
            raise Exception(f"Gemini API Error: {str(e)}")
