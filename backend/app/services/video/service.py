from app.services.video.interface import VideoProvider
from app.services.video.models import (
    VideoRequest,
    VideoResult,
)


class VideoService:

    def __init__(
        self,
        provider: VideoProvider,
    ):
        self.provider = provider

    async def generate(
        self,
        request: VideoRequest,
    ) -> VideoResult:

        return await self.provider.generate(request)

    async def get_status(
        self,
        job_id: str,
    ) -> VideoResult:

        return await self.provider.get_status(job_id)

    async def cancel(
        self,
        job_id: str,
    ) -> bool:

        return await self.provider.cancel(job_id)