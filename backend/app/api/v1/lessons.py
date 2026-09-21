from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import Chapter, Child, Family, Lesson, Question
from app.core.security import get_current_user
from app.schemas.learning import GenerateLessonRequest
from app.workers.tasks import generate_lesson_task
from celery.result import AsyncResult
from app.workers.celery_app import celery
from app.services.storage import storage


router = APIRouter()


async def owned_chapter(chapter_id, user, db):
    fam = (
        await db.execute(
            select(Family).where(Family.owner_id == user.id)
        )
    ).scalar_one()

    stmt = (
        select(Chapter)
        .join(Child, Child.id == Chapter.child_id)
        .where(
            Chapter.id == chapter_id,
            Child.family_id == fam.id,
        )
    )

    return (
        await db.execute(stmt)
    ).scalar_one_or_none()


@router.post("/generate")
async def generate(
    chapter_id: str,
    body: GenerateLessonRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    # ------------------------------------------------------------
    # 1. Check that the chapter belongs to the logged-in parent
    # ------------------------------------------------------------

    ch = await owned_chapter(chapter_id, user, db)

    if not ch:
        raise HTTPException(
            status_code=404,
            detail="Chapter not found",
        )

    # ------------------------------------------------------------
    # 2. Reuse an already completed lesson
    # ------------------------------------------------------------

    existing_lesson_result = await db.execute(
        select(Lesson)
        .where(
            Lesson.chapter_id == chapter_id,
            Lesson.status == "ready",
        )
        .order_by(Lesson.created_at.desc())
    )

    existing_lesson = existing_lesson_result.scalars().first()

    if existing_lesson:
        print(
            f"REUSING EXISTING LESSON: "
            f"chapter={chapter_id}, "
            f"lesson={existing_lesson.id}"
        )

        return {
            "job_id": None,
            "status": "ready",
            "lesson_id": existing_lesson.id,
            "message": "Existing lesson reused",
            "video_url": (
                storage.presign_get(existing_lesson.video_key)
                if existing_lesson.video_key
                else None
            ),
        }

    # ------------------------------------------------------------
    # 3. Check whether generation is already running
    # ------------------------------------------------------------

    generating_result = await db.execute(
        select(Lesson)
        .where(
            Lesson.chapter_id == chapter_id,
            Lesson.status.in_(
                [
                    "generating",
                    "video_generating",
                    "analyzing",
                ]
            ),
        )
        .order_by(Lesson.created_at.desc())
    )

    generating_lesson = generating_result.scalars().first()

    if generating_lesson:
        print(
            f"GENERATION ALREADY RUNNING: "
            f"chapter={chapter_id}, "
            f"lesson={generating_lesson.id}"
        )

        return {
            "job_id": None,
            "status": generating_lesson.status,
            "lesson_id": generating_lesson.id,
            "message": "Lesson generation is already running",
        }

    # ------------------------------------------------------------
    # 4. Create a persistent Lesson record BEFORE Celery starts
    # ------------------------------------------------------------

    placeholder = Lesson(
        chapter_id=chapter_id,
        title="Generating AI Lesson...",
        payload={},
        status="generating",
    )

    db.add(placeholder)

    await db.commit()
    await db.refresh(placeholder)

    print(
        f"CREATED GENERATION RECORD: "
        f"chapter={chapter_id}, "
        f"lesson={placeholder.id}"
    )

    # ------------------------------------------------------------
    # 5. Start Celery using the existing Lesson ID
    # ------------------------------------------------------------

    task = generate_lesson_task.delay(
        chapter_id,
        body.topic,
        body.student_age,
        body.number_of_questions,
        str(placeholder.id),
    )

    print(
        f"STARTED NEW LESSON GENERATION: "
        f"chapter={chapter_id}, "
        f"lesson={placeholder.id}, "
        f"job={task.id}"
    )

    return {
        "job_id": task.id,
        "lesson_id": str(placeholder.id),
        "status": "queued",
    }


@router.get("/{lesson_id}")
async def get_lesson(
    lesson_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    lesson = (
        await db.execute(
            select(Lesson)
            .join(
                Chapter,
                Chapter.id == Lesson.chapter_id,
            )
            .join(
                Child,
                Child.id == Chapter.child_id,
            )
            .join(
                Family,
                Family.id == Child.family_id,
            )
            .where(
                Lesson.id == lesson_id,
                Family.owner_id == user.id,
            )
        )
    ).scalar_one_or_none()

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found",
        )

    # ------------------------------------------------------------
    # Get practice questions for this lesson
    # ------------------------------------------------------------

    questions_result = await db.execute(
        select(Question)
        .where(Question.lesson_id == lesson.id)
    )

    questions = questions_result.scalars().all()

    return {
        "id": lesson.id,
        "title": lesson.title,
        "status": lesson.status,
        "payload": lesson.payload,
        "video_url": (
            storage.presign_get(lesson.video_key)
            if lesson.video_key
            else None
        ),

        "questions": [
            {
                "id": question.id,
                "question": question.question,
                "expected_answer": question.expected_answer,
                "explanation": question.explanation,
            }
            for question in questions
        ],
    }


@router.get("/jobs/{job_id}")
async def job_status(
    job_id: str,
    user=Depends(get_current_user),
):
    result = AsyncResult(job_id, app=celery)

    payload = {
        "job_id": job_id,
        "status": result.status,
    }

    if result.successful():
        payload["result"] = result.result

    if result.failed():
        payload["error"] = str(result.result)

    return payload