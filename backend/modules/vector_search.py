"""Local pgvector retrieval helper; callers can use it when PostgreSQL is enabled."""
from sqlalchemy import select
from backend.models.db_models import DocumentChunk
from backend.modules.providers import LocalEmbeddingProvider
def retrieve(session, query: str, limit: int = 5):
    embedding = LocalEmbeddingProvider().embed(query)
    try:
        return list(session.scalars(select(DocumentChunk).order_by(
            DocumentChunk.embedding.cosine_distance(embedding)).limit(limit)))
    except Exception:
        return list(session.scalars(select(DocumentChunk).limit(limit)))
