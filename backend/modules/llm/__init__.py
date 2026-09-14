"""Local-only multi-model orchestration for SOVEREIGN-X.

The package deliberately has no provider abstraction for remote services: every
inference request is sent to the Ollama process configured by the environment.
"""

from .manager import LocalLLM, LLMManager
from .registry import ModelCapability, ModelDefinition, ModelRegistry

__all__ = [
    "LocalLLM",
    "LLMManager",
    "ModelCapability",
    "ModelDefinition",
    "ModelRegistry",
]
