# SOVEREIGN-X

## SIH 2026 — MRPL Problem Statement 26117

### Complete Evidence Chain + Local Multimodal LLM Prototype

You are the lead full-stack AI engineer responsible for building a working prototype of **SOVEREIGN-X** for Smart India Hackathon 2026.

Your objective is to implement **one complete end-to-end vertical slice** of SOVEREIGN-X that can be demonstrated live to SIH judges.

Do NOT attempt to build the entire enterprise platform.

The prototype must focus on:

> **Confidential refinery inspection report → local OCR → local RAG → local multimodal LLM reasoning → deterministic Python verification → Evidence Chain → engineer review → Approval Note**

The system must be designed around **local/on-premise execution**.

---

# 1. PRODUCT VISION

SOVEREIGN-X is a sovereign, on-premise AI workbench that transforms confidential refinery documents into **evidence-backed engineering decisions**.

The engineer should be able to provide a task such as:

> "Analyze this inspection report against the applicable SOP, identify the relevant finding, verify the measurement against the permitted limit, and prepare an approval note."

SOVEREIGN-X should perform the workflow automatically.

The system should NOT behave like a generic chatbot.

It should behave like an:

> **Engineering Document Intelligence + Evidence Verification Workbench**

---

# 2. CORE PROTOTYPE

Build exactly this workflow:

```text
                 INSPECTION REPORT
                        │
                        ▼
                 DOCUMENT UPLOAD
                        │
                        ▼
                    PADDLEOCR
                        │
                        ▼
             STRUCTURED DOCUMENT
                        │
                        ▼
                 EVIDENCE EXTRACTION
                        │
                        ▼
                 BGE-M3 EMBEDDINGS
                        │
                        ▼
                    CHROMADB
                        │
                        ▼
                  RELEVANT SOP
                        │
                        ▼
                 QWEN2-VL / LLM
                 LOCAL REASONING
                        │
                        ▼
             STRUCTURED AI ANALYSIS
                        │
                        ▼
             PYTHON VERIFICATION
                        │
                        ▼
                 EVIDENCE CHAIN
                        │
                        ▼
                ENGINEER REVIEW
                        │
                        ▼
                APPROVAL NOTE
```

Every stage should be visible or traceable.

---

# 3. TECHNOLOGY STACK

Use:

## Frontend

* React
* Tailwind CSS
* Axios

## Backend

* Python
* FastAPI
* Pydantic

## OCR

* PaddleOCR

## Embeddings

* BGE-M3

## Vector Database

* ChromaDB

## Local Multimodal LLM

* Qwen2-VL
* Ollama

## Calculation Verification

* Python

## Document Generation

* python-docx

## Containerization

* Docker
* Docker Compose

---

# 4. LOCAL LLM IS MANDATORY

The prototype MUST integrate a real local Large Language Model.

The LLM must not be merely mentioned in the README.

It must participate in the actual analysis pipeline.

Preferred model:

```text
Qwen2-VL
```

Run locally using:

```text
Ollama
```

The architecture must support:

```text
Frontend
    ↓
FastAPI
    ↓
LLM abstraction
    ↓
Ollama
    ↓
Qwen2-VL
```

No cloud LLM may be used.

Do NOT use:

* OpenAI API
* Gemini API
* Claude API
* Azure OpenAI
* Hugging Face hosted inference
* any external AI inference API

---

# 5. RESPONSIBILITIES OF EACH AI COMPONENT

The architecture must clearly separate responsibilities.

## PaddleOCR

Responsible for:

> Understanding the document text.

It extracts:

* text
* page numbers
* tables where possible
* document structure
* image/photo references

---

## BGE-M3

Responsible for:

> Converting text into semantic embeddings.

---

## ChromaDB

Responsible for:

> Retrieving relevant SOP knowledge.

---

## Qwen2-VL

Responsible for:

> Multimodal contextual reasoning.

The LLM receives:

* inspection text
* extracted measurements
* retrieved SOP passages
* relevant inspection images where available

It determines:

* finding
* severity
* contextual interpretation
* recommendation
* confidence

---

## Python Verification

Responsible for:

> Deterministic numerical verification.

The LLM must NOT be treated as the authoritative calculator.

For example:

```text
Measured pit depth = 2.0 mm
Allowed limit = 1.5 mm
```

Python determines:

```text
2.0 > 1.5
```

and returns the authoritative result.

---

## Evidence Chain

Responsible for:

> Connecting the recommendation back to its supporting evidence.

---

# 6. DEMO SCENARIO

Create a synthetic demonstration scenario.

Clearly label it:

```text
DEMO / SYNTHETIC ENGINEERING DATA
```

Do NOT claim that synthetic documents are actual MRPL documents.

Use:

### Equipment

```text
Flange B-12
```

### Finding

```text
Pitting corrosion
```

### Measured pit depth

```text
2.0 mm
```

### Permitted threshold

```text
1.5 mm
```

### Inspection source

```text
Inspection_Report.pdf
Page 6
Photo 3
```

### Synthetic SOP

```text
SOP-MRPL-INS-04
Section 4.3
```

### Requirement

```text
Pitting exceeding 1.5 mm requires engineering assessment.
```

Therefore:

```text
2.0 mm > 1.5 mm
```

The final recommendation should be:

```text
Engineering assessment required.
```

---

# 7. PROJECT STRUCTURE

Create:

```text
sovereign-x/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── UploadPanel.jsx
│   │   │   ├── ProcessingPipeline.jsx
│   │   │   ├── FindingCard.jsx
│   │   │   ├── EvidenceChain.jsx
│   │   │   ├── EvidenceCard.jsx
│   │   │   ├── SOPEvidence.jsx
│   │   │   ├── CalculationVerification.jsx
│   │   │   ├── Recommendation.jsx
│   │   │   ├── ApprovalNote.jsx
│   │   │   ├── AuditTimeline.jsx
│   │   │   └── SovereigntyDashboard.jsx
│   │   │
│   │   ├── pages/
│   │   │   └── Dashboard.jsx
│   │   │
│   │   ├── services/
│   │   │   └── api.js
│   │   │
│   │   ├── App.jsx
│   │   └── main.jsx
│   │
│   ├── package.json
│   └── tailwind.config.js
│
├── backend/
│   ├── main.py
│   │
│   ├── modules/
│   │   ├── ocr.py
│   │   ├── document_parser.py
│   │   ├── evidence_extractor.py
│   │   ├── embeddings.py
│   │   ├── rag.py
│   │   ├── llm.py
│   │   ├── analysis.py
│   │   ├── verification.py
│   │   ├── evidence_chain.py
│   │   ├── approval.py
│   │   ├── audit.py
│   │   └── sovereignty.py
│   │
│   ├── models/
│   │   └── schemas.py
│   │
│   ├── knowledge_base/
│   │   └── sops/
│   │       └── demo_sop.txt
│   │
│   ├── uploads/
│   ├── generated/
│   ├── data/
│   │   ├── evidence/
│   │   └── chroma/
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── docker-compose.yml
└── README.md
```

---

# 8. DOCUMENT UPLOAD

Create an upload interface.

Supported:

```text
PDF
PNG
JPG
```

UI:

```text
CONFIDENTIAL ENGINEERING DOCUMENT

Drop inspection report here

PDF / PNG / JPG

[ Select Document ]
```

After upload:

```text
Inspection_Report.pdf

Uploaded ✓
```

Then:

```text
[ Analyze Report ]
```

---

# 9. OCR PIPELINE

Implement:

```text
PDF / Image
    ↓
PaddleOCR
    ↓
Page-level structured representation
```

Example:

```json
{
  "document": "Inspection_Report.pdf",
  "pages": [
    {
      "page": 6,
      "text": "Corrosion observed near Flange B-12. Pit depth measured at 2.0 mm.",
      "images": [
        {
          "photo_id": "photo_3"
        }
      ]
    }
  ]
}
```

Preserve source metadata.

Every extracted fact should be capable of pointing back to:

```text
Document
Page
Photo
```

---

# 10. DEMO MODE

Implement reliable Demo Mode.

Environment variable:

```text
DEMO_MODE=true
```

When Demo Mode is enabled, use deterministic synthetic inspection data.

The UI must clearly display:

```text
DEMO MODE
Synthetic Engineering Data
```

Do NOT falsely claim that the real OCR/LLM executed if Demo Mode is being used.

When Demo Mode is disabled, the real OCR and LLM pipeline must be used.

---

# 11. SOP KNOWLEDGE BASE

Create a synthetic SOP.

Example:

```text
SOP-MRPL-INS-04

Section 4.3

Pitting exceeding 1.5 mm requires engineering assessment.
```

Clearly label it:

```text
Synthetic Demo SOP
```

Store appropriate metadata:

```json
{
  "document": "SOP-MRPL-INS-04",
  "section": "4.3",
  "page": 12
}
```

---

# 12. RAG PIPELINE

Implement:

```text
SOP
 ↓
Chunking
 ↓
BGE-M3
 ↓
ChromaDB
```

At application startup or via an initialization command, index the synthetic SOP.

When the inspection report is analyzed:

```text
OCR evidence
      ↓
Search query
      ↓
BGE-M3
      ↓
ChromaDB
      ↓
Relevant SOP chunks
```

Return:

```json
{
  "document": "SOP-MRPL-INS-04",
  "section": "4.3",
  "page": 12,
  "text": "Pitting exceeding 1.5 mm requires engineering assessment."
}
```

---

# 13. LOCAL LLM MODULE

Create:

```text
backend/modules/llm.py
```

Do not place Ollama calls throughout the application.

Create a clean abstraction:

```python
class LocalLLM:

    def analyze(
        self,
        inspection_evidence,
        sop_context,
        images=None
    ):
        ...
```

The rest of the backend should call this class.

---

# 14. OLLAMA INTEGRATION

Configure:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2-vl
```

The application should call Ollama locally.

Implement connection checking.

For example:

```text
GET /api/llm/status
```

Return:

```json
{
  "available": true,
  "model": "qwen2-vl",
  "provider": "ollama",
  "execution": "local"
}
```

If unavailable:

```json
{
  "available": false,
  "model": "qwen2-vl",
  "execution": "local"
}
```

---

# 15. LLM PROMPTING

Do not send a vague prompt such as:

```text
Analyze this document.
```

Construct a structured engineering prompt.

Provide:

```text
ROLE:
You are a refinery engineering document analysis assistant.

TASK:
Analyze the inspection evidence using the retrieved SOP.

IMPORTANT:
Do not invent facts.
Use only supplied evidence and retrieved SOP context.
Do not perform unsupported numerical calculations.
Return structured JSON.
```

Then provide:

```text
INSPECTION EVIDENCE

Document:
Inspection_Report.pdf

Page:
6

Photo:
Photo 3

Equipment:
Flange B-12

Finding:
Pitting corrosion

Measured pit depth:
2.0 mm
```

Then:

```text
RETRIEVED SOP

Document:
SOP-MRPL-INS-04

Section:
4.3

Requirement:
Pitting exceeding 1.5 mm requires engineering assessment.
```

Ask the model to return:

```json
{
  "finding": "...",
  "severity": "...",
  "recommendation": "...",
  "confidence": "...",
  "reasoning_summary": "..."
}
```

The backend must validate the returned JSON.

---

# 16. DO NOT TRUST LLM NUMERICAL RESULTS

If the LLM says:

```text
2.0 mm exceeds 1.5 mm
```

do NOT accept that as the authoritative calculation.

Extract the numerical values.

Send them to:

```text
backend/modules/verification.py
```

Perform the calculation independently.

---

# 17. PYTHON VERIFICATION MODULE

Implement:

```python
def verify_threshold(measured: float, limit: float):
    exceeds = measured > limit

    return {
        "measured": measured,
        "limit": limit,
        "operator": ">",
        "expression": f"{measured} > {limit}",
        "result": exceeds,
        "status": (
            "EXCEEDS_LIMIT"
            if exceeds
            else "WITHIN_LIMIT"
        ),
        "verified_by": "Python"
    }
```

For the demo:

```text
Measured = 2.0
Limit = 1.5
```

Output:

```text
2.0 > 1.5

EXCEEDS_LIMIT
```

---

# 18. EVIDENCE CHAIN

Create:

```text
backend/modules/evidence_chain.py
```

The Evidence Chain must combine:

```text
Inspection Evidence
        +
SOP Evidence
        +
LLM Analysis
        +
Python Verification
        ↓
Evidence Chain
```

Example:

```json
{
  "finding_id": "F-001",

  "finding": "Pitting corrosion at Flange B-12",

  "inspection_evidence": {
    "document": "Inspection_Report.pdf",
    "page": 6,
    "photo": "Photo 3",
    "measurement": "2.0 mm"
  },

  "sop_evidence": {
    "document": "SOP-MRPL-INS-04",
    "section": "4.3",
    "page": 12,
    "limit": "1.5 mm"
  },

  "ai_analysis": {
    "model": "Qwen2-VL",
    "severity": "HIGH",
    "recommendation": "Engineering assessment required",
    "confidence": "HIGH"
  },

  "calculation": {
    "expression": "2.0 > 1.5",
    "result": true,
    "status": "EXCEEDS_LIMIT",
    "verified_by": "Python"
  }
}
```

---

# 19. EVIDENCE CHAIN UI

Make this the hero component of the application.

Show:

```text
ENGINEERING FINDING F-001

Pitting corrosion detected at Flange B-12

Severity
HIGH

Confidence
HIGH
```

Then:

```text
INSPECTION EVIDENCE

Inspection_Report.pdf
Page 6
Photo 3

Pit depth:
2.0 mm

[ View Source ]
```

Then:

```text
SOP EVIDENCE

SOP-MRPL-INS-04
Section 4.3

Permitted limit:
1.5 mm

[ View SOP ]
```

Then:

```text
AI ANALYSIS

Model:
Qwen2-VL

Execution:
LOCAL

Recommendation:
Engineering assessment required.
```

Then:

```text
VERIFIED CALCULATION

2.0 mm > 1.5 mm

✓ EXCEEDS LIMIT

Verified independently by Python
```

---

# 20. EVIDENCE GRAPH

Create a visual chain:

```text
Inspection Report
       │
       ▼
Page 6 / Photo 3
       │
       ▼
Pit Depth: 2.0 mm
       │
       ▼
Retrieved SOP §4.3
       │
       ▼
Limit: 1.5 mm
       │
       ▼
Python Verification
       │
       ▼
Qwen2-VL Analysis
       │
       ▼
Recommendation
```

The purpose is to visually communicate traceability.

---

# 21. APPROVAL NOTE

Use python-docx.

Endpoint:

```text
POST /api/approval/{document_id}
```

Generate:

```text
SOVEREIGN-X
ENGINEERING APPROVAL NOTE

Equipment:
Flange B-12

Finding:
Pitting corrosion detected.

Measured Value:
2.0 mm

Applicable Requirement:
SOP-MRPL-INS-04 §4.3

Permitted Limit:
1.5 mm

Verification:
2.0 mm > 1.5 mm

Verification Status:
EXCEEDS LIMIT

AI Recommendation:
Engineering assessment required.

Source Evidence:
Inspection Report — Page 6 — Photo 3

AI Model:
Qwen2-VL — Local

Confidence:
HIGH

Processing Mode:
LOCAL / OFFLINE

----------------------------------

AI-GENERATED DRAFT
ENGINEER REVIEW REQUIRED
```

The approval note must never claim that the AI has final approval authority.

---

# 22. ENGINEER REVIEW

The engineer must remain the final decision maker.

Provide:

```text
AI Recommendation

Engineering assessment required.

[ Accept Recommendation ]
[ Reject ]
[ Request Review ]
```

For the MVP, these actions can simply be recorded in the audit log.

Do NOT implement complex approval workflows.

---

# 23. AUDIT LOG

Record:

```text
DOCUMENT_UPLOADED
OCR_COMPLETED
EVIDENCE_EXTRACTED
SOP_RETRIEVED
LLM_ANALYSIS_COMPLETED
CALCULATION_VERIFIED
EVIDENCE_CHAIN_CREATED
APPROVAL_NOTE_GENERATED
ENGINEER_REVIEWED
```

Example:

```json
{
  "timestamp": "2026-09-07T19:00:00",
  "document": "Inspection_Report.pdf",
  "action": "CALCULATION_VERIFIED",
  "execution": "LOCAL"
}
```

Display these in a timeline.

---

# 24. SOVEREIGNTY DASHBOARD

Create:

```text
SOVEREIGNTY STATUS

Internet Calls       0
Cloud API Calls      0
Data Egress          0
External AI APIs     0

OCR                  LOCAL
Embeddings           LOCAL
Vector DB            LOCAL
LLM                  LOCAL

Qwen2-VL             ACTIVE
Ollama               ACTIVE

SYSTEM

● SOVEREIGN / OFFLINE
```

The application should maintain local telemetry for outbound requests.

Do not silently call external services.

---

# 25. API ENDPOINTS

Implement:

```text
GET  /api/health

GET  /api/llm/status

POST /api/upload

POST /api/analyze/{document_id}

GET  /api/evidence/{document_id}

POST /api/approval/{document_id}

GET  /api/audit/{document_id}

GET  /api/sovereignty
```

---

# 26. ANALYSIS ENDPOINT

The primary pipeline endpoint:

```text
POST /api/analyze/{document_id}
```

must execute:

```text
1. Load document
2. OCR
3. Extract evidence
4. Generate RAG query
5. Search ChromaDB
6. Retrieve SOP evidence
7. Send evidence + SOP to Qwen2-VL
8. Parse structured LLM result
9. Extract numerical values
10. Verify calculation using Python
11. Construct Evidence Chain
12. Save audit events
13. Return result
```

The response should contain:

```json
{
  "document_id": "...",
  "finding": {},
  "inspection_evidence": {},
  "sop_evidence": {},
  "ai_analysis": {},
  "calculation": {},
  "evidence_chain": {},
  "processing_mode": "LOCAL"
}
```

---

# 27. ERROR HANDLING

Handle:

* invalid files
* unsupported file types
* corrupted PDFs
* OCR failures
* empty OCR output
* ChromaDB failures
* missing SOP
* Ollama unavailable
* malformed LLM response
* invalid numerical values
* document generation errors

Show clear frontend error messages.

Never display a blank screen.

---

# 28. LLM FALLBACK

If Qwen2-VL is unavailable:

Display:

```text
LOCAL MODEL UNAVAILABLE

Qwen2-VL could not be reached.

[ Run Demo Mode ]
```

If Demo Mode is selected:

```text
DEMO MODE
Synthetic Engineering Data
```

Do NOT pretend that the local LLM ran.

---

# 29. FRONTEND DESIGN

The frontend should NOT resemble ChatGPT.

It should look like a professional industrial engineering workbench.

Use:

* dark technical interface
* clear status indicators
* cards
* evidence panels
* timeline
* pipeline visualization
* engineering terminology

Primary sections:

```text
HEADER
│
├── Sovereignty Status
│
├── Document Upload
│
├── Processing Pipeline
│
├── Engineering Finding
│
├── Evidence Chain
│
├── SOP Evidence
│
├── AI Analysis
│
├── Calculation Verification
│
├── Recommendation
│
├── Audit Timeline
│
└── Generate Approval Note
```

---

# 30. PRIMARY DEMO SCREEN

The final result should resemble:

```text
╔════════════════════════════════════════════════════╗
║                  SOVEREIGN-X                      ║
║       Sovereign Engineering Intelligence          ║
║                                                  ║
║  ● LOCAL / OFFLINE                               ║
╠════════════════════════════════════════════════════╣
║                                                  ║
║ ENGINEERING FINDING F-001                        ║
║                                                  ║
║ Pitting corrosion at Flange B-12                 ║
║                                                  ║
║ Severity       HIGH                              ║
║ Confidence     HIGH                              ║
║                                                  ║
╠════════════════════════════════════════════════════╣
║ INSPECTION EVIDENCE                              ║
║                                                  ║
║ Inspection_Report.pdf                            ║
║ Page 6                                          ║
║ Photo 3                                         ║
║ Pit depth: 2.0 mm                               ║
╠════════════════════════════════════════════════════╣
║ SOP EVIDENCE                                     ║
║                                                  ║
║ SOP-MRPL-INS-04                                 ║
║ Section 4.3                                     ║
║ Limit: 1.5 mm                                   ║
╠════════════════════════════════════════════════════╣
║ LOCAL AI ANALYSIS                                ║
║                                                  ║
║ Model: Qwen2-VL                                 ║
║ Runtime: Ollama                                 ║
║ Execution: LOCAL                                ║
║                                                  ║
║ Engineering assessment required.                ║
╠════════════════════════════════════════════════════╣
║ VERIFIED CALCULATION                             ║
║                                                  ║
║ 2.0 mm > 1.5 mm                                 ║
║                                                  ║
║ ✓ EXCEEDS LIMIT                                 ║
║ ✓ VERIFIED BY PYTHON                            ║
╠════════════════════════════════════════════════════╣
║ EVIDENCE CHAIN                                   ║
║                                                  ║
║ Page 6 → Photo 3 → 2.0 mm                       ║
║          ↓                                       ║
║ SOP §4.3 → 1.5 mm                               ║
║          ↓                                       ║
║ Python verification                             ║
║          ↓                                       ║
║ Qwen2-VL reasoning                               ║
║          ↓                                       ║
║ Engineering recommendation                      ║
╠════════════════════════════════════════════════════╣
║                                                  ║
║ [ Generate Approval Note ]                      ║
║                                                  ║
╠════════════════════════════════════════════════════╣
║ SOVEREIGNTY                                     ║
║                                                  ║
║ Internet Calls:     0                           ║
║ Cloud API Calls:    0                           ║
║ Data Egress:        0                           ║
║ Local AI:            ACTIVE                      ║
╚════════════════════════════════════════════════════╝
```

---

# 31. ENVIRONMENT CONFIGURATION

Create:

```text
.env.example
```

with:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2-vl

CHROMA_PATH=./data/chroma

UPLOAD_DIR=./uploads
GENERATED_DIR=./generated

DEMO_MODE=true
```

Do not commit actual `.env` secrets.

---

# 32. DOCKER

Create Docker configuration where practical.

The application should be capable of running locally using Docker Compose.

However, do NOT attempt to containerize Ollama in a way that makes GPU configuration unnecessarily complicated for the first prototype.

Prioritize a reliable local laptop demonstration.

---

# 33. HARDWARE AWARENESS

The local multimodal model can be computationally expensive.

Therefore:

* detect whether Ollama is available
* detect whether the configured model is available
* provide clear status
* allow Demo Mode fallback
* avoid crashing if inference is slow or unavailable

Do not silently replace Qwen2-VL with a cloud model.

---

# 34. SECURITY PRINCIPLES

Uploaded documents are confidential.

Therefore:

* process files locally
* don't upload files externally
* don't call external APIs
* don't expose uploaded files unnecessarily
* store temporary files locally
* provide cleanup where appropriate
* never log entire confidential documents unnecessarily

---

# 35. IMPORTANT DATA FLOW RULE

The LLM should receive only the relevant context.

Do not blindly send an entire large document to the model.

Use:

```text
OCR
 ↓
Relevant evidence extraction
 ↓
RAG retrieval
 ↓
Relevant SOP
 ↓
LLM
```

This reduces context size and improves traceability.

---

# 36. STRUCTURED OUTPUT

Use Pydantic schemas for LLM output.

Example:

```python
class AIAnalysis(BaseModel):
    finding: str
    severity: str
    recommendation: str
    confidence: str
    reasoning_summary: str
```

Reject malformed responses.

Where possible, use structured JSON output from the model.

---

# 37. TRACEABILITY RULE

Every major claim displayed to the engineer must have a source.

For example:

```text
Claim:
Pit depth = 2.0 mm

Source:
Inspection_Report.pdf
Page 6
Photo 3
```

And:

```text
Claim:
Limit = 1.5 mm

Source:
SOP-MRPL-INS-04
Section 4.3
```

And:

```text
Claim:
2.0 > 1.5

Verifier:
Python
```

And:

```text
Recommendation:
Engineering assessment required

Reason:
LLM contextual interpretation based on supplied evidence + SOP.
```

---

# 38. DO NOT BUILD

Do NOT implement:

* authentication
* user registration
* role management
* predictive maintenance
* process optimization
* IoT integration
* real-time sensor data
* blockchain
* multi-agent swarm
* Kubernetes
* cloud deployment
* external AI APIs
* complex enterprise administration
* engineering peer-review module
* large analytics dashboards

These are outside the prototype.

---

# 39. DEVELOPMENT PHASES

Build incrementally.

## Phase 1 — Project Foundation

Create:

* frontend
* backend
* basic API
* health endpoint
* dashboard

Test that both applications start.

---

## Phase 2 — Upload

Implement:

```text
POST /api/upload
```

Test PDF upload.

---

## Phase 3 — Demo Pipeline

Implement synthetic Demo Mode.

Make:

```text
Upload
 ↓
Analyze
 ↓
Evidence Chain
```

work before adding complex AI.

---

## Phase 4 — OCR

Integrate PaddleOCR.

Verify page-level extraction.

---

## Phase 5 — RAG

Integrate:

```text
BGE-M3
ChromaDB
```

Index the synthetic SOP.

Test retrieval independently.

---

## Phase 6 — Local LLM

Integrate:

```text
Ollama
Qwen2-VL
```

Test:

```text
inspection evidence
+
SOP context
↓
Qwen2-VL
↓
structured JSON
```

---

## Phase 7 — Verification

Implement Python calculation verification.

---

## Phase 8 — Evidence Chain

Combine:

```text
OCR
+
RAG
+
Qwen2-VL
+
Python
```

---

## Phase 9 — Approval Note

Generate DOCX.

---

## Phase 10 — Audit + Sovereignty

Implement:

* audit timeline
* local model status
* sovereignty dashboard

---

## Phase 11 — Integration

Connect everything.

---

## Phase 12 — Testing

Test the complete demo from beginning to end.

---

# 40. ACCEPTANCE CRITERIA

The prototype is complete ONLY when this exact flow works:

```text
1. Start SOVEREIGN-X

2. See:
   LOCAL / OFFLINE

3. Upload:
   Inspection_Report.pdf

4. Click:
   Analyze Report

5. OCR executes or clearly enters Demo Mode.

6. Finding:
   Pitting at Flange B-12

7. RAG retrieves:
   SOP-MRPL-INS-04 §4.3

8. Qwen2-VL executes locally when available.

9. Qwen2-VL produces structured analysis.

10. Python independently verifies:
    2.0 > 1.5

11. Evidence Chain is generated.

12. UI displays:
    Page 6
    Photo 3
    SOP §4.3
    Qwen2-VL
    Python verification

13. Engineer sees:
    Engineering assessment required.

14. Engineer can generate:
    Approval_Note.docx

15. Audit log records the workflow.

16. Sovereignty dashboard shows:
    Internet Calls: 0
    Cloud API Calls: 0
    Data Egress: 0
    Local AI: ACTIVE
```

---

# 41. TESTING

Create tests for:

### Verification

```text
2.0 > 1.5 → EXCEEDS_LIMIT
1.0 > 1.5 → WITHIN_LIMIT
```

### RAG

Verify that the correct SOP section is retrieved.

### LLM

Verify that structured output is parsed correctly.

### Evidence Chain

Verify that:

```text
inspection evidence
+
SOP evidence
+
AI analysis
+
calculation
```

are combined correctly.

### Approval

Verify that DOCX is generated.

### API

Test all primary endpoints.

---

# 42. README

The README must explain:

## What is SOVEREIGN-X?

## Problem being solved

## Prototype scope

## Architecture

```text
OCR
 ↓
RAG
 ↓
Qwen2-VL
 ↓
Python Verification
 ↓
Evidence Chain
 ↓
Approval Note
```

## Why local AI?

## Why RAG?

## Why multimodal AI?

## Why Python verification?

## Why Evidence Chain?

## How to install

## How to run Ollama

## How to configure Qwen2-VL

## How to start backend

## How to start frontend

## How to use Demo Mode

## Demo walkthrough

## Limitations

Clearly distinguish prototype functionality from production functionality.

---

# 43. FINAL PRODUCT MESSAGE

The prototype must communicate this:

> **SOVEREIGN-X does not ask engineers to blindly trust AI.**

Instead:

```text
The document provides evidence.
        ↓
RAG provides the applicable SOP.
        ↓
Qwen2-VL provides contextual reasoning.
        ↓
Python verifies numerical claims.
        ↓
Evidence Chain connects everything.
        ↓
Engineer makes the final decision.
```

Everything runs locally.

---

# 44. SIH DEMONSTRATION SCRIPT

The final application should support this live demo:

### Step 1

Show the sovereignty dashboard.

Say:

> "This is SOVEREIGN-X, an on-premise AI workbench designed for confidential refinery engineering work."

### Step 2

Upload the inspection report.

Say:

> "The engineer has received a confidential inspection report."

### Step 3

Click Analyze.

Show:

```text
OCR ✓
Evidence Extraction ✓
SOP Retrieval ✓
Qwen2-VL ✓
Python Verification ✓
Evidence Chain ✓
```

### Step 4

Show:

```text
Pitting at Flange B-12
```

### Step 5

Show the evidence:

```text
Page 6
Photo 3
2.0 mm
```

### Step 6

Show retrieved SOP:

```text
SOP §4.3
Limit: 1.5 mm
```

### Step 7

Show:

```text
2.0 > 1.5

✓ Python Verified
```

### Step 8

Show:

```text
Qwen2-VL
Local Analysis

Engineering assessment required.
```

### Step 9

Open the Evidence Chain.

Say:

> "The important part is that the recommendation is not a black box."

### Step 10

Generate the Approval Note.

Say:

> "The engineer receives an evidence-backed draft rather than an unsupported AI answer."

---

# 45. MOST IMPORTANT IMPLEMENTATION PRINCIPLE

Prioritize:

1. Working end-to-end flow
2. Real local Qwen2-VL integration
3. Evidence Chain
4. Deterministic Python verification
5. RAG
6. OCR
7. Professional UI
8. Offline execution
9. Reliability

Do NOT prioritize unnecessary features.

A smaller prototype that works perfectly is much better than a huge system that fails during the SIH presentation.

---

# 46. FIRST ACTION

Before implementing anything:

1. Inspect the existing repository.
2. Identify existing React code.
3. Identify existing FastAPI code.
4. Identify existing dependencies.
5. Reuse working components.
6. Identify what is missing.
7. Create a concise implementation plan.
8. Do not rewrite functioning code unnecessarily.

Then implement Phase 1.

After each phase:

1. Run the application.
2. Test the feature.
3. Fix errors.
4. Only then proceed to the next phase.

Never claim that a component is complete without testing it.

The final result must be a **working SOVEREIGN-X Evidence Chain prototype with a real local Qwen2-VL multimodal LLM**, suitable for a live SIH 2026 demonstration.
