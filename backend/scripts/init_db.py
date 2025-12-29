"""
Initialize database with default roles and admin user
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal, init_db
from app.models.user import User, Role
from app.auth.service import get_password_hash
import structlog

logger = structlog.get_logger()


def create_default_roles(db: Session):
    """Create default roles"""
    roles = [
        {
            "name": "admin",
            "description": "System administrator with full access",
            "permissions": '["*"]',
        },
        {
            "name": "recruiter",
            "description": "Recruiter with access to manage jobs and candidates",
            "permissions": '["jobs:read", "jobs:write", "candidates:read", "candidates:write", "resumes:read", "resumes:write", "matching:read"]',
        },
        {
            "name": "hiring_manager",
            "description": "Hiring manager with read-only access to insights",
            "permissions": '["jobs:read", "candidates:read", "matching:read"]',
        },
    ]
    
    for role_data in roles:
        existing = db.query(Role).filter(Role.name == role_data["name"]).first()
        if not existing:
            role = Role(**role_data)
            db.add(role)
            logger.info("role_created", role=role_data["name"])
        else:
            logger.info("role_exists", role=role_data["name"])
    
    db.commit()


def create_admin_user(db: Session):
    """Create default admin user"""
    admin_email = "rohitravikantrane@gmail.com"
    admin_password = "admin123"  # Change in production!
    
    existing = db.query(User).filter(User.email == admin_email).first()
    if existing:
        logger.info("admin_user_exists", email=admin_email)
        return
    
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        logger.error("admin_role_not_found")
        return
    
    admin_user = User(
        email=admin_email,
        hashed_password=get_password_hash(admin_password),
        full_name="Rohit Rane",
        is_active=True,
        is_verified=True,
    )
    admin_user.roles = [admin_role]
    
    db.add(admin_user)
    db.commit()
    
    logger.info("admin_user_created", email=admin_email, password=admin_password)


def main():
    """Main initialization function"""
    logger.info("initializing_database")
    
    # Initialize database tables
    init_db()
    
    # Create session
    db: Session = SessionLocal()
    try:
        # Create default roles
        create_default_roles(db)
        
        # Create admin user
        create_admin_user(db)
        
        logger.info("database_initialization_complete")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

