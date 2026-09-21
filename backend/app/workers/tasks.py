import asyncio
import os

from sqlalchemy import select

from app.workers.celery_app import celery
from app.db.database import SessionLocal
from app.db.models import Lesson, Question
from app.ai.graph import build_graph
from app.services.storage import storage
from app.services.video import get_video_service
from app.services.video.models import (
    VideoRequest,
    LessonScript,
    LessonScene,
)


@celery.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def generate_lesson_task(
    self,
    chapter_id,
    topic,
    age,
    n,
    lesson_id,
):
    return asyncio.run(
        _run(
            chapter_id,
            topic,
            age,
            n,
            lesson_id,
        )
    )


async def _run(
    chapter_id,
    topic,
    age,
    n,
    lesson_id,
):

    async with SessionLocal() as db:

        video_path = None
        row = None

        try:

            # ----------------------------------------------------
            # 1. Load the Lesson record created by the API
            # ----------------------------------------------------

            result = await db.execute(
                select(Lesson).where(
                    Lesson.id == lesson_id,
                    Lesson.chapter_id == chapter_id,
                )
            )

            row = result.scalar_one_or_none()

            if not row:
                raise RuntimeError(
                    f"Lesson record {lesson_id} was not found."
                )

            # ----------------------------------------------------
            # 2. Protect against duplicate/retry execution
            # ----------------------------------------------------

            if row.status == "ready" and row.video_key:
                print(
                    f"LESSON ALREADY READY: "
                    f"lesson={row.id}"
                )

                return {
                    "lesson_id": str(row.id),
                    "status": "ready",
                    "video_key": row.video_key,
                }

            # ----------------------------------------------------
            # 3. Mark lesson as analyzing
            # ----------------------------------------------------

            row.status = "analyzing"

            await db.commit()

            print(
                f"STARTING AI ANALYSIS: "
                f"chapter={chapter_id}, "
                f"lesson={row.id}"
            )

            # ----------------------------------------------------
            # 4. Generate lesson using LangGraph
            # ----------------------------------------------------

            graph = build_graph()

            result = await graph.ainvoke(
                {
                    "chapter_id": chapter_id,
                    "topic": topic,
                    "age": age,
                    "number_of_questions": n,
                    "db": db,
                }
            )

            lesson = result.get("lesson")

            if not lesson:
                raise RuntimeError(
                    "AI did not generate a lesson."
                )

            questions = result.get(
                "questions",
                {},
            )

            if not isinstance(
                questions,
                dict,
            ):
                questions = {}

            # ----------------------------------------------------
            # 5. Save generated lesson into existing row
            # ----------------------------------------------------

            row.title = lesson.get(
                "title",
                "AI Lesson",
            )

            row.payload = {
                "concepts": result.get(
                    "concepts",
                    {},
                ),
                "lesson": lesson,
                "questions": questions,
            }

            row.status = "video_generating"

            await db.commit()

            print(
                f"AI ANALYSIS COMPLETE: "
                f"lesson={row.id}"
            )

            # ----------------------------------------------------
            # 6. Save questions
            # ----------------------------------------------------

            question_rows = []

            for q in questions.get(
                "questions",
                [],
            ):

                if not isinstance(
                    q,
                    dict,
                ):
                    continue

                question_text = q.get(
                    "question",
                    "",
                ).strip()

                expected_answer = q.get(
                    "expected_answer",
                    "",
                ).strip()

                explanation = q.get(
                    "explanation",
                    "",
                ).strip()

                if not question_text:
                    continue

                question_row = Question(
                    lesson_id=row.id,
                    question=question_text,
                    expected_answer=expected_answer,
                    explanation=explanation,
                )

                db.add(question_row)

                question_rows.append(
                    question_row
                )

            await db.commit()

            # ----------------------------------------------------
            # 7. Add database IDs to payload
            # ----------------------------------------------------

            generated_questions = questions.get(
                "questions",
                [],
            )

            for index, question_row in enumerate(
                question_rows
            ):

                if index < len(
                    generated_questions
                ):

                    generated_questions[index]["id"] = str(
                        question_row.id
                    )

            row.payload = {
                "concepts": result.get(
                    "concepts",
                    {},
                ),
                "lesson": lesson,
                "questions": questions,
            }

            await db.commit()

            # ----------------------------------------------------
            # 8. Build video lesson script
            # ----------------------------------------------------

            scenes = []

            for scene in lesson.get(
                "scenes",
                [],
            ):

                if not isinstance(
                    scene,
                    dict,
                ):
                    continue

                scenes.append(
                    LessonScene(
                        title=scene.get(
                            "title",
                            "Lesson Scene",
                        ),
                        narration=scene.get(
                            "narration",
                            "",
                        ),
                        visual_description=scene.get(
                            "visual_description",
                            "",
                        ),
                        duration_seconds=scene.get(
                            "duration_seconds",
                            30,
                        ),
                    )
                )

            if not scenes:
                raise RuntimeError(
                    "AI lesson did not contain "
                    "any video scenes."
                )

            lesson_script = LessonScript(
                title=lesson.get(
                    "title",
                    "AI Lesson",
                ),
                introduction=lesson.get(
                    "introduction",
                    "",
                ),
                scenes=scenes,
                conclusion=lesson.get(
                    "conclusion",
                    "",
                ),
            )

            # ----------------------------------------------------
            # 9. Create video request
            # ----------------------------------------------------

            video_request = VideoRequest(
                lesson_id=str(row.id),
                script=lesson_script,
                provider=None,
                language="en",
                resolution="720p",
            )

            # ----------------------------------------------------
            # 10. Get video provider
            # ----------------------------------------------------

            video_service = get_video_service()

            # ----------------------------------------------------
            # 11. Generate video
            # ----------------------------------------------------

            print(
                f"GENERATING VIDEO: "
                f"lesson={row.id}"
            )

            video_result = await video_service.generate(
                video_request
            )

            if not video_result.success:

                row.status = "failed"

                await db.commit()

                raise RuntimeError(
                    video_result.error
                    or "Video generation failed."
                )

            # ----------------------------------------------------
            # 12. Get generated video path
            # ----------------------------------------------------

            video_path = video_result.local_path

            if not video_path:

                row.status = "failed"

                await db.commit()

                raise RuntimeError(
                    "Video provider did not return "
                    "a local video path."
                )

            if not os.path.exists(video_path):

                row.status = "failed"

                await db.commit()

                raise RuntimeError(
                    "Generated video file does "
                    "not exist."
                )

            # ----------------------------------------------------
            # 13. Upload video to MinIO
            # ----------------------------------------------------

            key = (
                f"lessons/"
                f"{chapter_id}/"
                f"{row.id}.mp4"
            )

            print(
                f"UPLOADING VIDEO TO MINIO: "
                f"{key}"
            )

            with open(
                video_path,
                "rb",
            ) as video_file:

                storage.put(
                    key,
                    video_file,
                    "video/mp4",
                )

            # ----------------------------------------------------
            # 14. Mark lesson ready
            # ----------------------------------------------------

            row.video_key = key
            row.status = "ready"

            await db.commit()

            print(
                f"LESSON READY: "
                f"lesson={row.id}, "
                f"video={key}"
            )

            # ----------------------------------------------------
            # 15. Cleanup local video
            # ----------------------------------------------------

            try:

                if os.path.exists(video_path):

                    os.remove(video_path)

            except OSError:
                pass

            return {
                "lesson_id": str(row.id),
                "status": "ready",
                "video_key": key,
                "provider": video_service.provider.name,
            }

        except Exception:

            try:

                if row:

                    row.status = "failed"

                    await db.commit()

            except Exception:
                pass

            raise