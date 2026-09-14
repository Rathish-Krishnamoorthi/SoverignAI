"""Complete the requested local SQLite metadata fields."""
from alembic import op
import sqlalchemy as sa

revision = "0004_requested_local_fields"
down_revision = "0003_sop_metadata_table"


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    additions = {
        "users": [
            ("department", sa.String(120)),
            ("updated_at", sa.DateTime(timezone=True)),
        ],
        "document_chunks": [
            ("metadata_json", sa.JSON()),
        ],
        "audit_logs": [
            ("timestamp", sa.DateTime(timezone=True)),
        ],
    }
    for table, columns in additions.items():
        existing = {column["name"] for column in inspector.get_columns(table)}
        for name, column_type in columns:
            if name not in existing:
                op.add_column(table, sa.Column(name, column_type, nullable=True))


def downgrade():
    pass
