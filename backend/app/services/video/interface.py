from abc import ABC, abstractmethod

from app.services.video.models import (
    LessonScript,
    VideoRequest,
    VideoResult,
)


class VideoProvider(ABC):

    @property
    @abstractmethod
    def name(self) -> str:
        """Return provider name."""
        pass

    @abstractmethod
    async def generate(
        self,
        request: VideoRequest,
    ) -> VideoResult:
        """Generate a video from a lesson."""
        pass

    @abstractmethod
    async def get_status(
        self,
        job_id: str,
    ) -> VideoResult:
        """Check generation status."""
        pass

    @abstractmethod
    async def cancel(
        self,
        job_id: str,
    ) -> bool:
        """Cancel a running video generation."""
        pass