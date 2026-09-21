import uuid
from app.ai.service import generate_chapter_from_text
from app.ai.rag import add_chunks
from app.services.chapter import index_pdf, checksum, chunk_pages

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException,
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import (
    Child,
    Chapter,
    Document,
    Family,
)
from app.core.security import get_current_user
from app.services.storage import storage
from app.services.chapter import (
    index_pdf,
    checksum,
)
from app.core.config import settings


router = APIRouter()


# =========================================================
# POST /api/v1/chapters
#
# Accepts:
#
# 1. One PDF
#
# OR
#
# 2. Multiple JPG/JPEG images
#
# PDF and images cannot be mixed.
# =========================================================

@router.post("")
async def upload_chapter(
    child_id: str = Form(...),
    title: str = Form(...),
    subject: str = Form(...),
    grade: str = Form(...),

    files: list[UploadFile] = File(...),

    db: AsyncSession = Depends(get_db),

    user=Depends(get_current_user),
):

    # =====================================================
    # 1. Find parent's family
    # =====================================================

    result = await db.execute(
        select(Family).where(
            Family.owner_id == user.id
        )
    )

    family = result.scalar_one_or_none()

    if not family:
        raise HTTPException(
            status_code=404,
            detail="Family not found",
        )

    # =====================================================
    # 2. Verify child belongs to parent
    # =====================================================

    result = await db.execute(
        select(Child).where(
            Child.id == child_id,
            Child.family_id == family.id,
        )
    )

    child = result.scalar_one_or_none()

    if not child:
        raise HTTPException(
            status_code=404,
            detail="Child not found",
        )

    # =====================================================
    # 3. Validate files
    # =====================================================

    if not files:
        raise HTTPException(
            status_code=400,
            detail="At least one file is required.",
        )

    # -----------------------------------------------------
    # Maximum number of files
    # -----------------------------------------------------

    max_files = 50

    if len(files) > max_files:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Too many files. Maximum "
                f"{max_files} files are allowed."
            ),
        )

    # -----------------------------------------------------
    # Determine upload type
    # -----------------------------------------------------

    pdf_files = []
    image_files = []

    for uploaded_file in files:

        filename = (
            uploaded_file.filename
            or ""
        )

        extension = (
            filename.rsplit(".", 1)[-1].lower()
            if "." in filename
            else ""
        )

        content_type = (
            uploaded_file.content_type
            or ""
        ).lower()

        # -------------------------------------------------
        # PDF
        # -------------------------------------------------

        if (
            extension == "pdf"
            or content_type == "application/pdf"
        ):
            pdf_files.append(
                uploaded_file
            )

        # -------------------------------------------------
        # JPEG/JPG
        # -------------------------------------------------

        elif (
            extension in {"jpg", "jpeg"}
            or content_type in {
                "image/jpeg",
                "image/jpg",
            }
        ):
            image_files.append(
                uploaded_file
            )

        # -------------------------------------------------
        # Unsupported
        # -------------------------------------------------

        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file type: "
                    f"{filename}. "
                    f"Only PDF, JPG and JPEG files "
                    f"are supported."
                ),
            )

    # =====================================================
    # 4. Do not allow PDF + images together
    # =====================================================

    if pdf_files and image_files:
        raise HTTPException(
            status_code=400,
            detail=(
                "Please upload either one PDF "
                "or multiple JPG/JPEG images. "
                "Do not mix PDF and image files."
            ),
        )

    # =====================================================
    # 5. PDF validation
    # =====================================================

    if pdf_files:

        if len(pdf_files) != 1:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Only one PDF file can be uploaded "
                    "for a chapter."
                ),
            )

        uploaded_file = pdf_files[0]

        data = await uploaded_file.read()

        max_size = (
            settings.max_upload_mb
            * 1024
            * 1024
        )

        if len(data) > max_size:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File too large. Maximum size "
                    f"is {settings.max_upload_mb} MB."
                ),
            )

        if not data:
            raise HTTPException(
                status_code=400,
                detail="Uploaded PDF is empty.",
            )

        upload_filename = (
            uploaded_file.filename
            or "chapter.pdf"
        )

        upload_content_type = (
            "application/pdf"
        )

        upload_data = data

        upload_type = "pdf"

    # =====================================================
    # 6. IMAGE validation
    # =====================================================

    else:

        if not image_files:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Please upload one PDF or "
                    "one or more JPG/JPEG images."
                ),
            )

        image_data = []

        total_size = 0

        max_size = (
            settings.max_upload_mb
            * 1024
            * 1024
        )

        for uploaded_file in image_files:

            data = await uploaded_file.read()

            if not data:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Uploaded image "
                        f"'{uploaded_file.filename}' "
                        f"is empty."
                    ),
                )

            total_size += len(data)

            image_data.append(
                data
            )

        # -------------------------------------------------
        # Total upload size
        # -------------------------------------------------

        if total_size > max_size:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"Total image upload is too large. "
                    f"Maximum size is "
                    f"{settings.max_upload_mb} MB."
                ),
            )

        upload_filename = (
            "chapter_images.pdf"
        )

        upload_content_type = (
            "application/pdf"
        )

        upload_type = "images"

        # -------------------------------------------------
        # Convert images to PDF
        #
        # This PDF is also what we store and index.
        # -------------------------------------------------

        from app.services.chapter import (
            images_to_pdf,
        )

        try:

            upload_data = images_to_pdf(
                image_data
            )

        except Exception as exc:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Could not process image pages: "
                    f"{str(exc)}"
                ),
            )

    # =====================================================
    # 7. Create chapter
    # =====================================================

    chapter_id = str(
        uuid.uuid4()
    )

    chapter_content_hash = checksum(upload_data)

    chapter = Chapter(
        id=chapter_id,
        child_id=child.id,
        title=title,
        subject=subject,
        grade=grade,
        content_hash=chapter_content_hash,
        status="processing",
    )

    db.add(chapter)

    await db.flush()

    # =====================================================
    # 8. Store chapter document
    # =====================================================

    storage_key = (
        f"chapters/"
        f"{user.id}/"
        f"{child.id}/"
        f"{chapter_id}/"
        f"{upload_filename}"
    )

    try:

        storage.put(
            storage_key,
            upload_data,
            content_type=upload_content_type,
        )

    except Exception as exc:

        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not store uploaded chapter: "
                f"{str(exc)}"
            ),
        )

    # =====================================================
    # 9. Save document metadata
    # =====================================================

    document = Document(
    id=str(uuid.uuid4()),
    chapter_id=chapter_id,
    storage_key=storage_key,
    filename=upload_filename,
    mime_type=upload_content_type,
    size_bytes=len(upload_data),
    checksum=chapter_content_hash,
    )

    db.add(document)

    await db.commit()

    # =====================================================
    # 10. Extract + index
    # =====================================================

    try:

        pages = await index_pdf(
            db,
            chapter_id,
            upload_data,
        )

        chapter.status = "ready"

        await db.commit()

    except Exception as exc:

        chapter.status = "failed"

        await db.commit()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Chapter processing failed: "
                f"{str(exc)}"
            ),
        )

    # =====================================================
    # 11. Return result
    # =====================================================

    return {
        "chapter_id": chapter_id,
        "status": chapter.status,
        "pages": pages,
        "filename": upload_filename,
        "upload_type": upload_type,
        "files_received": len(files),
        "content_hash": chapter.content_hash,
    }

@router.post("/from-text")
async def create_chapter_from_text(
    child_id: str = Form(...),
    text: str = Form(...),
    grade: str = Form(...),
    subject: str = Form("General"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Create an educational chapter from a parent's
    topic or text input.

    The generated chapter is stored as a Chapter,
    Document, and Chunk so it can use the same
    RAG -> Lesson -> Video pipeline as uploaded chapters.
    """

    # ---------------------------------------------------------
    # 1. Validate input
    # ---------------------------------------------------------

    text = text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Please enter a topic or text.",
        )

    if len(text) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Topic or text must be 2000 characters or less.",
        )

    # ---------------------------------------------------------
    # 2. Verify parent owns the child
    # ---------------------------------------------------------

    family_result = await db.execute(
        select(Family).where(
            Family.owner_id == user.id
        )
    )

    family = family_result.scalar_one_or_none()

    if not family:
        raise HTTPException(
            status_code=403,
            detail="Family not found.",
        )

    child_result = await db.execute(
        select(Child).where(
            Child.id == child_id,
            Child.family_id == family.id,
        )
    )

    child = child_result.scalar_one_or_none()

    if not child:
        raise HTTPException(
            status_code=404,
            detail="Child not found.",
        )

    # ---------------------------------------------------------
    # 3. Generate educational chapter with AI
    # ---------------------------------------------------------

    try:
        generated = generate_chapter_from_text(
            input_text=text,
            grade=grade or child.grade,
            language=child.language,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Chapter generation failed: {str(exc)}",
        )

    # ---------------------------------------------------------
    # 4. Validate AI response
    # ---------------------------------------------------------

    title = str(
        generated.get("title") or text[:255]
    ).strip()

    generated_subject = str(
        generated.get("subject") or subject or "General"
    ).strip()

    content = str(
        generated.get("content") or ""
    ).strip()

    if not content:
        raise HTTPException(
            status_code=500,
            detail="AI generated an empty chapter.",
        )

    if len(title) > 255:
        title = title[:255]

    if len(generated_subject) > 100:
        generated_subject = generated_subject[:100]

    # ---------------------------------------------------------
    # 5. Create Chapter
    # ---------------------------------------------------------

    chapter_id = str(uuid.uuid4())

    chapter_content_hash = checksum(
    content.encode("utf-8")
)

    chapter = Chapter(
        id=chapter_id,
        child_id=child.id,
        title=title,
        subject=generated_subject,
        grade=grade or child.grade,
        content_hash=chapter_content_hash,
        status="processing",
    )

    db.add(chapter)

    await db.flush()

    # ---------------------------------------------------------
    # 6. Create a Document record
    #
    # There is no uploaded physical file for a text chapter,
    # so we store metadata indicating that it was AI-generated.
    # ---------------------------------------------------------

    document = Document(
    id=str(uuid.uuid4()),
    chapter_id=chapter.id,
    storage_key=f"text-chapters/{chapter.id}.txt",
    filename=f"{title}.txt",
    mime_type="text/plain",
    size_bytes=len(content.encode("utf-8")),
    checksum=chapter_content_hash,
    )

    db.add(document)

    await db.flush()

    # ---------------------------------------------------------
    # 7. Convert generated chapter into RAG chunks
    # ---------------------------------------------------------

    try:
        await add_chunks(
            db,
            chapter.id,
            chunk_pages(
                [
                    (
                        1,
                        content,
                    )
                ]
            ),
        )

    except Exception as exc:
        chapter.status = "failed"
        await db.commit()

        raise HTTPException(
            status_code=500,
            detail=f"Chapter indexing failed: {str(exc)}",
        )

    # ---------------------------------------------------------
    # 8. Mark chapter ready
    # ---------------------------------------------------------

    chapter.status = "ready"

    await db.commit()

    # ---------------------------------------------------------
    # 9. Return result
    # ---------------------------------------------------------

    return {
        "chapter_id": chapter.id,
        "title": chapter.title,
        "subject": chapter.subject,
        "grade": chapter.grade,
        "status": chapter.status,
        "source": "text",
        "content_length": len(content),
         "content_hash": chapter.content_hash,
    }
# =========================================================
# GET /api/v1/chapters?child_id=...
#
# Get all chapters belonging to a child
# =========================================================

@router.get("")
async def get_chapters(
    child_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):

    # =====================================================
    # 1. Find parent's family
    # =====================================================

    result = await db.execute(
        select(Family).where(
            Family.owner_id == user.id
        )
    )

    family = result.scalar_one_or_none()

    if not family:
        raise HTTPException(
            status_code=404,
            detail="Family not found",
        )

    # =====================================================
    # 2. Verify child belongs to parent
    # =====================================================

    result = await db.execute(
        select(Child).where(
            Child.id == child_id,
            Child.family_id == family.id,
        )
    )

    child = result.scalar_one_or_none()

    if not child:
        raise HTTPException(
            status_code=404,
            detail="Child not found",
        )

    # =====================================================
    # 3. Get chapters
    # =====================================================

    result = await db.execute(
        select(Chapter)
        .where(
            Chapter.child_id == child_id
        )
        .order_by(Chapter.title)
    )

    chapters = result.scalars().all()

    # =====================================================
    # 4. Return chapters
    # =====================================================

    return [
        {
            "id": chapter.id,
            "title": chapter.title,
            "subject": chapter.subject,
            "grade": chapter.grade,
            "status": chapter.status,
        }
        for chapter in chapters
    ]

# =========================================================
# DELETE /api/v1/chapters/{chapter_id}
#
# Deletes:
#   1. Chapter-related MinIO documents
#   2. Lesson video files from MinIO
#   3. Chapter and related PostgreSQL records
#
# Only the parent who owns the child can delete the chapter.
# =========================================================

@router.delete("/{chapter_id}")
async def delete_chapter(
    chapter_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):

    # =====================================================
    # 1. Find parent's family
    # =====================================================

    result = await db.execute(
        select(Family).where(
            Family.owner_id == user.id
        )
    )

    family = result.scalar_one_or_none()

    if not family:
        raise HTTPException(
            status_code=404,
            detail="Family not found",
        )

    # =====================================================
    # 2. Find chapter and verify ownership
    #
    # Chapter -> Child -> Family
    # =====================================================

    result = await db.execute(
        select(Chapter)
        .join(
            Child,
            Child.id == Chapter.child_id,
        )
        .where(
            Chapter.id == chapter_id,
            Child.family_id == family.id,
        )
    )

    chapter = result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(
            status_code=404,
            detail="Chapter not found",
        )

    # =====================================================
    # 3. Find all documents belonging to this chapter
    # =====================================================

    result = await db.execute(
        select(Document).where(
            Document.chapter_id == chapter.id
        )
    )

    documents = result.scalars().all()

    # =====================================================
    # 4. Delete document objects from MinIO
    # =====================================================

    deleted_storage_objects = 0

    for document in documents:

        # AI text chapters only have metadata in PostgreSQL.
        # There is no physical text file in MinIO.
        if document.storage_key.startswith("text-chapters/"):
            continue

        try:

            storage.delete(
                document.storage_key
            )

            deleted_storage_objects += 1

        except Exception as exc:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Could not delete chapter file "
                    f"from storage: {str(exc)}"
                ),
            )

    # =====================================================
    # 5. Find lessons belonging to this chapter
    # =====================================================

    from app.db.models import Lesson

    result = await db.execute(
        select(Lesson).where(
            Lesson.chapter_id == chapter.id
        )
    )

    lessons = result.scalars().all()

    # =====================================================
    # 6. Delete lesson videos from MinIO
    # =====================================================

    deleted_video_objects = 0

    for lesson in lessons:

        if not lesson.video_key:
            continue

        try:

            storage.delete(
                lesson.video_key
            )

            deleted_video_objects += 1

        except Exception as exc:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Could not delete lesson video "
                    f"from storage: {str(exc)}"
                ),
            )

    # =====================================================
    # 7. Delete chapter from PostgreSQL
    #
    # Foreign-key CASCADE will remove:
    #
    #   Documents
    #   Chunks
    #   Concepts
    #   Lessons
    #   Questions
    #
    # and other dependent records where CASCADE is configured.
    # =====================================================

    await db.delete(chapter)

    await db.commit()

    # =====================================================
    # 8. Return result
    # =====================================================

    return {
        "message": "Chapter deleted successfully",
        "chapter_id": chapter_id,
        "deleted_storage_objects": deleted_storage_objects,
        "deleted_video_objects": deleted_video_objects,
    }



    # =========================================================
# DELETE /api/v1/chapters/{chapter_id}
#
# Deletes:
#   1. Chapter document from MinIO
#   2. Lesson videos from MinIO
#   3. Chapter and all related PostgreSQL records
#
# Only the parent who owns the child can delete the chapter.
# =========================================================

@router.delete("/{chapter_id}")
async def delete_chapter(
    chapter_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):

    # =====================================================
    # 1. Find parent's family
    # =====================================================

    result = await db.execute(
        select(Family).where(
            Family.owner_id == user.id
        )
    )

    family = result.scalar_one_or_none()

    if not family:
        raise HTTPException(
            status_code=404,
            detail="Family not found",
        )

    # =====================================================
    # 2. Find chapter and verify ownership
    #
    # Chapter -> Child -> Family
    # =====================================================

    result = await db.execute(
        select(Chapter)
        .join(
            Child,
            Child.id == Chapter.child_id,
        )
        .where(
            Chapter.id == chapter_id,
            Child.family_id == family.id,
        )
    )

    chapter = result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(
            status_code=404,
            detail="Chapter not found",
        )

    # =====================================================
    # 3. Find chapter documents
    # =====================================================

    result = await db.execute(
        select(Document).where(
            Document.chapter_id == chapter.id
        )
    )

    documents = result.scalars().all()

    # =====================================================
    # 4. Find lessons
    # =====================================================

    # Import here so we don't need to change the existing
    # import section at the top of your file.
    from app.db.models import Lesson

    result = await db.execute(
        select(Lesson).where(
            Lesson.chapter_id == chapter.id
        )
    )

    lessons = result.scalars().all()

    # =====================================================
    # 5. Delete chapter documents from MinIO
    # =====================================================

    deleted_storage_objects = 0

    for document in documents:

        # AI text chapters currently don't have a physical
        # object in MinIO. They only have a database record.
        if document.storage_key.startswith("text-chapters/"):
            continue

        try:

            storage.delete(
                document.storage_key
            )

            deleted_storage_objects += 1

        except Exception as exc:

            await db.rollback()

            raise HTTPException(
                status_code=500,
                detail=(
                    "Could not delete chapter file "
                    f"from storage: {str(exc)}"
                ),
            )

    # =====================================================
    # 6. Delete lesson videos from MinIO
    # =====================================================

    deleted_video_objects = 0

    for lesson in lessons:

        if not lesson.video_key:
            continue

        try:

            storage.delete(
                lesson.video_key
            )

            deleted_video_objects += 1

        except Exception as exc:

            await db.rollback()

            raise HTTPException(
                status_code=500,
                detail=(
                    "Could not delete lesson video "
                    f"from storage: {str(exc)}"
                ),
            )

    # =====================================================
    # 7. Delete chapter from PostgreSQL
    #
    # PostgreSQL CASCADE will remove:
    #
    # Chapter
    # ├── Documents
    # ├── Chunks
    # ├── Concepts
    # │    └── Progress
    # └── Lessons
    #      └── Questions
    #           └── Attempts
    # =====================================================

    await db.delete(chapter)

    await db.commit()

    # =====================================================
    # 8. Return result
    # =====================================================

    return {
        "message": "Chapter deleted successfully",
        "chapter_id": chapter_id,
        "deleted_storage_objects": deleted_storage_objects,
        "deleted_video_objects": deleted_video_objects,
    }