import os
from dotenv import load_dotenv

def get_llm_provider():
    # Deterministically load .env from the backend root
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))
    load_dotenv(dotenv_path=env_path)

    provider_name = os.getenv("SCRIPT_WRITER_PROVIDER") or os.getenv("LLM_PROVIDER")
    
    if not provider_name:
        raise ValueError("Configuration Error: SCRIPT_WRITER_PROVIDER environment variable is not set.")
        
    provider_name = provider_name.lower()
    
    if provider_name == "gemini":
        from app.providers.llm.gemini_provider import GeminiLLMProvider
        return GeminiLLMProvider()
    elif provider_name == "openai":
        from app.providers.llm.openai_provider import OpenAILLMProvider
        return OpenAILLMProvider()
    elif provider_name == "mock":
        from app.providers.llm.mock_provider import MockLLMProvider
        return MockLLMProvider()
        
    raise ValueError(f"Configuration Error: Invalid SCRIPT_WRITER_PROVIDER '{provider_name}'. Must be 'mock', 'gemini', or 'openai'.")
