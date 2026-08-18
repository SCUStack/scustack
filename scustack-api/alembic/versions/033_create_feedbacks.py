"""create feedbacks table and workflow fields"""
from collections.abc import Sequence
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '033'
down_revision: str | None = '032'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.create_table(
        'feedbacks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('handled_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('handled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('admin_note', sa.Text, nullable=True),
    )
    op.create_index('ix_feedbacks_user_id', 'feedbacks', ['user_id'])
    op.create_index('ix_feedbacks_status', 'feedbacks', ['status'])

def downgrade() -> None:
    op.drop_index('ix_feedbacks_status', table_name='feedbacks')
    op.drop_index('ix_feedbacks_user_id', table_name='feedbacks')
    op.drop_table('feedbacks')
