"""add is_fallback to departments, make ticket.department_id NOT NULL

Revision ID: 0001
Revises: 
Create Date: 2026-06-06
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Add is_fallback to departments (nullable first, then set default)
    op.add_column("departments", sa.Column("is_fallback", sa.Boolean(), nullable=True))
    op.execute("UPDATE departments SET is_fallback = 0 WHERE is_fallback IS NULL")
    with op.batch_alter_table("departments") as batch_op:
        batch_op.alter_column("is_fallback", nullable=False, server_default=sa.text("0"))

    # Step 2: Ensure a fallback department exists
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT id FROM departments WHERE is_fallback = 1 LIMIT 1")
    )
    fallback = result.scalar()
    if fallback is None:
        conn.execute(
            sa.text(
                "INSERT INTO departments (name, parent_id, is_fallback) "
                "VALUES ('未分类', NULL, 1)"
            )
        )

    # Step 3: Migrate NULL department_id to fallback department
    fallback_id = conn.execute(
        sa.text("SELECT id FROM departments WHERE is_fallback = 1 LIMIT 1")
    ).scalar()
    conn.execute(
        sa.text(
            "UPDATE tickets SET department_id = :fb WHERE department_id IS NULL"
        ),
        {"fb": fallback_id},
    )

    # Step 4: Make department_id NOT NULL (batch mode for SQLite compat)
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.alter_column("department_id", nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("tickets") as batch_op:
        batch_op.alter_column("department_id", nullable=True)

    op.drop_column("departments", "is_fallback")
