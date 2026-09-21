from app.services.video.interface import VideoProvider
from app.services.video.models import VideoRequest, VideoResult


class HeyGenVideoProvider(VideoProvider):

    @property
    def name(self) -> str:
        return "heygen"

    async def generate(
        self,
        request: VideoRequest,
    ) -> VideoResult:

        """
        Send lesson script to HeyGen API.
        """

        # TODO:
        # Call HeyGen API here.

        return VideoResult(
            success=True,
            provider=self.name,
            job_id="heygen-job-placeholder",
            status="processing",
        )

    async def get_status(
        self,
        job_id: str,
    ) -> VideoResult:

        # TODO:
        # Check HeyGen API

        return VideoResult(
            success=True,
            provider=self.name,
            job_id=job_id,
            status="processing",
        )

    async def cancel(
        self,
        job_id: str,
    ) -> bool:

        # TODO:
        # Cancel HeyGen generation

        return True