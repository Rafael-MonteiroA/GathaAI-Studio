"""add provider column to conversation_settings

Revision ID: 003_add_provider_to_settings
Revises: 002_provider_keys
Create Date: 2026-07-29

Adds the `provider` column to conversation_settings (introduced in v0.4
of the domain model but missing from the original migration 001).
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "003_add_provider_to_settings"
down_revision = "002_provider_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "conversation_settings",
        sa.Column(
            "provider",
            sa.String(32),
            nullable=True,
            default=None,
            comment="Provider override: ollama | groq | gemini | openrouter",
        ),
    )


def downgrade() -> None:
    op.drop_column("conversation_settings", "provider")
