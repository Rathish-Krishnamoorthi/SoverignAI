# SOVEREIGN-X

SOVEREIGN-X is a local engineering document intelligence workbench for the SIH 2026 MRPL prototype. It turns a confidential inspection report into a traceable finding, retrieves the applicable synthetic SOP, asks a local Qwen2.5-VL model for contextual reasoning, independently verifies the measurement in Python, and produces an engineer-reviewable approval note.

## Architecture

```text
Upload → PaddleOCR → Evidence Extraction → BGE-M3 / ChromaDB
       → Qwen2.5-VL through Ollama → Python Verification
       → Evidence Chain → Engineer Review → DOCX Approval Note
```

The repository defaults to `DEMO_MODE=true`, so a live demonstration is deterministic and does not falsely claim that OCR or an LLM ran. Set `DEMO_MODE=false` to require the local OCR and Ollama pipeline. No cloud AI provider is used.

## Run locally

### Backend

```powershell
cd "d:\VS code\SoverignAI"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8001
```

Copy `.env.example` to `.env`. For local inference, install Ollama and run:

```powershell
ollama pull qwen2.5vl:3b
```

Then set `DEMO_MODE=false`. Ollama is checked at `GET /api/llm/status`; if unavailable, the API returns a clear local-model error rather than using a cloud fallback. The Ollama registry uses `qwen2.5vl` (not `qwen2-vl`); `:3b` is the recommended starting tag for a laptop.

On CPU-heavy laptops, first inference can take several minutes while the model loads. `OLLAMA_TIMEOUT_SECONDS=600` prevents the API from abandoning a valid local inference too early. This setup uses `OLLAMA_NUM_GPU=0` to avoid CUDA driver/toolchain issues; remove or increase it after updating your compatible GPU runtime.

For full local OCR, embeddings, and ChromaDB retrieval, install the optional packages on a machine with the required native build/runtime support:

```powershell
pip install -r backend\requirements-optional.txt
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Select a valid PDF/image and use **Analyze Report** for real OCR + Qwen2.5-VL analysis. **Run Demo Mode** remains available as a deterministic fallback. The demo scenario is explicitly synthetic: Flange B-12, pitting corrosion, 2.0 mm versus the SOP-MRPL-INS-04 §4.3 limit of 1.5 mm.

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

`GET /api/health`, `GET /api/llm/status`, `POST /api/upload`, `POST /api/analyze/{document_id}`, `GET /api/evidence/{document_id}`, `POST /api/approval/{document_id}`, `GET /api/approval/{document_id}/download`, `POST /api/review/{document_id}`, `GET /api/audit/{document_id}`, and `GET /api/sovereignty`.

## Scope and limitations

This prototype intentionally excludes authentication, enterprise workflow, predictive maintenance, IoT, cloud deployment, blockchain, and external AI services. PaddleOCR, BGE-M3, and ChromaDB are integrated with local fallbacks so the demo can remain reliable on a laptop when optional model assets are not already cached. The generated note is always an AI-generated draft and requires an engineer decision.
