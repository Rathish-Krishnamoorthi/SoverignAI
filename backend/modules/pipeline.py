from typing import Any


def build_pipeline(model: str, mode: str, responsibility_matrix: list[dict[str, str]] | None = None) -> list[dict[str, Any]]:
    """Return the trace contract consumed by the API and frontend."""
    routes = {item["capability"]: item for item in (responsibility_matrix or [])}
    return [
        {"stage": "OCR", "responsibility": "document", **routes.get("document", {}), "status": "complete", "execution": "LOCAL"},
        {"stage": "Evidence Extraction", "responsibility": "document", **routes.get("document", {}), "status": "complete", "execution": "LOCAL"},
        {"stage": "SOP Retrieval", "responsibility": "sop", **routes.get("sop", {}), "status": "complete", "execution": "LOCAL"},
        {"stage": model, "responsibility": "vision", **routes.get("vision", {}), "status": "complete" if mode == "LOCAL" else "demo",
         "execution": mode, "provider": "ollama" if mode == "LOCAL" else "synthetic"},
        {"stage": "Engineering Reasoning", "responsibility": "engineering", **routes.get("engineering", {}), "status": "complete" if mode == "LOCAL" else "demo", "execution": mode},
        {"stage": "Finding Summary", "responsibility": "summary", **routes.get("summary", {}), "status": "complete" if mode == "LOCAL" else "demo", "execution": mode},
        {"stage": "Approval Draft", "responsibility": "approval", **routes.get("approval", {}), "status": "complete" if mode == "LOCAL" else "demo", "execution": mode},
        {"stage": "Python Verification", "status": "complete", "execution": "LOCAL", "authoritative": True},
        {"stage": "Evidence Chain", "status": "complete", "execution": "LOCAL"},
    ]
