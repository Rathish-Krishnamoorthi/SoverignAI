import os
import uuid
import json
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
DATA_ROOT = ROOT.parent / "data"
DOCUMENT_ROOT = DATA_ROOT / "documents"
PROCESSED_ROOT = DATA_ROOT / "processed"
LOG_ROOT = DATA_ROOT / "logs" / "audit"

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.models.schemas import AnalysisResponse, DocumentRecord, ReviewRequest
from backend.modules.approval import generate_approval_note
from backend.modules.audit import add_event
from backend.modules.document_parser import extract_evidence
from backend.modules.evidence_chain import build_chain
from backend.modules.evidence_extractor import build_query
from backend.modules.embeddings import embed
from backend.modules.llm import LocalLLM, ModelCapability
from backend.modules.ocr import extract_document, ocr_runtime_health
from backend.modules.pipeline import build_pipeline
from backend.modules.rag import retrieve_sop
from backend.modules.sovereignty import status as sovereignty_status
from backend.modules.verification import verify_threshold
from backend.db import SessionLocal, database_health, init_db
from backend.modules.storage import ObjectStorage
from backend.modules.auth import authenticate_user, bootstrap_admin, create_local_user, create_token, current_user, delete_local_user, list_local_users, require_role, can_access_project, reset_local_password, update_local_user, ROLES
from backend.models.db_models import AIAnalysis, AuditLog, Document, DocumentChunk, DocumentText, SystemSetting, User
from backend.modules.sop_api import router as sop_router, service as sop_service
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", DOCUMENT_ROOT))
GENERATED_DIR = Path(os.getenv("GENERATED_DIR", PROCESSED_ROOT))
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
AIR_GAPPED_MODE = os.getenv("AIR_GAPPED_MODE", "true").lower() == "true"
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
ALLOWED_MIME = {
    "application/pdf", "image/png", "image/jpeg", "image/webp", "image/bmp", "image/tiff",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain", "text/markdown", "text/csv", "application/json", "application/octet-stream",
}
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
for directory in (
    DOCUMENT_ROOT / "sops", DOCUMENT_ROOT / "manuals", DOCUMENT_ROOT / "reports",
    DOCUMENT_ROOT / "other", PROCESSED_ROOT / "text", PROCESSED_ROOT / "chunks",
    PROCESSED_ROOT / "embeddings", LOG_ROOT,
):
    directory.mkdir(parents=True, exist_ok=True)
LOG_DIR = LOG_ROOT
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
app.include_router(sop_router)

class AdminUserCreate(BaseModel):
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=200)
    roles: list[str] = Field(min_length=1, max_length=4)

class AdminUserUpdate(BaseModel):
    roles: list[str] | None = Field(default=None, max_length=4)
    is_active: bool | None = None

class AdminPasswordReset(BaseModel):
    password: str = Field(min_length=8, max_length=200)

class AdminSecurityUpdate(BaseModel):
    air_gapped_mode: bool | None = None
    audit_logging: bool | None = None
    session_timeout_hours: int | None = Field(default=None, ge=1, le=24)
    password_minimum_length: int | None = Field(default=None, ge=8, le=128)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
llm = LocalLLM()
storage = ObjectStorage()
init_db()
bootstrap_admin()
documents: dict[str, Path] = {}
document_records: dict[str, DocumentRecord] = {}
results: dict[str, AnalysisResponse] = {}
audit_log: dict[str, list[dict]] = {}
admin_audit_events: list[dict] = []
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


def persist_document_record(record: DocumentRecord, user: dict, path: Path) -> None:
    if not SessionLocal:
        return
    with SessionLocal() as session:
        user_row = session.query(User).filter(User.username == user.get("sub")).first()
        user_id = user_row.id if user_row else None
        existing = session.query(Document).filter(Document.document_id == record.document_id).first()
        values = {
            "document_id": record.document_id, "filename": record.filename,
            "original_filename": record.filename, "file_path": str(path),
            "document_type": path.suffix.lower().lstrip(".") or "other",
            "object_key": f"{record.document_id}/{record.filename}",
            "mime_type": "application/octet-stream", "size_bytes": record.size_bytes,
            "uploaded_by": user.get("sub"), "status": "UPLOADED", "version": "1.0",
            "sha256": "",
        }
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
        else:
            session.add(Document(**values))
        session.add(AuditLog(user_id=user_id, action="UPLOAD", resource_type="document",
                             resource_id=record.document_id, details={"filename": record.filename}))
        session.commit()


def persist_document_text(document_id: str, text: str, method: str, user: dict) -> None:
    (PROCESSED_ROOT / "text" / f"{document_id}.txt").write_text(text, encoding="utf-8")
    chunks = [part.strip() for part in text.split("\n\n") if part.strip()]
    (PROCESSED_ROOT / "chunks" / f"{document_id}.json").write_text(
        json.dumps([{"chunk_index": index, "chunk_text": chunk} for index, chunk in enumerate(chunks)], indent=2),
        encoding="utf-8",
    )
    (PROCESSED_ROOT / "embeddings" / f"{document_id}.json").write_text(
        json.dumps([embed(chunk) for chunk in chunks]), encoding="utf-8",
    )
    if not SessionLocal:
        return
    with SessionLocal() as session:
        user_row = session.query(User).filter(User.username == user.get("sub")).first()
        session.add(DocumentText(document_id=document_id, extracted_text=text, extraction_method=method))
        for index, chunk in enumerate(chunks):
            session.add(DocumentChunk(document_id=document_id, chunk_index=index, content=chunk))
        session.add(AuditLog(user_id=user_row.id if user_row else None, action="VIEW", resource_type="document",
                             resource_id=document_id, details={"operation": "text_extraction"}))
        session.commit()


def persist_audit(user: dict, action: str, resource_type: str, resource_id: str, details: dict | None = None) -> None:
    if not SessionLocal:
        return
    with SessionLocal() as session:
        user_row = session.query(User).filter(User.username == user.get("sub")).first()
        session.add(AuditLog(user_id=user_row.id if user_row else None, action=action, resource_type=resource_type,
                             resource_id=resource_id, details=details or {}))
        session.commit()

def record_admin_event(user: dict, action: str, resource: str, resource_id: str | None = None, details: str = "LOCAL") -> None:
    admin_audit_events.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": user.get("sub", "system"),
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "status": "SUCCESS",
        "details": details,
    })

def authorize_document(document_id: str, user: dict) -> None:
    """Apply the project/document boundary before touching document content."""
    record = document_records.get(document_id)
    if not record or document_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found.")
    # Legacy JSON records have no owner/project. They remain accessible for the
    # demo and are treated as unscoped during migration.
    if not can_access_project(user, getattr(record, "owner_id", None), getattr(record, "project_id", None)):
        raise HTTPException(status_code=403, detail="Document is outside the user's project access.")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "SOVEREIGN-X", "processing_mode": "DEMO" if DEMO_MODE else "LOCAL"}

@app.get("/api/health/ocr")
def ocr_health(run_test: bool = False) -> dict:
    return ocr_runtime_health(run_test=run_test)

@app.get("/health")
def root_health() -> dict:
    return health()

@app.post("/api/auth/token")
def auth_token(form: OAuth2PasswordRequestForm = Depends()) -> dict:
    user = authenticate_user(form.username, form.password)
    if not user:
        record_admin_event({"sub": form.username.strip().lower()}, "LOGIN_FAILED", "authentication", details="Invalid local credentials")
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    record_admin_event(user, "LOGIN_SUCCESS", "authentication")
    return {"access_token": create_token(user["sub"], user["roles"]), "token_type": "bearer", "user": user}

@app.get("/api/auth/me")
def auth_me(user: dict = Depends(current_user)) -> dict:
    if user.get("sub") == "admin@gmai.com" and os.getenv("ADMIN_EMAIL", "admin@gmail.com").strip().lower() == "admin@gmail.com":
        user = {**user, "sub": "admin@gmail.com"}
    return {"user": user}

@app.get("/api/admin/users")
def admin_users(user: dict = Depends(require_role("ADMIN"))) -> dict:
    permissions = {}
    if SessionLocal:
        from backend.models.db_models import Role
        with SessionLocal() as session:
            permissions = {role.name: sorted(permission.name for permission in role.permissions) for role in session.query(Role).all()}
    return {"users": list_local_users(), "roles": sorted(ROLES), "permissions": permissions}

@app.post("/api/admin/users")
def admin_create_user(payload: AdminUserCreate, user: dict = Depends(require_role("ADMIN"))) -> dict:
    try:
        created = create_local_user(payload.email, payload.password, payload.roles)
        record_admin_event(user, "USER_CREATED", created["username"], created["id"], ", ".join(created["roles"]))
        return {"user": created}
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.patch("/api/admin/users/{user_id}")
def admin_update_user(user_id: str, payload: AdminUserUpdate, user: dict = Depends(require_role("ADMIN"))) -> dict:
    try:
        current = next((item for item in list_local_users() if item["username"] == user.get("sub")), None)
        if current and user_id == current["id"] and payload.is_active is False:
            raise ValueError("You cannot disable your own administrator account.")
        updated = update_local_user(user_id, payload.roles, payload.is_active)
        record_admin_event(user, "ROLE_CHANGED" if payload.roles is not None else "USER_STATUS_CHANGED", updated["username"], user_id, ", ".join(updated["roles"]) if payload.roles is not None else ("ACTIVE" if updated["is_active"] else "DISABLED"))
        return {"user": updated}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/api/admin/users/{user_id}/reset-password")
def admin_reset_password(user_id: str, payload: AdminPasswordReset, user: dict = Depends(require_role("ADMIN"))) -> dict:
    try:
        updated = reset_local_password(user_id, payload.password)
        record_admin_event(user, "PASSWORD_RESET", updated["username"], user_id)
        return {"user": updated}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.delete("/api/admin/users/{user_id}")
def admin_delete_user(user_id: str, user: dict = Depends(require_role("ADMIN"))) -> dict:
    try:
        deleted = delete_local_user(user_id, next((item["id"] for item in list_local_users() if item["username"] == user.get("sub")), ""))
        record_admin_event(user, "USER_DELETED", deleted["username"], user_id)
        return {"user": deleted}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/api/admin/audit")
def admin_audit(user: dict = Depends(require_role("ADMIN"))) -> list[dict]:
    events = list(admin_audit_events)
    for document_id, records in audit_log.items():
        for record in records:
            events.append({
                "timestamp": record.get("timestamp"),
                "user": record.get("user", "system"),
                "action": record.get("action", "UNKNOWN"),
                "resource": record.get("document") or document_id,
                "resource_id": document_id,
                "status": "SUCCESS",
                "details": record.get("execution", "LOCAL"),
            })
    for record_id, records in sop_service.audit.items():
        for record in records:
            events.append({
                "timestamp": record.get("timestamp"),
                "user": record.get("user", "system"),
                "action": record.get("action", "UNKNOWN"),
                "resource": record.get("sop_id", record_id),
                "resource_id": record_id,
                "status": "SUCCESS",
                "details": record.get("status", "LOCAL"),
            })
    return sorted(events, key=lambda item: item.get("timestamp") or "", reverse=True)

@app.get("/api/admin/security")
def admin_security(user: dict = Depends(require_role("ADMIN"))) -> dict:
    settings = _security_settings()
    return {
        **settings,
        "local_identity_store": bool(SessionLocal),
        "secrets_exposed": False,
    }

def _security_settings() -> dict:
    defaults = {
        "air_gapped_mode": AIR_GAPPED_MODE,
        "audit_logging": True,
        "session_timeout_hours": 8,
        "password_minimum_length": 8,
    }
    if not SessionLocal:
        return defaults
    with SessionLocal() as session:
        for key, value in defaults.items():
            setting = session.query(SystemSetting).filter(SystemSetting.key == key).first()
            if setting:
                if isinstance(value, bool):
                    defaults[key] = setting.value.lower() == "true"
                else:
                    defaults[key] = int(setting.value)
        return defaults

@app.put("/api/admin/security")
def update_admin_security(payload: AdminSecurityUpdate, user: dict = Depends(require_role("ADMIN"))) -> dict:
    values = payload.model_dump(exclude_none=True)
    if not SessionLocal:
        raise HTTPException(status_code=503, detail="Persistent settings storage is unavailable.")
    with SessionLocal() as session:
        for key, value in values.items():
            setting = session.query(SystemSetting).filter(SystemSetting.key == key).first()
            if not setting:
                setting = SystemSetting(key=key, value=str(value))
                session.add(setting)
            else:
                setting.value = str(value)
        session.commit()
    record_admin_event(user, "SECURITY_CONFIGURATION_CHANGED", "system_settings", details=", ".join(values))
    return admin_security(user)

@app.get("/api/admin/status")
def admin_status(user: dict = Depends(require_role("ADMIN"))) -> dict:
    database = database_health()
    storage_state = storage.health()
    llm_state = llm.status()
    return {
        "api": {"status": "ok", "service": "SOVEREIGN-X"},
        "database": database,
        "storage": storage_state,
        "vector_database": {"status": "ok" if database.get("status") == "ok" else "unavailable", "database": database.get("database")},
        "llm": llm_state,
        "ocr": {"status": "ok", "provider": "local PyMuPDF/Tesseract"},
        "authentication": {"status": "ok", "provider": "local JWT"},
        "air_gapped_mode": _security_settings()["air_gapped_mode"],
    }

@app.get("/health/database")
def health_database() -> dict:
    return database_health()

@app.get("/health/storage")
def health_storage() -> dict:
    return storage.health()

@app.get("/health/llm")
def health_llm() -> dict:
    return llm.status()


@app.get("/api/status")
def system_status() -> dict:
    """Single status payload for operators and the frontend."""
    llm_state = llm.status()
    return {
        "service": "SOVEREIGN-X",
        "processing_mode": "DEMO" if DEMO_MODE else "LOCAL",
        "llm": {**llm_state, "responsibility_matrix": llm.responsibility_matrix()},
        "sovereignty": sovereignty_status(llm_state.get("available", False)),
        "documents": len(document_records),
        "analyses": len(results),
    }


@app.get("/api/llm/status")
def llm_status() -> dict:
    state = llm.status()
    state["responsibility_matrix"] = llm.responsibility_matrix()
    return state

@app.post("/api/llm/modules/{capability}/toggle")
def toggle_llm_module(capability: str, enabled: bool, user: dict = Depends(require_role("ADMIN", "ENGINEER"))) -> dict:
    """Enable or disable one local model route for subsequent work."""
    try:
        return {"route": llm.set_enabled(capability, enabled)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.post("/api/llm/modules/{capability}/model")
def set_llm_module_model(capability: str, model: str, user: dict = Depends(require_role("ADMIN", "ENGINEER"))) -> dict:
    """Route one module to an installed local Ollama model."""
    try:
        return {"route": llm.set_model(capability, model)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/llm/models")
def llm_models() -> dict:
    """Expose configured local routes without exposing any cloud provider."""
    return {"provider": "ollama", "execution": "local", "models": llm.status().get("configured_models", [])}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...), user: dict = Depends(require_role("ADMIN", "ENGINEER", "OPERATOR"))) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    supported_suffixes = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".docx", ".txt", ".md", ".csv", ".json"}
    if suffix not in supported_suffixes or (file.content_type and file.content_type not in ALLOWED_MIME):
        raise HTTPException(status_code=400, detail="Unsupported file type. Upload PDF, DOCX, TXT, Markdown, CSV, JSON, or a PNG/JPG/TIFF/WEBP/BMP image.")
    document_id = str(uuid.uuid4())
    original_name = Path(file.filename or f"{document_id}{suffix}").name
    document_dir = UPLOAD_DIR / document_id
    document_dir.mkdir(parents=True, exist_ok=True)
    destination = document_dir / original_name
    payload = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(payload) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Upload exceeds {MAX_UPLOAD_BYTES} byte limit.")
    if not payload:
        raise HTTPException(status_code=400, detail="The uploaded document is empty.")
    destination.write_bytes(payload)
    storage.put(f"{document_id}/{original_name}", payload, file.content_type or "application/octet-stream")
    documents[document_id] = destination
    document_records[document_id] = DocumentRecord(
        document_id=document_id,
        filename=original_name,
        size_bytes=destination.stat().st_size,
        uploaded_at=datetime.now(timezone.utc).isoformat(),
        owner_id=user.get("sub") if user.get("sub") != "demo" else None,
    )
    persist_document_record(document_records[document_id], user, destination)
    save_document_index()
    add_event(audit_log, document_id, "DOCUMENT_UPLOADED", original_name)
    return {"document_id": document_id, "filename": original_name, "status": "uploaded"}


@app.get("/api/documents", response_model=list[DocumentRecord])
def list_documents(user: dict = Depends(current_user)) -> list[DocumentRecord]:
    return list(reversed(list(document_records.values())))


@app.post("/api/documents/upload")
async def upload_document_alias(file: UploadFile = File(...), user: dict = Depends(require_role("ADMIN", "ENGINEER", "OPERATOR"))) -> dict:
    return await upload(file, user)


@app.get("/api/documents/{document_id}", response_model=DocumentRecord)
def get_document(document_id: str, user: dict = Depends(current_user)) -> DocumentRecord:
    authorize_document(document_id, user)
    return document_records[document_id]


@app.get("/api/documents/{document_id}/download")
def download_document(document_id: str, user: dict = Depends(current_user)) -> FileResponse:
    authorize_document(document_id, user)
    path = documents[document_id]
    persist_audit(user, "DOWNLOAD", "document", document_id, {"filename": path.name})
    return FileResponse(path, filename=path.name, media_type="application/octet-stream")


@app.delete("/api/documents/{document_id}")
def delete_document(document_id: str, user: dict = Depends(require_role("ADMIN", "ENGINEER"))) -> dict:
    authorize_document(document_id, user)
    path = documents.get(document_id)
    record = document_records.get(document_id)
    if not path or not record:
        raise HTTPException(status_code=404, detail="Document not found.")
    document_dir = UPLOAD_DIR / document_id
    import shutil

    if document_dir.exists():
        shutil.rmtree(document_dir)
    generated_dir = GENERATED_DIR / document_id
    if generated_dir.exists():
        shutil.rmtree(generated_dir)
    for processed_file in (
        PROCESSED_ROOT / "text" / f"{document_id}.txt",
        PROCESSED_ROOT / "chunks" / f"{document_id}.json",
        PROCESSED_ROOT / "embeddings" / f"{document_id}.json",
    ):
        if processed_file.exists():
            processed_file.unlink()
    documents.pop(document_id, None)
    document_records.pop(document_id, None)
    results.pop(document_id, None)
    audit_log.pop(document_id, None)
    persist_audit(user, "DELETE", "document", document_id)
    if SessionLocal:
        with SessionLocal() as session:
            db_record = session.query(Document).filter(Document.document_id == document_id).first()
            if db_record:
                session.delete(db_record)
            session.commit()
    save_document_index()
    return {"document_id": document_id, "status": "deleted"}


@app.get("/api/documents/{document_id}/inspection")
def inspect_document(document_id: str, user: dict = Depends(require_role("ADMIN", "ENGINEER", "ANALYST", "OPERATOR"))) -> dict:
    authorize_document(document_id, user)
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
        persist_document_text(document_id, text, "local_ocr_and_text_parser", user)
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
            "recommended_format": (
                "Supported local formats: PDF, DOCX, TXT, Markdown, CSV, JSON, PNG, JPG, TIFF, WEBP, and BMP. "
                "Images and scanned PDFs require PaddleOCR with a local PaddlePaddle runtime."
            ),
        }


@app.post("/api/analyze/{document_id}", response_model=AnalysisResponse)
def analyze(document_id: str, user: dict = Depends(require_role("ADMIN", "ENGINEER", "ANALYST"))) -> AnalysisResponse:
    authorize_document(document_id, user)
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
                raise HTTPException(status_code=503, detail="LOCAL MODEL UNAVAILABLE: configured Ollama models could not be reached.")
            vision_route = next(route for route in llm.status()["routes"] if route["capability"] == "vision")
            if not vision_route["enabled"]:
                raise HTTPException(status_code=409, detail="The vision model route is inactive. Enable it from the model dashboard.")
            llm.set_working(ModelCapability.VISION, True)
            try:
                analysis = llm.analyze(evidence, sop)
            finally:
                llm.set_working(ModelCapability.VISION, False)
            mode = "LOCAL"
        add_event(audit_log, document_id, "LLM_ANALYSIS_COMPLETED", structured.document)
        for route in llm.responsibility_matrix():
            add_event(audit_log, document_id, f"MODEL_ROUTE_{route['capability'].upper()}", structured.document)
            audit_log[document_id][-1].update(route)
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
            pipeline=build_pipeline(analysis.model, mode, llm.responsibility_matrix()),
            provenance={
                "source": {"document": evidence.document, "page": evidence.page, "photo": evidence.photo},
                "sop": {"document": sop.document, "section": sop.section, "page": sop.page},
                "calculation_authority": "Python",
                "inference": chain["ai_analysis"]["provenance"],
                "responsibility_matrix": llm.responsibility_matrix(),
            },
        )
        results[document_id] = result
        if SessionLocal:
            with SessionLocal() as session:
                db_record = session.query(Document).filter(Document.document_id == document_id).first()
                if db_record:
                    db_record.status = "ANALYZED"
                session.add(AIAnalysis(
                    document_id=document_id, analysis_type="engineering",
                    result=analysis.model_dump(), model_name=analysis.model,
                    confidence_score=analysis.confidence,
                ))
                session.commit()
        persist_audit(user, "ANALYZE", "document", document_id, {"model": analysis.model})
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
def document_logs(document_id: str, user: dict = Depends(require_role("ADMIN", "AUDITOR", "ENGINEER"))) -> dict:
    authorize_document(document_id, user)
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
def evidence(document_id: str, user: dict = Depends(require_role("ADMIN", "AUDITOR", "ENGINEER", "ANALYST"))) -> dict:
    authorize_document(document_id, user)
    if document_id not in results:
        raise HTTPException(status_code=404, detail="No analysis found for this document.")
    return results[document_id].model_dump()


@app.post("/api/approval/{document_id}")
def approval(document_id: str, user: dict = Depends(require_role("ADMIN", "ENGINEER"))) -> dict:
    authorize_document(document_id, user)
    result = results.get(document_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analyze the document before generating an approval note.")
    path = generate_approval_note(result, GENERATED_DIR / document_id)
    add_event(audit_log, document_id, "APPROVAL_NOTE_GENERATED", result.finding.document)
    return {"filename": path.name, "download_url": f"/api/approval/{document_id}/download"}


@app.get("/api/approval/{document_id}/download")
def download_approval(document_id: str, user: dict = Depends(require_role("ADMIN", "ENGINEER", "ANALYST", "AUDITOR"))) -> FileResponse:
    authorize_document(document_id, user)
    path = GENERATED_DIR / document_id / "Approval_Note.docx"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Approval note has not been generated.")
    return FileResponse(path, filename="Approval_Note.docx")


@app.post("/api/review/{document_id}")
def review(document_id: str, request: ReviewRequest, user: dict = Depends(require_role("ADMIN", "ENGINEER"))) -> dict:
    authorize_document(document_id, user)
    if document_id not in results:
        raise HTTPException(status_code=404, detail="Analyze the document before reviewing it.")
    add_event(audit_log, document_id, "ENGINEER_REVIEWED", results[document_id].finding.document)
    audit_log[document_id][-1]["review_action"] = request.action
    return {"status": "recorded", "action": request.action}


@app.get("/api/audit/{document_id}")
def audit(document_id: str, user: dict = Depends(require_role("ADMIN", "AUDITOR", "ENGINEER"))) -> list[dict]:
    authorize_document(document_id, user)
    return audit_log.get(document_id, [])


@app.get("/api/sovereignty")
def sovereignty() -> dict:
    return sovereignty_status(llm.status()["available"])
