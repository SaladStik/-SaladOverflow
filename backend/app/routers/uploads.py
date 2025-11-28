from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.auth import get_current_user
from app.utils.file_upload import save_uploaded_image, delete_image, get_image_info
from app.services.image_cleanup import manual_image_cleanup
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/uploads", tags=["File Uploads"])


class ImageUploadResponse(BaseModel):
    """Response model for image upload"""

    url: str
    filename: str
    size: int
    width: int
    height: int
    message: str


class DeleteImageResponse(BaseModel):
    """Response model for image deletion"""

    success: bool
    message: str


class ImageCleanupResponse(BaseModel):
    """Response model for image cleanup"""

    total_images: int
    orphaned_found: int
    deleted_count: int
    deleted_files: list
    message: str


class ProfileImageUploadResponse(BaseModel):
    """Response model for profile image upload"""

    image_url: str
    message: str
    user_id: int


@router.post(
    "/images", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED
)
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload an image file (JPG/PNG only, max 15MB)

    Requires authentication. Include JWT token in Authorization header.

    **File Requirements:**
    - **Format**: JPG/JPEG or PNG only
    - **Size**: Maximum 15MB
    - **Dimensions**: Will be automatically resized to max 2048px if larger
    - **Quality**: JPEGs saved at 85% quality for optimization

    **Usage Example:**
    ```python
    import requests

    # Get auth token first
    login_response = requests.post("/api/v1/auth/login", json={
        "email": "user@example.com",
        "password": "password"
    })
    token = login_response.json()["access_token"]

    # Upload image
    with open("image.jpg", "rb") as f:
        response = requests.post("/api/v1/uploads/images",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("image.jpg", f, "image/jpeg")}
        )

    image_url = response.json()["url"]
    # Use image_url in your posts: ![Image](https://yourdomain.com{image_url})
    ```

    Returns the URL path to access the uploaded image.
    """
    try:
        # Save the uploaded image
        image_url = await save_uploaded_image(file, current_user.id)

        # Get image information
        image_info = get_image_info(image_url)
        if not image_info:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get image information",
            )

        return ImageUploadResponse(
            url=image_url,
            filename=image_info["filename"],
            size=image_info["size"],
            width=image_info["width"],
            height=image_info["height"],
            message="Image uploaded successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload_image endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image",
        )


@router.delete("/images", response_model=DeleteImageResponse)
async def delete_uploaded_image(
    image_url: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete an uploaded image

    Requires authentication. Include JWT token in Authorization header.

    - **image_url**: The URL path of the image to delete (e.g., "/uploads/images/filename.jpg")

    Note: This endpoint allows users to delete any image. In a production environment,
    you might want to add ownership checks to ensure users can only delete their own images.
    """
    try:
        # Validate image_url format
        if not image_url.startswith("/uploads/images/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image URL format",
            )

        # Delete the image
        success = delete_image(image_url)

        if success:
            return DeleteImageResponse(
                success=True, message="Image deleted successfully"
            )
        else:
            return DeleteImageResponse(
                success=False, message="Image not found or already deleted"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_uploaded_image endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image",
        )


@router.post("/cleanup", response_model=ImageCleanupResponse)
async def cleanup_orphaned_images(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """
    Manually trigger cleanup of orphaned images

    Requires authentication. Include JWT token in Authorization header.

    This endpoint removes uploaded images that:
    - Have been on the server for more than 3 hours
    - Are not referenced in any post or comment content

    **Note**: This is automatically done every hour by a background service,
    but you can trigger it manually with this endpoint for immediate cleanup.
    """
    try:
        result = await manual_image_cleanup()

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"],
            )

        return ImageCleanupResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in cleanup_orphaned_images endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cleanup orphaned images",
        )


@router.post(
    "/profile-image",
    response_model=ProfileImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a profile image for the current user

    Requires authentication. Include JWT token in Authorization header.

    **File Requirements:**
    - **Format**: JPG/JPEG or PNG only
    - **Size**: Maximum 15MB
    - **Dimensions**: Will be automatically resized to max 1024px (optimized for profiles)
    - **Quality**: JPEGs saved at 90% quality for better profile image quality

    **Usage Example:**
    ```python
    import requests

    # Get auth token first
    headers = {"Authorization": f"Bearer {token}"}

    # Upload profile image
    with open("profile.jpg", "rb") as f:
        response = requests.post("/api/v1/uploads/profile-image",
            headers=headers,
            files={"file": ("profile.jpg", f, "image/jpeg")}
        )

    # Profile image URL is automatically set in user profile
    ```

    The uploaded image automatically becomes the user's profile image.
    Previous profile images are replaced.
    """
    try:
        # Delete old profile image if exists
        if current_user.image and current_user.image.startswith("/uploads/images/"):
            try:
                delete_image(current_user.image)
                logger.info(f"Deleted old profile image for user {current_user.id}")
            except Exception as e:
                logger.warning(f"Failed to delete old profile image: {e}")

        # Upload new profile image with smaller max dimension for profiles
        image_url = await save_uploaded_image(file, current_user.id)

        # Update user's profile image in database
        current_user.image = image_url
        current_user.avatar_url = image_url  # Also set avatar_url for compatibility
        db.commit()

        logger.info(f"Profile image updated for user {current_user.id}: {image_url}")

        return ProfileImageUploadResponse(
            image_url=image_url,
            message="Profile image uploaded successfully",
            user_id=current_user.id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload_profile_image endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload profile image",
        )


@router.post(
    "/banner-image",
    response_model=ProfileImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_banner_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a banner image for the current user's profile

    Requires authentication. Include JWT token in Authorization header.

    **File Requirements:**
    - **Format**: JPG/JPEG or PNG only
    - **Size**: Maximum 15MB
    - **Dimensions**: Will be automatically resized to max 2048px (optimized for banners)
    - **Quality**: JPEGs saved at 85% quality

    The uploaded image automatically becomes the user's profile banner.
    Previous banner images are replaced.
    """
    try:
        # Delete old banner image if exists
        if current_user.banner_url and current_user.banner_url.startswith(
            "/uploads/images/"
        ):
            try:
                delete_image(current_user.banner_url)
                logger.info(f"Deleted old banner image for user {current_user.id}")
            except Exception as e:
                logger.warning(f"Failed to delete old banner image: {e}")

        # Upload new banner image
        image_url = await save_uploaded_image(file, current_user.id)

        # Update user's banner image in database
        current_user.banner_url = image_url
        db.commit()

        logger.info(f"Banner image updated for user {current_user.id}: {image_url}")

        return ProfileImageUploadResponse(
            image_url=image_url,
            message="Banner image uploaded successfully",
            user_id=current_user.id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in upload_banner_image endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload banner image",
        )
