from abc import ABC, abstractmethod
from typing import Dict, Any

class LLMProvider(ABC):
    @abstractmethod
    async def generate_json(self, prompt: str, schema: dict) -> dict:
        """Generates a JSON object conforming to the given JSON schema."""
        pass
        
    def normalize_schema(self, custom_schema: Any) -> Any:
        """Converts Gemini uppercase type strings to standard JSON Schema lowercase types."""
        if isinstance(custom_schema, dict):
            new_schema = {}
            for k, v in custom_schema.items():
                if k == "type" and isinstance(v, str):
                    new_schema[k] = v.lower()
                else:
                    new_schema[k] = self.normalize_schema(v)
            return new_schema
        elif isinstance(custom_schema, list):
            return [self.normalize_schema(i) for i in custom_schema]
        return custom_schema
