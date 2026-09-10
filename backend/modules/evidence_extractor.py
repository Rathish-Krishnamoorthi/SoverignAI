from backend.models.schemas import InspectionEvidence


def build_query(evidence: InspectionEvidence) -> str:
    return f"{evidence.finding} at {evidence.equipment}; measured {evidence.measurement} mm"

