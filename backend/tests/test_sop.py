from backend.modules.sop_service import SOPService


class FakeStorage:
    def __init__(self, root):
        self.root = root
        self.objects = {}

    def put(self, key, data, content_type):
        self.objects[key] = data
        import hashlib
        return {"object_key": key, "sha256": hashlib.sha256(data).hexdigest(), "size_bytes": len(data)}


def test_sop_lifecycle_and_version_replacement(tmp_path, monkeypatch):
    monkeypatch.setattr(SOPService, "_extract", staticmethod(lambda path, filename: [(1, "Approved local startup procedure.")]))
    service = SOPService(FakeStorage(tmp_path))
    admin = {"sub": "admin", "roles": ["ADMIN"]}
    payload = b"%PDF-1.4\n%local test"
    first = service.create(payload, "startup.pdf", "application/pdf", {
        "sop_id": "SOP-TEST-001", "version": "1.0", "title": "Startup",
    }, admin)
    assert first.status == "UPLOADED"
    service.transition(first.id, "submit-review", admin)
    service.transition(first.id, "approve", admin)
    service.transition(first.id, "activate", admin)
    second = service.create(payload, "startup-v2.pdf", "application/pdf", {
        "sop_id": "SOP-TEST-001", "version": "2.0", "title": "Startup",
    }, admin)
    service.transition(second.id, "submit-review", admin)
    service.transition(second.id, "approve", admin)
    service.transition(second.id, "activate", admin)
    assert service.get(first.id, admin).status == "SUPERSEDED"
    assert service.get(second.id, admin).status == "ACTIVE"


def test_sop_rejects_duplicate_versions(tmp_path, monkeypatch):
    monkeypatch.setattr(SOPService, "_extract", staticmethod(lambda path, filename: [(1, "Approved local startup procedure.")]))
    service = SOPService(FakeStorage(tmp_path))
    user = {"sub": "engineer", "roles": ["ENGINEER"]}
    metadata = {"sop_id": "SOP-TEST-002", "version": "1.0"}
    service.create(b"%PDF-1.4\n%local test", "one.pdf", "application/pdf", metadata, user)
    try:
        service.create(b"%PDF-1.4\n%local test", "two.pdf", "application/pdf", metadata, user)
    except ValueError as exc:
        assert "already exists" in str(exc)
    else:
        raise AssertionError("duplicate SOP version was accepted")
