"""add content hash to chapters"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "56d51932f983"
down_revision: Union[str, None] = "3fdb7eb71a28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # content_hash is already created by 0001_initial
    # because 0001_initial uses the current SQLAlchemy metadata.
    pass


def downgrade() -> None:
    # content_hash belongs to the initial schema.
    pass