from pydantic import (
    BaseModel,
    Field,
    field_validator,
    ConfigDict,
    field_serializer,
    computed_field,
)
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
import re
import html


def format_time_ago(dt: datetime) -> str:
    """Format datetime as 'X time ago' string"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    now = datetime.now(timezone.utc)
    diff = now - dt
    seconds = diff.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 2592000:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} year{'s' if years != 1 else ''} ago"


class PostType(str, Enum):
    QUESTION = "question"
    DISCUSSION = "discussion"
    ANNOUNCEMENT = "announcement"


class VoteType(str, Enum):
    UPVOTE = "upvote"
    DOWNVOTE = "downvote"


# Tag Schemas
class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")

    @field_validator("name")
    def validate_tag_name(cls, v):
        """Validate tag name format"""
        # Convert to lowercase and replace spaces with hyphens
        v = v.lower().strip().replace(" ", "-")

        # Only allow alphanumeric, hyphens, and plus signs
        if not re.match(r"^[a-zA-Z0-9+.-]+$", v):
            raise ValueError(
                "Tag name can only contain letters, numbers, hyphens, dots, and plus signs"
            )

        return v


class TagResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    post_count: int
    follower_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        if dt is None:
            return None
        # Ensure datetime is UTC and properly formatted
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat()


# Post Schemas
class PostCreate(BaseModel):
    title: str = Field(..., min_length=10, max_length=300)
    content: str = Field(..., min_length=10)
    post_type: PostType = PostType.QUESTION
    tags: List[str] = Field(..., min_items=1, max_items=5)

    @field_validator("title")
    def validate_title(cls, v):
        """Clean and validate title"""
        # HTML escape for safety
        v = html.escape(v.strip())

        if len(v) < 10:
            raise ValueError("Title must be at least 10 characters long")

        return v

    @field_validator("content")
    def validate_content(cls, v):
        """Validate and process content"""
        # Basic HTML escaping
        v = v.strip()

        if len(v) < 10:
            raise ValueError("Content must be at least 10 characters long")

        return v

    @field_validator("tags")
    def validate_tags(cls, v):
        """Validate tags list"""
        if len(v) < 1:
            raise ValueError("At least one tag is required")
        if len(v) > 5:
            raise ValueError("Maximum 5 tags allowed")

        # Clean and validate each tag
        cleaned_tags = []
        for tag in v:
            cleaned_tag = tag.lower().strip().replace(" ", "-")
            if not re.match(r"^[a-zA-Z0-9+.-]+$", cleaned_tag):
                raise ValueError(f"Invalid tag format: {tag}")
            cleaned_tags.append(cleaned_tag)

        return cleaned_tags


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=10, max_length=300)
    content: Optional[str] = Field(None, min_length=10)
    tags: Optional[List[str]] = Field(None, min_items=1, max_items=5)

    @field_validator("title")
    def validate_title(cls, v):
        if v is not None:
            v = html.escape(v.strip())
            if len(v) < 10:
                raise ValueError("Title must be at least 10 characters long")
        return v

    @field_validator("content")
    def validate_content(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 10:
                raise ValueError("Content must be at least 10 characters long")
        return v


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    content_plain: Optional[str] = None
    content_markdown: Optional[str] = None
    post_type: PostType
    slug: Optional[str] = None

    # Author info
    author_id: int
    author_display_name: Optional[str] = None
    author_avatar: Optional[str] = None
    author_is_verified: Optional[bool] = None

    # Metrics
    view_count: int
    upvote_count: int
    downvote_count: int
    comment_count: int
    answer_count: int

    # Question specific
    is_answered: bool
    accepted_answer_id: Optional[int] = None

    # Content flags
    has_code: bool
    has_images: bool

    # Status flags
    is_locked: bool
    is_deleted: bool
    is_featured: bool

    # User-specific fields (requires authentication)
    user_vote: Optional[str] = None  # 'upvote', 'downvote', or None
    is_bookmarked: Optional[bool] = None

    # Tags
    tags: List[TagResponse] = []

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_activity: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def created_at_relative(self) -> str:
        """Return relative time string like '5 minutes ago'"""
        return format_time_ago(self.created_at)

    @field_serializer("created_at", "updated_at", "last_activity")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        if dt is None:
            return None
        # Ensure datetime is UTC and properly formatted
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat()


# Comment Schemas
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=5)
    parent_id: Optional[int] = None
    is_answer: bool = False

    @field_validator("content")
    def validate_content(cls, v):
        """Validate and clean comment content"""
        v = v.strip()

        if len(v) < 5:
            raise ValueError("Comment must be at least 5 characters long")

        return v


class CommentUpdate(BaseModel):
    content: str = Field(..., min_length=5)

    @field_validator("content")
    def validate_content(cls, v):
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Comment must be at least 5 characters long")
        return v


class CommentResponse(BaseModel):
    id: int
    content: str
    content_plain: Optional[str] = None
    post_id: int
    parent_id: Optional[int] = None

    # Author info
    author_id: int
    author_display_name: Optional[str] = None
    author_avatar: Optional[str] = None
    author_is_verified: Optional[bool] = None

    # Metrics
    upvote_count: int
    downvote_count: int
    reply_count: int

    # Answer fields
    is_answer: bool
    is_accepted: bool

    # Content flags
    has_code: bool
    has_images: bool

    # Status
    is_deleted: bool

    # Nested replies
    replies: List["CommentResponse"] = []

    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def created_at_relative(self) -> str:
        """Return relative time string like '5 minutes ago'"""
        return format_time_ago(self.created_at)

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        if dt is None:
            return None
        # Ensure datetime is UTC and properly formatted
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat()


# Vote Schemas
class VoteCreate(BaseModel):
    vote_type: VoteType


class VoteResponse(BaseModel):
    id: int
    vote_type: VoteType
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Search and Filter Schemas
class PostFilters(BaseModel):
    tags: Optional[List[str]] = None
    post_type: Optional[PostType] = None
    author_id: Optional[int] = None
    is_answered: Optional[bool] = None
    has_accepted_answer: Optional[bool] = None
    min_votes: Optional[int] = None
    max_votes: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class PostSort(str, Enum):
    NEWEST = "newest"
    OLDEST = "oldest"
    MOST_VOTED = "most_voted"
    MOST_VIEWED = "most_viewed"
    MOST_ANSWERED = "most_answered"
    UNANSWERED = "unanswered"
    ACTIVE = "active"  # Most recent activity


class PostListResponse(BaseModel):
    posts: List[PostResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int


# Content Processing Schemas
class ContentAnalysis(BaseModel):
    """Schema for content analysis results"""

    has_code: bool = False
    has_images: bool = False
    code_blocks: List[str] = []
    image_urls: List[str] = []
    plain_text: str = ""
    word_count: int = 0


# Forward reference update for nested comments
CommentResponse.model_rebuild()
