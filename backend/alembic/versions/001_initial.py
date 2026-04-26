"""Initial migration - create all tables

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('email', sa.String(255), unique=True, index=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), default=True),
    )

    # user_profiles
    op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), unique=True),
        sa.Column('resume_text', sa.Text()),
        sa.Column('resume_file_path', sa.String(500)),
        sa.Column('parsed_resume', postgresql.JSON()),
        sa.Column('phone', sa.String(50)),
        sa.Column('linkedin_url', sa.String(500)),
        sa.Column('github_url', sa.String(500)),
        sa.Column('portfolio_url', sa.String(500)),
        sa.Column('location', sa.String(255)),
        sa.Column('target_roles', postgresql.ARRAY(sa.String())),
        sa.Column('target_industries', postgresql.ARRAY(sa.String())),
        sa.Column('preferred_locations', postgresql.ARRAY(sa.String())),
        sa.Column('work_mode_preference', sa.Enum('remote', 'hybrid', 'onsite', name='workmode')),
        sa.Column('experience_level', sa.Enum('intern', 'entry', 'mid', 'senior', 'staff', 'principal', 'executive', name='experiencelevel')),
        sa.Column('job_types', postgresql.ARRAY(sa.String()), default=['full_time']),
        sa.Column('min_salary', sa.Integer()),
        sa.Column('max_salary', sa.Integer()),
        sa.Column('visa_sponsorship_required', sa.Boolean(), default=False),
        sa.Column('willing_to_relocate', sa.Boolean(), default=False),
        sa.Column('notice_period_days', sa.Integer(), default=30),
        sa.Column('auto_apply_enabled', sa.Boolean(), default=False),
        sa.Column('auto_apply_min_match_score', sa.Float(), default=0.80),
        sa.Column('auto_apply_max_daily', sa.Integer(), default=5),
        sa.Column('require_approval_companies', postgresql.ARRAY(sa.String())),
        sa.Column('excluded_industries', postgresql.ARRAY(sa.String())),
        sa.Column('excluded_companies', postgresql.ARRAY(sa.String())),
        sa.Column('skills', postgresql.ARRAY(sa.String())),
        sa.Column('strengths', postgresql.ARRAY(sa.String())),
        sa.Column('gaps', postgresql.ARRAY(sa.String())),
        sa.Column('transferable_skills', postgresql.ARRAY(sa.String())),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # platform_credentials
    op.create_table(
        'platform_credentials',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('platform', sa.String(100), nullable=False),
        sa.Column('username_encrypted', sa.Text()),
        sa.Column('password_encrypted', sa.Text()),
        sa.Column('cookies_encrypted', sa.Text()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('last_used', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # job_listings
    op.create_table(
        'job_listings',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('source_platform', sa.String(100), nullable=False, index=True),
        sa.Column('source_url', sa.String(1000), unique=True, index=True),
        sa.Column('external_id', sa.String(255), index=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('company', sa.String(255), nullable=False, index=True),
        sa.Column('company_size', sa.String(50)),
        sa.Column('company_industry', sa.String(100)),
        sa.Column('location', sa.String(255)),
        sa.Column('work_mode', sa.Enum('remote', 'hybrid', 'onsite', name='workmode')),
        sa.Column('job_type', sa.Enum('full_time', 'part_time', 'contract', 'internship', 'freelance', name='jobtype')),
        sa.Column('experience_level', sa.Enum('intern', 'entry', 'mid', 'senior', 'staff', 'principal', 'executive', name='experiencelevel')),
        sa.Column('description', sa.Text()),
        sa.Column('requirements', postgresql.ARRAY(sa.String())),
        sa.Column('responsibilities', postgresql.ARRAY(sa.String())),
        sa.Column('skills_required', postgresql.ARRAY(sa.String())),
        sa.Column('salary_min', sa.Integer()),
        sa.Column('salary_max', sa.Integer()),
        sa.Column('salary_currency', sa.String(10), default='USD'),
        sa.Column('salary_period', sa.String(20), default='yearly'),
        sa.Column('apply_url', sa.String(1000)),
        sa.Column('apply_method', sa.String(50)),
        sa.Column('application_deadline', sa.DateTime()),
        sa.Column('is_ai_role', sa.Boolean(), default=False),
        sa.Column('ai_role_category', sa.String(100)),
        sa.Column('is_scam_flagged', sa.Boolean(), default=False),
        sa.Column('scam_reason', sa.String(500)),
        sa.Column('posted_at', sa.DateTime()),
        sa.Column('discovered_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_duplicate', sa.Boolean(), default=False),
        sa.Column('duplicate_of_id', sa.Integer(), sa.ForeignKey('job_listings.id')),
    )

    # job_match_scores
    op.create_table(
        'job_match_scores',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('job_listings.id')),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('overall_score', sa.Float(), nullable=False, index=True),
        sa.Column('skills_match', sa.Float()),
        sa.Column('experience_match', sa.Float()),
        sa.Column('location_match', sa.Float()),
        sa.Column('salary_match', sa.Float()),
        sa.Column('role_match', sa.Float()),
        sa.Column('culture_match', sa.Float()),
        sa.Column('matching_skills', postgresql.ARRAY(sa.String())),
        sa.Column('missing_skills', postgresql.ARRAY(sa.String())),
        sa.Column('transferable_skills_applicable', postgresql.ARRAY(sa.String())),
        sa.Column('gap_analysis', sa.Text()),
        sa.Column('recommendation', sa.Text()),
        sa.Column('tailored_resume_bullets', postgresql.JSON()),
        sa.Column('generated_cover_letter', sa.Text()),
        sa.Column('ats_keywords', postgresql.ARRAY(sa.String())),
        sa.Column('why_company_answer', sa.Text()),
        sa.Column('why_role_answer', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # job_applications
    op.create_table(
        'job_applications',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('job_id', sa.Integer(), sa.ForeignKey('job_listings.id')),
        sa.Column('status', sa.Enum('new', 'pending_approval', 'auto_applying', 'applied', 'screening', 'interview', 'offer', 'rejected', 'ghosted', 'withdrawn', 'saved', 'expired', name='applicationstatus'), default='new'),
        sa.Column('status_history', postgresql.JSON(), default=list),
        sa.Column('applied_at', sa.DateTime()),
        sa.Column('auto_applied', sa.Boolean(), default=False),
        sa.Column('required_approval', sa.Boolean(), default=False),
        sa.Column('approved_at', sa.DateTime()),
        sa.Column('approved_by', sa.String(50)),
        sa.Column('form_data', postgresql.JSON()),
        sa.Column('uploaded_resume_path', sa.String(500)),
        sa.Column('cover_letter_path', sa.String(500)),
        sa.Column('screening_answers', postgresql.JSON()),
        sa.Column('recruiter_name', sa.String(255)),
        sa.Column('recruiter_email', sa.String(255)),
        sa.Column('recruiter_phone', sa.String(50)),
        sa.Column('last_contact_date', sa.DateTime()),
        sa.Column('next_follow_up_date', sa.DateTime()),
        sa.Column('interview_rounds', postgresql.JSON(), default=list),
        sa.Column('offer_details', postgresql.JSON()),
        sa.Column('application_logs', postgresql.JSON(), default=list),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # job_alerts
    op.create_table(
        'job_alerts',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('alert_type', sa.String(50)),
        sa.Column('title', sa.String(255)),
        sa.Column('content', sa.Text()),
        sa.Column('jobs_referenced', postgresql.ARRAY(sa.Integer())),
        sa.Column('is_read', sa.Boolean(), default=False),
        sa.Column('sent_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # application_logs
    op.create_table(
        'application_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('application_id', sa.Integer(), sa.ForeignKey('job_applications.id')),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('details', postgresql.JSON()),
        sa.Column('screenshot_path', sa.String(500)),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('success', sa.Boolean()),
        sa.Column('error_message', sa.Text()),
    )

    # learning_feedback
    op.create_table(
        'learning_feedback',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('application_id', sa.Integer(), sa.ForeignKey('job_applications.id')),
        sa.Column('outcome', sa.String(50)),
        sa.Column('feedback_text', sa.Text()),
        sa.Column('successful_elements', postgresql.ARRAY(sa.String())),
        sa.Column('failed_elements', postgresql.ARRAY(sa.String())),
        sa.Column('match_score_at_apply', sa.Float()),
        sa.Column('resume_version', sa.String(50)),
        sa.Column('cover_letter_version', sa.String(50)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index('idx_platform_user', 'platform_credentials', ['user_id', 'platform'])
    op.create_index('idx_job_search', 'job_listings', ['title', 'company'])
    op.create_index('idx_job_active', 'job_listings', ['is_active', 'discovered_at'])
    op.create_index('idx_match_user_score', 'job_match_scores', ['user_id', 'overall_score'])
    op.create_index('idx_app_user_status', 'job_applications', ['user_id', 'status'])
    op.create_index('idx_app_dates', 'job_applications', ['applied_at', 'next_follow_up_date'])


def downgrade() -> None:
    op.drop_table('learning_feedback')
    op.drop_table('application_logs')
    op.drop_table('job_alerts')
    op.drop_table('job_applications')
    op.drop_table('job_match_scores')
    op.drop_table('job_listings')
    op.drop_table('platform_credentials')
    op.drop_table('user_profiles')
    op.drop_table('users')

    op.drop_index('idx_platform_user')
    op.drop_index('idx_job_search')
    op.drop_index('idx_job_active')
    op.drop_index('idx_match_user_score')
    op.drop_index('idx_app_user_status')
    op.drop_index('idx_app_dates')
