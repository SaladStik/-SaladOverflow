from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db, get_redis
from app.models.user import User
from app.models.tokens import (
    EmailVerificationToken,
    PasswordResetToken,
    PasswordResetToken,
)
from app.schemas.user import (
    UserRegistration,
    UserResponse,
    UserLogin,
    TokenResponse,
    UserUpdate,
    UserPublicProfile,
    PasswordResetRequest,
    PasswordReset,
)
from app.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.config import settings
from app.services.email_service import email_service
from datetime import timedelta, datetime
import logging
import redis
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

# Cache settings
CACHE_TTL_SHORT = 300  # 5 minutes for availability checks
CACHE_TTL_MEDIUM = 1800  # 30 minutes for profiles


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(user_data: UserRegistration, db: Session = Depends(get_db)):
    """
    Register a new user account

    This endpoint creates a new user account that can be used alongside NextAuth.js.
    For OAuth users (via NextAuth.js), you may not need this endpoint.
    """
    try:
        # Check if user already exists
        existing_user = (
            db.query(User)
            .filter(
                (User.email == user_data.email)
                | (User.username == user_data.username)
                | (User.display_name == user_data.display_name)
            )
            .first()
        )

        if existing_user:
            if existing_user.email == user_data.email:
                logger.info(
                    f"Registration failed: Email already registered - {user_data.email}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered",
                )
            elif existing_user.username == user_data.username:
                logger.info(
                    f"Registration failed: Username already taken - {user_data.username}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken",
                )
            else:
                logger.info(
                    f"Registration failed: Display name already taken - {user_data.display_name}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Display name already taken",
                )

        # Hash the password
        hashed_password = hash_password(user_data.password)

        # Create new user
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            display_name=user_data.display_name,
            full_name=user_data.full_name,
            bio=user_data.bio,
            name=user_data.display_name,  # For NextAuth.js compatibility
            password_hash=hashed_password,
            is_active=True,
            is_verified=False,  # You can implement email verification later
            profile_public=True,  # Default to public profile
            show_email=False,  # Default to private email
            show_real_name=False,  # Default to private real name
        )

        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        # Invalidate availability caches for username, email, and display_name
        # This is imported at function level to avoid circular dependency
        try:
            from app.database import get_redis

            redis_client = next(get_redis())
            redis_client.delete(f"auth:username:{db_user.username.lower()}")
            redis_client.delete(f"auth:email:{db_user.email}")
            redis_client.delete(f"auth:display_name:{db_user.display_name}")
            # Clear user stats cache since we added a user
            redis_client.delete("users:stats")
            # Clear top users cache
            for key in redis_client.scan_iter(match="users:top:*"):
                redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Failed to invalidate caches after registration: {e}")

        # Send verification email if email service is configured
        if email_service.is_email_configured():
            try:
                # Send welcome email (no verification needed)
                welcome_sent = email_service.send_welcome_email(db_user)

                if welcome_sent:
                    logger.info(f"Welcome email sent to {db_user.email}")
                else:
                    logger.warning(f"Failed to send welcome email to {db_user.email}")

                # Generate verification token for email verification
                verification_token = email_service.generate_verification_token()

                # Create verification record
                token_record = EmailVerificationToken(
                    user_id=db_user.id,
                    email=db_user.email,
                    token=verification_token,
                    expires_at=datetime.now() + timedelta(hours=24),
                )

                db.add(token_record)
                db.commit()

                # Send verification email
                email_sent = email_service.send_verification_email(
                    db_user, verification_token
                )

                if email_sent:
                    logger.info(f"Verification email sent to {db_user.email}")
                else:
                    logger.warning(
                        f"Failed to send verification email to {db_user.email}"
                    )

            except Exception as e:
                logger.error(f"Error sending welcome/verification emails: {e}")
                # Don't fail registration if email fails
        else:
            logger.info(
                "Email service not configured - skipping welcome and verification emails"
            )

        logger.info(f"New user registered: {db_user.username} ({db_user.email})")

        return UserResponse.model_validate(db_user)

    except HTTPException:
        db.rollback()
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error during user registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists",
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error during user registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration",
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email/username and password

    This provides JWT-based authentication for users who registered directly.
    For NextAuth.js users, this endpoint may not be needed.
    """
    try:
        # Find user by email or username
        db_user = (
            db.query(User)
            .filter(
                (User.email == user_credentials.email)
                | (User.username == user_credentials.email)
            )
            .first()
        )

        if not db_user:
            logger.warning(f"Login failed: User not found - {user_credentials.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        # Verify password
        logger.info(
            f"Attempting login for user: {db_user.username} (email: {db_user.email})"
        )
        logger.info(f"Password hash exists: {bool(db_user.password_hash)}")

        if not db_user.password_hash:
            logger.warning(
                f"Login failed: No password hash for user {db_user.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        password_valid = verify_password(
            user_credentials.password, db_user.password_hash
        )
        logger.info(f"Password verification result: {password_valid}")

        if not password_valid:
            logger.warning(
                f"Login failed: Invalid password for user {db_user.username}"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        if not db_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is disabled"
            )

        # Create access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(db_user.id), "username": db_user.username},
            expires_delta=access_token_expires,
        )

        logger.info(f"User logged in: {db_user.username}")

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponse.model_validate(db_user),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during user login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login",
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Get current authenticated user's profile

    Requires valid JWT token in Authorization header:
    Authorization: Bearer <your_jwt_token>
    """
    try:
        return UserResponse.model_validate(current_user)
    except Exception as e:
        logger.error(f"Error getting current user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving user profile",
        )


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update current authenticated user's profile

    Requires valid JWT token in Authorization header.
    """
    try:
        # Check if display_name is being changed and is available
        if (
            profile_data.display_name
            and profile_data.display_name != current_user.display_name
        ):
            existing_user = (
                db.query(User)
                .filter(
                    User.display_name == profile_data.display_name,
                    User.id != current_user.id,
                )
                .first()
            )

            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Display name already taken",
                )

        # Update fields
        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)

        # Update NextAuth.js compatibility field
        if profile_data.display_name:
            current_user.name = profile_data.display_name

        db.commit()
        db.refresh(current_user)

        # Invalidate user-related caches
        try:
            from app.database import get_redis

            redis_client = next(get_redis())
            redis_client.delete(f"user:profile:{current_user.display_name}")
            # Clear search and top users caches
            for key in redis_client.scan_iter(match="users:search:*"):
                redis_client.delete(key)
            for key in redis_client.scan_iter(match="users:top:*"):
                redis_client.delete(key)
        except Exception as e:
            logger.warning(f"Failed to invalidate caches after profile update: {e}")

        logger.info(f"User profile updated: {current_user.username}")

        return UserResponse.model_validate(current_user)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating profile",
        )


@router.post("/logout")
async def logout_user(current_user: User = Depends(get_current_user)):
    """
    Logout user (JWT tokens are stateless, so this is mainly for logging)

    In a production app, you might want to add token blacklisting.
    """
    logger.info(f"User logged out: {current_user.username}")

    return {
        "message": "Successfully logged out",
        "note": "JWT tokens are stateless. For complete security, implement token blacklisting or use short expiration times.",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """
    Refresh JWT token
    """
    try:
        # Create new access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(current_user.id), "username": current_user.username},
            expires_delta=access_token_expires,
        )

        logger.info(f"Token refreshed for user: {current_user.username}")

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=UserResponse.model_validate(current_user),
        )

    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error refreshing token",
        )


@router.post("/check-username")
async def check_username_availability(
    username: str,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Check if a username is available
    """
    # Try to get from cache
    cache_key = f"auth:username:{username.lower()}"
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data is not None:
            logger.info(f"Username availability cache hit: {username}")
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"Redis cache error: {e}")

    existing_user = db.query(User).filter(User.username == username.lower()).first()
    result = {"username": username, "available": existing_user is None}

    # Cache the result
    try:
        redis_client.setex(cache_key, CACHE_TTL_SHORT, json.dumps(result))
    except Exception as e:
        logger.warning(f"Failed to cache username availability: {e}")

    return result


@router.post("/check-display-name")
async def check_display_name_availability(
    display_name: str,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Check if a display name is available (like @SaladStik)
    """
    # Remove @ if included
    if display_name.startswith("@"):
        display_name = display_name[1:]

    # Try to get from cache
    cache_key = f"auth:display_name:{display_name}"
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data is not None:
            logger.info(f"Display name availability cache hit: {display_name}")
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"Redis cache error: {e}")

    existing_user = db.query(User).filter(User.display_name == display_name).first()
    result = {"display_name": display_name, "available": existing_user is None}

    # Cache the result
    try:
        redis_client.setex(cache_key, CACHE_TTL_SHORT, json.dumps(result))
    except Exception as e:
        logger.warning(f"Failed to cache display name availability: {e}")

    return result


@router.get("/profile/{display_name}", response_model=UserPublicProfile)
async def get_user_profile(
    display_name: str,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Get a user's public profile by display name (like @SaladStik)
    """
    # Remove @ if included
    if display_name.startswith("@"):
        display_name = display_name[1:]

    # Try to get from cache
    cache_key = f"user:profile:{display_name}"
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info(f"User profile cache hit: {display_name}")
            return UserPublicProfile(**json.loads(cached_data))
    except Exception as e:
        logger.warning(f"Redis cache error: {e}")

    user = db.query(User).filter(User.display_name == display_name).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if not user.profile_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Profile is private"
        )

    # Create public profile response respecting privacy settings
    profile_data = {
        "id": user.id,
        "display_name": user.display_name,
        "bio": user.bio,
        "avatar_url": user.avatar_url,
        "banner_url": user.banner_url,
        "website_url": user.website_url,
        "location": user.location,
        "twitter_handle": user.twitter_handle,
        "github_username": user.github_username,
        "linkedin_url": user.linkedin_url,
        "post_count": user.post_count,
        "comment_count": user.comment_count,
        "karma_score": user.karma_score,
        "is_verified": user.is_verified,
        "created_at": user.created_at,
        "full_name": user.full_name if user.show_real_name else None,
        "email": user.email if user.show_email else None,
    }

    profile = UserPublicProfile(**profile_data)

    # Cache the profile
    try:
        redis_client.setex(
            cache_key, CACHE_TTL_MEDIUM, json.dumps(profile.model_dump(), default=str)
        )
    except Exception as e:
        logger.warning(f"Failed to cache user profile: {e}")

    return profile


@router.get("/check-email")
async def check_email_availability(
    email: str,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Check if an email is available
    """
    # Try to get from cache
    cache_key = f"auth:email:{email}"
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data is not None:
            logger.info(f"Email availability cache hit: {email}")
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"Redis cache error: {e}")

    existing_user = db.query(User).filter(User.email == email).first()
    result = {"email": email, "available": existing_user is None}

    # Cache the result
    try:
        redis_client.setex(cache_key, CACHE_TTL_SHORT, json.dumps(result))
    except Exception as e:
        logger.warning(f"Failed to cache email availability: {e}")

    return result


@router.get("/verify-email")
async def verify_email(token: str, email: str, db: Session = Depends(get_db)):
    """
    Verify user email address using verification token

    This endpoint is typically called from a link in the verification email.
    After successful verification, the user's email is marked as verified.
    """
    try:
        # Find the verification token
        token_record = (
            db.query(EmailVerificationToken)
            .filter(
                EmailVerificationToken.token == token,
                EmailVerificationToken.email == email,
                EmailVerificationToken.is_used == False,
            )
            .first()
        )

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token",
            )

        if token_record.is_expired:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification token has expired",
            )

        # Find the user
        user = db.query(User).filter(User.id == token_record.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Mark email as verified
        user.is_verified = True
        user.email_verified = datetime.now()

        # Mark token as used
        token_record.is_used = True
        token_record.used_at = datetime.now()

        db.commit()

        logger.info(f"Email verified for user: {user.email}")

        return {
            "message": "Email verified successfully",
            "user_id": user.id,
            "email": user.email,
            "verified_at": user.email_verified,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error during email verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during email verification",
        )


@router.post("/resend-verification")
async def resend_verification_email(email: str, db: Session = Depends(get_db)):
    """
    Resend verification email to user

    Use this endpoint if the user didn't receive the initial verification email
    or if the previous token expired.
    """
    try:
        # Find the user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Don't reveal if email exists for security
            return {
                "message": "If the email exists, a verification email has been sent"
            }

        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already verified",
            )

        if not email_service.is_email_configured():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Email service is not configured",
            )

        # Invalidate old tokens
        db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.is_used == False,
        ).update({"is_used": True, "used_at": datetime.now()})

        # Generate new verification token
        verification_token = email_service.generate_verification_token()

        # Create verification record
        token_record = EmailVerificationToken(
            user_id=user.id,
            email=user.email,
            token=verification_token,
            expires_at=datetime.now() + timedelta(hours=24),
        )

        db.add(token_record)
        db.commit()

        # Send verification email
        email_sent = email_service.send_verification_email(user, verification_token)

        if email_sent:
            logger.info(f"Verification email resent to {user.email}")
            return {"message": "Verification email sent successfully"}
        else:
            logger.error(f"Failed to send verification email to {user.email}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email",
            )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error resending verification email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resending verification email",
        )


@router.post("/forgot-password")
async def request_password_reset(
    request: PasswordResetRequest, db: Session = Depends(get_db)
):
    """
    Request password reset email

    Sends a password reset email to the user if the email exists.
    For security, always returns success even if email doesn't exist.
    """
    try:
        # Find the user
        user = db.query(User).filter(User.email == request.email).first()

        if user:
            if not email_service.is_email_configured():
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Email service is not configured",
                )

            # Invalidate old password reset tokens
            db.query(PasswordResetToken).filter(
                PasswordResetToken.user_id == user.id,
                PasswordResetToken.is_used == False,
            ).update({"is_used": True, "used_at": datetime.now()})

            # Generate new reset token
            reset_token = email_service.generate_verification_token()

            # Create password reset record
            token_record = PasswordResetToken(
                user_id=user.id,
                email=user.email,
                token=reset_token,
                expires_at=datetime.now()
                + timedelta(hours=1),  # 1 hour expiry for security
            )

            db.add(token_record)
            db.commit()

            # Send password reset email
            email_sent = email_service.send_password_reset_email(user, reset_token)

            if email_sent:
                logger.info(f"Password reset email sent to {user.email}")
            else:
                logger.error(f"Failed to send password reset email to {user.email}")
        else:
            logger.info(
                f"Password reset requested for non-existent email: {request.email}"
            )

        # Always return success for security (don't reveal if email exists)
        return {
            "message": "If the email exists in our system, a password reset link has been sent",
            "email": request.email,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error requesting password reset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error requesting password reset",
        )


@router.post("/reset-password")
async def reset_password(reset_data: PasswordReset, db: Session = Depends(get_db)):
    """
    Reset password using token from email

    This endpoint processes the password reset token sent via email
    and updates the user's password if the token is valid.
    """
    try:
        # Find the reset token
        token_record = (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.token == reset_data.token,
                PasswordResetToken.email == reset_data.email,
                PasswordResetToken.is_used == False,
            )
            .first()
        )

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token",
            )

        if token_record.is_expired:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset token has expired",
            )

        # Find the user
        user = db.query(User).filter(User.id == token_record.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Update password
        user.password_hash = hash_password(reset_data.new_password)

        # Mark token as used
        token_record.is_used = True
        token_record.used_at = datetime.now()

        # Invalidate all other reset tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False,
            PasswordResetToken.id != token_record.id,
        ).update({"is_used": True, "used_at": datetime.now()})

        db.commit()

        logger.info(f"Password reset successfully for user: {user.email}")

        return {
            "message": "Password reset successfully",
            "user_id": user.id,
            "email": user.email,
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error resetting password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error resetting password",
        )


@router.get("/reset-password/verify")
async def verify_reset_token(token: str, email: str, db: Session = Depends(get_db)):
    """
    Verify if a password reset token is valid

    This endpoint can be used by the frontend to check if a reset token
    is valid before showing the password reset form.
    """
    try:
        # Find the reset token
        token_record = (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.token == token,
                PasswordResetToken.email == email,
                PasswordResetToken.is_used == False,
            )
            .first()
        )

        if not token_record or token_record.is_expired:
            return {
                "valid": False,
                "message": "Invalid or expired password reset token",
            }

        return {"valid": True, "email": email, "expires_at": token_record.expires_at}

    except Exception as e:
        logger.error(f"Error verifying reset token: {e}")
        return {"valid": False, "message": "Error verifying token"}
