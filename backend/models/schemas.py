from typing import Any, Literal

from pydantic import BaseModel, Field


class AIAnalysis(BaseModel):
    finding: str
    severity: str
    recommendation: str
    confidence: str
    reasoning_summary: str
    model: str = "Qwen2-VL"
    execution: Literal["LOCAL", "DEMO"] = "LOCAL"


class InspectionEvidence(BaseModel):
    document: str
    page: int
    photo: str
    equipment: str
    finding: str
    measurement: float
    unit: str = "mm"


class SOPEvidence(BaseModel):
    document: str
    section: str
    page: int
    text: str
    limit: float
    unit: str = "mm"


class CalculationVerification(BaseModel):
    measured: float
    limit: float
    operator: str
    expression: str
    result: bool
    status: Literal["EXCEEDS_LIMIT", "WITHIN_LIMIT"]
    verified_by: str = "Python"


class EvidenceChain(BaseModel):
    finding_id: str
    finding: str
    inspection_evidence: dict[str, Any]
    sop_evidence: dict[str, Any]
    ai_analysis: dict[str, Any]
    calculation: dict[str, Any]
    provenance: dict[str, Any] = Field(default_factory=dict)


class DocumentPage(BaseModel):
    page: int
    text: str
    images: list[dict[str, str]] = Field(default_factory=list)


class StructuredDocument(BaseModel):
    document: str
    pages: list[DocumentPage]


class AnalysisResponse(BaseModel):
    document_id: str
    finding: InspectionEvidence
    inspection_evidence: InspectionEvidence
    sop_evidence: SOPEvidence
    ai_analysis: AIAnalysis
    calculation: CalculationVerification
    evidence_chain: EvidenceChain
    processing_mode: Literal["LOCAL", "DEMO"]
    pipeline: list[dict[str, Any]]
    provenance: dict[str, Any] = Field(default_factory=dict)


class ReviewRequest(BaseModel):
    action: Literal["accepted", "rejected", "review_requested"]


class DocumentRecord(BaseModel):
    document_id: str
    filename: str
    size_bytes: int
    uploaded_at: str
    analyzed: bool = False
    extraction_status: Literal["pending", "success", "failed"] = "pending"
    extraction_message: str | None = None
    # Populated by the production relational repository; optional for legacy
    # demo JSON records created before project scoping existed.
    owner_id: str | None = None
    project_id: str | None = None
