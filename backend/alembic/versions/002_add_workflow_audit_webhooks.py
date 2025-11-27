"""add workflow, audit, webhooks, comments, templates

Revision ID: 002
Revises: 001
Create Date: 2025-11-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # ========================================
    # 1. CREATE AUDIT_LOGS TABLE
    # ========================================
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=False),
        sa.Column('user_name', sa.String(length=255), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('full_snapshot', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_logs_entity_type', 'audit_logs', ['entity_type'])
    op.create_index('ix_audit_logs_entity_id', 'audit_logs', ['entity_id'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])

    # ========================================
    # 2. CREATE CONTRACT_VERSIONS TABLE
    # ========================================
    op.create_table(
        'contract_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contract_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('version_date', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_by_email', sa.String(length=255), nullable=False),
        sa.Column('contract_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('change_type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['contract_id'], ['kobetsu_keiyakusho.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_contract_versions_contract_id', 'contract_versions', ['contract_id'])

    # ========================================
    # 3. CREATE CONTRACT_COMMENTS TABLE
    # ========================================
    op.create_table(
        'contract_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('contract_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('user_email', sa.String(length=255), nullable=False),
        sa.Column('user_name', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('comment_type', sa.String(length=20), server_default='general'),
        sa.Column('is_internal', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_edited', sa.Boolean(), server_default='false'),
        sa.Column('is_deleted', sa.Boolean(), server_default='false'),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['contract_id'], ['kobetsu_keiyakusho.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['contract_comments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_contract_comments_contract_id', 'contract_comments', ['contract_id'])
    op.create_index('ix_contract_comments_parent_id', 'contract_comments', ['parent_id'])
    op.create_index('ix_contract_comments_user_id', 'contract_comments', ['user_id'])
    op.create_index('ix_contract_comments_created_at', 'contract_comments', ['created_at'])
    op.create_index('ix_contract_comments_is_deleted', 'contract_comments', ['is_deleted'])

    # ========================================
    # 4. CREATE WEBHOOK_CONFIGS TABLE
    # ========================================
    op.create_table(
        'webhook_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('secret', sa.String(length=255), nullable=True),
        sa.Column('events', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('custom_headers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('max_retries', sa.Integer(), server_default='3'),
        sa.Column('retry_delay_seconds', sa.Integer(), server_default='60'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_webhook_configs_is_active', 'webhook_configs', ['is_active'])

    # ========================================
    # 5. CREATE WEBHOOK_LOGS TABLE
    # ========================================
    op.create_table(
        'webhook_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('webhook_config_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('attempt_number', sa.Integer(), server_default='1'),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), server_default='false'),
        sa.Column('attempted_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_webhook_logs_webhook_config_id', 'webhook_logs', ['webhook_config_id'])
    op.create_index('ix_webhook_logs_event_type', 'webhook_logs', ['event_type'])
    op.create_index('ix_webhook_logs_success', 'webhook_logs', ['success'])
    op.create_index('ix_webhook_logs_attempted_at', 'webhook_logs', ['attempted_at'])

    # ========================================
    # 6. CREATE DOCUMENT_TEMPLATES TABLE
    # ========================================
    op.create_table(
        'document_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('template_type', sa.String(length=50), nullable=False),
        sa.Column('is_default', sa.Boolean(), server_default='false'),
        sa.Column('factory_id', sa.Integer(), nullable=True),
        sa.Column('header_template', sa.Text(), nullable=True),
        sa.Column('body_template', sa.Text(), nullable=False),
        sa.Column('footer_template', sa.Text(), nullable=True),
        sa.Column('css_styles', sa.Text(), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('font_family', sa.String(length=100), server_default='MS Gothic'),
        sa.Column('available_variables', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('conditional_sections', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('version', sa.String(length=20), server_default='1.0'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['factory_id'], ['factories.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_document_templates_template_type', 'document_templates', ['template_type'])
    op.create_index('ix_document_templates_is_default', 'document_templates', ['is_default'])
    op.create_index('ix_document_templates_factory_id', 'document_templates', ['factory_id'])
    op.create_index('ix_document_templates_is_active', 'document_templates', ['is_active'])

    # ========================================
    # 7. CREATE TEMPLATE_VARIABLES TABLE
    # ========================================
    op.create_table(
        'template_variables',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('variable_name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('data_type', sa.String(length=20), server_default='text'),
        sa.Column('default_value', sa.Text(), nullable=True),
        sa.Column('is_required', sa.Boolean(), server_default='false'),
        sa.Column('validation_regex', sa.String(length=500), nullable=True),
        sa.Column('min_length', sa.Integer(), nullable=True),
        sa.Column('max_length', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='0'),
        sa.ForeignKeyConstraint(['template_id'], ['document_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_template_variables_template_id', 'template_variables', ['template_id'])

    # ========================================
    # 8. ADD WORKFLOW FIELDS TO kobetsu_keiyakusho
    # ========================================

    # Drop old constraint
    op.drop_constraint('ck_kobetsu_status', 'kobetsu_keiyakusho', type_='check')

    # Add new workflow fields
    op.add_column('kobetsu_keiyakusho', sa.Column('approval_status', sa.String(length=20), server_default='pending', nullable=False))
    op.add_column('kobetsu_keiyakusho', sa.Column('approved_by', sa.Integer(), nullable=True))
    op.add_column('kobetsu_keiyakusho', sa.Column('approved_at', sa.DateTime(), nullable=True))
    op.add_column('kobetsu_keiyakusho', sa.Column('rejection_reason', sa.Text(), nullable=True))
    op.add_column('kobetsu_keiyakusho', sa.Column('current_approver_id', sa.Integer(), nullable=True))
    op.add_column('kobetsu_keiyakusho', sa.Column('submitted_for_approval_at', sa.DateTime(), nullable=True))

    # Add indexes
    op.create_index('ix_kobetsu_approval_status', 'kobetsu_keiyakusho', ['approval_status'])
    op.create_index('ix_kobetsu_current_approver', 'kobetsu_keiyakusho', ['current_approver_id'])

    # Add foreign keys
    op.create_foreign_key('fk_kobetsu_approved_by', 'kobetsu_keiyakusho', 'users', ['approved_by'], ['id'])
    op.create_foreign_key('fk_kobetsu_current_approver', 'kobetsu_keiyakusho', 'users', ['current_approver_id'], ['id'])

    # Create new constraint with updated statuses
    op.create_check_constraint(
        'ck_kobetsu_status',
        'kobetsu_keiyakusho',
        "status IN ('draft', 'pending_review', 'pending_approval', 'active', 'expired', 'cancelled', 'renewed')"
    )

    # Create constraint for approval_status
    op.create_check_constraint(
        'ck_kobetsu_approval_status',
        'kobetsu_keiyakusho',
        "approval_status IN ('pending', 'approved', 'rejected')"
    )


def downgrade():
    # Drop constraints
    op.drop_constraint('ck_kobetsu_approval_status', 'kobetsu_keiyakusho', type_='check')
    op.drop_constraint('ck_kobetsu_status', 'kobetsu_keiyakusho', type_='check')

    # Drop foreign keys
    op.drop_constraint('fk_kobetsu_current_approver', 'kobetsu_keiyakusho', type_='foreignkey')
    op.drop_constraint('fk_kobetsu_approved_by', 'kobetsu_keiyakusho', type_='foreignkey')

    # Drop indexes
    op.drop_index('ix_kobetsu_current_approver', 'kobetsu_keiyakusho')
    op.drop_index('ix_kobetsu_approval_status', 'kobetsu_keiyakusho')

    # Drop columns
    op.drop_column('kobetsu_keiyakusho', 'submitted_for_approval_at')
    op.drop_column('kobetsu_keiyakusho', 'current_approver_id')
    op.drop_column('kobetsu_keiyakusho', 'rejection_reason')
    op.drop_column('kobetsu_keiyakusho', 'approved_at')
    op.drop_column('kobetsu_keiyakusho', 'approved_by')
    op.drop_column('kobetsu_keiyakusho', 'approval_status')

    # Recreate old constraint
    op.create_check_constraint(
        'ck_kobetsu_status',
        'kobetsu_keiyakusho',
        "status IN ('draft', 'active', 'expired', 'cancelled', 'renewed')"
    )

    # Drop tables in reverse order
    op.drop_table('template_variables')
    op.drop_table('document_templates')
    op.drop_table('webhook_logs')
    op.drop_table('webhook_configs')
    op.drop_table('contract_comments')
    op.drop_table('contract_versions')
    op.drop_table('audit_logs')
