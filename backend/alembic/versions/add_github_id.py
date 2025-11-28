"""Add github_id column to users table

Revision ID: add_github_id
Revises:
Create Date: 2025-11-20

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_github_id"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add github_id column to users table
    op.add_column("users", sa.Column("github_id", sa.String(length=100), nullable=True))


def downgrade():
    # Remove github_id column from users table
    op.drop_column("users", "github_id")
