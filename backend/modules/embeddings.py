import hashlib
import math


def embed(text: str, dimensions: int = 32) -> list[float]:
    """Small deterministic local fallback; BGE-M3 is used when installed."""
    try:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer("BAAI/bge-m3", local_files_only=True)
        return model.encode(text, normalize_embeddings=True).tolist()
    except Exception:
        digest = hashlib.sha256(text.lower().encode("utf-8")).digest()
        values = [(digest[index % len(digest)] / 255.0) for index in range(dimensions)]
        norm = math.sqrt(sum(value * value for value in values)) or 1
        return [value / norm for value in values]

