from backend.modules.auth import current_user
from backend.modules.evidence_chain import build_chain
from backend.modules.llm import LocalLLM
from backend.modules.verification import verify_threshold
from backend.modules.ocr import extract_document
from backend.models.schemas import AIAnalysis, InspectionEvidence, SOPEvidence


def test_threshold_verification():
    assert verify_threshold(2.0, 1.5)["status"] == "EXCEEDS_LIMIT"
    assert verify_threshold(1.0, 1.5)["status"] == "WITHIN_LIMIT"


def test_demo_structured_output():
    evidence = InspectionEvidence(
        document="Inspection_Report.pdf", page=6, photo="Photo 3", equipment="Flange B-12",
        finding="Pitting corrosion", measurement=2.0,
    )
    analysis = LocalLLM.demo_analysis(evidence)
    assert analysis.recommendation == "Engineering assessment required."
    assert analysis.execution == "DEMO"


def test_evidence_chain_combines_sources():
    evidence = InspectionEvidence(
        document="Inspection_Report.pdf", page=6, photo="Photo 3", equipment="Flange B-12",
        finding="Pitting corrosion", measurement=2.0,
    )
    sop = SOPEvidence(document="SOP-MRPL-INS-04", section="4.3", page=12,
                      text="Pitting exceeding 1.5 mm requires engineering assessment.", limit=1.5)
    analysis = LocalLLM.demo_analysis(evidence)
    calculation = verify_threshold(2.0, 1.5)
    chain = build_chain(evidence, sop, analysis, calculation)
    assert set(chain) == {"finding_id", "finding", "inspection_evidence", "sop_evidence", "ai_analysis", "calculation"}


def test_invalid_pdf_has_actionable_error(tmp_path):
    path = tmp_path / "not-a-pdf.pdf"
    path.write_text("this is not a PDF", encoding="utf-8")
    try:
        extract_document(path, demo_mode=False)
    except ValueError as exc:
        assert "valid, uncorrupted PDF" in str(exc)
    else:
        raise AssertionError("Invalid PDF should be rejected")


def test_text_document_extraction(tmp_path):
    path = tmp_path / "inspection.txt"
    path.write_text("Equipment: Pump A-1\nFinding: Leak", encoding="utf-8")
    document = extract_document(path, demo_mode=False)
    assert document.pages[0].text == "Equipment: Pump A-1\nFinding: Leak"


def test_demo_mode_allows_unauthenticated_uploads(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    assert current_user(None) == {"sub": "demo", "roles": ["ADMIN"]}
