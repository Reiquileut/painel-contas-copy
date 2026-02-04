"""Add proprietary trading fields

Revision ID: 002
Revises: 001
Create Date: 2024-01-02

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'copy_trade_accounts',
        sa.Column('margin_size', sa.Numeric(12, 2), nullable=True)
    )
    op.add_column(
        'copy_trade_accounts',
        sa.Column('phase1_target', sa.Numeric(12, 2), nullable=True)
    )
    op.add_column(
        'copy_trade_accounts',
        sa.Column(
            'phase1_status', sa.String(20), nullable=True,
            server_default='not_started'
        )
    )
    op.add_column(
        'copy_trade_accounts',
        sa.Column('phase2_target', sa.Numeric(12, 2), nullable=True)
    )
    op.add_column(
        'copy_trade_accounts',
        sa.Column('phase2_status', sa.String(20), nullable=True)
    )
    op.create_check_constraint(
        'valid_phase1_status',
        'copy_trade_accounts',
        "phase1_status IS NULL OR phase1_status IN ('not_started', 'in_progress', 'passed', 'failed')"
    )
    op.create_check_constraint(
        'valid_phase2_status',
        'copy_trade_accounts',
        "phase2_status IS NULL OR phase2_status IN ('not_started', 'in_progress', 'passed', 'failed')"
    )


def downgrade() -> None:
    op.drop_constraint('valid_phase2_status', 'copy_trade_accounts', type_='check')
    op.drop_constraint('valid_phase1_status', 'copy_trade_accounts', type_='check')
    op.drop_column('copy_trade_accounts', 'phase2_status')
    op.drop_column('copy_trade_accounts', 'phase2_target')
    op.drop_column('copy_trade_accounts', 'phase1_status')
    op.drop_column('copy_trade_accounts', 'phase1_target')
    op.drop_column('copy_trade_accounts', 'margin_size')
