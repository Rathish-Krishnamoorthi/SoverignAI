import json
import os
import re
from typing import Any

import requests
from urllib.parse import urlparse
import logging
logger = logging.getLogger("sovereign_x.network")


class OllamaClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "600"))
        self.num_gpu = int(os.getenv("OLLAMA_NUM_GPU", "0"))
        parsed = urlparse(self.base_url)
        allowed = {"localhost", "127.0.0.1", "::1", "ollama"}
        if os.getenv("AIR_GAPPED_MODE", "true").lower() == "true" and parsed.hostname not in allowed:
            logger.error("external_network_attempt blocked host=%s", parsed.hostname)
            raise ValueError("AIR_GAPPED_MODE permits only local Ollama endpoints")

    def models(self) -> list[str]:
        response = requests.get(f"{self.base_url}/api/tags", timeout=2)
        response.raise_for_status()
        return [item.get("name", "") for item in response.json().get("models", [])]

    def status(self, requested: list[str]) -> dict[str, Any]:
        try:
            available_models = self.models()
        except requests.RequestException as exc:
            return {"available": False, "error": str(exc), "models": []}
        return {
            "available": all(any(name == installed or name.split(":")[0] == installed.split(":")[0]
                                for installed in available_models) for name in requested),
            "models": available_models,
        }

    def generate(self, model: str, prompt: str, images: list[str] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model, "prompt": prompt, "stream": False,
            "format": "json", "options": {"num_gpu": self.num_gpu},
        }
        if images:
            payload["images"] = images
        response = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout)
        if not response.ok:
            raise RuntimeError(f"Ollama inference failed ({response.status_code}): {response.text[:500]}")
        raw = response.json().get("response", "")
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                raise ValueError("Ollama returned malformed structured output.") from exc
            return json.loads(match.group(0))
