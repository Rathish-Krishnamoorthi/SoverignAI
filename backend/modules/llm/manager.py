from typing import Any

from backend.models.schemas import AIAnalysis, InspectionEvidence, SOPEvidence
from .ollama_client import OllamaClient
from .registry import ModelCapability, ModelRegistry
from .specialized import VisionModule


class LLMManager:
    def __init__(self, registry: ModelRegistry | None = None, client: OllamaClient | None = None) -> None:
        self.registry = registry or ModelRegistry()
        self.client = client or OllamaClient()
        self.vision = VisionModule(self.client, self.registry.for_capability(ModelCapability.VISION))
        self._enabled = {model.capability.value: True for model in self.registry.all()}
        self._working: set[str] = set()

    def status(self) -> dict[str, Any]:
        definitions = self.registry.all()
        active_definitions = [self.registry.for_capability(model.capability) for model in definitions]
        result = self.client.status([model.name for model in active_definitions])
        installed = set(result.get("models", []))
        routes = []
        for base_model in definitions:
            model = self.registry.for_capability(base_model.capability)
            available = any(
                model.name == installed_model or model.name.split(":")[0] == installed_model.split(":")[0]
                for installed_model in installed
            )
            enabled = self._enabled[model.capability.value]
            routes.append({
                "name": model.name,
                "capability": model.capability.value,
                "description": model.description,
                "available": available,
                "enabled": enabled,
                "working": model.capability.value in self._working,
                "state": (
                    "working" if model.capability.value in self._working
                    else "active" if enabled and available
                    else "inactive" if not enabled
                    else "unavailable"
                ),
            })
        result.update({
            "provider": "ollama", "execution": "local", "base_url": self.client.base_url,
            "configured_models": routes,
            "routes": routes,
        })
        return result

    def analyze(self, evidence: InspectionEvidence, sop: SOPEvidence,
                images: list[str] | None = None) -> AIAnalysis:
        return self.vision.analyze(evidence, sop, images)

    def route(self, capability: ModelCapability) -> dict[str, str]:
        """Return the local route selected for a capability."""
        model = self.registry.for_capability(capability)
        return {"model": model.name, "capability": model.capability.value, "provider": "ollama"}

    def set_enabled(self, capability: str, enabled: bool) -> dict[str, Any]:
        if capability not in self._enabled:
            raise ValueError(f"Unknown model capability: {capability}")
        self._enabled[capability] = enabled
        return next(route for route in self.status()["routes"] if route["capability"] == capability)

    def set_model(self, capability: str, name: str) -> dict[str, Any]:
        if not name or name not in self.client.models():
            raise ValueError("Select an installed local Ollama model.")
        model = self.registry.set_model(capability, name)
        if model.capability == ModelCapability.VISION:
            self.vision.model = model
        return next(route for route in self.status()["routes"] if route["capability"] == capability)

    def set_working(self, capability: ModelCapability, working: bool) -> None:
        if working:
            self._working.add(capability.value)
        else:
            self._working.discard(capability.value)

    def responsibility_matrix(self) -> list[dict[str, str]]:
        return [self.route(capability) for capability in (
            ModelCapability.DOCUMENT, ModelCapability.VISION, ModelCapability.SOP,
            ModelCapability.ENGINEERING, ModelCapability.SUMMARY, ModelCapability.APPROVAL,
        )]

    @staticmethod
    def demo_analysis(evidence: InspectionEvidence) -> AIAnalysis:
        return AIAnalysis(
            finding=f"{evidence.finding} at {evidence.equipment}", severity="HIGH",
            recommendation="Engineering assessment required.", confidence="HIGH",
            reasoning_summary="The supplied inspection evidence identifies pitting above the retrieved SOP threshold.",
            execution="DEMO",
        )


# Backwards-compatible name used by the original API.
LocalLLM = LLMManager
