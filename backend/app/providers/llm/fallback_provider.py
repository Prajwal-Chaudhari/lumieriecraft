import asyncio
import logging
from app.providers.llm.base import LLMProvider

class TimeoutFallbackLLMProvider(LLMProvider):
    """
    Wraps two providers. Tries the primary provider first with a specified timeout.
    If it times out or raises an exception, it falls back to the secondary provider.
    """
    def __init__(self, primary: LLMProvider, secondary: LLMProvider, timeout_seconds: float = 30.0):
        self.primary = primary
        self.secondary = secondary
        self.timeout_seconds = timeout_seconds

    async def generate_json(self, prompt: str, schema: dict) -> dict:
        try:
            logging.info(f"Attempting primary provider with timeout {self.timeout_seconds}s...")
            return await asyncio.wait_for(
                self.primary.generate_json(prompt, schema),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            logging.warning(f"Primary provider timed out after {self.timeout_seconds}s. Falling back to secondary provider...")
        except Exception as e:
            logging.warning(f"Primary provider failed with error: {e}. Falling back to secondary provider...")

        # If we reach here, we fallback
        logging.info("Attempting secondary provider...")
        return await self.secondary.generate_json(prompt, schema)
