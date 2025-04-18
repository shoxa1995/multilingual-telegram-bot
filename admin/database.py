"""
Database configuration and session management for the Admin Panel.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from admin.config import DB_URL

# Create SQLAlchemy engine
engine = create_engine(DB_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for SQLAlchemy models
Base = declarative_base()

def get_db():
    """
    Get database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_admin_db():
    """
    Initialize database tables.
    """
    from admin.models import AdminUser
    Base.metadata.create_all(bind=engine)
    
    # Create default admin user if it doesn't exist
    from admin.config import ADMIN_USERNAME, ADMIN_PASSWORD
    from admin.auth import get_password_hash
    
    db = SessionLocal()
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == ADMIN_USERNAME).first()
        if not admin:
            admin = AdminUser(
                username=ADMIN_USERNAME,
                hashed_password=get_password_hash(ADMIN_PASSWORD),
                is_active=True
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()
