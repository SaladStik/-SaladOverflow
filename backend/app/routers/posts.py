from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, and_, or_, func
from app.database import get_db, get_redis
from app.models.user import User
from app.models.posts import (
    Post,
    Comment,
    Tag,
    PostVote,
    CommentVote,
    post_tags,
    Bookmark,
)
from app.schemas.posts import (
    PostCreate,
    PostUpdate,
    PostResponse,
    PostListResponse,
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    TagCreate,
    TagResponse,
    VoteCreate,
    VoteResponse,
    PostFilters,
    PostSort,
    ContentAnalysis,
)
from app.utils.content import process_post_content, create_slug, analyze_content
from app.auth import get_current_user, get_optional_user
from app.services.email_service import email_service
from typing import List, Optional
import logging
import redis
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/posts", tags=["Posts"])

# Cache settings
CACHE_TTL_SHORT = 180  # 3 minutes for frequently changing data
CACHE_TTL_MEDIUM = 600  # 10 minutes for post lists
CACHE_TTL_LONG = 1800  # 30 minutes for tags and individual posts


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_data: PostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Create a new post (question, discussion, or announcement)

    Requires authentication. Include JWT token in Authorization header.
    """
    try:
        # Process content (markdown to HTML, sanitize, analyze)
        processed_content, content_analysis = process_post_content(
            post_data.content, "markdown"
        )

        # Create new post
        db_post = Post(
            title=post_data.title,
            content=processed_content,
            content_plain=content_analysis.plain_text,
            content_markdown=post_data.content,  # Store original markdown
            post_type=post_data.post_type,
            author_id=current_user.id,
            has_code=content_analysis.has_code,
            has_images=content_analysis.has_images,
        )

        db.add(db_post)
        db.flush()  # Flush to get the ID

        # Create slug
        db_post.slug = create_slug(post_data.title, db_post.id)

        # Handle tags
        for tag_name in post_data.tags:
            # Get or create tag
            tag = db.query(Tag).filter(Tag.name == tag_name.lower()).first()
            if not tag:
                tag = Tag(name=tag_name.lower(), post_count=1)
                db.add(tag)
            else:
                tag.post_count += 1

            db_post.tags.append(tag)

        # Update user post count
        current_user.post_count += 1

        db.commit()
        db.refresh(db_post)

        # Send email notifications (async, don't block on failures)
        try:
            # Send confirmation email to user
            email_service.send_post_created_notification(
                current_user, db_post.title, db_post.id, db_post.slug
            )
            # Send log email to admin
            email_service.send_admin_post_log(
                current_user,
                db_post.title,
                db_post.id,
                db_post.post_type,
                db_post.content_plain,
            )
            logger.info(f"Email notifications sent for post {db_post.id}")
        except Exception as e:
            logger.warning(f"Failed to send post creation emails: {e}")

        # Invalidate relevant caches
        try:
            # Clear post list caches
            for key in redis_client.scan_iter(match="posts:list:*"):
                redis_client.delete(key)
            # Clear tag caches
            for key in redis_client.scan_iter(match="posts:tags:*"):
                redis_client.delete(key)
            # Clear user profile cache (post count changed)
            redis_client.delete(f"user:profile:{current_user.display_name}")
            # Clear top users cache (post count changed)
            for key in redis_client.scan_iter(match="users:top:*"):
                redis_client.delete(key)
            logger.info(f"Cleared post-related caches after creating post {db_post.id}")
        except Exception as e:
            logger.warning(f"Failed to clear post caches: {e}")

        logger.info(f"New post created: {db_post.id} by user {current_user.username}")

        # Return post with author info
        return await get_post_response(db_post, db, current_user)

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating post",
        )


@router.get("/", response_model=PostListResponse)
async def get_posts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort: PostSort = PostSort.NEWEST,
    post_type: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    author: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get posts with filtering and sorting
    """
    try:
        # Skip cache for authenticated users (response includes user-specific data)
        use_cache = current_user is None

        # Create cache key from query parameters
        tags_str = ",".join(sorted(tags)) if tags else "none"
        cache_key = f"posts:list:{page}:{page_size}:{sort}:{post_type or 'all'}:{tags_str}:{author or 'all'}:{search or 'none'}"

        # Try to get from cache (only for non-authenticated users)
        if use_cache:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    logger.info(f"Post list cache hit: page {page}")
                    cached_response = json.loads(cached_data)
                    # Reconstruct response with proper models
                    posts = [PostResponse(**post) for post in cached_response["posts"]]
                    return PostListResponse(
                        posts=posts,
                        total_count=cached_response["total_count"],
                        page=cached_response["page"],
                        page_size=cached_response["page_size"],
                        total_pages=cached_response["total_pages"],
                    )
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")

        # Base query
        query = db.query(Post).filter(Post.is_deleted == False)

        # Apply filters
        if post_type:
            query = query.filter(Post.post_type == post_type)

        if tags:
            # Filter by tags
            query = (
                query.join(post_tags)
                .join(Tag)
                .filter(Tag.name.in_([tag.lower() for tag in tags]))
            )

        if author:
            # Filter by author display name
            query = query.join(User).filter(User.display_name == author)

        if search:
            # Search in title and plain content
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Post.title.ilike(search_term), Post.content_plain.ilike(search_term)
                )
            )

        # Apply sorting
        if sort == PostSort.NEWEST:
            query = query.order_by(desc(Post.created_at))
        elif sort == PostSort.OLDEST:
            query = query.order_by(asc(Post.created_at))
        elif sort == PostSort.MOST_VOTED:
            query = query.order_by(desc(Post.upvote_count - Post.downvote_count))
        elif sort == PostSort.MOST_VIEWED:
            query = query.order_by(desc(Post.view_count))
        elif sort == PostSort.MOST_ANSWERED:
            query = query.order_by(desc(Post.answer_count))
        elif sort == PostSort.UNANSWERED:
            query = query.filter(Post.answer_count == 0).order_by(desc(Post.created_at))
        elif sort == PostSort.ACTIVE:
            query = query.order_by(desc(Post.last_activity))

        # Get total count
        total_count = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        posts = query.offset(offset).limit(page_size).all()

        # Convert to response format
        post_responses = []
        for post in posts:
            post_response = await get_post_response(post, db, current_user)
            post_responses.append(post_response)

        total_pages = (total_count + page_size - 1) // page_size

        response = PostListResponse(
            posts=post_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

        # Cache the response only for non-authenticated users (shorter TTL for dynamic content)
        if use_cache:
            try:
                cache_data = {
                    "posts": [post.model_dump() for post in post_responses],
                    "total_count": total_count,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                }
                redis_client.setex(
                    cache_key, CACHE_TTL_MEDIUM, json.dumps(cache_data, default=str)
                )
            except Exception as e:
                logger.warning(f"Failed to cache post list: {e}")

        return response

    except Exception as e:
        logger.error(f"Error getting posts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving posts",
        )


@router.get("/bookmarks", response_model=PostListResponse)
async def get_user_bookmarks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get current user's bookmarked posts
    """
    try:
        logger.info(f"Getting bookmarks for user {current_user.id}")

        # Get bookmarks with post data (use joinedload for eager loading)
        query = (
            db.query(Bookmark)
            .options(joinedload(Bookmark.post))
            .filter(Bookmark.user_id == current_user.id)
            .join(Post)
            .filter(Post.is_deleted == False)
            .order_by(desc(Bookmark.created_at))
        )

        # Get total count
        total_count = query.count()
        logger.info(f"Found {total_count} bookmarks")

        # Apply pagination
        offset = (page - 1) * page_size
        bookmarks = query.offset(offset).limit(page_size).all()
        logger.info(f"Retrieved {len(bookmarks)} bookmarks for page {page}")

        # Get post responses
        post_responses = []
        for bookmark in bookmarks:
            try:
                post_response = await get_post_response(bookmark.post, db, current_user)
                post_responses.append(post_response)
            except Exception as e:
                logger.error(
                    f"Error creating post response for bookmark {bookmark.id}: {e}"
                )
                raise

        total_pages = (total_count + page_size - 1) // page_size

        logger.info(f"Returning {len(post_responses)} posts")
        return PostListResponse(
            posts=post_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.error(f"Error getting bookmarks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving bookmarks",
        )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get a single post by ID
    """
    try:
        # Skip cache for authenticated users (user-specific data like bookmarks/votes)
        use_cache = current_user is None

        # Try to get from cache (only for anonymous users)
        cache_key = f"post:{post_id}"
        if use_cache:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    logger.info(f"Post cache hit: {post_id}")
                    post_data = json.loads(cached_data)
                    # Still need to increment view count in DB
                    post = (
                        db.query(Post)
                        .filter(Post.id == post_id, Post.is_deleted == False)
                        .first()
                    )
                    if post:
                        post.view_count += 1
                        db.commit()
                        # Update cached view count
                        post_data["view_count"] = post.view_count
                    return PostResponse(**post_data)
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")

        post = (
            db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
        )

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        # Increment view count
        post.view_count += 1
        db.commit()

        post_response = await get_post_response(post, db, current_user)

        # Cache the post (only for anonymous users)
        if use_cache:
            try:
                redis_client.setex(
                    cache_key,
                    CACHE_TTL_LONG,
                    json.dumps(post_response.model_dump(), default=str),
                )
            except Exception as e:
                logger.warning(f"Failed to cache post: {e}")

        return post_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving post",
        )


async def get_post_response(
    post: Post, db: Session, current_user: Optional[User] = None
) -> PostResponse:
    """
    Helper function to convert Post model to PostResponse
    """
    # Get author info
    author = db.query(User).filter(User.id == post.author_id).first()

    # Get tags
    tags = [TagResponse.model_validate(tag) for tag in post.tags]

    # Get user-specific data if user is authenticated
    user_vote = None
    is_bookmarked = None

    if current_user:
        # Check if user has voted on this post
        vote = (
            db.query(PostVote)
            .filter(PostVote.user_id == current_user.id, PostVote.post_id == post.id)
            .first()
        )
        if vote:
            user_vote = vote.vote_type

        # Check if user has bookmarked this post
        bookmark = (
            db.query(Bookmark)
            .filter(Bookmark.user_id == current_user.id, Bookmark.post_id == post.id)
            .first()
        )
        is_bookmarked = bookmark is not None

    return PostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        content_plain=post.content_plain,
        content_markdown=post.content_markdown,
        post_type=post.post_type,
        slug=post.slug,
        author_id=post.author_id,
        author_display_name=author.display_name if author else None,
        author_avatar=author.avatar_url if author else None,
        author_is_verified=author.is_verified if author else False,
        view_count=post.view_count,
        upvote_count=post.upvote_count,
        downvote_count=post.downvote_count,
        comment_count=post.comment_count,
        answer_count=post.answer_count,
        is_answered=post.is_answered,
        accepted_answer_id=post.accepted_answer_id,
        has_code=post.has_code,
        has_images=post.has_images,
        is_locked=post.is_locked,
        is_deleted=post.is_deleted,
        is_featured=post.is_featured,
        user_vote=user_vote,
        is_bookmarked=is_bookmarked,
        tags=tags,
        created_at=post.created_at,
        updated_at=post.updated_at,
        last_activity=post.last_activity,
    )


@router.get("/{post_id}/comments", response_model=List[CommentResponse])
async def get_post_comments(
    post_id: int,
    sort: str = Query("newest", pattern="^(newest|oldest|most_voted)$"),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Get comments for a post
    """
    try:
        # Try to get from cache
        cache_key = f"post:{post_id}:comments:{sort}"
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Post comments cache hit: {post_id}")
                cached_comments = json.loads(cached_data)
                return [CommentResponse(**comment) for comment in cached_comments]
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")

        # Verify post exists
        post = (
            db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Get top-level comments (no parent)
        query = db.query(Comment).filter(
            Comment.post_id == post_id,
            Comment.parent_id.is_(None),
            Comment.is_deleted == False,
        )

        # Apply sorting
        if sort == "oldest":
            query = query.order_by(asc(Comment.created_at))
        elif sort == "most_voted":
            query = query.order_by(desc(Comment.upvote_count - Comment.downvote_count))
        else:  # newest
            query = query.order_by(desc(Comment.created_at))

        comments = query.all()

        # Convert to response format with nested replies
        comment_responses = []
        for comment in comments:
            comment_response = await get_comment_response(
                comment, db, include_replies=True
            )
            comment_responses.append(comment_response)

        # Cache the comments
        try:
            cache_data = [comment.model_dump() for comment in comment_responses]
            redis_client.setex(
                cache_key, CACHE_TTL_SHORT, json.dumps(cache_data, default=str)
            )
        except Exception as e:
            logger.warning(f"Failed to cache post comments: {e}")

        return comment_responses

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comments for post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving comments",
        )


async def get_comment_response(
    comment: Comment, db: Session, include_replies: bool = False
) -> CommentResponse:
    """
    Helper function to convert Comment model to CommentResponse
    """
    # Get author info
    author = db.query(User).filter(User.id == comment.author_id).first()

    # Get replies if requested (recursively)
    replies = []
    if include_replies:
        reply_comments = (
            db.query(Comment)
            .filter(Comment.parent_id == comment.id, Comment.is_deleted == False)
            .order_by(asc(Comment.created_at))
            .all()
        )

        for reply in reply_comments:
            # Recursively get replies for nested comments
            reply_response = await get_comment_response(reply, db, include_replies=True)
            replies.append(reply_response)

    return CommentResponse(
        id=comment.id,
        content=comment.content,
        content_plain=comment.content_plain,
        post_id=comment.post_id,
        parent_id=comment.parent_id,
        author_id=comment.author_id,
        author_display_name=author.display_name if author else None,
        author_avatar=author.avatar_url if author else None,
        author_is_verified=author.is_verified if author else False,
        upvote_count=comment.upvote_count,
        downvote_count=comment.downvote_count,
        reply_count=comment.reply_count,
        is_answer=comment.is_answer,
        is_accepted=comment.is_accepted,
        has_code=comment.has_code,
        has_images=comment.has_images,
        is_deleted=comment.is_deleted,
        replies=replies,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.get("/tags/", response_model=List[TagResponse])
async def get_tags(
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Get tags, optionally filtered by search term
    """
    try:
        # Try to get from cache
        cache_key = f"posts:tags:{search or 'all'}:{limit}"
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info("Tags cache hit")
                cached_tags = json.loads(cached_data)
                return [TagResponse(**tag) for tag in cached_tags]
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")

        query = db.query(Tag)

        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(Tag.name.ilike(search_term))

        tags = query.order_by(desc(Tag.post_count)).limit(limit).all()

        tag_responses = [TagResponse.model_validate(tag) for tag in tags]

        # Cache the tags (tags change infrequently)
        try:
            cache_data = [tag.model_dump() for tag in tag_responses]
            redis_client.setex(
                cache_key, CACHE_TTL_LONG, json.dumps(cache_data, default=str)
            )
        except Exception as e:
            logger.warning(f"Failed to cache tags: {e}")

        return tag_responses

    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving tags",
        )


@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Create a comment on a post

    Requires authentication. Include JWT token in Authorization header.
    """
    try:
        # Verify post exists and is not locked
        post = (
            db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if post.is_locked:
            raise HTTPException(status_code=403, detail="Post is locked for comments")

        # Verify parent comment exists if specified
        if comment_data.parent_id:
            parent_comment = (
                db.query(Comment)
                .filter(
                    Comment.id == comment_data.parent_id,
                    Comment.post_id == post_id,
                    Comment.is_deleted == False,
                )
                .first()
            )
            if not parent_comment:
                raise HTTPException(status_code=404, detail="Parent comment not found")

        # Process comment content
        processed_content, content_analysis = process_post_content(
            comment_data.content, "markdown"
        )

        # Create comment
        db_comment = Comment(
            content=processed_content,
            content_plain=content_analysis.plain_text,
            post_id=post_id,
            author_id=current_user.id,
            parent_id=comment_data.parent_id,
            is_answer=comment_data.is_answer,
            has_code=content_analysis.has_code,
            has_images=content_analysis.has_images,
        )

        db.add(db_comment)

        # Update counters
        post.comment_count += 1
        if comment_data.is_answer:
            post.answer_count += 1

        current_user.comment_count += 1

        # Update parent comment reply count if it's a reply
        if comment_data.parent_id:
            parent_comment.reply_count += 1

        # Update post last activity
        post.last_activity = func.now()

        db.commit()
        db.refresh(db_comment)

        # Send email notification if this is an answer to the post author (async, don't block)
        if comment_data.is_answer:
            try:
                # Get post author
                post_author = db.query(User).filter(User.id == post.author_id).first()
                # Only send if answerer is not the post author
                if post_author and post_author.id != current_user.id:
                    email_service.send_new_answer_notification(
                        post_author,
                        current_user,
                        post.title,
                        post.id,
                        post.slug,
                        db_comment.content_plain,
                        current_user.karma_score,
                    )
                    logger.info(
                        f"New answer notification sent to {post_author.email} for post {post_id}"
                    )
            except Exception as e:
                logger.warning(f"Failed to send new answer notification: {e}")

        # Invalidate relevant caches
        try:
            # Clear post cache (comment count changed)
            redis_client.delete(f"post:{post_id}")
            # Clear comments cache for this post
            for key in redis_client.scan_iter(match=f"post:{post_id}:comments:*"):
                redis_client.delete(key)
            # Clear post lists cache
            for key in redis_client.scan_iter(match="posts:list:*"):
                redis_client.delete(key)
            # Clear user profile cache (comment count changed)
            redis_client.delete(f"user:profile:{current_user.display_name}")
            logger.info(f"Cleared comment-related caches for post {post_id}")
        except Exception as e:
            logger.warning(f"Failed to clear comment caches: {e}")

        logger.info(
            f"New comment created: {db_comment.id} on post {post_id} by {current_user.username}"
        )

        return await get_comment_response(db_comment, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating comment",
        )


@router.post(
    "/{post_id}/vote", response_model=VoteResponse, status_code=status.HTTP_201_CREATED
)
async def vote_on_post(
    post_id: int,
    vote_data: VoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Vote on a post (upvote or downvote)

    Requires authentication. Users can change their vote or remove it by voting again.
    """
    try:
        # Verify post exists
        post = (
            db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Get post author for karma updates
        post_author = db.query(User).filter(User.id == post.author_id).first()

        # Check if user already voted
        existing_vote = (
            db.query(PostVote)
            .filter(PostVote.post_id == post_id, PostVote.user_id == current_user.id)
            .first()
        )

        if existing_vote:
            # Update existing vote or remove if same vote type
            if existing_vote.vote_type == vote_data.vote_type:
                # Remove vote (toggle off)
                if existing_vote.vote_type == "upvote":
                    post.upvote_count -= 1
                    if post_author:
                        post_author.karma_score -= 10  # Remove karma for removed upvote
                else:
                    post.downvote_count -= 1
                    if post_author:
                        post_author.karma_score += (
                            2  # Restore karma from removed downvote
                        )

                db.delete(existing_vote)
                db.commit()

                # Invalidate caches
                try:
                    redis_client.delete(f"post:{post_id}")
                    for key in redis_client.scan_iter(match="posts:list:*"):
                        redis_client.delete(key)
                    if post_author:
                        redis_client.delete(f"user:profile:{post_author.display_name}")
                        for key in redis_client.scan_iter(match="users:top:*"):
                            redis_client.delete(key)
                except Exception as e:
                    logger.warning(f"Failed to clear vote caches: {e}")

                return {"message": "Vote removed", "action": "removed"}
            else:
                # Change vote type
                old_vote = existing_vote.vote_type
                existing_vote.vote_type = vote_data.vote_type

                # Update counters and karma
                if old_vote == "upvote":
                    post.upvote_count -= 1
                    post.downvote_count += 1
                    if post_author:
                        post_author.karma_score -= 10  # Remove upvote karma
                        post_author.karma_score -= 2  # Apply downvote penalty
                else:
                    post.downvote_count -= 1
                    post.upvote_count += 1
                    if post_author:
                        post_author.karma_score += 2  # Remove downvote penalty
                        post_author.karma_score += 10  # Apply upvote karma

                db.commit()

                # Invalidate caches
                try:
                    redis_client.delete(f"post:{post_id}")
                    for key in redis_client.scan_iter(match="posts:list:*"):
                        redis_client.delete(key)
                    if post_author:
                        redis_client.delete(f"user:profile:{post_author.display_name}")
                        for key in redis_client.scan_iter(match="users:top:*"):
                            redis_client.delete(key)
                except Exception as e:
                    logger.warning(f"Failed to clear vote caches: {e}")

                return VoteResponse.model_validate(existing_vote)
        else:
            # Create new vote
            new_vote = PostVote(
                post_id=post_id, user_id=current_user.id, vote_type=vote_data.vote_type
            )

            db.add(new_vote)

            # Update counters and karma
            if vote_data.vote_type == "upvote":
                post.upvote_count += 1
                if post_author:
                    post_author.karma_score += 10  # Add karma for upvote
            else:
                post.downvote_count += 1
                if post_author:
                    post_author.karma_score -= 2  # Subtract karma for downvote

            db.commit()
            db.refresh(new_vote)

            # Invalidate caches
            try:
                redis_client.delete(f"post:{post_id}")
                for key in redis_client.scan_iter(match="posts:list:*"):
                    redis_client.delete(key)
                if post_author:
                    redis_client.delete(f"user:profile:{post_author.display_name}")
                    for key in redis_client.scan_iter(match="users:top:*"):
                        redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Failed to clear vote caches: {e}")

            return VoteResponse.model_validate(new_vote)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error voting on post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing vote",
        )


@router.post(
    "/comments/{comment_id}/vote",
    response_model=VoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def vote_on_comment(
    comment_id: int,
    vote_data: VoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Vote on a comment (upvote or downvote)

    Requires authentication. Users can change their vote or remove it by voting again.
    """
    try:
        # Verify comment exists
        comment = (
            db.query(Comment)
            .filter(Comment.id == comment_id, Comment.is_deleted == False)
            .first()
        )
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Get comment author for karma updates
        comment_author = db.query(User).filter(User.id == comment.author_id).first()

        # Check if user already voted
        existing_vote = (
            db.query(CommentVote)
            .filter(
                CommentVote.comment_id == comment_id,
                CommentVote.user_id == current_user.id,
            )
            .first()
        )

        if existing_vote:
            # Update existing vote or remove if same vote type
            if existing_vote.vote_type == vote_data.vote_type:
                # Remove vote (toggle off)
                if existing_vote.vote_type == "upvote":
                    comment.upvote_count -= 1
                    if comment_author:
                        comment_author.karma_score -= (
                            5  # Remove karma for removed upvote
                        )
                else:
                    comment.downvote_count -= 1
                    if comment_author:
                        comment_author.karma_score += (
                            1  # Restore karma from removed downvote
                        )

                db.delete(existing_vote)
                db.commit()

                # Invalidate comment caches
                try:
                    for key in redis_client.scan_iter(
                        match=f"post:{comment.post_id}:comments:*"
                    ):
                        redis_client.delete(key)
                    if comment_author:
                        redis_client.delete(
                            f"user:profile:{comment_author.display_name}"
                        )
                        for key in redis_client.scan_iter(match="users:top:*"):
                            redis_client.delete(key)
                except Exception as e:
                    logger.warning(f"Failed to clear comment vote caches: {e}")

                return {"message": "Vote removed", "action": "removed"}
            else:
                # Change vote type
                old_vote = existing_vote.vote_type
                existing_vote.vote_type = vote_data.vote_type

                # Update counters and karma
                if old_vote == "upvote":
                    comment.upvote_count -= 1
                    comment.downvote_count += 1
                    if comment_author:
                        comment_author.karma_score -= 5  # Remove upvote karma
                        comment_author.karma_score -= 1  # Apply downvote penalty
                else:
                    comment.downvote_count -= 1
                    comment.upvote_count += 1
                    if comment_author:
                        comment_author.karma_score += 1  # Remove downvote penalty
                        comment_author.karma_score += 5  # Apply upvote karma

                db.commit()

                # Invalidate comment caches
                try:
                    for key in redis_client.scan_iter(
                        match=f"post:{comment.post_id}:comments:*"
                    ):
                        redis_client.delete(key)
                    if comment_author:
                        redis_client.delete(
                            f"user:profile:{comment_author.display_name}"
                        )
                        for key in redis_client.scan_iter(match="users:top:*"):
                            redis_client.delete(key)
                except Exception as e:
                    logger.warning(f"Failed to clear comment vote caches: {e}")

                return VoteResponse.model_validate(existing_vote)
        else:
            # Create new vote
            new_vote = CommentVote(
                comment_id=comment_id,
                user_id=current_user.id,
                vote_type=vote_data.vote_type,
            )

            db.add(new_vote)

            # Update counters and karma
            if vote_data.vote_type == "upvote":
                comment.upvote_count += 1
                if comment_author:
                    comment_author.karma_score += 5  # Add karma for upvote
            else:
                comment.downvote_count += 1
                if comment_author:
                    comment_author.karma_score -= 1  # Subtract karma for downvote

            db.commit()
            db.refresh(new_vote)

            # Invalidate comment caches
            try:
                for key in redis_client.scan_iter(
                    match=f"post:{comment.post_id}:comments:*"
                ):
                    redis_client.delete(key)
                if comment_author:
                    redis_client.delete(f"user:profile:{comment_author.display_name}")
                    for key in redis_client.scan_iter(match="users:top:*"):
                        redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Failed to clear comment vote caches: {e}")

            return VoteResponse.model_validate(new_vote)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error voting on comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing vote",
        )


@router.post("/{post_id}/comments/{comment_id}/accept")
async def accept_answer(
    post_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Mark a comment as the accepted answer for a question

    Only the post author can accept answers. Only one answer can be accepted per post.
    Calling this on an already-accepted answer will unaccept it.
    """
    try:
        # Verify post exists and is a question
        post = (
            db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Only post author can accept answers
        if post.author_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Only the post author can accept answers"
            )

        # Only questions can have accepted answers
        if post.post_type != "question":
            raise HTTPException(
                status_code=400, detail="Only questions can have accepted answers"
            )

        # Verify comment exists and belongs to this post
        comment = (
            db.query(Comment)
            .filter(
                Comment.id == comment_id,
                Comment.post_id == post_id,
                Comment.is_deleted == False,
            )
            .first()
        )
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Check if this comment is already accepted
        if comment.is_accepted and post.accepted_answer_id == comment_id:
            # Unaccept the answer
            comment.is_accepted = False
            post.accepted_answer_id = None

            # Remove karma bonus for unaccepted answer
            comment_author = db.query(User).filter(User.id == comment.author_id).first()
            if comment_author:
                comment_author.karma_score -= 15  # Remove accepted answer karma bonus

            db.commit()

            # Invalidate caches
            try:
                redis_client.delete(f"post:{post_id}")
                for key in redis_client.scan_iter(match=f"post:{post_id}:comments:*"):
                    redis_client.delete(key)
                if comment_author:
                    redis_client.delete(f"user:profile:{comment_author.display_name}")
                    for key in redis_client.scan_iter(match="users:top:*"):
                        redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Failed to clear caches: {e}")

            return {"message": "Answer unaccepted", "is_accepted": False}
        else:
            # Unaccept any previously accepted answer
            if post.accepted_answer_id:
                old_accepted = (
                    db.query(Comment)
                    .filter(Comment.id == post.accepted_answer_id)
                    .first()
                )
                if old_accepted:
                    old_accepted.is_accepted = False
                    # Remove karma from previously accepted answer author
                    old_author = (
                        db.query(User).filter(User.id == old_accepted.author_id).first()
                    )
                    if old_author:
                        old_author.karma_score -= 15

            # Accept this answer
            comment.is_accepted = True
            post.accepted_answer_id = comment_id

            # Add karma bonus for accepted answer
            comment_author = db.query(User).filter(User.id == comment.author_id).first()
            if comment_author:
                comment_author.karma_score += 15  # Bonus for accepted answer

            db.commit()

            # Invalidate caches
            try:
                redis_client.delete(f"post:{post_id}")
                for key in redis_client.scan_iter(match=f"post:{post_id}:comments:*"):
                    redis_client.delete(key)
                if comment_author:
                    redis_client.delete(f"user:profile:{comment_author.display_name}")
                    for key in redis_client.scan_iter(match="users:top:*"):
                        redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Failed to clear caches: {e}")

            return {"message": "Answer accepted", "is_accepted": True}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error accepting answer: {e}")
        raise HTTPException(status_code=500, detail="Failed to accept answer")


@router.post("/{post_id}/bookmark")
async def toggle_bookmark(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Toggle bookmark on a post

    If post is bookmarked, remove bookmark. If not bookmarked, add bookmark.
    """
    try:
        # Verify post exists
        post = (
            db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Check if bookmark exists
        existing_bookmark = (
            db.query(Bookmark)
            .filter(Bookmark.post_id == post_id, Bookmark.user_id == current_user.id)
            .first()
        )

        if existing_bookmark:
            # Remove bookmark
            db.delete(existing_bookmark)
            db.commit()
            logger.info(
                f"Bookmark removed for post {post_id} by user {current_user.id}"
            )
            return {"message": "Bookmark removed", "is_bookmarked": False}
        else:
            # Add bookmark
            new_bookmark = Bookmark(post_id=post_id, user_id=current_user.id)
            db.add(new_bookmark)
            db.commit()
            logger.info(f"Bookmark added for post {post_id} by user {current_user.id}")
            return {"message": "Bookmark added", "is_bookmarked": True}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error toggling bookmark: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error toggling bookmark",
        )


@router.get("/bookmarks", response_model=PostListResponse)
async def get_user_bookmarks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get current user's bookmarked posts
    """
    try:
        logger.info(f"Getting bookmarks for user {current_user.id}")

        # Get bookmarks with post data (use joinedload for eager loading)
        query = (
            db.query(Bookmark)
            .options(joinedload(Bookmark.post))
            .filter(Bookmark.user_id == current_user.id)
            .join(Post)
            .filter(Post.is_deleted == False)
            .order_by(desc(Bookmark.created_at))
        )

        # Get total count
        total_count = query.count()
        logger.info(f"Found {total_count} bookmarks")

        # Apply pagination
        offset = (page - 1) * page_size
        bookmarks = query.offset(offset).limit(page_size).all()
        logger.info(f"Retrieved {len(bookmarks)} bookmarks for page {page}")

        # Get post responses
        post_responses = []
        for bookmark in bookmarks:
            try:
                post_response = await get_post_response(bookmark.post, db, current_user)
                post_responses.append(post_response)
            except Exception as e:
                logger.error(
                    f"Error creating post response for bookmark {bookmark.id}: {e}"
                )
                raise

        total_pages = (total_count + page_size - 1) // page_size

        logger.info(f"Returning {len(post_responses)} posts")
        return PostListResponse(
            posts=post_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    except Exception as e:
        logger.error(f"Error getting bookmarks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving bookmarks",
        )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Get a single post by ID
    """
    try:
        # Skip cache for authenticated users (user-specific data like bookmarks/votes)
        use_cache = current_user is None

        # Try to get from cache (only for anonymous users)
        cache_key = f"post:{post_id}"
        if use_cache:
            try:
                cached_data = redis_client.get(cache_key)
                if cached_data:
                    logger.info(f"Post cache hit: {post_id}")
                    post_data = json.loads(cached_data)
                    # Still need to increment view count in DB
                    post = (
                        db.query(Post)
                        .filter(Post.id == post_id, Post.is_deleted == False)
                        .first()
                    )
                    if post:
                        post.view_count += 1
                        db.commit()
                        # Update cached view count
                        post_data["view_count"] = post.view_count
                    return PostResponse(**post_data)
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")

        post = (
            db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
        )

        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
            )

        # Increment view count
        post.view_count += 1
        db.commit()

        post_response = await get_post_response(post, db, current_user)

        # Cache the post (only for anonymous users)
        if use_cache:
            try:
                redis_client.setex(
                    cache_key,
                    CACHE_TTL_LONG,
                    json.dumps(post_response.model_dump(), default=str),
                )
            except Exception as e:
                logger.warning(f"Failed to cache post: {e}")

        return post_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving post",
        )


async def get_post_response(
    post: Post, db: Session, current_user: Optional[User] = None
) -> PostResponse:
    """
    Helper function to convert Post model to PostResponse
    """
    # Get author info
    author = db.query(User).filter(User.id == post.author_id).first()

    # Get tags
    tags = [TagResponse.model_validate(tag) for tag in post.tags]

    # Get user-specific data if user is authenticated
    user_vote = None
    is_bookmarked = None

    if current_user:
        # Check if user has voted on this post
        vote = (
            db.query(PostVote)
            .filter(PostVote.user_id == current_user.id, PostVote.post_id == post.id)
            .first()
        )
        if vote:
            user_vote = vote.vote_type

        # Check if user has bookmarked this post
        bookmark = (
            db.query(Bookmark)
            .filter(Bookmark.user_id == current_user.id, Bookmark.post_id == post.id)
            .first()
        )
        is_bookmarked = bookmark is not None

    return PostResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        content_plain=post.content_plain,
        content_markdown=post.content_markdown,
        post_type=post.post_type,
        slug=post.slug,
        author_id=post.author_id,
        author_display_name=author.display_name if author else None,
        author_avatar=author.avatar_url if author else None,
        author_is_verified=author.is_verified if author else False,
        view_count=post.view_count,
        upvote_count=post.upvote_count,
        downvote_count=post.downvote_count,
        comment_count=post.comment_count,
        answer_count=post.answer_count,
        is_answered=post.is_answered,
        accepted_answer_id=post.accepted_answer_id,
        has_code=post.has_code,
        has_images=post.has_images,
        is_locked=post.is_locked,
        is_deleted=post.is_deleted,
        is_featured=post.is_featured,
        user_vote=user_vote,
        is_bookmarked=is_bookmarked,
        tags=tags,
        created_at=post.created_at,
        updated_at=post.updated_at,
        last_activity=post.last_activity,
    )


@router.get("/{post_id}/comments", response_model=List[CommentResponse])
async def get_post_comments(
    post_id: int,
    sort: str = Query("newest", pattern="^(newest|oldest|most_voted)$"),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Get comments for a post
    """
    try:
        # Try to get from cache
        cache_key = f"post:{post_id}:comments:{sort}"
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Post comments cache hit: {post_id}")
                cached_comments = json.loads(cached_data)
                return [CommentResponse(**comment) for comment in cached_comments]
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")

        # Verify post exists
        post = (
            db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Get top-level comments (no parent)
        query = db.query(Comment).filter(
            Comment.post_id == post_id,
            Comment.parent_id.is_(None),
            Comment.is_deleted == False,
        )

        # Apply sorting
        if sort == "oldest":
            query = query.order_by(asc(Comment.created_at))
        elif sort == "most_voted":
            query = query.order_by(desc(Comment.upvote_count - Comment.downvote_count))
        else:  # newest
            query = query.order_by(desc(Comment.created_at))

        comments = query.all()

        # Convert to response format with nested replies
        comment_responses = []
        for comment in comments:
            comment_response = await get_comment_response(
                comment, db, include_replies=True
            )
            comment_responses.append(comment_response)

        # Cache the comments
        try:
            cache_data = [comment.model_dump() for comment in comment_responses]
            redis_client.setex(
                cache_key, CACHE_TTL_SHORT, json.dumps(cache_data, default=str)
            )
        except Exception as e:
            logger.warning(f"Failed to cache post comments: {e}")

        return comment_responses

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comments for post {post_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving comments",
        )


async def get_comment_response(
    comment: Comment, db: Session, include_replies: bool = False
) -> CommentResponse:
    """
    Helper function to convert Comment model to CommentResponse
    """
    # Get author info
    author = db.query(User).filter(User.id == comment.author_id).first()

    # Get replies if requested (recursively)
    replies = []
    if include_replies:
        reply_comments = (
            db.query(Comment)
            .filter(Comment.parent_id == comment.id, Comment.is_deleted == False)
            .order_by(asc(Comment.created_at))
            .all()
        )

        for reply in reply_comments:
            # Recursively get replies for nested comments
            reply_response = await get_comment_response(reply, db, include_replies=True)
            replies.append(reply_response)

    return CommentResponse(
        id=comment.id,
        content=comment.content,
        content_plain=comment.content_plain,
        post_id=comment.post_id,
        parent_id=comment.parent_id,
        author_id=comment.author_id,
        author_display_name=author.display_name if author else None,
        author_avatar=author.avatar_url if author else None,
        author_is_verified=author.is_verified if author else False,
        upvote_count=comment.upvote_count,
        downvote_count=comment.downvote_count,
        reply_count=comment.reply_count,
        is_answer=comment.is_answer,
        is_accepted=comment.is_accepted,
        has_code=comment.has_code,
        has_images=comment.has_images,
        is_deleted=comment.is_deleted,
        replies=replies,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
    )


@router.get("/tags/", response_model=List[TagResponse])
async def get_tags(
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Get tags, optionally filtered by search term
    """
    try:
        # Try to get from cache
        cache_key = f"posts:tags:{search or 'all'}:{limit}"
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info("Tags cache hit")
                cached_tags = json.loads(cached_data)
                return [TagResponse(**tag) for tag in cached_tags]
        except Exception as e:
            logger.warning(f"Redis cache error: {e}")

        query = db.query(Tag)

        if search:
            search_term = f"%{search.lower()}%"
            query = query.filter(Tag.name.ilike(search_term))

        tags = query.order_by(desc(Tag.post_count)).limit(limit).all()

        tag_responses = [TagResponse.model_validate(tag) for tag in tags]

        # Cache the tags (tags change infrequently)
        try:
            cache_data = [tag.model_dump() for tag in tag_responses]
            redis_client.setex(
                cache_key, CACHE_TTL_LONG, json.dumps(cache_data, default=str)
            )
        except Exception as e:
            logger.warning(f"Failed to cache tags: {e}")

        return tag_responses

    except Exception as e:
        logger.error(f"Error getting tags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving tags",
        )


@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    post_id: int,
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Create a comment on a post

    Requires authentication. Include JWT token in Authorization header.
    """
    try:
        # Verify post exists and is not locked
        post = (
            db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if post.is_locked:
            raise HTTPException(status_code=403, detail="Post is locked for comments")

        # Verify parent comment exists if specified
        if comment_data.parent_id:
            parent_comment = (
                db.query(Comment)
                .filter(
                    Comment.id == comment_data.parent_id,
                    Comment.post_id == post_id,
                    Comment.is_deleted == False,
                )
                .first()
            )
            if not parent_comment:
                raise HTTPException(status_code=404, detail="Parent comment not found")

        # Process comment content
        processed_content, content_analysis = process_post_content(
            comment_data.content, "markdown"
        )

        # Create comment
        db_comment = Comment(
            content=processed_content,
            content_plain=content_analysis.plain_text,
            post_id=post_id,
            author_id=current_user.id,
            parent_id=comment_data.parent_id,
            is_answer=comment_data.is_answer,
            has_code=content_analysis.has_code,
            has_images=content_analysis.has_images,
        )

        db.add(db_comment)

        # Update counters
        post.comment_count += 1
        if comment_data.is_answer:
            post.answer_count += 1

        current_user.comment_count += 1

        # Update parent comment reply count if it's a reply
        if comment_data.parent_id:
            parent_comment.reply_count += 1

        # Update post last activity
        post.last_activity = func.now()

        db.commit()
        db.refresh(db_comment)

        # Send email notification if this is an answer to the post author (async, don't block)
        if comment_data.is_answer:
            try:
                # Get post author
                post_author = db.query(User).filter(User.id == post.author_id).first()
                # Only send if answerer is not the post author
                if post_author and post_author.id != current_user.id:
                    email_service.send_new_answer_notification(
                        post_author,
                        current_user,
                        post.title,
                        post.id,
                        post.slug,
                        db_comment.content_plain,
                        current_user.karma_score,
                    )
                    logger.info(
                        f"New answer notification sent to {post_author.email} for post {post_id}"
                    )
            except Exception as e:
                logger.warning(f"Failed to send new answer notification: {e}")

        # Invalidate relevant caches
        try:
            # Clear post cache (comment count changed)
            redis_client.delete(f"post:{post_id}")
            # Clear comments cache for this post
            for key in redis_client.scan_iter(match=f"post:{post_id}:comments:*"):
                redis_client.delete(key)
            # Clear post lists cache
            for key in redis_client.scan_iter(match="posts:list:*"):
                redis_client.delete(key)
            # Clear user profile cache (comment count changed)
            redis_client.delete(f"user:profile:{current_user.display_name}")
            logger.info(f"Cleared comment-related caches for post {post_id}")
        except Exception as e:
            logger.warning(f"Failed to clear comment caches: {e}")

        logger.info(
            f"New comment created: {db_comment.id} on post {post_id} by {current_user.username}"
        )

        return await get_comment_response(db_comment, db)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating comment",
        )


@router.post(
    "/{post_id}/vote", response_model=VoteResponse, status_code=status.HTTP_201_CREATED
)
async def vote_on_post(
    post_id: int,
    vote_data: VoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Vote on a post (upvote or downvote)

    Requires authentication. Users can change their vote or remove it by voting again.
    """
    try:
        # Verify post exists
        post = (
            db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Get post author for karma updates
        post_author = db.query(User).filter(User.id == post.author_id).first()

        # Check if user already voted
        existing_vote = (
            db.query(PostVote)
            .filter(PostVote.post_id == post_id, PostVote.user_id == current_user.id)
            .first()
        )

        if existing_vote:
            # Update existing vote or remove if same vote type
            if existing_vote.vote_type == vote_data.vote_type:
                # Remove vote (toggle off)
                if existing_vote.vote_type == "upvote":
                    post.upvote_count -= 1
                    if post_author:
                        post_author.karma_score -= 10  # Remove karma for removed upvote
                else:
                    post.downvote_count -= 1
                    if post_author:
                        post_author.karma_score += (
                            2  # Restore karma from removed downvote
                        )

                db.delete(existing_vote)
                db.commit()

                # Invalidate caches
                try:
                    redis_client.delete(f"post:{post_id}")
                    for key in redis_client.scan_iter(match="posts:list:*"):
                        redis_client.delete(key)
                    if post_author:
                        redis_client.delete(f"user:profile:{post_author.display_name}")
                        for key in redis_client.scan_iter(match="users:top:*"):
                            redis_client.delete(key)
                except Exception as e:
                    logger.warning(f"Failed to clear vote caches: {e}")

                return {"message": "Vote removed", "action": "removed"}
            else:
                # Change vote type
                old_vote = existing_vote.vote_type
                existing_vote.vote_type = vote_data.vote_type

                # Update counters and karma
                if old_vote == "upvote":
                    post.upvote_count -= 1
                    post.downvote_count += 1
                    if post_author:
                        post_author.karma_score -= 10  # Remove upvote karma
                        post_author.karma_score -= 2  # Apply downvote penalty
                else:
                    post.downvote_count -= 1
                    post.upvote_count += 1
                    if post_author:
                        post_author.karma_score += 2  # Remove downvote penalty
                        post_author.karma_score += 10  # Apply upvote karma

                db.commit()

                # Invalidate caches
                try:
                    redis_client.delete(f"post:{post_id}")
                    for key in redis_client.scan_iter(match="posts:list:*"):
                        redis_client.delete(key)
                    if post_author:
                        redis_client.delete(f"user:profile:{post_author.display_name}")
                        for key in redis_client.scan_iter(match="users:top:*"):
                            redis_client.delete(key)
                except Exception as e:
                    logger.warning(f"Failed to clear vote caches: {e}")

                return VoteResponse.model_validate(existing_vote)
        else:
            # Create new vote
            new_vote = PostVote(
                post_id=post_id, user_id=current_user.id, vote_type=vote_data.vote_type
            )

            db.add(new_vote)

            # Update counters and karma
            if vote_data.vote_type == "upvote":
                post.upvote_count += 1
                if post_author:
                    post_author.karma_score += 10  # Add karma for upvote
            else:
                post.downvote_count += 1
                if post_author:
                    post_author.karma_score -= 2  # Subtract karma for downvote

            db.commit()
            db.refresh(new_vote)

            # Invalidate caches
            try:
                redis_client.delete(f"post:{post_id}")
                for key in redis_client.scan_iter(match="posts:list:*"):
                    redis_client.delete(key)
                if post_author:
                    redis_client.delete(f"user:profile:{post_author.display_name}")
                    for key in redis_client.scan_iter(match="users:top:*"):
                        redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Failed to clear vote caches: {e}")

            return VoteResponse.model_validate(new_vote)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error voting on post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing vote",
        )


@router.post(
    "/comments/{comment_id}/vote",
    response_model=VoteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def vote_on_comment(
    comment_id: int,
    vote_data: VoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Vote on a comment (upvote or downvote)

    Requires authentication. Users can change their vote or remove it by voting again.
    """
    try:
        # Verify comment exists
        comment = (
            db.query(Comment)
            .filter(Comment.id == comment_id, Comment.is_deleted == False)
            .first()
        )
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Get comment author for karma updates
        comment_author = db.query(User).filter(User.id == comment.author_id).first()

        # Check if user already voted
        existing_vote = (
            db.query(CommentVote)
            .filter(
                CommentVote.comment_id == comment_id,
                CommentVote.user_id == current_user.id,
            )
            .first()
        )

        if existing_vote:
            # Update existing vote or remove if same vote type
            if existing_vote.vote_type == vote_data.vote_type:
                # Remove vote (toggle off)
                if existing_vote.vote_type == "upvote":
                    comment.upvote_count -= 1
                    if comment_author:
                        comment_author.karma_score -= (
                            5  # Remove karma for removed upvote
                        )
                else:
                    comment.downvote_count -= 1
                    if comment_author:
                        comment_author.karma_score += (
                            1  # Restore karma from removed downvote
                        )

                db.delete(existing_vote)
                db.commit()

                # Invalidate comment caches
                try:
                    for key in redis_client.scan_iter(
                        match=f"post:{comment.post_id}:comments:*"
                    ):
                        redis_client.delete(key)
                    if comment_author:
                        redis_client.delete(
                            f"user:profile:{comment_author.display_name}"
                        )
                        for key in redis_client.scan_iter(match="users:top:*"):
                            redis_client.delete(key)
                except Exception as e:
                    logger.warning(f"Failed to clear comment vote caches: {e}")

                return {"message": "Vote removed", "action": "removed"}
            else:
                # Change vote type
                old_vote = existing_vote.vote_type
                existing_vote.vote_type = vote_data.vote_type

                # Update counters and karma
                if old_vote == "upvote":
                    comment.upvote_count -= 1
                    comment.downvote_count += 1
                    if comment_author:
                        comment_author.karma_score -= 5  # Remove upvote karma
                        comment_author.karma_score -= 1  # Apply downvote penalty
                else:
                    comment.downvote_count -= 1
                    comment.upvote_count += 1
                    if comment_author:
                        comment_author.karma_score += 1  # Remove downvote penalty
                        comment_author.karma_score += 5  # Apply upvote karma

                db.commit()

                # Invalidate comment caches
                try:
                    for key in redis_client.scan_iter(
                        match=f"post:{comment.post_id}:comments:*"
                    ):
                        redis_client.delete(key)
                    if comment_author:
                        redis_client.delete(
                            f"user:profile:{comment_author.display_name}"
                        )
                        for key in redis_client.scan_iter(match="users:top:*"):
                            redis_client.delete(key)
                except Exception as e:
                    logger.warning(f"Failed to clear comment vote caches: {e}")

                return VoteResponse.model_validate(existing_vote)
        else:
            # Create new vote
            new_vote = CommentVote(
                comment_id=comment_id,
                user_id=current_user.id,
                vote_type=vote_data.vote_type,
            )

            db.add(new_vote)

            # Update counters and karma
            if vote_data.vote_type == "upvote":
                comment.upvote_count += 1
                if comment_author:
                    comment_author.karma_score += 5  # Add karma for upvote
            else:
                comment.downvote_count += 1
                if comment_author:
                    comment_author.karma_score -= 1  # Subtract karma for downvote

            db.commit()
            db.refresh(new_vote)

            # Invalidate comment caches
            try:
                for key in redis_client.scan_iter(
                    match=f"post:{comment.post_id}:comments:*"
                ):
                    redis_client.delete(key)
                if comment_author:
                    redis_client.delete(f"user:profile:{comment_author.display_name}")
                    for key in redis_client.scan_iter(match="users:top:*"):
                        redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Failed to clear comment vote caches: {e}")

            return VoteResponse.model_validate(new_vote)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error voting on comment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing vote",
        )


@router.post("/{post_id}/comments/{comment_id}/accept")
async def accept_answer(
    post_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Mark a comment as the accepted answer for a question

    Only the post author can accept answers. Only one answer can be accepted per post.
    Calling this on an already-accepted answer will unaccept it.
    """
    try:
        # Verify post exists and is a question
        post = (
            db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Only post author can accept answers
        if post.author_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Only the post author can accept answers"
            )

        # Only questions can have accepted answers
        if post.post_type != "question":
            raise HTTPException(
                status_code=400, detail="Only questions can have accepted answers"
            )

        # Verify comment exists and belongs to this post
        comment = (
            db.query(Comment)
            .filter(
                Comment.id == comment_id,
                Comment.post_id == post_id,
                Comment.is_deleted == False,
            )
            .first()
        )
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")

        # Check if this comment is already accepted
        if comment.is_accepted and post.accepted_answer_id == comment_id:
            # Unaccept the answer
            comment.is_accepted = False
            post.accepted_answer_id = None

            # Remove karma bonus for unaccepted answer
            comment_author = db.query(User).filter(User.id == comment.author_id).first()
            if comment_author:
                comment_author.karma_score -= 15  # Remove accepted answer karma bonus

            db.commit()

            # Invalidate caches
            try:
                redis_client.delete(f"post:{post_id}")
                for key in redis_client.scan_iter(match=f"post:{post_id}:comments:*"):
                    redis_client.delete(key)
                if comment_author:
                    redis_client.delete(f"user:profile:{comment_author.display_name}")
                    for key in redis_client.scan_iter(match="users:top:*"):
                        redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Failed to clear caches: {e}")

            return {"message": "Answer unaccepted", "is_accepted": False}
        else:
            # Unaccept any previously accepted answer
            if post.accepted_answer_id:
                old_accepted = (
                    db.query(Comment)
                    .filter(Comment.id == post.accepted_answer_id)
                    .first()
                )
                if old_accepted:
                    old_accepted.is_accepted = False
                    # Remove karma from previously accepted answer author
                    old_author = (
                        db.query(User).filter(User.id == old_accepted.author_id).first()
                    )
                    if old_author:
                        old_author.karma_score -= 15

            # Accept this answer
            comment.is_accepted = True
            post.accepted_answer_id = comment_id

            # Add karma bonus for accepted answer
            comment_author = db.query(User).filter(User.id == comment.author_id).first()
            if comment_author:
                comment_author.karma_score += 15  # Bonus for accepted answer

            db.commit()

            # Invalidate caches
            try:
                redis_client.delete(f"post:{post_id}")
                for key in redis_client.scan_iter(match=f"post:{post_id}:comments:*"):
                    redis_client.delete(key)
                if comment_author:
                    redis_client.delete(f"user:profile:{comment_author.display_name}")
                    for key in redis_client.scan_iter(match="users:top:*"):
                        redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Failed to clear caches: {e}")

            return {"message": "Answer accepted", "is_accepted": True}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error accepting answer: {e}")
        raise HTTPException(status_code=500, detail="Failed to accept answer")


@router.post("/{post_id}/bookmark")
async def toggle_bookmark(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Toggle bookmark on a post

    If post is bookmarked, remove bookmark. If not bookmarked, add bookmark.
    """
    try:
        # Verify post exists
        post = (
            db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Check if bookmark exists
        existing_bookmark = (
            db.query(Bookmark)
            .filter(Bookmark.post_id == post_id, Bookmark.user_id == current_user.id)
            .first()
        )

        if existing_bookmark:
            # Remove bookmark
            db.delete(existing_bookmark)
            db.commit()
            logger.info(
                f"Bookmark removed for post {post_id} by user {current_user.id}"
            )
            return {"message": "Bookmark removed", "is_bookmarked": False}
        else:
            # Add bookmark
            new_bookmark = Bookmark(post_id=post_id, user_id=current_user.id)
            db.add(new_bookmark)
            db.commit()
            logger.info(f"Bookmark added for post {post_id} by user {current_user.id}")
            return {"message": "Bookmark added", "is_bookmarked": True}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error toggling bookmark: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error toggling bookmark",
        )


@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
):
    """
    Delete a post (soft delete)

    Only the post author can delete their own posts.
    """
    try:
        # Get post
        post = (
            db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
        )
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Check if user is the author
        if post.author_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="You can only delete your own posts"
            )

        # Soft delete
        post.is_deleted = True
        db.commit()

        # Invalidate caches
        try:
            redis_client.delete(f"post:{post_id}")
            for key in redis_client.scan_iter(match="posts:list:*"):
                redis_client.delete(key)
            redis_client.delete(f"user:profile:{current_user.display_name}")
        except Exception as e:
            logger.warning(f"Failed to clear caches: {e}")

        logger.info(f"Post {post_id} deleted by user {current_user.id}")
        return {"message": "Post deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting post",
        )
