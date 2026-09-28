import os

import httpx


KLING_BASE_URL = "https://api-singapore.klingai.com"

KLING_API_KEY = os.getenv("KLING_API_KEY")


class KlingError(Exception):
    pass


async def create_kling_video(
    prompt: str,
    duration: int = 5,
    resolution: str = "720p",
    aspect_ratio: str = "16:9",
    audio: str = "off",
    multi_shot: bool = False,
):
    if not KLING_API_KEY:
        raise KlingError(
            "KLING_API_KEY is not configured"
        )

    url = (
        f"{KLING_BASE_URL}"
        "/text-to-video/kling-3.0"
    )

    headers = {
        "Authorization": f"Bearer {KLING_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "prompt": prompt,
        "settings": {
            "multi_shot": multi_shot,
            "audio": audio,
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "duration": duration,
        },
        "options": {
            "watermark_info": {
                "enabled": False
            }
        },
    }

    async with httpx.AsyncClient(
        timeout=60
    ) as client:

        response = await client.post(
            url,
            headers=headers,
            json=payload,
        )

    if response.status_code != 200:
        raise KlingError(
            f"Kling API HTTP {response.status_code}: "
            f"{response.text}"
        )

    data = response.json()

    if data.get("code") != 0:
        raise KlingError(
            f"Kling API error: {data}"
    )

    task = data.get("data")

    if not task:
        raise KlingError(
            f"Kling returned no task data: {data}"
        )

    return task