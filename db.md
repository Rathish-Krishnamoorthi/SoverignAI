Modify my **Sovereign-X** project to implement a completely **on-premise, air-gapped data storage architecture**.

### Core requirement

Sovereign-X is designed for confidential industrial/refinery environments. **No confidential data must leave the local infrastructure.**

Do NOT use:

* MongoDB Atlas
* Firebase
* Supabase
* AWS S3
* Cloud databases
* OpenAI/Gemini/Claude APIs
* Cloud vector databases
* External embedding APIs
* External OCR APIs

Everything must be capable of running inside the organization's private network without Internet access.

### Target architecture

Implement:

Frontend
→ FastAPI Backend
→ PostgreSQL + pgvector
→ MinIO
→ Local LLM (Ollama/vLLM)

Use Docker Compose so the complete backend infrastructure can run locally.

### 1. PostgreSQL

Use PostgreSQL as the primary relational database.

Create tables/models for:

* users
* roles
* permissions
* user_roles
* projects
* equipment
* sensor_metadata
* conversations
* messages
* documents
* document_chunks
* ai_results
* audit_logs
* system_settings

Use proper:

* Primary keys
* Foreign keys
* Unique constraints
* Indexes
* Created/updated timestamps
* Soft deletion where appropriate

Implement database migrations using Alembic.

### 2. pgvector

Enable the PostgreSQL `pgvector` extension.

Use it for local document embeddings and RAG.

Document pipeline:

PDF/document
→ local text extraction
→ chunking
→ local embedding model
→ pgvector
→ similarity search
→ relevant chunks
→ local LLM

Never call an external embedding API.

Make the embedding model configurable through environment variables.

### 3. MinIO

Use MinIO as the S3-compatible object storage, but run it completely locally.

Store large files such as:

* PDF documents
* Engineering reports
* Images
* Inspection reports
* Equipment documents
* Uploaded datasets

Do not store large binary files directly inside PostgreSQL.

Instead store:

* object key
* filename
* MIME type
* size
* checksum
* uploader
* project ID
* created timestamp

inside PostgreSQL.

The actual file must be stored in MinIO.

### 4. Local LLM

Integrate a local LLM through Ollama or vLLM.

Create an abstraction such as:

LLMProvider
├── OllamaProvider
└── VLLMProvider

The application must never directly depend on an external AI API.

All inference must happen locally.

Make the following configurable:

LLM_BASE_URL
LLM_MODEL
EMBEDDING_MODEL

Example:

LLM_BASE_URL=http://ollama:11434
LLM_MODEL=qwen2.5
EMBEDDING_MODEL=<local-embedding-model>

### 5. Local OCR

Implement document OCR locally.

Use:

* PyMuPDF
* Tesseract OCR
* pytesseract

Do not use cloud OCR services.

The document-processing pipeline should support:

PDF
→ text extraction
→ OCR if required
→ chunking
→ embedding
→ PostgreSQL/pgvector

### 6. Security

Implement strong security appropriate for confidential industrial data.

Use:

* JWT authentication
* RBAC
* Password hashing with bcrypt/Argon2
* HTTPS-ready configuration
* Input validation
* File validation
* File size limits
* MIME-type validation
* Audit logging
* Secure environment variables
* No secrets in source code

Roles should include:

ADMIN
ENGINEER
ANALYST
OPERATOR
AUDITOR

Ensure each role can access only its authorized modules.

### 7. Encryption

Design the application so sensitive data can be encrypted at rest.

Support:

* PostgreSQL encrypted storage/volume
* MinIO encrypted storage
* TLS for internal service communication
* Secret management through environment variables or a local secret manager

Never hard-code encryption keys or passwords.

### 8. Audit logging

Every sensitive operation must generate an audit log.

Track:

* user
* action
* resource
* resource ID
* timestamp
* IP address where appropriate
* success/failure
* metadata

Examples:

LOGIN
DOCUMENT_UPLOAD
DOCUMENT_DELETE
DOCUMENT_VIEW
AI_QUERY
AI_RESPONSE
PROJECT_CREATE
PROJECT_UPDATE
USER_CREATE
ROLE_CHANGE
DATA_EXPORT

Audit logs should be append-oriented and accessible only to authorized users.

### 9. Air-gapped mode

Add an explicit configuration:

AIR_GAPPED_MODE=true

When enabled:

* Block external API integrations
* Disable telemetry
* Disable analytics sent outside the system
* Prevent external LLM calls
* Prevent external embedding calls
* Prevent external OCR calls
* Prevent cloud storage usage
* Log any attempted external network access

The application should continue working normally using only local services.

### 10. Docker Compose

Create a production-oriented `docker-compose.yml` containing:

* frontend
* backend
* postgres
* minio
* ollama

If necessary, include a separate worker service for document processing.

Use persistent Docker volumes.

Example conceptual structure:

services:
frontend
backend
postgres
minio
ollama
worker

Do not expose PostgreSQL, MinIO, or Ollama directly to the public Internet.

Only expose the required frontend/backend ports.

### 11. Environment configuration

Create `.env.example`.

Include variables such as:

DATABASE_URL=
MINIO_ENDPOINT=
MINIO_ACCESS_KEY=
MINIO_SECRET_KEY=
MINIO_BUCKET=
JWT_SECRET_KEY=
JWT_ALGORITHM=
LLM_BASE_URL=
LLM_MODEL=
EMBEDDING_MODEL=
AIR_GAPPED_MODE=true
MAX_UPLOAD_SIZE_MB=

Never commit the actual `.env`.

Update `.gitignore` to exclude:

.env
*.key
*.pem
secrets/
postgres-data/
minio-data/
models/
uploads/
logs/

### 12. Data flow

Implement this secure flow:

User
→ Authentication
→ RBAC
→ FastAPI
→ PostgreSQL/MinIO
→ Local document processing
→ Local embeddings
→ pgvector
→ RAG retrieval
→ Local LLM
→ AI response
→ Audit log

At no point should confidential refinery data leave the local infrastructure.

### 13. RAG security

Implement project-level/document-level access control.

A user must NOT be able to retrieve embeddings or documents that they are not authorized to access.

Before vector similarity search:

1. Authenticate user
2. Determine user's roles/projects
3. Apply metadata filters
4. Perform vector search only on authorized documents
5. Send retrieved chunks to the local LLM

Prevent cross-project data leakage.

### 14. Health checks

Create health endpoints:

GET /health
GET /health/database
GET /health/storage
GET /health/llm

Return service status without exposing secrets.

### 15. Do not rewrite unnecessarily

First inspect the existing Sovereign-X project structure.

Reuse the existing:

* authentication
* FastAPI routes
* models
* frontend
* AI modules

Only modify what is necessary.

Do not delete existing functionality.

If the project currently uses MongoDB Atlas, migrate the persistence layer to PostgreSQL while preserving the existing API behavior wherever possible.

### 16. Deliverables

Create/update:

docker-compose.yml
.env.example
.gitignore
Dockerfiles if required
database configuration
SQLAlchemy models
Alembic migrations
MinIO storage service
pgvector integration
local embedding service
local LLM service
local OCR service
document processing pipeline
RAG service
RBAC
audit logging
health checks
README.md

The README must contain:

1. Architecture diagram
2. Data-flow explanation
3. Database schema explanation
4. Docker setup
5. Air-gapped deployment instructions
6. How to run without Internet
7. Security considerations
8. Backup and restore procedure
9. How documents are stored
10. How RAG works
11. How local LLM inference works

### Final acceptance criteria

The implementation is considered complete only if:

* The entire system can run locally.
* Confidential data never needs to leave the local network.
* PostgreSQL stores structured data.
* pgvector stores embeddings.
* MinIO stores large documents/files.
* Ollama/vLLM performs local LLM inference.
* OCR runs locally.
* RAG works locally.
* RBAC prevents unauthorized document retrieval.
* Audit logs capture sensitive actions.
* Docker volumes persist data.
* No cloud dependency exists in air-gapped mode.
* `.env` and secrets are not committed.
* The system can operate with Internet completely disconnected.

Before making changes, inspect the existing project and provide a short summary of the current architecture and the files that need modification. Then implement the changes incrementally without breaking existing functionality.
