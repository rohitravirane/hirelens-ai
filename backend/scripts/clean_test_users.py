"""
Remove test users (keep only admin user)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User
import structlog

logger = structlog.get_logger()


def clean_test_users():
    """Remove test users, keep only admin"""
    db: Session = SessionLocal()
    try:
        # Keep admin user
        admin = db.query(User).filter(User.email == "admin@hirelens.ai").first()
        
        if not admin:
            print("❌ Admin user not found!")
            return
        
        # Delete all other users
        test_users = db.query(User).filter(User.id != admin.id).all()
        test_users_count = len(test_users)
        
        for user in test_users:
            db.delete(user)
            logger.info("deleted_test_user", email=user.email)
        
        db.commit()
        
        print(f"\n✅ Test users cleaned!")
        print(f"   - Deleted {test_users_count} test users")
        print(f"   - Kept admin user: {admin.email}")
        
    except Exception as e:
        logger.error("cleanup_failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clean_test_users()

