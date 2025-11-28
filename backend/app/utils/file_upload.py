import os
import uuid
import logging
from typing import Optional
from fastapi import UploadFile, HTTPException, status
from PIL import Image
import aiofiles
from pathlib import Path

logger = logging.getLogger(__name__)

# Configuration
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB in bytes
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png"}
UPLOAD_DIR = Path("uploads/images")
MAX_IMAGE_DIMENSION = 2048  # Max width/height in pixels

# Create upload directory if it doesn't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


async def validate_image_file(file: UploadFile) -> bool:
    """
    Validate uploaded image file
    """
    try:
        # Check file size
        if file.size and file.size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({file.size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)",
            )

        # Check MIME type
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Only JPG and PNG images are allowed. Got: {file.content_type}",
            )

        # Check file extension
        file_ext = Path(file.filename or "").suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file extension. Only .jpg, .jpeg, and .png are allowed. Got: {file_ext}",
            )

        return True

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating image file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file"
        )


async def process_image(
    file_path: Path, max_dimension: int = MAX_IMAGE_DIMENSION
) -> bool:
    """
    Process uploaded image (resize if needed, optimize)
    """
    try:
        with Image.open(file_path) as img:
            # Convert RGBA to RGB if necessary (for JPEG compatibility)
            if img.mode in ("RGBA", "LA", "P"):
                # Create white background
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(
                    img, mask=img.split()[-1] if img.mode == "RGBA" else None
                )
                img = background

            # Resize if image is too large
            if img.width > max_dimension or img.height > max_dimension:
                img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                logger.info(f"Resized image to {img.width}x{img.height}")

            # Save optimized image
            if file_path.suffix.lower() in [".jpg", ".jpeg"]:
                img.save(file_path, "JPEG", quality=85, optimize=True)
            else:  # PNG
                img.save(file_path, "PNG", optimize=True)

            return True

    except Exception as e:
        logger.error(f"Error processing image: {e}")
        # Clean up the file if processing failed
        if file_path.exists():
            file_path.unlink()
        return False


async def save_uploaded_image(file: UploadFile, user_id: int) -> str:
    """
    Save uploaded image and return the URL path
    """
    try:
        # Validate the file
        await validate_image_file(file)

        # Generate unique filename
        file_ext = Path(file.filename or "").suffix.lower()
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename

        # Save file to disk
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()

            # Double-check file size after reading
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)",
                )

            await f.write(content)

        # Process the image (resize, optimize)
        if not await process_image(file_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process image file",
            )

        # Return the full URL with backend domain
        from app.config import settings

        image_url = f"{settings.backend_url}/uploads/images/{unique_filename}"

        logger.info(f"Image uploaded successfully: {image_url} by user {user_id}")
        return image_url

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving uploaded image: {e}")
        # Clean up file if it was created
        if "file_path" in locals() and file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image",
        )


def delete_image(image_url: str) -> bool:
    """
    Delete an uploaded image file
    """
    try:
        # Extract filename from URL
        filename = Path(image_url).name
        file_path = UPLOAD_DIR / filename

        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted image: {image_url}")
            return True
        else:
            logger.warning(f"Image file not found for deletion: {image_url}")
            return False

    except Exception as e:
        logger.error(f"Error deleting image {image_url}: {e}")
        return False


def get_image_info(image_url: str) -> Optional[dict]:
    """
    Get information about an uploaded image
    """
    try:
        filename = Path(image_url).name
        file_path = UPLOAD_DIR / filename

        if not file_path.exists():
            return None

        # Get file stats
        stat = file_path.stat()

        # Get image dimensions
        with Image.open(file_path) as img:
            width, height = img.size

        return {
            "filename": filename,
            "size": stat.st_size,
            "width": width,
            "height": height,
            "created": stat.st_ctime,
        }

    except Exception as e:
        logger.error(f"Error getting image info for {image_url}: {e}")
        return None
