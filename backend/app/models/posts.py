from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    ForeignKey,
    Table,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from enum import Enum
from .base import Base


def utc_now():
    """Return current UTC time"""
    return datetime.now(timezone.utc)


class PostType(str, Enum):
    QUESTION = "question"
    DISCUSSION = "discussion"
    ANNOUNCEMENT = "announcement"


class VoteType(str, Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"


# Association table for post tags (many-to-many)
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
)


class Post(Base):
    """
    Posts table - questions, discussions, announcements
    """

    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False, index=True)
    content = Column(Text, nullable=False)  # Rich text content (HTML safe)
    content_plain = Column(Text, nullable=True)  # Plain text for search
    content_markdown = Column(Text, nullable=True)  # Original markdown for editing

    # Post metadata
    post_type = Column(SQLEnum(PostType), default=PostType.QUESTION, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Engagement metrics
    view_count = Column(Integer, default=0)
    upvote_count = Column(Integer, default=0)
    downvote_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    answer_count = Column(Integer, default=0)  # For questions

    # Question-specific fields
    is_answered = Column(Boolean, default=False)  # Has accepted answer
    accepted_answer_id = Column(Integer, ForeignKey("comments.id"), nullable=True)

    # Content flags
    has_code = Column(Boolean, default=False)  # Contains code blocks
    has_images = Column(Boolean, default=False)  # Contains images

    # Moderation
    is_locked = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)

    # SEO
    slug = Column(String(400), nullable=True, index=True)  # URL-friendly title

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    last_activity = Column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )

    # Relationships
    author = relationship("User", back_populates="posts")
    comments = relationship(
        "Comment",
        back_populates="post",
        foreign_keys="Comment.post_id",
        cascade="all, delete-orphan",
    )
    votes = relationship(
        "PostVote", back_populates="post", cascade="all, delete-orphan"
    )
    tags = relationship("Tag", secondary=post_tags, back_populates="posts")
    accepted_answer = relationship(
        "Comment", foreign_keys=[accepted_answer_id], uselist=False
    )

    def __repr__(self):
        return f"<Post(id={self.id}, title='{self.title[:50]}...', author_id={self.author_id})>"


class Comment(Base):
    """
    Comments table - answers and replies
    """

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)  # Rich text content
    content_plain = Column(Text, nullable=True)  # Plain text for search

    # Comment metadata
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    parent_id = Column(
        Integer, ForeignKey("comments.id"), nullable=True, index=True
    )  # For nested replies

    # Engagement metrics
    upvote_count = Column(Integer, default=0)
    downvote_count = Column(Integer, default=0)
    reply_count = Column(Integer, default=0)

    # Answer-specific fields
    is_answer = Column(Boolean, default=False)  # Is this an answer to the question?
    is_accepted = Column(Boolean, default=False)  # Accepted by question author

    # Content flags
    has_code = Column(Boolean, default=False)
    has_images = Column(Boolean, default=False)

    # Moderation
    is_deleted = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    post = relationship("Post", back_populates="comments", foreign_keys=[post_id])
    author = relationship("User", back_populates="comments")
    parent = relationship(
        "Comment", remote_side=[id], foreign_keys=[parent_id], backref="replies"
    )
    votes = relationship(
        "CommentVote", back_populates="comment", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Comment(id={self.id}, post_id={self.post_id}, author_id={self.author_id})>"


class Tag(Base):
    """
    Tags for categorizing posts
    """

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex color code

    # Usage metrics
    post_count = Column(Integer, default=0)
    follower_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )

    # Relationships
    posts = relationship("Post", secondary=post_tags, back_populates="tags")

    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"


class PostVote(Base):
    """
    Votes on posts
    """

    __tablename__ = "post_votes"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    vote_type = Column(SQLEnum(VoteType), nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    post = relationship("Post", back_populates="votes")
    user = relationship("User", back_populates="post_votes")

    # Unique constraint - one vote per user per post
    __table_args__ = ({"mysql_engine": "InnoDB"},)

    def __repr__(self):
        return f"<PostVote(id={self.id}, post_id={self.post_id}, user_id={self.user_id}, vote={self.vote_type})>"


class CommentVote(Base):
    """
    Votes on comments
    """

    __tablename__ = "comment_votes"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(Integer, ForeignKey("comments.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    vote_type = Column(SQLEnum(VoteType), nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    # Relationships
    comment = relationship("Comment", back_populates="votes")
    user = relationship("User", back_populates="comment_votes")

    def __repr__(self):
        return f"<CommentVote(id={self.id}, comment_id={self.comment_id}, user_id={self.user_id}, vote={self.vote_type})>"


class Bookmark(Base):
    """
    User bookmarks for posts
    """

    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), default=utc_now, server_default=func.now()
    )

    # Relationships
    post = relationship("Post")
    user = relationship("User", back_populates="bookmarks")

    # Unique constraint - one bookmark per user per post
    __table_args__ = ({"mysql_engine": "InnoDB"},)

    def __repr__(self):
        return (
            f"<Bookmark(id={self.id}, post_id={self.post_id}, user_id={self.user_id})>"
        )
