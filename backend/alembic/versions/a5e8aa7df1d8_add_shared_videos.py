"""add shared videos"""

from alembic import op
import sqlalchemy as sa

# Revision identifiers
revision = "a5e8aa7df1d8"
down_revision = "a0f934e71f72"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "shared_videos",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("topic", sa.String(length=200), nullable=False),
        sa.Column("grade", sa.String(length=40), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.String(length=36), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )

    op.create_index(
        op.f("ix_shared_videos_grade"),
        "shared_videos",
        ["grade"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shared_videos_topic"),
        "shared_videos",
        ["topic"],
        unique=False,
    )
    op.create_index(
        op.f("ix_shared_videos_uploaded_by"),
        "shared_videos",
        ["uploaded_by"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_shared_videos_uploaded_by"),
        table_name="shared_videos",
    )
    op.drop_index(
        op.f("ix_shared_videos_topic"),
        table_name="shared_videos",
    )
    op.drop_index(
        op.f("ix_shared_videos_grade"),
        table_name="shared_videos",
    )
    op.drop_table("shared_videos")
