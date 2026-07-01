"""add username and password_hash columns for account login

Revision ID: 0001_account_login
Revises:
Create Date: 2026-07-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_account_login"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.String(256), nullable=True))
    op.create_unique_constraint("uq_users_username", "users", ["username"])
    op.alter_column("users", "openid", existing_type=sa.String(64), nullable=True)


def downgrade() -> None:
    op.alter_column("users", "openid", existing_type=sa.String(64), nullable=False)
    op.drop_constraint("uq_users_username", "users", type_="unique")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "username")
