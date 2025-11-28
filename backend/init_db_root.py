#!/usr/bin/env python3
"""
Database initialization script using root user
"""
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from app.models.base import Base
from app.models import (
    User,
    Account,
    Post,
    Comment,
    Tag,
    PostVote,
    CommentVote,
    EmailVerificationToken,
    PasswordResetToken,
)


def init_db():
    """Initialize database tables"""
    try:
        print("Creating database tables...")

        # Use root credentials temporarily
        DATABASE_URL = "mysql://root:root_password@127.0.0.1:3306/saladoverflow"

        engine = create_engine(DATABASE_URL, echo=True)

        # Create all tables
        Base.metadata.create_all(bind=engine)

        print("✅ Database tables created successfully!")

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    init_db()
