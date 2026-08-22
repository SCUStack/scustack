"""add thumbnail generation state"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '034'
down_revision: str | None = '033'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'materials',
        sa.Column('thumbnail_status', sa.String(20), nullable=False, server_default='missing'),
    )
    op.add_column(
        'materials',
        sa.Column('thumbnail_version_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        'fk_materials_thumbnail_version_id',
        'materials',
        'material_versions',
        ['thumbnail_version_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_materials_thumbnail_version_id', 'materials', ['thumbnail_version_id'])
    op.execute("""
        UPDATE materials AS material
        SET thumbnail_version_id = latest.id,
            thumbnail_status = 'unknown'
        FROM (
            SELECT DISTINCT ON (material_id) id, material_id
            FROM material_versions
            ORDER BY material_id, version_number DESC
        ) AS latest
        WHERE latest.material_id = material.id
    """)


def downgrade() -> None:
    op.drop_index('ix_materials_thumbnail_version_id', table_name='materials')
    op.drop_constraint('fk_materials_thumbnail_version_id', 'materials', type_='foreignkey')
    op.drop_column('materials', 'thumbnail_version_id')
    op.drop_column('materials', 'thumbnail_status')
