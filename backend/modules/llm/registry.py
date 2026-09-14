from dataclasses import dataclass
from enum import StrEnum
import os


class ModelCapability(StrEnum):
    DOCUMENT = "document"
    VISION = "vision"
    SOP = "sop"
    ENGINEERING = "engineering"
    SUMMARY = "summary"
    APPROVAL = "approval"
    # Legacy aliases retained for callers using the initial upgrade API.
    REASONING = "engineering"
    EXTRACTION = "document"


@dataclass(frozen=True)
class ModelDefinition:
    name: str
    capability: ModelCapability
    description: str


class ModelRegistry:
    """Deterministic model routing table; names are Ollama model tags."""

    def __init__(self) -> None:
        capability_defaults = {
            ModelCapability.DOCUMENT: "qwen2.5vl:3b",
            ModelCapability.VISION: "qwen2.5vl:3b",
            ModelCapability.SOP: "qwen2.5vl:3b",
            ModelCapability.ENGINEERING: "qwen2.5vl:3b",
            ModelCapability.SUMMARY: "qwen2.5vl:3b",
            ModelCapability.APPROVAL: "qwen2.5vl:3b",
        }
        definitions = (
                ("OLLAMA_DOCUMENT_MODEL", ModelCapability.DOCUMENT, "OCR and structured document extraction"),
                ("OLLAMA_VISION_MODEL", ModelCapability.VISION, "Inspection image and document reasoning"),
                ("OLLAMA_SOP_MODEL", ModelCapability.SOP, "SOP retrieval interpretation"),
                ("OLLAMA_ENGINEERING_MODEL", ModelCapability.ENGINEERING, "Evidence-grounded engineering reasoning"),
                ("OLLAMA_SUMMARY_MODEL", ModelCapability.SUMMARY, "Traceable finding summary"),
                ("OLLAMA_APPROVAL_MODEL", ModelCapability.APPROVAL, "Engineer-reviewable approval draft"),
        )
        models = []
        for env, capability, description in definitions:
            if env not in os.environ:
                legacy = {
                    ModelCapability.ENGINEERING: "OLLAMA_REASONING_MODEL",
                    ModelCapability.DOCUMENT: "OLLAMA_EXTRACTION_MODEL",
                }.get(capability)
                if legacy and os.getenv(legacy):
                    name = os.getenv(legacy, capability_defaults[capability])
                else:
                    name = capability_defaults[capability]
            else:
                name = os.getenv(env, capability_defaults[capability])
            models.append(ModelDefinition(name, capability, description))
        self._models = tuple(models)
        self._overrides: dict[str, str] = {}

    def all(self) -> list[ModelDefinition]:
        return list(self._models)

    def for_capability(self, capability: ModelCapability) -> ModelDefinition:
        model = next(model for model in self._models if model.capability.value == capability.value)
        override = self._overrides.get(capability.value)
        return ModelDefinition(override, model.capability, model.description) if override else model

    def set_model(self, capability: str, name: str) -> ModelDefinition:
        model = next((item for item in self._models if item.capability.value == capability), None)
        if model is None:
            raise ValueError(f"Unknown model capability: {capability}")
        self._overrides[capability] = name
        return self.for_capability(model.capability)
