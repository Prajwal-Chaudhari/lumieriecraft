from abc import ABC, abstractmethod
from typing import List
from app.models.project import CharacterAsset

class ProviderAsset(ABC):
    """Represents a resolved asset ready for provider consumption."""
    @abstractmethod
    def get_url(self) -> str:
        """Return the URL or data URI to pass to the provider."""
        ...

class URLProviderAsset(ProviderAsset):
    def __init__(self, url: str):
        self.url = url
        
    def get_url(self) -> str:
        return self.url

class ReferenceAssetResolver(ABC):
    """
    Decouples local domain assets from provider-specific requirements.
    Resolves a CharacterAsset into a Provider-accessible asset.
    """
    
    @abstractmethod
    async def resolve(self, asset: CharacterAsset) -> ProviderAsset:
        """Resolve a single asset into a provider-ready format."""
        ...
        
class LocalToDataURIResolver(ReferenceAssetResolver):
    """
    A simple resolver that converts local file paths to base64 Data URIs 
    for providers that accept them (like Fal.ai).
    """
    async def resolve(self, asset: CharacterAsset) -> ProviderAsset:
        import base64
        import mimetypes
        import os
        
        # If it's already a URL, just return it
        if asset.file_path.startswith("http://") or asset.file_path.startswith("https://") or asset.file_path.startswith("data:"):
            return URLProviderAsset(asset.file_path)
            
        if not os.path.exists(asset.file_path):
            raise FileNotFoundError(f"Local asset not found: {asset.file_path}")
            
        mime_type, _ = mimetypes.guess_type(asset.file_path)
        if not mime_type:
            mime_type = "image/png"
            
        with open(asset.file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            
        data_uri = f"data:{mime_type};base64,{encoded}"
        return URLProviderAsset(data_uri)
