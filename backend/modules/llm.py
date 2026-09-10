import json
import os
import re
from typing import Any

import requests

from backend.models.schemas import AIAnalysis, InspectionEvidence, SOPEvidence


class LocalLLM:
    def __init__(self) -> None:
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5vl:3b")
        self.timeout_seconds = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "600"))
        self.num_gpu = int(os.getenv("OLLAMA_NUM_GPU", "0"))

    def status(self) -> dict[str, Any]:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            response.raise_for_status()
            models = [item.get("name", "") for item in response.json().get("models", [])]
            available = any(self.model in name for name in models)
        except requests.RequestException:
            available = False
        return {"available": available, "model": self.model, "provider": "ollama", "execution": "local"}

    def analyze(
        self, inspection_evidence: InspectionEvidence, sop_context: SOPEvidence, images: list[str] | None = None
    ) -> AIAnalysis:
        prompt = f"""ROLE:
You are a refinery engineering document analysis assistant.
TASK:
Analyze the inspection evidence using the retrieved SOP.
IMPORTANT:
Do not invent facts. Use only supplied evidence and SOP context.
Do not perform unsupported numerical calculations. Return JSON only.
INSPECTION EVIDENCE:
Document: {inspection_evidence.document}
Page: {inspection_evidence.page}
Photo: {inspection_evidence.photo}
Equipment: {inspection_evidence.equipment}
Finding: {inspection_evidence.finding}
Measured pit depth: {inspection_evidence.measurement} mm
RETRIEVED SOP:
Document: {sop_context.document}
Section: {sop_context.section}
Requirement: {sop_context.text}
Return keys: finding, severity, recommendation, confidence, reasoning_summary."""
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"num_gpu": self.num_gpu},
            },
            timeout=self.timeout_seconds,
        )
        if not response.ok:
            raise RuntimeError(f"Ollama inference failed ({response.status_code}): {response.text[:500]}")
        response.raise_for_status()
        payload = response.json()
        raw = payload.get("response", "")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if not match:
                raise ValueError("Ollama returned malformed structured output.") from exc
            parsed = json.loads(match.group(0))
        return AIAnalysis.model_validate({**parsed, "model": self.model, "execution": "LOCAL"})

    @staticmethod
    def demo_analysis(evidence: InspectionEvidence) -> AIAnalysis:
        return AIAnalysis(
            finding=f"{evidence.finding} at {evidence.equipment}",
            severity="HIGH",
            recommendation="Engineering assessment required.",
            confidence="HIGH",
            reasoning_summary="The supplied inspection evidence identifies pitting above the retrieved SOP threshold.",
            execution="DEMO",
        )
