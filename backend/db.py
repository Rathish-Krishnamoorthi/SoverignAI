"""Local SQLite database bootstrap for the air-gapped workbench."""
import os
from pathlib import Path
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import DeclarativeBase, sessionmaker
    SQLALCHEMY_AVAILABLE = True
except ImportError:  # demo environments may not install production dependencies
    SQLALCHEMY_AVAILABLE = False

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
DATA_ROOT.mkdir(parents=True, exist_ok=True)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(DATA_ROOT / 'sovereign.db').as_posix()}")
if SQLALCHEMY_AVAILABLE:
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    if DATABASE_URL.startswith("sqlite:///"):
        sqlite_path = DATABASE_URL.removeprefix("sqlite:///")
        os.makedirs(os.path.dirname(sqlite_path) or ".", exist_ok=True)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    class Base(DeclarativeBase): pass
else:
    engine = None
    SessionLocal = None
    class Base: pass

def database_health() -> dict:
    try:
        if not engine: return {"status": "unavailable", "error": "SQLAlchemy is not installed (demo mode)"}
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "postgresql" if DATABASE_URL.startswith("postgres") else "sqlite-demo"}
    except Exception as exc:
        return {"status": "unavailable", "error": str(exc)[:200]}

def init_db() -> None:
    # Demo startup remains usable without production dependencies. Production
    # must fail fast rather than silently serving an un-migrated schema.
    demo = os.getenv("DEMO_MODE", "true").lower() == "true"
    if not engine:
        if demo: return
        raise RuntimeError("SQLAlchemy is required when DEMO_MODE=false")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        from alembic.config import Config
        from alembic import command
        config = Config(os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini"))
        command.upgrade(config, "head")
    except Exception:
        if demo: return
        raise
