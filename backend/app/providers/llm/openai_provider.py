import os
import json
from openai import AsyncOpenAI
from app.providers.llm.base import LLMProvider

class OpenAILLMProvider(LLMProvider):
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY", "dummy"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    async def generate_json(self, prompt: str, schema: dict) -> dict:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"You are a master screenwriter. You MUST return ONLY valid JSON matching this JSON Schema:\n{json.dumps(schema)}\nDo not include ```json markdown blocks, just raw JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
