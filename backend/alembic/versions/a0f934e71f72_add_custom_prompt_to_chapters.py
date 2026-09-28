"""add custom prompt to chapters"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "a0f934e71f72"
down_revision: Union[str, None] = "56d51932f983"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # custom_prompt is already created by 0001_initial
    # because 0001_initial uses the current SQLAlchemy metadata.
    pass


def downgrade() -> None:
    # custom_prompt belongs to the initial schema.
    pass