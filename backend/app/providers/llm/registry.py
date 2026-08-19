import os
from app.providers.llm.mock_provider import MockLLMProvider
from app.providers.llm.openai_provider import OpenAILLMProvider

def get_llm_provider():
    provider_name = os.getenv("SCRIPT_WRITER_PROVIDER", "mock").lower()
    if provider_name == "openai":
        return OpenAILLMProvider()
    return MockLLMProvider()
