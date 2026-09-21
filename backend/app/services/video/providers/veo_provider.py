from app.services.video.interface import VideoProvider
from app.services.video.models import VideoRequest, VideoResult


class VeoVideoProvider(VideoProvider):

    @property
    def name(self) -> str:
        return "veo"

    async def generate(
        self,
        request: VideoRequest,
    ) -> VideoResult:

        """
        Generate educational visual scenes using Google Veo.
        """

        # TODO:
        # Call Gemini/Veo API.

        return VideoResult(
            success=True,
            provider=self.name,
            job_id="veo-job-placeholder",
            status="processing",
        )

    async def get_status(
        self,
        job_id: str,
    ) -> VideoResult:

        # TODO

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

        # TODO

        return True