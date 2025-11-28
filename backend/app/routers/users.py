from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session
from app.database import get_db, get_redis
from app.models.user import User
from app.models.posts import Comment, Post
from app.schemas.user import UserResponse, UserUpdate, UserPublicProfile
from app.auth import get_current_user
from typing import List, Optional
import logging
import redis
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["Users"])

# Cache settings
CACHE_TTL_SHORT = 300  # 5 minutes
CACHE_TTL_MEDIUM = 1800  # 30 minutes
CACHE_TTL_LONG = 3600  # 1 hour


@router.get("/search", response_model=List[UserPublicProfile])
async def search_users(
    q: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Search for users by display name or bio
    """
    # Try to get from cache
    cache_key = f"users:search:{q or 'all'}:{limit}:{offset}"
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info(f"User search cache hit: {cache_key}")
            cached_profiles = json.loads(cached_data)
            return [UserPublicProfile(**profile) for profile in cached_profiles]
    except Exception as e:
        logger.warning(f"Redis cache error: {e}")

    query = db.query(User).filter(User.profile_public == True, User.is_active == True)

    if q:
        search_term = f"%{q}%"
        query = query.filter(
            (User.display_name.ilike(search_term)) | (User.bio.ilike(search_term))
        )

    users = query.offset(offset).limit(limit).all()

    # Convert to public profiles
    public_profiles = []
    for user in users:
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
        public_profiles.append(UserPublicProfile(**profile_data))

    # Cache the results (longer TTL for leaderboards)
    try:
        cache_data = [profile.model_dump() for profile in public_profiles]
        redis_client.setex(
            cache_key, CACHE_TTL_LONG, json.dumps(cache_data, default=str)
        )
    except Exception as e:
        logger.warning(f"Failed to cache top users: {e}")

    return public_profiles


@router.get("/top", response_model=List[UserPublicProfile])
async def get_top_users(
    sort_by: str = "karma",  # karma, posts, comments
    limit: int = 10,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Get top users by karma, posts, or comments
    """
    # Try to get from cache (top users change infrequently, so longer cache)
    cache_key = f"users:top:{sort_by}:{limit}"
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info(f"Top users cache hit: {cache_key}")
            cached_profiles = json.loads(cached_data)
            return [UserPublicProfile(**profile) for profile in cached_profiles]
    except Exception as e:
        logger.warning(f"Redis cache error: {e}")

    query = db.query(User).filter(User.profile_public == True, User.is_active == True)

    if sort_by == "karma":
        query = query.order_by(User.karma_score.desc())
    elif sort_by == "posts":
        query = query.order_by(User.post_count.desc())
    elif sort_by == "comments":
        query = query.order_by(User.comment_count.desc())
    else:
        # Default to karma
        query = query.order_by(User.karma_score.desc())

    users = query.limit(limit).all()

    # Convert to public profiles
    public_profiles = []
    for user in users:
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
        public_profiles.append(UserPublicProfile(**profile_data))

    # Cache the results (longer TTL for leaderboards)
    try:
        cache_data = [profile.model_dump() for profile in public_profiles]
        redis_client.setex(
            cache_key, CACHE_TTL_LONG, json.dumps(cache_data, default=str)
        )
    except Exception as e:
        logger.warning(f"Failed to cache top users: {e}")

    return public_profiles


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Update current user's profile

    Requires authentication. Include JWT token in Authorization header.
    """
    try:
        # Invalidate user-related caches
        try:
            # Clear user profile cache
            redis_client.delete(f"user:profile:{current_user.display_name}")
            # Clear search caches (pattern delete)
            for key in redis_client.scan_iter(match="users:search:*"):
                redis_client.delete(key)
            # Clear top users caches
            for key in redis_client.scan_iter(match="users:top:*"):
                redis_client.delete(key)
            # Clear stats cache
            redis_client.delete("users:stats")
            logger.info(f"Cleared user caches for {current_user.display_name}")
        except Exception as e:
            logger.warning(f"Failed to clear user caches: {e}")
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


@router.get("/{display_name}/comments")
async def get_user_comments(
    display_name: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Get comments by a specific user
    """
    # Try to get from cache
    cache_key = f"user:comments:{display_name}:{limit}:{offset}"
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info(f"User comments cache hit: {display_name}")
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"Redis cache error: {e}")

    # Find user
    user = (
        db.query(User)
        .filter(User.display_name == display_name, User.is_active == True)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    # Get user's comments with post info
    comments = (
        db.query(Comment)
        .join(Post, Comment.post_id == Post.id)
        .filter(
            Comment.author_id == user.id,
            Comment.is_deleted == False,
            Post.is_deleted == False,
        )
        .order_by(Comment.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    # Format response
    comment_list = []
    for comment in comments:
        comment_data = {
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at,
            "upvote_count": comment.upvote_count,
            "downvote_count": comment.downvote_count,
            "is_accepted": comment.is_accepted,
            "post_id": comment.post_id,
            "post_title": comment.post.title if comment.post else "Unknown",
        }
        comment_list.append(comment_data)

    # Cache the results
    try:
        redis_client.setex(
            cache_key, CACHE_TTL_MEDIUM, json.dumps(comment_list, default=str)
        )
    except Exception as e:
        logger.warning(f"Failed to cache user comments: {e}")

    return comment_list


@router.get("/stats")
async def get_user_stats(
    db: Session = Depends(get_db), redis_client: redis.Redis = Depends(get_redis)
):
    """
    Get overall user statistics
    """
    # Try to get from cache
    cache_key = "users:stats"
    try:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.info("User stats cache hit")
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"Redis cache error: {e}")

    total_users = db.query(User).filter(User.is_active == True).count()
    verified_users = (
        db.query(User).filter(User.is_verified == True, User.is_active == True).count()
    )

    stats = {
        "total_users": total_users,
        "verified_users": verified_users,
        "verification_rate": (
            round((verified_users / total_users * 100), 2) if total_users > 0 else 0
        ),
    }

    # Cache the results (stats change infrequently)
    try:
        redis_client.setex(cache_key, CACHE_TTL_LONG, json.dumps(stats))
    except Exception as e:
        logger.warning(f"Failed to cache user stats: {e}")

    return stats
