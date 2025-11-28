#!/usr/bin/env python3
"""
Database initialization script to run INSIDE Docker container
This script will be copied into the container and executed there
"""
import sys
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

# Create Base
Base = declarative_base()

# Import all models here to register them with Base
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey,
    Table,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum


# User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(100))
    password_hash = Column(String(255))
    is_email_verified = Column(Boolean, default=False)
    reputation = Column(Integer, default=0)
    bio = Column(Text)
    avatar_url = Column(String(500))
    github_id = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    posts = relationship("Post", back_populates="author", foreign_keys="Post.author_id")
    comments = relationship(
        "Comment", back_populates="author", foreign_keys="Comment.author_id"
    )
    post_votes = relationship("PostVote", back_populates="user")
    comment_votes = relationship("CommentVote", back_populates="user")
    accounts = relationship("Account", back_populates="user")


# Account model (for OAuth)
class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider = Column(String(50), nullable=False)
    provider_account_id = Column(String(255), nullable=False)
    access_token = Column(Text)
    refresh_token = Column(Text)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="accounts")


# Post model
class VoteType(enum.Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    view_count = Column(Integer, default=0)
    vote_count = Column(Integer, default=0)
    is_answered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author = relationship("User", back_populates="posts", foreign_keys=[author_id])
    comments = relationship(
        "Comment",
        back_populates="post",
        foreign_keys="Comment.post_id",
        cascade="all, delete-orphan",
    )
    votes = relationship(
        "PostVote", back_populates="post", cascade="all, delete-orphan"
    )
    tags = relationship("Tag", secondary="post_tags", back_populates="posts")


# Comment model
class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    post_id = Column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    author_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    parent_id = Column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    is_answer = Column(Boolean, default=False)
    is_accepted = Column(Boolean, default=False)
    vote_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    post = relationship("Post", back_populates="comments", foreign_keys=[post_id])
    author = relationship("User", back_populates="comments", foreign_keys=[author_id])
    parent = relationship(
        "Comment", remote_side=[id], backref="replies", foreign_keys=[parent_id]
    )
    votes = relationship(
        "CommentVote", back_populates="comment", cascade="all, delete-orphan"
    )


# Tag model
class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text)
    post_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    posts = relationship("Post", secondary="post_tags", back_populates="tags")


# PostVote model
class PostVote(Base):
    __tablename__ = "post_votes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    vote_type = Column(SQLEnum(VoteType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    post = relationship("Post", back_populates="votes")
    user = relationship("User", back_populates="post_votes")


# CommentVote model
class CommentVote(Base):
    __tablename__ = "comment_votes"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    vote_type = Column(SQLEnum(VoteType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    comment = relationship("Comment", back_populates="votes")
    user = relationship("User", back_populates="comment_votes")


# EmailVerificationToken model
class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# PasswordResetToken model
class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# Association table for post_tags
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column(
        "post_id", Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    ),
)


def init_db():
    """Initialize database tables"""
    try:
        print("Creating database tables...")

        # Connect to database running on localhost from inside container
        DATABASE_URL = "mysql://salad_user:salad_password@localhost:3306/saladoverflow"

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
