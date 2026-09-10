from typing import Any

from backend.models.schemas import AIAnalysis, CalculationVerification, InspectionEvidence, SOPEvidence


def build_chain(
    evidence: InspectionEvidence, sop: SOPEvidence, analysis: AIAnalysis, calculation: CalculationVerification | dict[str, Any]
) -> dict:
    calculation_data = calculation.model_dump() if isinstance(calculation, CalculationVerification) else calculation
    return {
        "finding_id": "F-001",
        "finding": f"{evidence.finding} at {evidence.equipment}",
        "inspection_evidence": evidence.model_dump(),
        "sop_evidence": sop.model_dump(),
        "ai_analysis": analysis.model_dump(),
        "calculation": calculation_data,
    }
