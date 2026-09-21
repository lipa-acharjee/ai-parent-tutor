import asyncio

from app.services.video import get_video_service
from app.services.video.models import (
    VideoRequest,
    LessonScript,
    LessonScene,
)


async def main():

    script = LessonScript(
        title="Our Solar System",
        introduction=(
            "Today we are going to learn about our solar system."
        ),
        scenes=[
            LessonScene(
                title="The Sun",
                narration=(
                    "The Sun is a star at the center "
                    "of our solar system."
                ),
                visual_description=(
                    "Show the Sun at the center with planets "
                    "moving around it."
                ),
            ),
            LessonScene(
                title="Earth",
                narration=(
                    "Earth is the third planet from the Sun "
                    "and is the planet where we live."
                ),
                visual_description=(
                    "Show Earth orbiting around the Sun."
                ),
            ),
        ],
        conclusion=(
            "Today we learned about the Sun and Earth "
            "in our solar system."
        ),
    )

    request = VideoRequest(
        lesson_id="test-lesson-001",
        script=script,
        provider="local",
        language="en",
        resolution="720p",
    )

    service = get_video_service()

    print("Video provider:", service.provider.name)

    result = await service.generate(request)

    print(result)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio

from app.services.video import get_video_service
from app.services.video.models import (
    VideoRequest,
    LessonScript,
    LessonScene,
)


async def main():

    script = LessonScript(
        title="Our Solar System",
        introduction=(
            "Today we are going to learn about our solar system."
        ),
        scenes=[
            LessonScene(
                title="The Sun",
                narration=(
                    "The Sun is a star at the center "
                    "of our solar system."
                ),
                visual_description=(
                    "Show the Sun at the center with planets "
                    "moving around it."
                ),
            ),
            LessonScene(
                title="Earth",
                narration=(
                    "Earth is the third planet from the Sun "
                    "and is the planet where we live."
                ),
                visual_description=(
                    "Show Earth orbiting around the Sun."
                ),
            ),
        ],
        conclusion=(
            "Today we learned about the Sun and Earth "
            "in our solar system."
        ),
    )

    request = VideoRequest(
        lesson_id="test-lesson-001",
        script=script,
        provider="local",
        language="en",
        resolution="720p",
    )

    service = get_video_service()

    print("Video provider:", service.provider.name)

    result = await service.generate(request)

    print(result)


if __name__ == "__main__":
    asyncio.run(main())