from app.core.config import settings

from app.services.video.service import VideoService

from app.services.video.providers.local_provider import (
    LocalVideoProvider,
)

from app.services.video.providers.heygen_provider import (
    HeyGenVideoProvider,
)

from app.services.video.providers.veo_provider import (
    VeoVideoProvider,
)


def get_video_provider():

    provider = settings.video_provider.lower()

    if provider == "local":
        return LocalVideoProvider()

    if provider == "heygen":
        return HeyGenVideoProvider()

    if provider == "veo":
        return VeoVideoProvider()

    raise ValueError(
        f"Unsupported video provider: {provider}"
    )


def get_video_service():

    provider = get_video_provider()

    return VideoService(provider)