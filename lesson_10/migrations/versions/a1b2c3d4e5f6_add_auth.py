"""Add auth tables

Revision ID: a1b2c3d4e5f6
Revises: 4fa3c2b98b05
Create Date: 2026-05-12 01:28:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "4fa3c2b98b05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.add_column("todos", sa.Column("user_id", sa.Integer(), nullable=True))

    connection = op.get_bind()
    todos_count = connection.execute(sa.text("SELECT count(*) FROM todos")).scalar()
    if todos_count:
        legacy_user_id = connection.execute(
            sa.text(
                """
                INSERT INTO users (username, email, password_hash, created_at)
                VALUES ('legacy_user', 'legacy@example.com', 'disabled', CURRENT_TIMESTAMP)
                RETURNING id
                """
            )
        ).scalar_one()
        connection.execute(
            sa.text("UPDATE todos SET user_id = :user_id WHERE user_id IS NULL"),
            {"user_id": legacy_user_id},
        )

    op.alter_column("todos", "user_id", nullable=False)
    op.create_index(op.f("ix_todos_user_id"), "todos", ["user_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_todos_user_id_users"),
        "todos",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_refresh_tokens_token_hash"),
        "refresh_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_token_hash"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    op.drop_constraint(op.f("fk_todos_user_id_users"), "todos", type_="foreignkey")
    op.drop_index(op.f("ix_todos_user_id"), table_name="todos")
    op.drop_column("todos", "user_id")

    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
