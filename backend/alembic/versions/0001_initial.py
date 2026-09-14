"""Initial Sovereign-X relational schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
revision = "0001_initial"
down_revision = None
def upgrade():
    # Metadata-driven migration keeps this initial revision aligned with the ORM,
    # while PostgreSQL deployments can enable pgvector before running it.
    from backend.models.db_models import Base
    from backend.db import engine
    Base.metadata.create_all(engine)
def downgrade():
    from backend.models.db_models import Base
    from backend.db import engine
    Base.metadata.drop_all(engine)
