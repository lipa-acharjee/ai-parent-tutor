from fastapi import APIRouter, HTTPException

from app.services.video import get_video_service
from app.services.video.models import VideoRequest


router = APIRouter()


@router.post("/generate")
async def generate_video(
    request: VideoRequest,
):

    service = get_video_service()

    result = await service.generate(request)

    if not result.success:

        raise HTTPException(
            status_code=500,
            detail=result.error,
        )

    return result