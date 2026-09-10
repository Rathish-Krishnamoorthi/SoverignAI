import os
import uuid
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.models.schemas import AnalysisResponse, DocumentRecord, ReviewRequest
from backend.modules.approval import generate_approval_note
from backend.modules.audit import add_event
from backend.modules.document_parser import extract_evidence
from backend.modules.evidence_chain import build_chain
from backend.modules.evidence_extractor import build_query
from backend.modules.llm import LocalLLM
from backend.modules.ocr import extract_document
from backend.modules.rag import retrieve_sop
from backend.modules.sovereignty import status as sovereignty_status
from backend.modules.verification import verify_threshold

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", ROOT / "uploads"))
GENERATED_DIR = Path(os.getenv("GENERATED_DIR", ROOT / "generated"))
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR = ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logger = logging.getLogger("sovereign_x")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = RotatingFileHandler(
        LOG_DIR / "sovereign-x.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)

app = FastAPI(title="SOVEREIGN-X", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
llm = LocalLLM()
documents: dict[str, Path] = {}
document_records: dict[str, DocumentRecord] = {}
results: dict[str, AnalysisResponse] = {}
audit_log: dict[str, list[dict]] = {}
DOCUMENT_INDEX = UPLOAD_DIR / "documents.json"
if DOCUMENT_INDEX.exists():
    for raw in json.loads(DOCUMENT_INDEX.read_text(encoding="utf-8")):
        record = DocumentRecord.model_validate(raw)
        document_records[record.document_id] = record
        candidate = UPLOAD_DIR / record.document_id / record.filename
        if candidate.exists():
            documents[record.document_id] = candidate


def save_document_index() -> None:
    DOCUMENT_INDEX.write_text(
        json.dumps([record.model_dump() for record in document_records.values()], indent=2),
        encoding="utf-8",
    )


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "SOVEREIGN-X", "processing_mode": "DEMO" if DEMO_MODE else "LOCAL"}


@app.get("/api/llm/status")
def llm_status() -> dict:
    return llm.status()


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".png", ".jpg", ".jpeg"}:
        raise HTTPException(status_code=400, detail="Unsupported file type. Upload a PDF, PNG, or JPG.")
    document_id = str(uuid.uuid4())
    original_name = Path(file.filename or f"{document_id}{suffix}").name
    document_dir = UPLOAD_DIR / document_id
    document_dir.mkdir(parents=True, exist_ok=True)
    destination = document_dir / original_name
    destination.write_bytes(await file.read())
    documents[document_id] = destination
    document_records[document_id] = DocumentRecord(
        document_id=document_id,
        filename=original_name,
        size_bytes=destination.stat().st_size,
        uploaded_at=datetime.now(timezone.utc).isoformat(),
    )
    save_document_index()
    add_event(audit_log, document_id, "DOCUMENT_UPLOADED", original_name)
    return {"document_id": document_id, "filename": original_name, "status": "uploaded"}


@app.get("/api/documents", response_model=list[DocumentRecord])
def list_documents() -> list[DocumentRecord]:
    return list(reversed(list(document_records.values())))


@app.delete("/api/documents/{document_id}")
def delete_document(document_id: str) -> dict:
    path = documents.get(document_id)
    record = document_records.get(document_id)
    if not path or not record:
        raise HTTPException(status_code=404, detail="Document not found.")
    document_dir = UPLOAD_DIR / document_id
    import shutil

    shutil.rmtree(document_dir, ignore_errors=False)
    generated_dir = GENERATED_DIR / document_id
    if generated_dir.exists():
        shutil.rmtree(generated_dir, ignore_errors=False)
    documents.pop(document_id, None)
    document_records.pop(document_id, None)
    results.pop(document_id, None)
    audit_log.pop(document_id, None)
    save_document_index()
    return {"document_id": document_id, "status": "deleted"}


@app.get("/api/documents/{document_id}/inspection")
def inspect_document(document_id: str) -> dict:
    path = documents.get(document_id)
    record = document_records.get(document_id)
    if not path or not record:
        raise HTTPException(status_code=404, detail="Document not found.")
    try:
        logger.info("document_id=%s stage=ocr_start filename=%s", document_id, record.filename)
        structured = extract_document(path, False)
        logger.info(
            "document_id=%s stage=ocr_complete pages=%d characters=%d",
            document_id,
            len(structured.pages),
            sum(len(page.text) for page in structured.pages),
        )
        text = "\n".join(page.text for page in structured.pages)
        try:
            extracted = extract_evidence(structured).model_dump()
            message = "OCR and engineering field extraction completed successfully."
            record.extraction_status = "success"
            record.extraction_message = message
            diagnostics = []
        except ValueError as exc:
            extracted = {}
            message = str(exc)
            record.extraction_status = "failed"
            record.extraction_message = message
            diagnostics = [message]
        record.analyzed = document_id in results
        save_document_index()
        return {
            "document_id": document_id,
            "filename": record.filename,
            "ocr_status": "success",
            "pages": len(structured.pages),
            "characters": len(text),
            "extracted_fields": extracted,
            "issues": diagnostics,
            "recommended_format": (
                "PDF with a searchable text layer, or a clear 300 DPI scanned PDF/image. "
                "Use labels Equipment, Finding, and Pit depth measured at <number> mm."
            ),
        }
    except (ValueError, RuntimeError) as exc:
        logger.exception("document_id=%s stage=inspection_failed error=%s", document_id, exc)
        record.extraction_status = "failed"
        record.extraction_message = str(exc)
        save_document_index()
        return {
            "document_id": document_id,
            "filename": record.filename,
            "ocr_status": "failed",
            "pages": 0,
            "characters": 0,
            "extracted_fields": {},
            "issues": [str(exc)],
            "recommended_format": "Use a valid PDF, PNG, or JPG. For scanned PDFs, install PaddleOCR optional dependencies.",
        }


@app.post("/api/analyze/{document_id}", response_model=AnalysisResponse)
def analyze(document_id: str) -> AnalysisResponse:
    path = documents.get(document_id)
    if not path:
        raise HTTPException(status_code=404, detail="Document not found. Upload a document first.")
    try:
        logger.info("document_id=%s stage=analysis_start filename=%s", document_id, path.name)
        structured = extract_document(path, DEMO_MODE)
        logger.info(
            "document_id=%s stage=ocr_complete pages=%d characters=%d",
            document_id,
            len(structured.pages),
            sum(len(page.text) for page in structured.pages),
        )
        add_event(audit_log, document_id, "OCR_COMPLETED", structured.document)
        evidence = extract_evidence(structured)
        if document_id in document_records:
            document_records[document_id].analyzed = True
            document_records[document_id].extraction_status = "success"
            document_records[document_id].extraction_message = "OCR and engineering field extraction completed successfully."
            save_document_index()
        add_event(audit_log, document_id, "EVIDENCE_EXTRACTED", structured.document)
        sop = retrieve_sop(build_query(evidence))
        add_event(audit_log, document_id, "SOP_RETRIEVED", structured.document)
        if DEMO_MODE:
            analysis = llm.demo_analysis(evidence)
            mode = "DEMO"
        else:
            if not llm.status()["available"]:
                raise HTTPException(status_code=503, detail="LOCAL MODEL UNAVAILABLE: Qwen2-VL could not be reached.")
            analysis = llm.analyze(evidence, sop)
            mode = "LOCAL"
        add_event(audit_log, document_id, "LLM_ANALYSIS_COMPLETED", structured.document)
        calculation = verify_threshold(evidence.measurement, sop.limit)
        add_event(audit_log, document_id, "CALCULATION_VERIFIED", structured.document)
        chain = build_chain(evidence, sop, analysis, calculation)
        add_event(audit_log, document_id, "EVIDENCE_CHAIN_CREATED", structured.document)
        result = AnalysisResponse(
            document_id=document_id,
            finding=evidence,
            inspection_evidence=evidence,
            sop_evidence=sop,
            ai_analysis=analysis,
            calculation=calculation,
            evidence_chain=chain,
            processing_mode=mode,
            pipeline=[
                {"stage": "OCR", "status": "complete"},
                {"stage": "Evidence Extraction", "status": "complete"},
                {"stage": "SOP Retrieval", "status": "complete"},
                {"stage": "Qwen2-VL", "status": "complete" if mode == "LOCAL" else "demo"},
                {"stage": "Python Verification", "status": "complete"},
                {"stage": "Evidence Chain", "status": "complete"},
            ],
        )
        results[document_id] = result
        return result
    except HTTPException:
        raise
    except (ValueError, RuntimeError) as exc:
        logger.exception("document_id=%s stage=analysis_failed error=%s", document_id, exc)
        if document_id in document_records:
            document_records[document_id].extraction_status = "failed"
            document_records[document_id].extraction_message = str(exc)
            save_document_index()
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/logs/{document_id}")
def document_logs(document_id: str) -> dict:
    if document_id not in document_records:
        raise HTTPException(status_code=404, detail="Document not found.")
    log_path = LOG_DIR / "sovereign-x.log"
    if not log_path.exists():
        return {"document_id": document_id, "log_file": str(log_path), "entries": []}
    entries = [
        line.rstrip()
        for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        if f"document_id={document_id}" in line
    ]
    return {"document_id": document_id, "log_file": str(log_path), "entries": entries[-100:]}


@app.get("/api/evidence/{document_id}")
def evidence(document_id: str) -> dict:
    if document_id not in results:
        raise HTTPException(status_code=404, detail="No analysis found for this document.")
    return results[document_id].model_dump()


@app.post("/api/approval/{document_id}")
def approval(document_id: str) -> dict:
    result = results.get(document_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analyze the document before generating an approval note.")
    path = generate_approval_note(result, GENERATED_DIR / document_id)
    add_event(audit_log, document_id, "APPROVAL_NOTE_GENERATED", result.finding.document)
    return {"filename": path.name, "download_url": f"/api/approval/{document_id}/download"}


@app.get("/api/approval/{document_id}/download")
def download_approval(document_id: str) -> FileResponse:
    path = GENERATED_DIR / document_id / "Approval_Note.docx"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Approval note has not been generated.")
    return FileResponse(path, filename="Approval_Note.docx")


@app.post("/api/review/{document_id}")
def review(document_id: str, request: ReviewRequest) -> dict:
    if document_id not in results:
        raise HTTPException(status_code=404, detail="Analyze the document before reviewing it.")
    add_event(audit_log, document_id, "ENGINEER_REVIEWED", results[document_id].finding.document)
    audit_log[document_id][-1]["review_action"] = request.action
    return {"status": "recorded", "action": request.action}


@app.get("/api/audit/{document_id}")
def audit(document_id: str) -> list[dict]:
    return audit_log.get(document_id, [])


@app.get("/api/sovereignty")
def sovereignty() -> dict:
    return sovereignty_status(llm.status()["available"])
