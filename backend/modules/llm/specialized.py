from typing import Any

from backend.models.schemas import AIAnalysis, InspectionEvidence, SOPEvidence
from .ollama_client import OllamaClient
from .registry import ModelDefinition


class VisionModule:
    def __init__(self, client: OllamaClient, model: ModelDefinition) -> None:
        self.client, self.model = client, model

    def analyze(self, evidence: InspectionEvidence, sop: SOPEvidence, images: list[str] | None = None) -> AIAnalysis:
        prompt = (
            "You are a refinery engineering assistant. Use only the supplied evidence and SOP. "
            "Do not invent facts or calculate thresholds. Return JSON keys finding,severity,"
            "recommendation,confidence,reasoning_summary.\n"
            f"Evidence: {evidence.model_dump()}\nSOP: {sop.model_dump()}"
        )
        result: dict[str, Any] = self.client.generate(self.model.name, prompt, images)
        return AIAnalysis.model_validate({**result, "model": self.model.name, "execution": "LOCAL"})
