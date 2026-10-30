import uuid
import logging
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_current_user

from app.db.database import get_db
from app.db.models import (
    Child,
    Family,
    SharedVideo,
)

from app.services.storage import storage


router = APIRouter()
logger = logging.getLogger(__name__)

# ============================================================
# HELPERS
# ============================================================

async def get_parent_grades(user, db: AsyncSession) -> set[str]:
    """
    Return the grades belonging to the logged-in parent's
    children.
    """

    family_result = await db.execute(
        select(Family).where(
            Family.owner_id == user.id
        )
    )

    family = family_result.scalar_one_or_none()

    if not family:
        raise HTTPException(
            status_code=404,
            detail="Family not found.",
        )

    result = await db.execute(
        select(Child.grade).where(
            Child.family_id == family.id
        )
    )

    return {
        grade.strip()
        for grade in result.scalars().all()
        if grade and grade.strip()
    }


def video_metadata(video: SharedVideo) -> dict:
    """
    Return video metadata without exposing the storage key.
    """

    return {
        "id": video.id,
        "topic": video.topic,
        "grade": video.grade,
        "original_filename": video.original_filename,
        "content_type": video.content_type,
        "size_bytes": video.size_bytes,
        "uploaded_by": video.uploaded_by,
        "created_at": video.created_at,
    }


# ============================================================
# POST /api/v1/shared-videos
#
# Upload an MP4 video and associate it with a grade.
# ============================================================

@router.post("")
async def upload_shared_video(
    topic: str = Form(...),
    grade: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    topic = topic.strip()
    grade = grade.strip()

    if not topic:
        raise HTTPException(
            status_code=400,
            detail="Topic name is required.",
        )

    if len(topic) > 200:
        raise HTTPException(
            status_code=400,
            detail="Topic name cannot exceed 200 characters.",
        )

    if not grade:
        raise HTTPException(
            status_code=400,
            detail="Grade is required.",
        )

    if len(grade) > 40:
        raise HTTPException(
            status_code=400,
            detail="Grade cannot exceed 40 characters.",
        )

    # Only accept MP4 filenames.
    filename = file.filename or ""

    if not filename.lower().endswith(".mp4"):
        raise HTTPException(
            status_code=400,
            detail="Only MP4 video files are supported.",
        )

    # Verify the parent's grade.
    #
    # A parent can upload a video for a grade only if at
    # least one of their own children belongs to that grade.

    parent_grades = await get_parent_grades(
        user,
        db,
    )

    if grade not in parent_grades:
        raise HTTPException(
            status_code=403,
            detail=(
                "You can upload videos only for grades "
                "belonging to your children."
            ),
        )

    # Use the existing application upload limit.
    max_bytes = settings.max_upload_mb * 1024 * 1024

    # Read at most one byte beyond the permitted size.
    data = await file.read(max_bytes + 1)

    if not data:
        raise HTTPException(
            status_code=400,
            detail="The uploaded video is empty.",
        )

    if len(data) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=(
                f"Video exceeds the maximum upload size "
                f"of {settings.max_upload_mb} MB."
            ),
        )

    # Check that the file resembles an MP4 container.
    #
    # Standard MP4 files normally contain 'ftyp' at
    # bytes 4-7. This is a basic format check, not a
    # complete security or media validation process.

    if len(data) < 12 or data[4:8] != b"ftyp":
        raise HTTPException(
            status_code=400,
            detail="The uploaded file does not appear to be a valid MP4.",
        )

    # Use a generated storage filename rather than trusting
    # the original filename as a storage path.

    video_id = str(uuid.uuid4())

    storage_key = (
        f"shared-videos/{video_id}.mp4"
    )

    storage_uploaded = False

    try:
        # Upload the actual MP4 to Supabase Storage through
        # the existing S3-compatible storage service.

        storage.put(
            key=storage_key,
            body=data,
            content_type="video/mp4",
        )

        storage_uploaded = True

        # Create the database record.
        video = SharedVideo(
            id=video_id,
            topic=topic,
            grade=grade,
            storage_key=storage_key,
            original_filename=filename[:255],
            content_type="video/mp4",
            size_bytes=len(data),
            uploaded_by=user.id,
        )

        db.add(video)

        await db.commit()

        await db.refresh(video)

        return {
            "message": "Video uploaded successfully.",
            "video": video_metadata(video),
        }

    except Exception as exc:
        logger.exception("Shared video upload failed")
        
        await db.rollback()

        # If database insertion fails after the storage
        # upload, try to remove the orphaned storage object.

        if storage_uploaded:
            try:
                storage.delete(storage_key)
            except Exception:
                pass

        if isinstance(exc, HTTPException):
            raise

        raise HTTPException(
            status_code=500,
            detail="Could not upload the video.",
        ) from exc

    finally:
        await file.close()


# ============================================================
# GET /api/v1/shared-videos
#
# List videos matching the logged-in parent's children's
# grades.
# ============================================================

@router.get("")
async def list_shared_videos(
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    parent_grades = await get_parent_grades(
        user,
        db,
    )

    if not parent_grades:
        return []

    result = await db.execute(
        select(SharedVideo)
        .where(
            SharedVideo.grade.in_(parent_grades)
        )
        .order_by(
            SharedVideo.created_at.desc()
        )
    )

    videos = result.scalars().all()

    return [
        video_metadata(video)
        for video in videos
    ]


# ============================================================
# GET /api/v1/shared-videos/{video_id}/play
#
# Return a temporary playback URL after checking grade access.
# ============================================================

@router.get("/{video_id}/play")
async def play_shared_video(
    video_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    parent_grades = await get_parent_grades(
        user,
        db,
    )

    result = await db.execute(
        select(SharedVideo).where(
            SharedVideo.id == video_id
        )
    )

    video = result.scalar_one_or_none()

    if not video:
        raise HTTPException(
            status_code=404,
            detail="Video not found.",
        )

    # Enforce grade-based authorization on every playback
    # request, even if the caller knows the video ID.

    if video.grade not in parent_grades:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this video.",
        )

    try:
        video_url = storage.presign_get(
            video.storage_key,
            expires=900,
        )

        return {
            "id": video.id,
            "topic": video.topic,
            "grade": video.grade,
            "video_url": video_url,
            "expires_in": 900,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Could not generate the video playback URL.",
        ) from exc