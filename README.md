# SOVEREIGN-X

SOVEREIGN-X is a local engineering document intelligence workbench for the SIH 2026 MRPL prototype. It turns a confidential inspection report into a traceable finding, retrieves the applicable synthetic SOP, asks a local Qwen2.5-VL model for contextual reasoning, independently verifies the measurement in Python, and produces an engineer-reviewable approval note.

## Architecture

```text
Upload → PaddleOCR → Evidence Extraction → BGE-M3 / ChromaDB
       → Local multi-LLM registry / Ollama → Python Verification
       → Evidence Chain → Engineer Review → DOCX Approval Note
```

The repository defaults to `DEMO_MODE=true`, so a live demonstration is deterministic and does not falsely claim that OCR or an LLM ran. Set `DEMO_MODE=false` to require the local OCR and Ollama pipeline. No cloud AI provider is used.

The local orchestration registry routes six specialized responsibilities to
independently configured Ollama tags: document extraction, vision analysis, SOP
interpretation, engineering reasoning, report summarization, and approval drafting.
If any required local model is unavailable, live analysis fails closed; there is no
cloud fallback. Python remains authoritative for numerical verification and BGE-M3
remains separate for semantic retrieval.

## Run locally

### Backend

```powershell
cd "d:\VS code\SoverignAI"
.\.venv-ocr312\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
```

Copy `.env.example` to `.env`. For local inference, install Ollama and run:

```powershell
ollama pull qwen2.5vl:3b
```

Then set `DEMO_MODE=false`. Ollama is checked at `GET /api/llm/status`; if unavailable, the API returns a clear local-model error rather than using a cloud fallback. The Ollama registry uses `qwen2.5vl` (not `qwen2-vl`); `:3b` is the recommended starting tag for a laptop.

On CPU-heavy laptops, first inference can take several minutes while the model loads. `OLLAMA_TIMEOUT_SECONDS=600` prevents the API from abandoning a valid local inference too early. This setup uses `OLLAMA_NUM_GPU=0` to avoid CUDA driver/toolchain issues; remove or increase it after updating your compatible GPU runtime.

For full local OCR, embeddings, and ChromaDB retrieval, install the optional packages on a machine with the required native build/runtime support. PaddleOCR and PaddlePaddle are both included so image and scanned-PDF extraction can run locally without a cloud OCR service:

```powershell
pip install -r backend\requirements-optional.txt
```

Document intake supports PDF, DOCX, TXT, Markdown, CSV, JSON, PNG, JPG/JPEG,
WEBP, BMP, and TIFF. Text-layer PDFs and text-native documents are parsed
locally. Images and scanned PDFs use PaddleOCR first; Tesseract is only a
fallback for image OCR. In an air-gapped deployment, stage the dependency
wheels and PaddleOCR model files on the internal artifact repository before
disconnecting the host from the Internet. PaddleOCR may otherwise attempt to
download model assets on first use, so pre-cache those assets for a fully
offline startup.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Select a supported local document and use
**Analyze Report** for local extraction/OCR plus Qwen2.5-VL analysis. **Run
Demo Mode** remains available as a deterministic fallback. The demo scenario
is explicitly synthetic: Flange B-12, pitting corrosion, 2.0 mm versus the
SOP-MRPL-INS-04 §4.3 limit of 1.5 mm.

Check the backend before uploading:

```powershell
Invoke-RestMethod http://127.0.0.1:8001/api/health
Invoke-RestMethod http://127.0.0.1:8001/api/llm/status
```

Backend diagnostics are written to `backend\logs\sovereign-x.log`. The UI's Audit Timeline also shows the diagnostic entries for the selected document. An OCR-complete message followed by an extraction error means the PDF was readable but did not contain the required `Equipment:`, `Finding:`, and `Pit depth measured at <number> mm` labels.

### Docker Compose

```powershell
docker compose up --build
```

Ollama intentionally remains on the host for a reliable laptop demonstration.

## API

`GET /api/health`, `GET /api/status`, `GET /api/llm/status`, `GET /api/llm/models`, `POST /api/upload`, `POST /api/analyze/{document_id}`, `GET /api/evidence/{document_id}`, `POST /api/approval/{document_id}`, `GET /api/approval/{document_id}/download`, `POST /api/review/{document_id}`, `GET /api/audit/{document_id}`, and `GET /api/sovereignty`.

### SOP management

The **SOP Library** is a local-only controlled knowledge module. Uploads accept
PDF and DOCX files, write the original object under
`sops/{sop_id}/{version}/{filename}` through MinIO (or the demo filesystem
fallback), extract text locally, create local embedding vectors, and retain
source page/chunk metadata. No public repository, cloud OCR, cloud storage, or
external embedding endpoint is used.

The lifecycle is:

```text
UPLOADED → UNDER_REVIEW → APPROVED → ACTIVE → SUPERSEDED → ARCHIVED
```

Only approved/active SOPs are returned by operational search and RAG. Activating
a new version automatically marks the prior active version `SUPERSEDED`; it is
never deleted. Every view, upload, approval, activation, and supersede action is
recorded in the local SOP audit trail. Access is authenticated through the
existing JWT/RBAC dependency and restricted to the uploader plus `ADMIN` and
`AUDITOR` roles until project/plant permissions are connected to the production
repository.

SOP endpoints include `POST /api/sops`, `GET /api/sops`, `GET
/api/sops/{id}`, `GET /api/sops/{id}/versions`, `POST
/api/sops/{id}/submit-review`, `POST /api/sops/{id}/approve`, `POST
/api/sops/{id}/activate`, `POST /api/sops/search`, `POST /api/sops/rag/query`,
and `GET /api/sops/{id}/audit`. RAG responses return SOP ID, version, status,
section, page, and chunk identifiers and explicitly state when no approved
supporting procedure is available. The local LLM is advisory only; operators
remain responsible for authorized execution.

## Sovereign-X local production architecture

The production compose stack uses SQLite, the local filesystem, Ollama, an
offline worker, backend, and frontend. All structured data is stored in
`data/sovereign.db`; original documents are stored below
`data/documents/{sops,manuals,reports,other}`; extracted text, chunks, and
embeddings are stored below `data/processed`; and audit logs are stored below
`data/logs/audit`. MinIO, PostgreSQL, and cloud APIs are not required or used.

`AIR_GAPPED_MODE=true` rejects non-local Ollama endpoints and logs attempted
external network targets. Uploads enforce MIME, extension, empty-file, and
`MAX_UPLOAD_BYTES` limits. JWT plus Argon2/bcrypt hashing and roles
`ADMIN`, `ENGINEER`, `ANALYST`, `OPERATOR`, and `AUDITOR` are provided for
production routes. Health probes are `/health`, `/health/database`,
`/health/storage`, and `/health/llm` (legacy `/api` endpoints remain unchanged).

### Backup and restore

Back up the `data` directory as one unit so SQLite metadata and local documents
remain consistent. Never place real credentials in `.env.example`; copy it to
`.env` and set long random passwords/secrets. Before disconnecting the host from
the network, install the pinned dependencies and pull the configured Ollama model
locally, for example `ollama pull qwen2.5vl:3b`.

### Local administrator and role-aware UI

On first database initialization, the backend creates the local administrator
from `ADMIN_EMAIL` and `ADMIN_PASSWORD`. The development defaults are
`admin@gmail.com` and `admin123`; replace them before production deployment.
The administrator receives the `ADMIN` role and can see the Access Control
module and local model-routing controls. Other authenticated roles see the
normal engineering workspace, while FastAPI RBAC remains the authoritative
enforcement layer for protected operations.
