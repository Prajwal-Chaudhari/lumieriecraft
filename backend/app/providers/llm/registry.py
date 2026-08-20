import os
from app.providers.llm.mock_provider import MockLLMProvider
from app.providers.llm.openai_provider import OpenAILLMProvider
from app.providers.llm.gemini_provider import GeminiLLMProvider

def get_llm_provider():
    provider_name = os.getenv("LLM_PROVIDER", os.getenv("SCRIPT_WRITER_PROVIDER", "mock")).lower()
    if provider_name == "openai":
        return OpenAILLMProvider()
    if provider_name == "gemini":
        return GeminiLLMProvider()
    return MockLLMProvider()
