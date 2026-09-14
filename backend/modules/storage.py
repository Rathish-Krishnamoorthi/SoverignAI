"""Air-gapped object storage with opt-in MinIO and a local filesystem fallback."""
import hashlib
import io
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class ObjectStorage:
    def __init__(self):
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.bucket = os.getenv("MINIO_BUCKET", "sovereign-documents")
        self.demo_mode = os.getenv("DEMO_MODE", "true").lower() == "true"
        self.minio_enabled = os.getenv("MINIO_ENABLED", "false").lower() == "true"
        self.root = Path(os.getenv("UPLOAD_DIR", str(Path(__file__).resolve().parents[2] / "data" / "documents")))
        self.root.mkdir(parents=True, exist_ok=True)
        for folder in ("sops", "manuals", "reports", "other"):
            (self.root / folder).mkdir(parents=True, exist_ok=True)
        self.client = None
        if self.minio_enabled:
            try:
                from minio import Minio
                self.client = Minio(self.endpoint, access_key=os.getenv("MINIO_ROOT_USER", "sovereign"),
                                    secret_key=os.getenv("MINIO_ROOT_PASSWORD", "change-me"), secure=False)
            except Exception:
                if not self.demo_mode:
                    raise
    def health(self):
        if not self.client: return {"status": "ok", "backend": "filesystem-demo"}
        try:
            self.client.bucket_exists(self.bucket)
            return {"status": "ok", "backend": "minio", "bucket": self.bucket}
        except Exception as exc:
            if self.demo_mode:
                return {"status": "ok", "backend": "filesystem-demo", "minio": "unavailable"}
            return {"status": "unavailable", "backend": "minio", "error": str(exc)[:200]}
    def put(self, key: str, data: bytes, content_type: str) -> dict:
        if self.client:
            try:
                if not self.client.bucket_exists(self.bucket): self.client.make_bucket(self.bucket)
                self.client.put_object(self.bucket, key, io.BytesIO(data), len(data), content_type=content_type)
            except Exception:
                if not self.demo_mode:
                    raise
                logger.warning("MinIO unavailable; storing demo object locally: %s", key, exc_info=True)
                self._put_local(key, data)
        else:
            self._put_local(key, data)
        return {"object_key": key, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}
    def get(self, key: str) -> bytes:
        if self.client:
            try:
                return self.client.get_object(self.bucket, key).read()
            except Exception:
                if not self.demo_mode:
                    raise
                logger.warning("MinIO unavailable; reading demo object locally: %s", key, exc_info=True)
        return (self.root / key).read_bytes()

    def _put_local(self, key: str, data: bytes) -> None:
        dest = self.root / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
