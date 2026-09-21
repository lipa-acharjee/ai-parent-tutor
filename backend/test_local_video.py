import asyncio

from app.services.video.providers.local_provider import (
    LocalVideoProvider,
)
from app.services.video.models import (
    LessonScene,
    LessonScript,
    VideoRequest,
)


async def main():

    script = LessonScript(
        title="Why Do We Have Day and Night?",

        introduction=(
            "Today we are going to understand "
            "why Earth has day and night."
        ),

        scenes=[
            LessonScene(
                title="The Earth",
                narration=(
                    "Earth is a planet that moves through space. "
                    "It also spins around an imaginary line called "
                    "its axis."
                ),
                visual_description=(
                    "The Earth spinning around its axis."
                ),
            ),

            LessonScene(
                title="Sunlight",
                narration=(
                    "The Sun gives us light. The side of Earth "
                    "facing the Sun experiences daytime."
                ),
                visual_description=(
                    "The Sun shining on one side of Earth."
                ),
            ),

            LessonScene(
                title="Night",
                narration=(
                    "The side of Earth facing away from the Sun "
                    "experiences nighttime. As Earth rotates, "
                    "different places experience day and night."
                ),
                visual_description=(
                    "One side of Earth experiencing night."
                ),
            ),
        ],

        conclusion=(
            "So, day and night happen because Earth rotates "
            "on its axis while receiving light from the Sun."
        ),
    )

    request = VideoRequest(
        lesson_id="test-001",
        script=script,
        provider="local",
        voice="en-US-JennyNeural",
        language="en",
        resolution="720p",
    )

    provider = LocalVideoProvider()

    result = await provider.generate(
        request
    )

    print()
    print("==============================")
    print("VIDEO GENERATION RESULT")
    print("==============================")
    print(result)
    print("==============================")


if __name__ == "__main__":
    asyncio.run(main())