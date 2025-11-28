from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    ConfigDict,
    field_serializer,
)
from typing import Optional
from datetime import datetime, timezone
import re


class UserRegistration(BaseModel):
    """
    Schema for user registration
    """

    email: EmailStr = Field(..., description="User's email address")
    username: str = Field(
        ..., min_length=3, max_length=50, description="Internal username (lowercase)"
    )
    display_name: str = Field(
        ..., min_length=2, max_length=50, description="Display name like @SaladStik"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=72,
        description="User's password (max 72 chars for bcrypt)",
    )
    full_name: Optional[str] = Field(
        None, max_length=150, description="Real name (optional)"
    )
    bio: Optional[str] = Field(None, max_length=500, description="User bio/description")

    @field_validator("username")
    def validate_username(cls, v):
        """
        Validate username format - internal identifier
        """
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, underscores, and hyphens"
            )
        return v.lower()

    @field_validator("display_name")
    def validate_display_name(cls, v):
        """
        Validate display name format - what users see (like @SaladStik)
        """
        # Remove @ if user includes it
        if v.startswith("@"):
            v = v[1:]

        # Check format - allow letters, numbers, underscores
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Display name can only contain letters, numbers, and underscores"
            )

        if len(v) < 2:
            raise ValueError("Display name must be at least 2 characters")

        return v

    @field_validator("password")
    def validate_password(cls, v):
        """
        Basic password validation
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v


class UserResponse(BaseModel):
    """
    Schema for user response (without sensitive data)
    """

    id: int
    email: str
    username: str  # Internal username
    display_name: str  # What users see (like @SaladStik)
    full_name: Optional[str] = None
    bio: Optional[str] = None

    # Profile images
    image: Optional[str] = None  # For NextAuth.js compatibility
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None

    # Profile info
    website_url: Optional[str] = None
    location: Optional[str] = None

    # Social links
    twitter_handle: Optional[str] = None
    github_username: Optional[str] = None
    linkedin_url: Optional[str] = None

    # Status and metrics
    is_active: bool
    is_verified: bool
    post_count: int
    comment_count: int
    karma_score: int

    # Privacy settings
    profile_public: bool
    show_email: bool
    show_real_name: bool

    # Timestamps
    created_at: datetime
    last_active: Optional[datetime] = None

    # For NextAuth.js compatibility
    name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "last_active")
    def serialize_datetime(self, dt: Optional[datetime], _info):
        if dt is None:
            return None
        # Ensure datetime is UTC and properly formatted
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat()


class UserLogin(BaseModel):
    """
    Schema for user login
    """

    email: str = Field(..., description="User's email or username")
    password: str = Field(..., description="User's password")


class PasswordResetRequest(BaseModel):
    """
    Schema for requesting password reset
    """

    email: EmailStr = Field(..., description="Email address to send password reset to")


class PasswordReset(BaseModel):
    """
    Schema for resetting password with token
    """

    token: str = Field(..., description="Password reset token from email")
    email: EmailStr = Field(..., description="Email address")
    new_password: str = Field(
        ..., min_length=8, description="New password (min 8 characters)"
    )

    @field_validator("new_password")
    def validate_new_password(cls, v):
        """
        Validate new password
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v


class UserUpdate(BaseModel):
    """
    Schema for updating user profile
    """

    display_name: Optional[str] = Field(None, min_length=2, max_length=50)
    full_name: Optional[str] = Field(None, max_length=150)
    bio: Optional[str] = Field(None, max_length=500)

    # Profile images
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    website_url: Optional[str] = None
    location: Optional[str] = Field(None, max_length=100)

    # Social links
    twitter_handle: Optional[str] = Field(None, max_length=50)
    github_username: Optional[str] = Field(None, max_length=100)
    linkedin_url: Optional[str] = None

    # Privacy settings
    profile_public: Optional[bool] = None
    show_email: Optional[bool] = None
    show_real_name: Optional[bool] = None

    @field_validator("display_name")
    def validate_display_name(cls, v):
        """
        Validate display name format
        """
        if v is None:
            return v

        # Remove @ if user includes it
        if v.startswith("@"):
            v = v[1:]

        # Check format - allow letters, numbers, underscores
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Display name can only contain letters, numbers, and underscores"
            )

        return v

    @field_validator("twitter_handle")
    def validate_twitter_handle(cls, v):
        """
        Validate Twitter handle (remove @ if present)
        """
        if v is None:
            return v
        if v.startswith("@"):
            v = v[1:]
        return v

    model_config = ConfigDict(from_attributes=True)


class UserPublicProfile(BaseModel):
    """
    Public profile schema (respects privacy settings)
    """

    id: int
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    website_url: Optional[str] = None
    location: Optional[str] = None

    # Social links (only if public)
    twitter_handle: Optional[str] = None
    github_username: Optional[str] = None
    linkedin_url: Optional[str] = None

    # Conditional fields based on privacy settings
    full_name: Optional[str] = None  # Only if show_real_name is True
    email: Optional[str] = None  # Only if show_email is True

    # Public metrics
    post_count: int
    comment_count: int
    karma_score: int
    is_verified: bool

    # Join date
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


class TokenResponse(BaseModel):
    """
    JWT token response
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
