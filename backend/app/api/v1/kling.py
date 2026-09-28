from fastapi import APIRouter, HTTPException

from app.services.kling import (
    create_kling_video,
    KlingError,
)


router = APIRouter()


@router.post("/test")
async def test_kling():

    prompt = """
A friendly cartoon elephant and three tiny cartoon mice
are standing together in a colorful magical forest.
The elephant gently lowers its trunk toward the mice.
The mice smile and wave.
Bright children's educational animation style,
warm colors, expressive characters,
smooth gentle movement, cheerful atmosphere,
high quality 3D cartoon animation.
"""

    try:

        task = await create_kling_video(
            prompt=prompt,
            duration=5,
            resolution="720p",
            aspect_ratio="16:9",
            audio="off",
            multi_shot=False,
        )

        return {
            "success": True,
            "kling_task": task,
        }

    except KlingError as e:

        raise HTTPException(
            status_code=502,
            detail=str(e),
        )