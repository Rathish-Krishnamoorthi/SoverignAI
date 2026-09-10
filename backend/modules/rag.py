import json
from pathlib import Path

from backend.modules.embeddings import embed
from backend.models.schemas import SOPEvidence


SOP_PATH = Path(__file__).resolve().parents[1] / "knowledge_base" / "sops" / "demo_sop.txt"


def retrieve_sop(query: str) -> SOPEvidence:
    text = SOP_PATH.read_text(encoding="utf-8").strip()
    if not text:
        raise RuntimeError("Synthetic Demo SOP is missing or empty.")
    embedding = embed(query)
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(Path(__file__).resolve().parents[1] / "data" / "chroma"))
        collection = client.get_or_create_collection("sops")
        collection.upsert(
            ids=["sop-mrpl-ins-04-4.3"],
            documents=[text],
            metadatas=[{"document": "SOP-MRPL-INS-04", "section": "4.3", "page": 12}],
            embeddings=[embedding],
        )
        result = collection.query(query_embeddings=[embedding], n_results=1)
        text = result["documents"][0][0]
    except Exception:
        # The semantic index remains local and the deterministic SOP is still available offline.
        pass
    return SOPEvidence(
        document="SOP-MRPL-INS-04",
        section="4.3",
        page=12,
        text=text,
        limit=1.5,
    )

