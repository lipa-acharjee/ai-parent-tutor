from pydantic import BaseModel, Field


class GenerateLessonRequest(BaseModel):
    topic: str = Field(
        min_length=1,
        max_length=255,
    )

    student_age: int = Field(
        default=10,
        ge=5,
        le=18,
    )

    number_of_questions: int = Field(
        default=5,
        ge=1,
        le=20,
    )


class AnswerRequest(BaseModel):
    question_id: str
    child_id: str

    answer: str = Field(
        min_length=1,
        max_length=5000,
    )
