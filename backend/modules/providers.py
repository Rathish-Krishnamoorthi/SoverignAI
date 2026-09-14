"""Provider-neutral local inference and embedding interfaces (no network/cloud fallback)."""
import os
from typing import Protocol
class LLMProvider(Protocol):
    name: str
    def status(self) -> dict: ...
    def generate(self, prompt: str) -> str: ...
class OllamaProvider:
    name = "ollama"
    def __init__(self): self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    def status(self):
        from backend.modules.llm.manager import LocalLLM
        return LocalLLM().status()
    def generate(self, prompt):
        from backend.modules.llm.manager import LocalLLM
        return LocalLLM().client.generate(prompt)
class VLLMProvider:
    name = "vllm"
    def __init__(self): self.base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
    def status(self): return {"available": False, "provider": "vllm", "execution": "local", "configured": bool(os.getenv("VLLM_MODEL"))}
class LocalEmbeddingProvider:
    def __init__(self):
        self.model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    def embed(self, text: str) -> list[float]:
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer(self.model).encode(text).tolist()
        except Exception:
            # deterministic, offline fallback keeps demo/RAG usable without model assets
            import hashlib
            raw = hashlib.sha256(text.encode()).digest()
            return [(raw[i % len(raw)] / 255.0) for i in range(768)]
