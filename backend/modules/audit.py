from datetime import datetime, timezone
from typing import Any


def add_event(store: dict[str, list[dict[str, Any]]], document_id: str, action: str, document: str) -> None:
    store.setdefault(document_id, []).append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "document": document,
            "action": action,
            "execution": "LOCAL",
        }
    )

