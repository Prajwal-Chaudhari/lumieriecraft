import os
from dotenv import load_dotenv

def get_llm_provider(purpose: str = "SCRIPT_WRITER"):
    # Deterministically load .env from the backend root
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))
    load_dotenv(dotenv_path=env_path)

    provider_name = os.getenv(f"{purpose.upper()}_PROVIDER") or os.getenv("LLM_PROVIDER")
    
    if not provider_name:
        raise ValueError(f"Configuration Error: {purpose.upper()}_PROVIDER or LLM_PROVIDER environment variable is not set.")
        
    provider_name = provider_name.lower()
    
    if provider_name == "openrouter":
        from app.providers.llm.openrouter_provider import OpenRouterLLMProvider
        from app.providers.llm.groq_provider import GroqLLMProvider
        from app.providers.llm.fallback_provider import TimeoutFallbackLLMProvider
        return TimeoutFallbackLLMProvider(
            primary=OpenRouterLLMProvider(),
            secondary=GroqLLMProvider(),
            timeout_seconds=300.0
        )
    elif provider_name == "bytez":
        from app.providers.llm.bytez_provider import BytezLLMProvider
        return BytezLLMProvider()
    elif provider_name == "gemini":
        from app.providers.llm.gemini_provider import GeminiLLMProvider
        return GeminiLLMProvider()
    elif provider_name == "mock":
        from app.providers.llm.mock_provider import MockLLMProvider
        return MockLLMProvider()
    elif provider_name == "ollama":
        from app.providers.llm.ollama_provider import OllamaLLMProvider
        return OllamaLLMProvider()
        
    raise ValueError(f"Configuration Error: Invalid provider '{provider_name}' configured for {purpose.upper()}_PROVIDER. Must be 'mock', 'openrouter', 'gemini', 'bytez', or 'ollama'.")
