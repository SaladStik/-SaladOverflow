import os
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.utils.file_upload import UPLOAD_DIR, delete_image

logger = logging.getLogger(__name__)

# Cleanup configuration
ORPHAN_IMAGE_TIMEOUT = timedelta(hours=3)  # 3 hours
CLEANUP_INTERVAL = timedelta(hours=1)  # Run cleanup every hour


class ImageCleanupService:
    """
    Service to clean up orphaned images that aren't referenced in any posts
    """

    def __init__(self):
        self.running = False

    async def start_cleanup_task(self):
        """Start the background cleanup task"""
        if self.running:
            logger.warning("Image cleanup task is already running")
            return

        self.running = True
        logger.info("Starting image cleanup background task")

        try:
            while self.running:
                await self.cleanup_orphaned_images()
                # Wait for the next cleanup interval
                await asyncio.sleep(CLEANUP_INTERVAL.total_seconds())
        except Exception as e:
            logger.error(f"Image cleanup task failed: {e}")
        finally:
            self.running = False

    def stop_cleanup_task(self):
        """Stop the background cleanup task"""
        logger.info("Stopping image cleanup background task")
        self.running = False

    async def cleanup_orphaned_images(self):
        """
        Clean up orphaned images that have been on the server for more than 3 hours
        without being referenced in any posts
        """
        try:
            logger.info("Starting orphaned image cleanup...")

            # Get list of all uploaded images
            uploaded_images = self._get_uploaded_images()
            if not uploaded_images:
                logger.info("No uploaded images found")
                return

            logger.info(f"Found {len(uploaded_images)} uploaded images to check")

            # Get database session
            db = next(get_db())
            try:
                # Find orphaned images
                orphaned_images = await self._find_orphaned_images(db, uploaded_images)

                if not orphaned_images:
                    logger.info("No orphaned images found")
                    return

                logger.info(f"Found {len(orphaned_images)} orphaned images to clean up")

                # Delete orphaned images
                deleted_count = 0
                for image_info in orphaned_images:
                    try:
                        if self._delete_orphaned_image(image_info):
                            deleted_count += 1
                            logger.info(
                                f"Deleted orphaned image: {image_info['filename']}"
                            )
                        else:
                            logger.warning(
                                f"Failed to delete orphaned image: {image_info['filename']}"
                            )
                    except Exception as e:
                        logger.error(
                            f"Error deleting image {image_info['filename']}: {e}"
                        )

                logger.info(
                    f"Cleanup completed: {deleted_count} orphaned images deleted"
                )

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error during orphaned image cleanup: {e}")

    def _get_uploaded_images(self) -> List[dict]:
        """Get list of all uploaded images with their metadata"""
        images = []

        try:
            if not UPLOAD_DIR.exists():
                return images

            for file_path in UPLOAD_DIR.glob("*"):
                if file_path.is_file() and file_path.suffix.lower() in [
                    ".jpg",
                    ".jpeg",
                    ".png",
                ]:
                    stat = file_path.stat()
                    images.append(
                        {
                            "filename": file_path.name,
                            "path": str(file_path),
                            "url": f"/uploads/images/{file_path.name}",
                            "created_at": datetime.fromtimestamp(stat.st_ctime),
                            "size": stat.st_size,
                        }
                    )

            return images

        except Exception as e:
            logger.error(f"Error getting uploaded images: {e}")
            return []

    async def _find_orphaned_images(
        self, db: Session, uploaded_images: List[dict]
    ) -> List[dict]:
        """Find images that are orphaned (not referenced in posts and older than timeout)"""
        orphaned = []
        cutoff_time = datetime.now() - ORPHAN_IMAGE_TIMEOUT

        try:
            for image_info in uploaded_images:
                # Check if image is old enough to be considered for cleanup
                if image_info["created_at"] > cutoff_time:
                    continue  # Image is too new, skip

                # Check if image is referenced in any post content
                if not await self._is_image_referenced(db, image_info["url"]):
                    orphaned.append(image_info)

            return orphaned

        except Exception as e:
            logger.error(f"Error finding orphaned images: {e}")
            return []

    async def _is_image_referenced(self, db: Session, image_url: str) -> bool:
        """Check if an image URL is referenced in any post or comment content"""
        try:
            # Check posts
            post_query = text(
                """
                SELECT COUNT(*) FROM posts 
                WHERE content LIKE :image_pattern
            """
            )
            post_result = db.execute(
                post_query, {"image_pattern": f"%{image_url}%"}
            ).scalar()

            if post_result and post_result > 0:
                return True

            # Check comments
            comment_query = text(
                """
                SELECT COUNT(*) FROM comments 
                WHERE content LIKE :image_pattern
            """
            )
            comment_result = db.execute(
                comment_query, {"image_pattern": f"%{image_url}%"}
            ).scalar()

            if comment_result and comment_result > 0:
                return True

            # Check user profiles (avatar_url and banner_url)
            user_query = text(
                """
                SELECT COUNT(*) FROM users 
                WHERE avatar_url LIKE :image_pattern 
                OR banner_url LIKE :image_pattern
            """
            )
            user_result = db.execute(
                user_query, {"image_pattern": f"%{image_url}%"}
            ).scalar()

            if user_result and user_result > 0:
                return True

            return False

        except Exception as e:
            logger.error(f"Error checking if image is referenced: {e}")
            return True  # Assume referenced on error to be safe

    def _delete_orphaned_image(self, image_info: dict) -> bool:
        """Delete an orphaned image file"""
        try:
            file_path = Path(image_info["path"])
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting orphaned image file: {e}")
            return False

    async def manual_cleanup(self) -> dict:
        """
        Manually trigger cleanup and return results
        """
        try:
            logger.info("Manual image cleanup triggered")

            # Get list of all uploaded images
            uploaded_images = self._get_uploaded_images()

            # Get database session
            db = next(get_db())
            try:
                # Find orphaned images
                orphaned_images = await self._find_orphaned_images(db, uploaded_images)

                # Delete orphaned images
                deleted_count = 0
                deleted_files = []

                for image_info in orphaned_images:
                    if self._delete_orphaned_image(image_info):
                        deleted_count += 1
                        deleted_files.append(image_info["filename"])

                return {
                    "total_images": len(uploaded_images),
                    "orphaned_found": len(orphaned_images),
                    "deleted_count": deleted_count,
                    "deleted_files": deleted_files,
                    "message": f"Cleanup completed: {deleted_count} orphaned images deleted",
                }

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Error during manual cleanup: {e}")
            return {"error": str(e), "message": "Cleanup failed due to error"}


# Global cleanup service instance
cleanup_service = ImageCleanupService()


async def start_image_cleanup_service():
    """Start the image cleanup background service"""
    await cleanup_service.start_cleanup_task()


def stop_image_cleanup_service():
    """Stop the image cleanup background service"""
    cleanup_service.stop_cleanup_task()


async def manual_image_cleanup():
    """Manually trigger image cleanup"""
    return await cleanup_service.manual_cleanup()


def is_cleanup_service_running() -> bool:
    """Check if the cleanup service is currently running"""
    return cleanup_service.running
