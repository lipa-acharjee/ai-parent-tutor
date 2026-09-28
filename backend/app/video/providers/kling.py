import os
import httpx


KLING_API_KEY = os.getenv("KLING_API_KEY")

KLING_BASE_URL = "https://api-singapore.klingai.com"


async def create_kling_video(
    prompt: str,
    duration: int = 5,
    resolution: str = "720p",
    aspect_ratio: str = "16:9",
):
    if not KLING_API_KEY:
        raise RuntimeError("KLING_API_KEY is not configured")

    url = f"{KLING_BASE_URL}/text-to-video/kling-3.0"

    headers = {
        "Authorization": f"Bearer {KLING_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "prompt": prompt,
        "settings": {
            "resolution": resolution,
            "aspect_ratio": aspect_ratio,
            "duration": duration,
            "audio": "off",
            "multi_shot": False,
        },
        "options": {
            "watermark_info": {
                "enabled": False
            }
        },
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            url,
            headers=headers,
            json=payload,
        )

    response.raise_for_status()

    data = response.json()

    if data.get("code") != 0:
        raise RuntimeError(
            f"Kling API error: {data}"
        )

    return data["data"]