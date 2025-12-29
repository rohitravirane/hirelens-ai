"""
Script to create test data for development
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User, Role
from app.models.job import JobDescription
from app.models.resume import Resume, ResumeVersion
from app.models.candidate import Candidate
from app.auth.service import get_password_hash
import structlog

logger = structlog.get_logger()


def create_test_users(db: Session):
    """Create test users"""
    recruiter_role = db.query(Role).filter(Role.name == "recruiter").first()
    hiring_manager_role = db.query(Role).filter(Role.name == "hiring_manager").first()
    
    users = [
        {
            "email": "recruiter@hirelens.ai",
            "password": "recruiter123",
            "full_name": "Test Recruiter",
            "role": recruiter_role,
        },
        {
            "email": "manager@hirelens.ai",
            "password": "manager123",
            "full_name": "Test Hiring Manager",
            "role": hiring_manager_role,
        },
    ]
    
    for user_data in users:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing:
            user = User(
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                full_name=user_data["full_name"],
                is_active=True,
                is_verified=True,
            )
            user.roles = [user_data["role"]]
            db.add(user)
            logger.info("test_user_created", email=user_data["email"])


def create_test_job(db: Session):
    """Create a test job description"""
    admin = db.query(User).filter(User.email == "rohitravikantrane@gmail.com").first()
    if not admin:
        logger.warning("admin_user_not_found")
        return
    
    existing = db.query(JobDescription).filter(JobDescription.title == "Senior Backend Engineer").first()
    if existing:
        logger.info("test_job_exists")
        return
    
    job = JobDescription(
        title="Senior Backend Engineer",
        company="Tech Corp",
        department="Engineering",
        raw_text="""
        We are looking for a Senior Backend Engineer to join our team.
        
        Required Skills:
        - Python (5+ years)
        - FastAPI or Django
        - PostgreSQL
        - AWS
        - Docker
        - REST API design
        - Microservices architecture
        
        Nice to Have:
        - Kubernetes
        - GraphQL
        - Redis
        - CI/CD experience
        
        Experience: 5+ years of backend development experience required.
        """,
        required_skills=["python", "fastapi", "postgresql", "aws", "docker"],
        nice_to_have_skills=["kubernetes", "graphql", "redis"],
        experience_years_required=5,
        seniority_level="senior",
        location="San Francisco, CA",
        remote_allowed=True,
        employment_type="full-time",
        created_by=admin.id,
        is_active=True,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info("test_job_created", job_id=job.id)


def main():
    """Main function"""
    db: Session = SessionLocal()
    try:
        create_test_users(db)
        create_test_job(db)
        db.commit()
        logger.info("test_data_created")
    except Exception as e:
        logger.error("test_data_creation_failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

