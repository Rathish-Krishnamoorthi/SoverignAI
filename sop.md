Implement a complete **SOP (Standard Operating Procedure) Management Module** inside my existing **Sovereign-X** project.

Sovereign-X is an **air-gapped, on-premise industrial AI platform** for confidential refinery/industrial operations.

The SOP module must be completely local and must never send SOPs, extracted text, embeddings, metadata, or user queries to external/cloud services.

---

# 1. Core Objective

Build an SOP system where authorized personnel can:

* Upload approved/internal SOP documents
* Import SOPs from internal file servers
* Store original SOP files locally
* Extract text locally
* Perform OCR locally when required
* Version SOPs
* Review and approve SOPs
* Search SOPs
* Ask the local AI questions about SOPs
* Retrieve relevant SOP sections using local RAG
* Track who uploaded/approved/modified/viewed an SOP
* Retire/supersede old SOP versions
* Prevent unauthorized users from accessing SOP content

The AI must **not invent operational procedures**.

The local LLM should answer operational questions using approved SOPs and clearly identify the source SOP and version.

---

# 2. SOP Data Sources

SOP data must originate from the organization's internal sources only.

Support:

1. Local PDF/DOCX uploads
2. Internal network file shares
3. Internal document management systems where an approved internal connector exists
4. Existing engineering/operations document repositories
5. Authorized manual uploads by engineers/supervisors

Do NOT fetch SOPs from the public Internet.

Do NOT use cloud storage.

Do NOT use external document APIs.

For the prototype, implement local upload/import first and create an abstraction for future internal repository connectors.

---

# 3. SOP Lifecycle

Implement this lifecycle:

UPLOADED
→ UNDER_REVIEW
→ APPROVED
→ ACTIVE
→ SUPERSEDED
→ ARCHIVED

Rules:

* Newly uploaded SOPs start as `UPLOADED`.
* Authorized reviewers can move them to `UNDER_REVIEW`.
* Only authorized approvers can mark them `APPROVED`.
* Only approved SOPs can become `ACTIVE`.
* When a new version becomes active, the previous active version becomes `SUPERSEDED`.
* Superseded SOPs remain available for audit/history.
* Archived SOPs must not normally be used by operational RAG.
* Users must not be able to manually mark an SOP as ACTIVE unless their role allows approval.

---

# 4. SOP Metadata

Create a PostgreSQL model/table called `SOP`.

Include:

* id
* sop_id
* title
* description
* department
* plant
* unit
* equipment
* category
* version
* revision_number
* status
* effective_date
* review_date
* expiry_date
* author
* reviewer
* approver
* approval_date
* classification
* source_type
* source_location
* file_object_key
* file_name
* mime_type
* file_size
* checksum
* created_by
* updated_by
* created_at
* updated_at

Use proper:

* Foreign keys
* Indexes
* Unique constraints
* Timestamps

Ensure `(sop_id, version)` is unique.

---

# 5. SOP Versioning

Implement proper version control.

Example:

SOP-DIST-001

* v1.0 → ARCHIVED
* v2.0 → SUPERSEDED
* v3.0 → ACTIVE

The system must never delete historical versions automatically.

When a new version is approved:

1. Locate the currently ACTIVE version.
2. Mark it SUPERSEDED.
3. Mark the new version ACTIVE.
4. Record the change in the audit log.

Users should be able to view version history.

---

# 6. File Storage

Use **MinIO running locally** for SOP files.

Do NOT store large PDF/DOCX files directly in PostgreSQL.

Example object structure:

`sops/{sop_id}/{version}/{filename}`

Example:

`sops/SOP-DIST-001/v3.2/distillation_startup.pdf`

PostgreSQL stores metadata and the MinIO object key.

MinIO must run inside the Sovereign-X private infrastructure.

---

# 7. Document Processing Pipeline

When an SOP is uploaded:

```text
Upload SOP
    ↓
Validate file
    ↓
Calculate checksum
    ↓
Store original in MinIO
    ↓
Extract text locally
    ↓
If scanned:
    OCR using Tesseract
    ↓
Clean text
    ↓
Split into meaningful chunks
    ↓
Generate local embeddings
    ↓
Store chunks + embeddings in PostgreSQL/pgvector
```

Use local libraries such as:

* PyMuPDF
* python-docx
* pytesseract
* Tesseract OCR

Never call external OCR APIs.

---

# 8. SOP Chunk Metadata

Create an `SOPChunk` model/table.

Store:

* id
* sop_id
* sop_version
* chunk_index
* section
* subsection
* page_number
* content
* embedding
* created_at

The embedding must be generated using a **local embedding model**.

Do not use OpenAI, Gemini, Cohere, Pinecone, Weaviate Cloud, or another external service.

Use PostgreSQL + pgvector.

---

# 9. SOP RAG

Integrate SOPs with the existing Sovereign-X local AI assistant.

Example:

User asks:

"What is the approved startup procedure for the distillation column?"

System:

```text
User Question
      ↓
Authentication
      ↓
RBAC
      ↓
Identify accessible plant/unit
      ↓
Search ACTIVE/APPROVED SOPs
      ↓
Apply authorization filters
      ↓
Vector similarity search
      ↓
Retrieve relevant SOP chunks
      ↓
Local LLM
      ↓
Grounded response
      ↓
Source citation
      ↓
Audit log
```

The local LLM must receive only the authorized retrieved content.

---

# 10. RAG Authorization

This is critical.

Never perform unrestricted vector search.

Before retrieving SOP chunks:

1. Authenticate the user.
2. Determine their role.
3. Determine their authorized plant/unit/project.
4. Filter SOPs based on permissions.
5. Search only authorized SOPs.
6. Pass retrieved chunks to the local LLM.

Prevent cross-department and cross-project data leakage.

For example:

An engineer authorized for:

`Plant A → CDU`

must not retrieve:

`Plant B → Hydrogen Unit`

unless explicitly authorized.

---

# 11. AI Response Format

When the local AI answers an SOP-related question, return:

```text
Answer

According to the approved procedure, ...

Source:
SOP ID: SOP-DIST-001
Title: Distillation Column Startup Procedure
Version: 3.2
Status: ACTIVE
Section: 4.2
Page: 12
```

The answer must distinguish between:

* Information explicitly present in SOPs
* AI-generated explanation
* Information not found in available SOPs

If the answer cannot be supported by an active/approved SOP, respond with something like:

"I could not find an approved SOP section supporting this procedure."

Do NOT hallucinate an operational procedure.

---

# 12. Citation Support

Every SOP-derived AI response should contain source references.

Store:

* SOP ID
* Version
* Section
* Page
* Chunk ID

This allows the frontend to show:

`View Source`

which opens the relevant SOP page/section.

---

# 13. SOP Search

Implement search filters:

* SOP ID
* Title
* Department
* Plant
* Unit
* Equipment
* Category
* Version
* Status
* Effective date
* Review date
* Author
* Approver

Support both:

1. Metadata search
2. Semantic/vector search

Example:

Search:

`distillation startup`

should return relevant approved SOPs even if the exact phrase isn't present.

---

# 14. SOP Management UI

Create a dedicated frontend page:

`/sops`

Include:

### Dashboard

Display:

* Total SOPs
* Active SOPs
* Pending review
* Expiring soon
* Superseded
* Archived

### SOP Table

Columns:

* SOP ID
* Title
* Department
* Unit
* Version
* Status
* Effective Date
* Review Date
* Approver
* Actions

Actions:

* View
* Download
* Search
* View versions
* Submit for review
* Approve
* Reject
* Supersede
* Archive

Only show actions permitted by RBAC.

---

# 15. SOP Upload UI

Create an upload form:

* SOP ID
* Title
* Description
* Department
* Plant
* Unit
* Equipment
* Category
* Version
* Revision
* Effective date
* Review date
* Expiry date
* Classification
* PDF/DOCX upload

Validate:

* File type
* File size
* Required metadata
* Duplicate version
* Checksum

Show processing status:

```text
Uploading
   ↓
Stored
   ↓
Extracting text
   ↓
OCR
   ↓
Generating embeddings
   ↓
Indexed
   ↓
Ready for review
```

---

# 16. Approval Workflow

Implement:

```text
Uploader
    ↓
Submit for Review
    ↓
Reviewer
    ↓
Approve / Reject
    ↓
Approver
    ↓
ACTIVE
```

Separate uploader/reviewer/approver permissions where appropriate.

Prevent users from approving their own SOP if organizational policy requires separation of duties.

Make this configurable through RBAC.

---

# 17. Roles

Integrate SOP permissions with existing Sovereign-X RBAC.

Suggested permissions:

### ADMIN

Full access.

### ENGINEER

* View authorized SOPs
* Search SOPs
* Ask AI questions
* Upload SOPs
* Submit for review

### SUPERVISOR

* Review SOPs
* Approve SOPs
* Manage versions
* View audit history

### OPERATOR

* View authorized active SOPs
* Search SOPs
* Ask SOP-related AI questions

### AUDITOR

* View SOP history
* View approvals
* View audit logs
* No modification

Do not assume these roles are sufficient if the existing Sovereign-X RBAC already defines roles. Extend the existing RBAC instead of replacing it.

---

# 18. Audit Logging

Log every sensitive SOP action.

Examples:

SOP_UPLOADED
SOP_VIEWED
SOP_DOWNLOADED
SOP_SUBMITTED_FOR_REVIEW
SOP_APPROVED
SOP_REJECTED
SOP_VERSION_CREATED
SOP_SUPERSEDED
SOP_ARCHIVED
SOP_SEARCHED
SOP_AI_QUERY
SOP_AI_RESPONSE

Store:

* user ID
* role
* action
* SOP ID
* version
* timestamp
* success/failure
* relevant metadata

Do not store sensitive information unnecessarily in logs.

---

# 19. Security

The SOP module must inherit Sovereign-X's security architecture.

Use:

* JWT authentication
* RBAC
* Password hashing
* Input validation
* File validation
* MIME validation
* File size limits
* Checksum validation
* Audit logging
* Secure environment variables

Do not expose MinIO directly to the public Internet.

Do not expose PostgreSQL directly to the public Internet.

---

# 20. Air-Gapped Operation

Support:

`AIR_GAPPED_MODE=true`

When enabled:

* No external SOP imports
* No external AI APIs
* No external embeddings
* No cloud storage
* No cloud OCR
* No telemetry
* No external analytics

The complete SOP workflow must continue functioning offline.

---

# 21. Internal SOP Import

Create an abstraction:

```text
SOPSource
├── LocalFileSource
├── NetworkShareSource
└── InternalDMSSource
```

Initially implement:

`LocalFileSource`

and a secure internal network-share importer.

The architecture should allow an organization's internal DMS to be integrated later without redesigning the SOP module.

Never create a public web scraper for SOP collection.

---

# 22. Database Relationships

Implement relationships approximately as:

```text
User
 │
 ├── uploads ───────> SOP
 │
 ├── reviews ───────> SOP
 │
 └── approves ──────> SOP

SOP
 │
 ├── has versions
 │
 ├── has chunks
 │
 ├── stored in MinIO
 │
 └── has audit events

SOPChunk
 │
 └── embedding → pgvector
```

Use normalized relational design.

---

# 23. API Endpoints

Create REST APIs such as:

POST   /api/sops
GET    /api/sops
GET    /api/sops/{id}
PUT    /api/sops/{id}
DELETE /api/sops/{id}

POST   /api/sops/{id}/submit-review
POST   /api/sops/{id}/approve
POST   /api/sops/{id}/reject
POST   /api/sops/{id}/supersede
POST   /api/sops/{id}/archive

GET    /api/sops/{id}/versions
GET    /api/sops/{id}/document

POST   /api/sops/search
POST   /api/sops/rag/query

GET    /api/sops/{id}/audit

Follow the existing Sovereign-X API naming conventions if they differ.

---

# 24. Local Storage Architecture

Use:

```text
Sovereign-X
│
├── PostgreSQL
│   ├── SOP metadata
│   ├── versions
│   ├── chunks
│   ├── permissions
│   └── audit logs
│
├── pgvector
│   └── SOP embeddings
│
├── MinIO
│   └── Original SOP files
│
├── Local OCR
│   └── Tesseract
│
├── Local Embedding Model
│   └── Embeddings
│
└── Local LLM
    └── RAG answers
```

No confidential SOP information should require cloud connectivity.

---

# 25. Important Safety Requirement

The SOP module is a **knowledge and retrieval system**, not an autonomous control system.

The AI must NOT:

* Directly control refinery equipment
* Change DCS/SCADA parameters
* Automatically execute operational procedures
* Override safety systems
* Claim authority over human operators

For operationally sensitive recommendations, clearly indicate that the information is based on the retrieved SOP and that execution remains under authorized human/operator procedures.

---

# 26. Existing Project Integration

Before modifying anything:

1. Inspect the current Sovereign-X directory.
2. Identify the existing FastAPI architecture.
3. Identify existing authentication/RBAC.
4. Identify existing PostgreSQL/MongoDB configuration.
5. Identify existing local LLM integration.
6. Identify existing RAG/document processing.
7. Reuse existing components where possible.

Do NOT create duplicate authentication, database, LLM, or RAG implementations.

Do NOT delete existing functionality.

If MongoDB is currently used, migrate SOP persistence to the planned PostgreSQL + pgvector architecture while preserving existing APIs wherever possible.

---

# 27. Testing

Create tests for:

* SOP upload
* Invalid file rejection
* Duplicate SOP version
* Version creation
* Approval workflow
* Superseding old versions
* RBAC
* Unauthorized SOP access
* Vector retrieval
* RAG response
* Source citation
* Audit logging
* Air-gapped mode
* Local document processing

Include tests proving that a user cannot retrieve an SOP they are not authorized to access.

---

# 28. Documentation

Update README documentation with:

* SOP architecture
* SOP lifecycle
* Data sources
* Storage architecture
* RAG pipeline
* Versioning
* Approval workflow
* RBAC
* Security
* Air-gapped deployment
* Database schema
* API documentation
* Example SOP workflow

Also provide an architecture diagram.

---

# Final acceptance criteria

The implementation is complete only when:

1. SOPs can be uploaded locally.
2. Original SOP files are stored in local MinIO.
3. SOP metadata is stored in PostgreSQL.
4. SOP versions are tracked.
5. Approval workflow works.
6. Only approved/active SOPs are used by operational RAG.
7. Historical SOP versions remain available for audit.
8. SOP text is extracted locally.
9. OCR works locally.
10. Embeddings are generated locally.
11. Embeddings are stored in pgvector.
12. RAG runs against authorized SOPs only.
13. AI responses cite SOP ID/version/section/page.
14. Unauthorized users cannot retrieve restricted SOP content.
15. All sensitive actions are audited.
16. No cloud service is required.
17. The module works with Internet disconnected.
18. The local LLM cannot invent an unsupported SOP procedure.
19. Existing Sovereign-X functionality remains intact.
20. The implementation is production-oriented and modular.

First inspect the existing project and explain which existing files/modules should be reused or modified. Then implement the SOP module incrementally.
