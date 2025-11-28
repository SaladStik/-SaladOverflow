from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from .base import Base


def utc_now():
    """Return current UTC time"""
    return datetime.now(timezone.utc)


class User(Base):
    """
    User model for SaladOverflow
    Compatible with NextAuth.js user structure
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(
        String(50), unique=True, index=True, nullable=False
    )  # Internal username

    # Display fields (what users see)
    display_name = Column(
        String(100), unique=True, index=True, nullable=False
    )  # Like @SaladStik
    full_name = Column(String(150), nullable=True)  # Real name (optional)
    bio = Column(Text, nullable=True)  # User bio/description

    # NextAuth.js compatibility fields
    name = Column(String(100), nullable=True)  # For NextAuth.js (maps to display_name)
    image = Column(Text, nullable=True)  # Profile image URL

    # Profile customization
    avatar_url = Column(Text, nullable=True)  # Custom avatar
    banner_url = Column(Text, nullable=True)  # Profile banner image
    website_url = Column(String(255), nullable=True)  # Personal website
    location = Column(String(100), nullable=True)  # User location

    # Social links
    twitter_handle = Column(String(50), nullable=True)  # Without @
    github_username = Column(String(100), nullable=True)
    github_id = Column(String(100), nullable=True)  # GitHub user ID for OAuth
    linkedin_url = Column(String(255), nullable=True)

    # Authentication fields
    password_hash = Column(String(255), nullable=True)  # For local auth
    email_verified = Column(DateTime, nullable=True)

    # OAuth provider fields (for NextAuth.js)
    provider_id = Column(String(100), nullable=True)  # e.g., "google", "github"
    provider_account_id = Column(String(255), nullable=True)

    # User status and metrics
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    # Engagement metrics (will be calculated from posts/comments)
    post_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    karma_score = Column(Integer, default=0)  # Based on upvotes/downvotes

    # Privacy settings
    profile_public = Column(Boolean, default=True)
    show_email = Column(Boolean, default=False)
    show_real_name = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    last_active = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    posts = relationship("Post", back_populates="author")
    comments = relationship("Comment", back_populates="author")
    post_votes = relationship("PostVote", back_populates="user")
    comment_votes = relationship("CommentVote", back_populates="user")
    bookmarks = relationship("Bookmark", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, display_name='@{self.display_name}', email='{self.email}')>"


class Account(Base):
    """
    OAuth accounts table - for NextAuth.js compatibility
    Stores OAuth provider information
    """

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    provider = Column(String(100), nullable=False)  # "google", "github", etc.
    provider_account_id = Column(String(255), nullable=False)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    expires_at = Column(Integer, nullable=True)
    token_type = Column(String(50), nullable=True)
    scope = Column(String(255), nullable=True)
    id_token = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
