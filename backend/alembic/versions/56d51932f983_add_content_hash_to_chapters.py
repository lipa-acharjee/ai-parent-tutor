"""add content hash to chapters

Revision ID: 56d51932f983
Revises: 3fdb7eb71a28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "56d51932f983"
down_revision: Union[str, Sequence[str], None] = "3fdb7eb71a28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "chapters",
        sa.Column(
            "content_hash",
            sa.String(length=64),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_chapters_content_hash",
        "chapters",
        ["content_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_chapters_content_hash",
        table_name="chapters",
    )

    op.drop_column(
        "chapters",
        "content_hash",
    )