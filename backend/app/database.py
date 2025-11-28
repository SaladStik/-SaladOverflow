from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import redis
from app.config import settings
from app.models.user import Base
from app.models.posts import Post, Comment, Tag, PostVote, CommentVote
import logging

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug,  # Log SQL queries in debug mode
    connect_args={"init_command": "SET time_zone='+00:00'"},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Database dependency for FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all database tables
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def init_db():
    """
    Initialize database - create tables if they don't exist
    """
    create_tables()


# Redis connection
redis_client = None


def get_redis_client():
    """
    Get Redis client instance
    """
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(settings.redis_url)
            # Test connection
            redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            redis_client = None
    return redis_client


def get_redis():
    """
    Redis dependency for FastAPI
    """
    client = get_redis_client()
    if client:
        return client
    else:
        # Return a mock Redis client that doesn't actually cache
        return MockRedisClient()


class MockRedisClient:
    """
    Mock Redis client for when Redis is unavailable
    """

    def get(self, key):
        return None

    def setex(self, key, seconds, value):
        pass

    def ping(self):
        return True
