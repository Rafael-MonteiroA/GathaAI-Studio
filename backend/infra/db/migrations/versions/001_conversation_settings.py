"""add conversation_settings table

Revision ID: 001_conversation_settings
Revises: 
Create Date: 2026-07-27

Creates the conversation_settings table for per-conversation AI configuration:
  - model override
  - temperature override
  - custom system prompt
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "001_conversation_settings"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversation_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column(
            "model",
            sa.String(128),
            nullable=True,
            comment="Override model for this conversation",
        ),
        sa.Column(
            "temperature",
            sa.Float(),
            nullable=True,
            comment="Override temperature (0.0-2.0)",
        ),
        sa.Column(
            "system_prompt",
            sa.Text(),
            nullable=True,
            comment="Custom system prompt for this conversation",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id"),
    )
    op.create_index(
        "ix_conversation_settings_conversation_id",
        "conversation_settings",
        ["conversation_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_conversation_settings_conversation_id",
        table_name="conversation_settings",
    )
    op.drop_table("conversation_settings")
