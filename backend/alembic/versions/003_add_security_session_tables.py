"""Add refresh token and security audit tables

Revision ID: 003
Revises: 002
Create Date: 2026-02-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("csrf_token", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_ip", sa.String(length=64), nullable=True),
        sa.Column("created_user_agent", sa.String(length=255), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash")
    )
    op.create_index("ix_refresh_tokens_id", "refresh_tokens", ["id"], unique=False)
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"], unique=False)
    op.create_index("ix_refresh_tokens_session_id", "refresh_tokens", ["session_id"], unique=False)
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"], unique=True)
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"], unique=False)

    op.create_table(
        "security_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=True),
        sa.Column("target_id", sa.String(length=64), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id")
    )
    op.create_index("ix_security_audit_logs_id", "security_audit_logs", ["id"], unique=False)
    op.create_index(
        "ix_security_audit_logs_user_id",
        "security_audit_logs",
        ["user_id"],
        unique=False
    )
    op.create_index(
        "ix_security_audit_logs_action",
        "security_audit_logs",
        ["action"],
        unique=False
    )
    op.create_index(
        "ix_security_audit_logs_target_type",
        "security_audit_logs",
        ["target_type"],
        unique=False
    )
    op.create_index(
        "ix_security_audit_logs_target_id",
        "security_audit_logs",
        ["target_id"],
        unique=False
    )
    op.create_index(
        "ix_security_audit_logs_success",
        "security_audit_logs",
        ["success"],
        unique=False
    )
    op.create_index(
        "ix_security_audit_logs_created_at",
        "security_audit_logs",
        ["created_at"],
        unique=False
    )


def downgrade() -> None:
    op.drop_table("security_audit_logs")
    op.drop_table("refresh_tokens")
