"""Authenticated SOP APIs backed by local storage and processing."""
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field

from backend.modules.auth import require_role
from backend.modules.sop_service import SOPService

router = APIRouter(prefix="/api/sops", tags=["sops"])
service = SOPService()


class SOPSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    include_historical: bool = False


@router.post("")
@router.post("/upload")
async def create_sop(
    file: UploadFile = File(...),
    sop_id: str = Form(...),
    version: str = Form(...),
    title: str = Form(""),
    description: str = Form(""),
    department: str = Form(""),
    plant: str = Form(""),
    unit: str = Form(""),
    equipment: str = Form(""),
    category: str = Form(""),
    revision_number: int = Form(1),
    classification: str = Form("INTERNAL"),
    source_location: str | None = Form(None),
    user: dict[str, Any] = Depends(require_role("ADMIN", "ENGINEER", "OPERATOR")),
) -> dict[str, Any]:
    try:
        payload = await file.read()
        record = service.create(payload, file.filename or "sop.pdf", file.content_type or "", {
            "sop_id": sop_id, "version": version, "title": title, "description": description,
            "department": department, "plant": plant, "unit": unit, "equipment": equipment,
            "category": category, "revision_number": revision_number, "classification": classification,
            "source_location": source_location,
        }, user)
        return record.public()
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("")
def list_sops(
    sop_id: str | None = None, title: str | None = None, department: str | None = None,
    plant: str | None = None, unit: str | None = None, status: str | None = None,
    user: dict[str, Any] = Depends(require_role("ADMIN", "ENGINEER", "ANALYST", "OPERATOR", "AUDITOR")),
) -> list[dict[str, Any]]:
    return service.list(user, {
        "sop_id": sop_id, "title": title, "department": department, "plant": plant,
        "unit": unit, "status": status,
    })


@router.get("/{record_id}")
def get_sop(record_id: str, user: dict[str, Any] = Depends(require_role("ADMIN", "ENGINEER", "ANALYST", "OPERATOR", "AUDITOR"))) -> dict[str, Any]:
    try:
        return service.get(record_id, user).public()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{record_id}/versions")
def sop_versions(record_id: str, user: dict[str, Any] = Depends(require_role("ADMIN", "ENGINEER", "ANALYST", "OPERATOR", "AUDITOR"))) -> list[dict[str, Any]]:
    try:
        return service.versions(record_id, user)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{record_id}/document")
def sop_document(record_id: str, user: dict[str, Any] = Depends(require_role("ADMIN", "ENGINEER", "ANALYST", "OPERATOR", "AUDITOR"))) -> Response:
    try:
        record, content = service.document(record_id, user)
        return Response(content=content, media_type=record.mime_type,
                        headers={"Content-Disposition": f'inline; filename="{record.file_name}"'})
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/search")
def search_sops(payload: SOPSearchRequest, user: dict[str, Any] = Depends(require_role("ADMIN", "ENGINEER", "ANALYST", "OPERATOR", "AUDITOR"))) -> list[dict[str, Any]]:
    return service.search(payload.query, user, payload.include_historical)


@router.post("/rag/query")
def rag_query(payload: SOPSearchRequest, user: dict[str, Any] = Depends(require_role("ADMIN", "ENGINEER", "ANALYST", "OPERATOR", "AUDITOR"))) -> dict[str, Any]:
    results = service.search(payload.query, user)
    if not results:
        return {
            "answer": "I could not find an approved SOP section supporting this procedure.",
            "grounded": False, "sources": [],
        }
    sources = [{
        "sop_id": item["sop"]["sop_id"], "title": item["sop"]["title"],
        "version": item["sop"]["version"], "status": item["sop"]["status"],
        "section": item["chunk"].get("section"), "page": item["chunk"].get("page_number"),
        "chunk_id": item["chunk"].get("id"),
    } for item in results if item.get("chunk")]
    excerpts = "\n\n".join(item["chunk"]["content"] for item in results if item.get("chunk"))
    return {
        "answer": f"According to the approved procedure:\n\n{excerpts}",
        "grounded": True, "sources": sources,
        "disclaimer": "Execution remains under authorized human/operator procedures.",
    }


@router.post("/{record_id}/{action}")
def transition_sop(record_id: str, action: str, user: dict[str, Any] = Depends(require_role("ADMIN", "ENGINEER", "SUPERVISOR", "AUDITOR"))) -> dict[str, Any]:
    try:
        return service.transition(record_id, action, user).public()
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{record_id}/audit")
def sop_audit(record_id: str, user: dict[str, Any] = Depends(require_role("ADMIN", "AUDITOR"))) -> list[dict[str, Any]]:
    try:
        return service.audit_for(record_id, user)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
