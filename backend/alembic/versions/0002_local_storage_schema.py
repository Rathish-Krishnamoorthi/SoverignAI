"""Add local document processing and audit storage fields."""
from alembic import op
import sqlalchemy as sa

revision = "0002_local_storage_schema"
down_revision = "0001_initial"


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "documents" in tables:
        columns = {column["name"] for column in inspector.get_columns("documents")}
        additions = [
            ("document_id", sa.String(120)),
            ("original_filename", sa.String(255)),
            ("file_path", sa.String(500)),
            ("document_type", sa.String(80)),
            ("uploaded_by", sa.String(120)),
            ("department", sa.String(120)),
            ("status", sa.String(40), {"server_default": "UPLOADED"}),
            ("version", sa.String(40), {"server_default": "1.0"}),
            ("updated_at", sa.DateTime(timezone=True)),
        ]
        for item in additions:
            name, column_type = item[0], item[1]
            kwargs = item[2] if len(item) == 3 else {}
            if name not in columns:
                op.add_column("documents", sa.Column(name, column_type, nullable=True, **kwargs))

    from backend.models.db_models import Base
    from backend.db import engine
    Base.metadata.create_all(engine)


def downgrade():
    # Local deployments retain data during rollback; schema removal is unsafe.
    pass
