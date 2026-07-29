"""add provider_keys table and provider field to conversation_settings

Revision ID: 002_provider_keys
Revises: 001_conversation_settings
Create Date: 2026-07-28

Changes:
  1. Creates provider_keys table for encrypted API key storage
  2. Adds provider VARCHAR(32) column to conversation_settings
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "002_provider_keys"
down_revision = "001_conversation_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add provider column to conversation_settings
    op.add_column(
        "conversation_settings",
        sa.Column(
            "provider",
            sa.String(32),
            nullable=True,
            comment="Provider override: ollama | groq | gemini | openrouter",
        ),
    )

    # 2. Create provider_keys table
    op.create_table(
        "provider_keys",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False,
                  comment="Provider slug: groq | gemini | openrouter"),
        sa.Column("encrypted_key", sa.Text(), nullable=False,
                  comment="Fernet-encrypted API key"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider"),
    )
    op.create_index("ix_provider_keys_provider", "provider_keys", ["provider"])


def downgrade() -> None:
    op.drop_index("ix_provider_keys_provider", table_name="provider_keys")
    op.drop_table("provider_keys")
    op.drop_column("conversation_settings", "provider")
