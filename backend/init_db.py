"""
Database initialization script
Creates all tables for SaladOverflow
"""

import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.database import Base, engine
from app.models import *  # Import all models


def init_db():
    """Initialize database tables"""
    print("Creating database tables...")

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")

        # List created tables
        from sqlalchemy import inspect

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print(f"\n📊 Created {len(tables)} tables:")
        for table in sorted(tables):
            print(f"  - {table}")

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise


if __name__ == "__main__":
    init_db()
