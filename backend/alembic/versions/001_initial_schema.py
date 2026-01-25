"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now()
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now()
        ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # Copy Trade Accounts table
    op.create_table(
        'copy_trade_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_number', sa.String(50), nullable=False),
        sa.Column('account_password', sa.String(255), nullable=False),
        sa.Column('server', sa.String(100), nullable=False),
        sa.Column('buyer_name', sa.String(100), nullable=False),
        sa.Column('buyer_email', sa.String(100), nullable=True),
        sa.Column('buyer_phone', sa.String(20), nullable=True),
        sa.Column('buyer_notes', sa.Text(), nullable=True),
        sa.Column('purchase_date', sa.Date(), nullable=False),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('purchase_price', sa.Numeric(10, 2), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('copy_count', sa.Integer(), default=0),
        sa.Column('max_copies', sa.Integer(), default=1),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now()
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now()
        ),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'in_copy', 'expired', 'suspended')",
            name='valid_status'
        )
    )
    op.create_index('ix_copy_trade_accounts_id', 'copy_trade_accounts', ['id'])
    op.create_index(
        'ix_copy_trade_accounts_account_number',
        'copy_trade_accounts',
        ['account_number'],
        unique=True
    )
    op.create_index(
        'ix_copy_trade_accounts_status',
        'copy_trade_accounts',
        ['status']
    )


def downgrade() -> None:
    op.drop_table('copy_trade_accounts')
    op.drop_table('users')
