"""initial schema"""
from alembic import op
from app.db.database import Base
from app.db import models
revision="0001_initial"; down_revision=None; branch_labels=None; depends_on=None
def upgrade():
    from sqlalchemy import text
    op.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(op.get_bind())
def downgrade(): Base.metadata.drop_all(op.get_bind())
