"""Create the explicit SOP metadata table used by local administration."""
from backend.db import Base, engine
from backend.models.db_models import SOPDocument

revision = "0003_sop_metadata_table"
down_revision = "0002_local_storage_schema"


def upgrade():
    SOPDocument.__table__.create(bind=engine, checkfirst=True)


def downgrade():
    SOPDocument.__table__.drop(bind=engine, checkfirst=True)
