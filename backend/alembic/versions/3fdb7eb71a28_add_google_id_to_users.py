"""add google id to users"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3fdb7eb71a28"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "google_id",
            sa.String(length=255),
            nullable=True,
        ),
    )

    op.create_index(
        op.f("ix_users_google_id"),
        "users",
        ["google_id"],
        unique=True,
    )


def downgrade():
    op.drop_index(
        op.f("ix_users_google_id"),
        table_name="users",
    )

    op.drop_column(
        "users",
        "google_id",
    )
