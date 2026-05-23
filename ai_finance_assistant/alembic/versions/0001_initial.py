"""initial migration

Revision ID: 0001_initial
Revises: 
Create Date: 2026-05-23
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('user_id', sa.String(length=36), primary_key=True),
        sa.Column('risk_tolerance', sa.String(length=20), nullable=True),
        sa.Column('investment_horizon', sa.String(length=20), nullable=True),
        sa.Column('experience_level', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.Float(), nullable=True),
    )

    op.create_table(
        'conversation_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=10), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('agent', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.Float(), nullable=True),
    )
    op.create_index('ix_history_user_id', 'conversation_history', ['user_id'])

    op.create_table(
        'portfolio_holdings',
        sa.Column('user_id', sa.String(length=36), primary_key=True),
        sa.Column('portfolio_json', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.Float(), nullable=True),
    )

    op.create_table(
        'sessions',
        sa.Column('session_id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('created_at', sa.Float(), nullable=True),
    )
    op.create_index('ix_sessions_user_id', 'sessions', ['user_id'])


def downgrade():
    op.drop_index('ix_sessions_user_id', table_name='sessions')
    op.drop_table('sessions')
    op.drop_table('portfolio_holdings')
    op.drop_index('ix_history_user_id', table_name='conversation_history')
    op.drop_table('conversation_history')
    op.drop_table('users')
