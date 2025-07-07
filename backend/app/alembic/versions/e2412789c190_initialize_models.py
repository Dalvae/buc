"""Initialize models

Revision ID: e2412789c190
Revises: None
Create Date: 2023-11-24 22:55:43.195942

"""
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e2412789c190"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Step 0: Enable necessary extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Step 1: Create all ENUM types explicitly and safely.
    userrole_enum = postgresql.ENUM('ADMIN', 'AUDITOR', 'USER', name='userrole', create_type=False)
    userrole_enum.create(op.get_bind(), checkfirst=True)
    questiontype_enum = postgresql.ENUM('TEXT', 'MULTIPLE_CHOICE_SINGLE', 'MULTIPLE_CHOICE_MULTIPLE', 'YES_NO', 'RATING_SCALE', 'SECTION_HEADER', name='questiontype', create_type=False)
    questiontype_enum.create(op.get_bind(), checkfirst=True)
    auditassignmentstatus_enum = postgresql.ENUM('PENDING', 'IN_PROGRESS', 'COMPLETED', 'OVERDUE', name='auditassignmentstatus', create_type=False)
    auditassignmentstatus_enum.create(op.get_bind(), checkfirst=True)
    auditperiodicity_enum = postgresql.ENUM('ONE_TIME', 'DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'ANNUALLY', name='auditperiodicity', create_type=False)
    auditperiodicity_enum.create(op.get_bind(), checkfirst=True)
    auditresponsestatus_enum = postgresql.ENUM('DRAFT', 'SUBMITTED', name='auditresponsestatus', create_type=False)
    auditresponsestatus_enum.create(op.get_bind(), checkfirst=True)
    
    # Step 2: Create tables in dependency order.
    
    # User Table
    op.create_table('user',
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('role', userrole_enum, nullable=False, server_default='USER'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False)
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    
    # Company Table
    op.create_table('company',
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('details', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('is_demo', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False)
    )
    op.create_index(op.f('ix_company_name'), 'company', ['name'], unique=True)
    op.create_foreign_key('fk_user_company_id', 'user', 'company', ['company_id'], ['id'])

    # Area Table
    op.create_table('area',
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['company.id'], ),
        sa.UniqueConstraint('name', 'company_id', name='uq_area_name_company_id')
    )

    # User-Area Link Table
    op.create_table('user_area_assignment_link',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('area_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['area_id'], ['area.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'area_id')
    )

    # Audit Template Table
    op.create_table('audit_template',
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False, unique=True),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('audit_type_definition_key', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], )
    )
    
    # Question Template Table
    op.create_table('question_template',
        sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('text', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('question_type', questiontype_enum, nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('is_mandatory', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('section_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('scoring_weight', sa.Float(), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('audit_template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['audit_template_id'], ['audit_template.id'], )
    )

    # Audit Assignment Table
    op.create_table('audit_assignment',
        sa.Column('title', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('description', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('status', auditassignmentstatus_enum, nullable=False, server_default='PENDING'),
        sa.Column('periodicity', auditperiodicity_enum, nullable=True),
        sa.Column('next_due_date', sa.Date(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('audit_template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('area_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['area_id'], ['area.id'], ),
        sa.ForeignKeyConstraint(['audit_template_id'], ['audit_template.id'], ),
        sa.ForeignKeyConstraint(['company_id'], ['company.id'], ),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], )
    )

    # Assigned Question Table
    op.create_table('assigned_question',
        sa.Column('text', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('question_type', questiontype_enum, nullable=False),
        sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('is_mandatory', sa.Boolean(), nullable=False),
        sa.Column('section_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('audit_assignment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('original_question_template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['audit_assignment_id'], ['audit_assignment.id'], ),
        sa.ForeignKeyConstraint(['original_question_template_id'], ['question_template.id'], )
    )

    # Audit Response Table
    op.create_table('audit_response',
        sa.Column('overall_comments', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('photo_urls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', auditresponsestatus_enum, nullable=False, server_default='DRAFT'),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('audit_assignment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('auditor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('submission_date', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['audit_assignment_id'], ['audit_assignment.id'], ),
        sa.ForeignKeyConstraint(['auditor_id'], ['user.id'], )
    )

    # Answer Table
    op.create_table('answer',
        sa.Column('answer_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('comments', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('photo_urls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column('audit_response_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assigned_question_id'], ['assigned_question.id'], ),
        sa.ForeignKeyConstraint(['audit_response_id'], ['audit_response.id'], )
    )


def downgrade():
    op.drop_table('answer')
    op.drop_table('audit_response')
    op.drop_table('assigned_question')
    op.drop_table('audit_assignment')
    op.drop_table('question_template')
    op.drop_table('audit_template')
    op.drop_table('user_area_assignment_link')
    op.drop_table('area')
    op.drop_constraint('fk_user_company_id', 'user', type_='foreignkey')
    op.drop_index(op.f('ix_company_name'), table_name='company')
    op.drop_table('company')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    
    op.execute('DROP TYPE IF EXISTS auditresponsestatus;')
    op.execute('DROP TYPE IF EXISTS auditperiodicity;')
    op.execute('DROP TYPE IF EXISTS auditassignmentstatus;')
    op.execute('DROP TYPE IF EXISTS questiontype;')
    op.execute('DROP TYPE IF EXISTS userrole;')
