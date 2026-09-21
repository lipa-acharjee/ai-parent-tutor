from typing import List, Optional

from pydantic import BaseModel, Field


class LessonScene(BaseModel):
    title: str = Field(min_length=1)
    narration: str = ""
    visual_description: Optional[str] = None
    duration_seconds: Optional[int] = Field(
        default=30,
        ge=1,
        le=300,
    )


class LessonScript(BaseModel):
    title: str = Field(min_length=1)
    introduction: str = ""
    scenes: List[LessonScene] = Field(default_factory=list)
    conclusion: str = ""


class VideoRequest(BaseModel):
    lesson_id: str
    script: LessonScript
    provider: Optional[str] = None
    voice: Optional[str] = None
    language: str = "en"
    resolution: str = "720p"


class VideoResult(BaseModel):
    success: bool
    provider: str
    video_url: Optional[str] = None
    local_path: Optional[str] = None
    job_id: Optional[str] = None
    status: str = "completed"
    error: Optional[str] = None