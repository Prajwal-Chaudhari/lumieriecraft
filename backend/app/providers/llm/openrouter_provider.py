import os
import json
import asyncio
import logging
import random
from openai import AsyncOpenAI
from app.providers.llm.base import LLMProvider

class OpenRouterLLMProvider(LLMProvider):
    """
    LLM Provider for OpenRouter (https://openrouter.ai).
    OpenRouter exposes an OpenAI-compatible API, so we use the AsyncOpenAI client
    pointed at OpenRouter's base URL.

    Required env vars:
        OPENROUTER_API_KEY  — your OpenRouter API key (starts with sk-or-...)
        OPENROUTER_MODEL    — model slug, e.g. "google/gemini-2.5-flash-lite:free"
                             Defaults to a capable free-tier model.
    Optional env vars:
        OPENROUTER_SITE_URL — your site URL (sent as HTTP-Referer, recommended by OpenRouter)
        OPENROUTER_APP_NAME — your app name (sent as X-Title header)
    """

    DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
    FALLBACK_MODELS = [
        "minimax/minimax-m2.7:free",
        "nvidia/nemotron-3.5-lightning:free",
        "minimax/minimax-m3:free",
    ]

    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", self.DEFAULT_MODEL)
        self.site_url = os.getenv("OPENROUTER_SITE_URL", "http://localhost:3000")
        self.app_name = os.getenv("OPENROUTER_APP_NAME", "Lumierecraft")

        if not self.api_key:
            raise ValueError(
                "Configuration Error: OPENROUTER_API_KEY environment variable is not set."
            )

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": self.site_url,
                "X-Title": self.app_name,
            },
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
            raise Exception(f"OpenRouter returned an empty response from {model}.")

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

        # Build the list of models to try: primary first, then fallbacks
        models_to_try = [self.model] + [
            m for m in self.FALLBACK_MODELS if m != self.model
        ]

        last_error = None
        for model in models_to_try:
            max_retries = 4
            base_delay = 2.0

            for attempt in range(max_retries):
                try:
                    logging.info(f"Trying OpenRouter model: {model} (attempt {attempt + 1})")
                    result = await self._call_model(model, system_prompt, prompt)
                    return result

                except json.JSONDecodeError as e:
                    raise Exception(f"Failed to parse JSON from OpenRouter response: {e}")

                except Exception as e:
                    error_msg = str(e)

                    # Mask API key if it appears in error messages
                    if self.api_key and self.api_key in error_msg:
                        error_msg = error_msg.replace(self.api_key, "***API_KEY_HIDDEN***")

                    last_error = error_msg

                    # Check if the model is unavailable (404) — skip to next model immediately
                    if "404" in error_msg:
                        logging.warning(f"Model {model} unavailable (404). Trying next model...")
                        break

                    # Retry on transient errors (rate limit, server errors)
                    is_transient = any(
                        code in error_msg for code in ["429", "500", "502", "503", "504"]
                    )

                    if not is_transient or attempt == max_retries - 1:
                        logging.warning(f"Model {model} failed: {error_msg}. Trying next model...")
                        break

                    delay = base_delay * (2 ** attempt) * (0.5 + random.random())
                    logging.warning(
                        f"Transient error with {model}. Retrying in {delay:.0f}s "
                        f"(Attempt {attempt + 1}/{max_retries}): {error_msg}"
                    )
                    await asyncio.sleep(delay)

        raise Exception(
            f"OpenRouter API Error: All models failed. Last error: {last_error}"
        )
