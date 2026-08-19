from abc import ABC, abstractmethod
from typing import Dict, Any

class LLMProvider(ABC):
    @abstractmethod
    async def generate_json(self, prompt: str, schema: dict) -> dict:
        """Generates a JSON object conforming to the given JSON schema."""
        pass
