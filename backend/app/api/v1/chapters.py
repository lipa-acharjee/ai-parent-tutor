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
# =========================================================

@router.post("")
async def upload_chapter(
    child_id: str = Form(...),
    title: str = Form(...),
    subject: str = Form(...),
    grade: str = Form(...),
    custom_prompt: str = Form(""),
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):

    print("CHAPTER UPLOAD: endpoint entered", flush=True)

    # =====================================================
    # Parent custom instructions
    # =====================================================

    print("CHAPTER UPLOAD: processing custom prompt", flush=True)

    custom_prompt = custom_prompt.strip()

    if len(custom_prompt) > 3000:
        raise HTTPException(
            status_code=400,
            detail=(
                "Custom instructions must be "
                "3000 characters or less."
            ),
        )

    if not custom_prompt:
        custom_prompt = None

    print("CHAPTER UPLOAD: custom prompt validated", flush=True)

    # =====================================================
    # 1. Find parent's family
    # =====================================================

    print("CHAPTER UPLOAD: looking up family", flush=True)

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

    print(
        f"CHAPTER UPLOAD: family found id={family.id}",
        flush=True,
    )

    # =====================================================
    # 2. Verify child belongs to parent
    # =====================================================

    print(
        f"CHAPTER UPLOAD: looking up child id={child_id}",
        flush=True,
    )

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

    print(
        f"CHAPTER UPLOAD: child found id={child.id}",
        flush=True,
    )

    # =====================================================
    # 3. Validate files
    # =====================================================

    print(
        f"CHAPTER UPLOAD: received {len(files)} files",
        flush=True,
    )

    if not files:
        raise HTTPException(
            status_code=400,
            detail="At least one file is required.",
        )

    max_files = 50

    if len(files) > max_files:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Too many files. Maximum "
                f"{max_files} files are allowed."
            ),
        )

    pdf_files = []
    image_files = []

    print(
        "CHAPTER UPLOAD: determining file types",
        flush=True,
    )

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

        if (
            extension == "pdf"
            or content_type == "application/pdf"
        ):
            pdf_files.append(
                uploaded_file
            )

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

    print(
        f"CHAPTER UPLOAD: PDF files={len(pdf_files)}, "
        f"image files={len(image_files)}",
        flush=True,
    )

    # =====================================================
    # 4. Do not allow PDF + images together
    # =====================================================

    print(
        "CHAPTER UPLOAD: validating upload combination",
        flush=True,
    )

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

        print(
            "CHAPTER UPLOAD: processing PDF upload",
            flush=True,
        )

        if len(pdf_files) != 1:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Only one PDF file can be uploaded "
                    "for a chapter."
                ),
            )

        uploaded_file = pdf_files[0]

        print(
            f"CHAPTER UPLOAD: reading PDF "
            f"{uploaded_file.filename}",
            flush=True,
        )

        data = await uploaded_file.read()

        print(
            f"CHAPTER UPLOAD: PDF read complete, "
            f"bytes={len(data)}",
            flush=True,
        )

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

        print(
            "CHAPTER UPLOAD: PDF validation complete",
            flush=True,
        )

    # =====================================================
    # 6. IMAGE validation
    # =====================================================

    else:

        print(
            "CHAPTER UPLOAD: processing image upload",
            flush=True,
        )

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

            print(
                f"CHAPTER UPLOAD: reading image "
                f"{uploaded_file.filename}",
                flush=True,
            )

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

        print(
            f"CHAPTER UPLOAD: total image bytes={total_size}",
            flush=True,
        )

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

        from app.services.chapter import (
            images_to_pdf,
        )

        print(
            "CHAPTER UPLOAD: converting images to PDF",
            flush=True,
        )

        try:

            upload_data = images_to_pdf(
                image_data
            )

        except Exception as exc:

            print(
                f"CHAPTER UPLOAD ERROR: image conversion failed: {exc}",
                flush=True,
            )

            raise HTTPException(
                status_code=400,
                detail=(
                    f"Could not process image pages: "
                    f"{str(exc)}"
                ),
            )

        print(
            f"CHAPTER UPLOAD: image PDF created, "
            f"bytes={len(upload_data)}",
            flush=True,
        )

    # =====================================================
    # 7. Create chapter
    # =====================================================

    print(
        "CHAPTER UPLOAD: creating chapter database record",
        flush=True,
    )

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
        custom_prompt=custom_prompt,
        content_hash=chapter_content_hash,
        status="processing",
    )

    db.add(chapter)

    await db.flush()

    print(
        f"CHAPTER UPLOAD: chapter created id={chapter_id}",
        flush=True,
    )

    # =====================================================
    # 8. Store chapter document
    # =====================================================

    print(
        "CHAPTER UPLOAD: preparing storage upload",
        flush=True,
    )

    storage_key = (
        f"chapters/"
        f"{user.id}/"
        f"{child.id}/"
        f"{chapter_id}/"
        f"{upload_filename}"
    )

    try:

        print(
            "CHAPTER UPLOAD: uploading to storage",
            flush=True,
        )

        storage.put(
            storage_key,
            upload_data,
            content_type=upload_content_type,
        )

        print(
            "CHAPTER UPLOAD: storage upload complete",
            flush=True,
        )

    except Exception as exc:

        print(
            f"CHAPTER UPLOAD ERROR: storage upload failed: {exc}",
            flush=True,
        )

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

    print(
        "CHAPTER UPLOAD: creating document record",
        flush=True,
    )

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

    print(
        "CHAPTER UPLOAD: document committed",
        flush=True,
    )

    # =====================================================
    # 10. Extract + index
    # =====================================================

    print(
        "CHAPTER UPLOAD: starting PDF indexing",
        flush=True,
    )

    try:

        pages = await index_pdf(
            db,
            chapter_id,
            upload_data,
        )

        print(
            f"CHAPTER UPLOAD: PDF indexing complete, "
            f"pages={pages}",
            flush=True,
        )

        chapter.status = "ready"

        await db.commit()

        print(
            "CHAPTER UPLOAD: chapter marked ready",
            flush=True,
        )

    except Exception as exc:

        print(
            f"CHAPTER UPLOAD ERROR: indexing failed: {exc}",
            flush=True,
        )

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

    print(
        f"CHAPTER UPLOAD: returning success for {chapter_id}",
        flush=True,
    )

    return {
        "chapter_id": chapter_id,
        "status": chapter.status,
        "pages": pages,
        "filename": upload_filename,
        "upload_type": upload_type,
        "files_received": len(files),
        "content_hash": chapter.content_hash,
        "custom_prompt": chapter.custom_prompt,
    }


# =========================================================
# POST /api/v1/chapters/from-text
#
# Create an educational chapter using AI.
# =========================================================

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
    """

    print(
        "FROM-TEXT: ========================================",
        flush=True,
    )

    print(
        "FROM-TEXT: endpoint entered",
        flush=True,
    )

    print(
        f"FROM-TEXT: child_id={child_id}",
        flush=True,
    )

    print(
        f"FROM-TEXT: grade={grade}",
        flush=True,
    )

    print(
        f"FROM-TEXT: subject={subject}",
        flush=True,
    )

    print(
        f"FROM-TEXT: text length={len(text)}",
        flush=True,
    )

    print(
        f"FROM-TEXT: authenticated user id={user.id}",
        flush=True,
    )

    # =====================================================
    # 1. Validate input
    # =====================================================

    print(
        "FROM-TEXT: STEP 1 - validating input",
        flush=True,
    )

    text = text.strip()

    print(
        f"FROM-TEXT: stripped text length={len(text)}",
        flush=True,
    )

    if not text:
        print(
            "FROM-TEXT: ERROR - empty text",
            flush=True,
        )

        raise HTTPException(
            status_code=400,
            detail="Please enter a topic or text.",
        )

    if len(text) > 2000:
        print(
            "FROM-TEXT: ERROR - text exceeds 2000 characters",
            flush=True,
        )

        raise HTTPException(
            status_code=400,
            detail="Topic or text must be 2000 characters or less.",
        )

    print(
        "FROM-TEXT: STEP 1 complete",
        flush=True,
    )

    # =====================================================
    # 2. Verify parent owns the child
    # =====================================================

    print(
        "FROM-TEXT: STEP 2 - looking up family",
        flush=True,
    )

    family_result = await db.execute(
        select(Family).where(
            Family.owner_id == user.id
        )
    )

    print(
        "FROM-TEXT: family database query completed",
        flush=True,
    )

    family = family_result.scalar_one_or_none()

    if not family:
        print(
            "FROM-TEXT: ERROR - family not found",
            flush=True,
        )

        raise HTTPException(
            status_code=403,
            detail="Family not found.",
        )

    print(
        f"FROM-TEXT: family found id={family.id}",
        flush=True,
    )

    print(
        f"FROM-TEXT: looking up child id={child_id}",
        flush=True,
    )

    child_result = await db.execute(
        select(Child).where(
            Child.id == child_id,
            Child.family_id == family.id,
        )
    )

    print(
        "FROM-TEXT: child database query completed",
        flush=True,
    )

    child = child_result.scalar_one_or_none()

    if not child:
        print(
            "FROM-TEXT: ERROR - child not found",
            flush=True,
        )

        raise HTTPException(
            status_code=404,
            detail="Child not found.",
        )

    print(
        f"FROM-TEXT: child found id={child.id}",
        flush=True,
    )

    print(
        f"FROM-TEXT: child language={child.language}",
        flush=True,
    )

    print(
        f"FROM-TEXT: child grade={child.grade}",
        flush=True,
    )

    print(
        "FROM-TEXT: STEP 2 complete",
        flush=True,
    )

    # =====================================================
    # 3. Generate educational chapter with AI
    # =====================================================

    print(
        "FROM-TEXT: STEP 3 - starting AI chapter generation",
        flush=True,
    )

    print(
        "FROM-TEXT: calling generate_chapter_from_text()",
        flush=True,
    )

    try:

        generated = generate_chapter_from_text(
            input_text=text,
            grade=grade or child.grade,
            language=child.language,
        )

        print(
            "FROM-TEXT: generate_chapter_from_text() returned",
            flush=True,
        )

        print(
            f"FROM-TEXT: generated object type={type(generated).__name__}",
            flush=True,
        )

    except Exception as exc:

        print(
            "FROM-TEXT ERROR: AI generation failed",
            flush=True,
        )

        print(
            f"FROM-TEXT ERROR TYPE: {type(exc).__name__}",
            flush=True,
        )

        print(
            f"FROM-TEXT ERROR MESSAGE: {str(exc)}",
            flush=True,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Chapter generation failed: {str(exc)}",
        )

    print(
        "FROM-TEXT: STEP 3 complete",
        flush=True,
    )

    # =====================================================
    # 4. Validate AI response
    # =====================================================

    print(
        "FROM-TEXT: STEP 4 - validating AI response",
        flush=True,
    )

    if not isinstance(generated, dict):
        print(
            "FROM-TEXT ERROR: AI response is not a dictionary",
            flush=True,
        )

        raise HTTPException(
            status_code=500,
            detail="AI generated an invalid chapter response.",
        )

    print(
        f"FROM-TEXT: AI response keys={list(generated.keys())}",
        flush=True,
    )

    title = str(
        generated.get("title") or text[:255]
    ).strip()

    generated_subject = str(
        generated.get("subject") or subject or "General"
    ).strip()

    content = str(
        generated.get("content") or ""
    ).strip()

    print(
        f"FROM-TEXT: generated title length={len(title)}",
        flush=True,
    )

    print(
        f"FROM-TEXT: generated subject={generated_subject}",
        flush=True,
    )

    print(
        f"FROM-TEXT: generated content length={len(content)}",
        flush=True,
    )

    if not content:
        print(
            "FROM-TEXT ERROR: AI generated empty content",
            flush=True,
        )

        raise HTTPException(
            status_code=500,
            detail="AI generated an empty chapter.",
        )

    if len(title) > 255:
        print(
            "FROM-TEXT: truncating title to 255 characters",
            flush=True,
        )

        title = title[:255]

    if len(generated_subject) > 100:
        print(
            "FROM-TEXT: truncating subject to 100 characters",
            flush=True,
        )

        generated_subject = generated_subject[:100]

    print(
        "FROM-TEXT: STEP 4 complete",
        flush=True,
    )

    # =====================================================
    # 5. Create Chapter
    # =====================================================

    print(
        "FROM-TEXT: STEP 5 - creating Chapter database record",
        flush=True,
    )

    chapter_id = str(uuid.uuid4())

    print(
        f"FROM-TEXT: generated chapter id={chapter_id}",
        flush=True,
    )

    chapter_content_hash = checksum(
        content.encode("utf-8")
    )

    print(
        "FROM-TEXT: content checksum calculated",
        flush=True,
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

    print(
        "FROM-TEXT: Chapter object created",
        flush=True,
    )

    db.add(chapter)

    print(
        "FROM-TEXT: Chapter added to database session",
        flush=True,
    )

    await db.flush()

    print(
        "FROM-TEXT: Chapter flush completed",
        flush=True,
    )

    print(
        "FROM-TEXT: STEP 5 complete",
        flush=True,
    )

    # =====================================================
    # 6. Create Document record
    # =====================================================

    print(
        "FROM-TEXT: STEP 6 - creating Document record",
        flush=True,
    )

    document = Document(
        id=str(uuid.uuid4()),
        chapter_id=chapter.id,
        storage_key=f"text-chapters/{chapter.id}.txt",
        filename=f"{title}.txt",
        mime_type="text/plain",
        size_bytes=len(content.encode("utf-8")),
        checksum=chapter_content_hash,
    )

    print(
        "FROM-TEXT: Document object created",
        flush=True,
    )

    db.add(document)

    print(
        "FROM-TEXT: Document added to database session",
        flush=True,
    )

    await db.flush()

    print(
        "FROM-TEXT: Document flush completed",
        flush=True,
    )

    print(
        "FROM-TEXT: STEP 6 complete",
        flush=True,
    )

    # =====================================================
    # 7. Convert generated chapter into RAG chunks
    # =====================================================

    print(
        "FROM-TEXT: STEP 7 - starting RAG chunk creation",
        flush=True,
    )

    try:

        print(
            "FROM-TEXT: calling chunk_pages()",
            flush=True,
        )

        chunks = chunk_pages(
            [
                (
                    1,
                    content,
                )
            ]
        )

        print(
            f"FROM-TEXT: chunk_pages() returned "
            f"{len(chunks)} chunks",
            flush=True,
        )

        print(
            "FROM-TEXT: calling add_chunks()",
            flush=True,
        )

        await add_chunks(
            db,
            chapter.id,
            chunks,
        )

        print(
            "FROM-TEXT: add_chunks() completed",
            flush=True,
        )

    except Exception as exc:

        print(
            "FROM-TEXT ERROR: RAG indexing failed",
            flush=True,
        )

        print(
            f"FROM-TEXT ERROR TYPE: {type(exc).__name__}",
            flush=True,
        )

        print(
            f"FROM-TEXT ERROR MESSAGE: {str(exc)}",
            flush=True,
        )

        chapter.status = "failed"

        print(
            "FROM-TEXT: attempting to commit failed status",
            flush=True,
        )

        await db.commit()

        print(
            "FROM-TEXT: failed status committed",
            flush=True,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Chapter indexing failed: {str(exc)}",
        )

    print(
        "FROM-TEXT: STEP 7 complete",
        flush=True,
    )

    # =====================================================
    # 8. Mark chapter ready
    # =====================================================

    print(
        "FROM-TEXT: STEP 8 - marking chapter ready",
        flush=True,
    )

    chapter.status = "ready"

    print(
        "FROM-TEXT: chapter status set to ready",
        flush=True,
    )

    print(
        "FROM-TEXT: committing final database transaction",
        flush=True,
    )

    await db.commit()

    print(
        "FROM-TEXT: final database commit completed",
        flush=True,
    )

    print(
        "FROM-TEXT: STEP 8 complete",
        flush=True,
    )

    # =====================================================
    # 9. Return result
    # =====================================================

    print(
        "FROM-TEXT: STEP 9 - preparing response",
        flush=True,
    )

    result = {
        "chapter_id": chapter.id,
        "title": chapter.title,
        "subject": chapter.subject,
        "grade": chapter.grade,
        "status": chapter.status,
        "source": "text",
        "content_length": len(content),
        "content_hash": chapter.content_hash,
    }

    print(
        f"FROM-TEXT: SUCCESS - returning chapter id={chapter.id}",
        flush=True,
    )

    print(
        "FROM-TEXT: ========================================",
        flush=True,
    )

    return result


# =========================================================
# GET /api/v1/chapters?child_id=...
# =========================================================

@router.get("")
async def get_chapters(
    child_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):

    print(
        f"GET CHAPTERS: endpoint entered child_id={child_id}",
        flush=True,
    )

    # =====================================================
    # 1. Find parent's family
    # =====================================================

    print(
        "GET CHAPTERS: looking up family",
        flush=True,
    )

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

    print(
        f"GET CHAPTERS: family found id={family.id}",
        flush=True,
    )

    # =====================================================
    # 2. Verify child belongs to parent
    # =====================================================

    print(
        f"GET CHAPTERS: looking up child id={child_id}",
        flush=True,
    )

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

    print(
        f"GET CHAPTERS: child found id={child.id}",
        flush=True,
    )

    # =====================================================
    # 3. Get chapters
    # =====================================================

    print(
        "GET CHAPTERS: querying chapters",
        flush=True,
    )

    result = await db.execute(
        select(Chapter)
        .where(
            Chapter.child_id == child_id
        )
        .order_by(Chapter.title)
    )

    chapters = result.scalars().all()

    print(
        f"GET CHAPTERS: found {len(chapters)} chapters",
        flush=True,
    )

    # =====================================================
    # 4. Return chapters
    # =====================================================

    print(
        "GET CHAPTERS: returning response",
        flush=True,
    )

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
# =========================================================

@router.delete("/{chapter_id}")
async def delete_chapter(
    chapter_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):

    print(
        f"DELETE CHAPTER: endpoint entered chapter_id={chapter_id}",
        flush=True,
    )

    # =====================================================
    # 1. Find parent's family
    # =====================================================

    print(
        "DELETE CHAPTER: looking up family",
        flush=True,
    )

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
    # =====================================================

    print(
        "DELETE CHAPTER: looking up chapter",
        flush=True,
    )

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

    print(
        f"DELETE CHAPTER: chapter found id={chapter.id}",
        flush=True,
    )

    # =====================================================
    # 3. Find documents
    # =====================================================

    print(
        "DELETE CHAPTER: finding documents",
        flush=True,
    )

    result = await db.execute(
        select(Document).where(
            Document.chapter_id == chapter.id
        )
    )

    documents = result.scalars().all()

    print(
        f"DELETE CHAPTER: found {len(documents)} documents",
        flush=True,
    )

    # =====================================================
    # 4. Delete document objects from storage
    # =====================================================

    deleted_storage_objects = 0

    for document in documents:

        if document.storage_key.startswith("text-chapters/"):
            continue

        print(
            f"DELETE CHAPTER: deleting storage object "
            f"{document.storage_key}",
            flush=True,
        )

        try:

            storage.delete(
                document.storage_key
            )

            deleted_storage_objects += 1

        except Exception as exc:

            print(
                f"DELETE CHAPTER ERROR: storage deletion failed: {exc}",
                flush=True,
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Could not delete chapter file "
                    f"from storage: {str(exc)}"
                ),
            )

    # =====================================================
    # 5. Find lessons
    # =====================================================

    print(
        "DELETE CHAPTER: finding lessons",
        flush=True,
    )

    from app.db.models import Lesson

    result = await db.execute(
        select(Lesson).where(
            Lesson.chapter_id == chapter.id
        )
    )

    lessons = result.scalars().all()

    print(
        f"DELETE CHAPTER: found {len(lessons)} lessons",
        flush=True,
    )

    # =====================================================
    # 6. Delete lesson videos
    # =====================================================

    deleted_video_objects = 0

    for lesson in lessons:

        if not lesson.video_key:
            continue

        print(
            f"DELETE CHAPTER: deleting video "
            f"{lesson.video_key}",
            flush=True,
        )

        try:

            storage.delete(
                lesson.video_key
            )

            deleted_video_objects += 1

        except Exception as exc:

            print(
                f"DELETE CHAPTER ERROR: video deletion failed: {exc}",
                flush=True,
            )

            raise HTTPException(
                status_code=500,
                detail=(
                    "Could not delete lesson video "
                    f"from storage: {str(exc)}"
                ),
            )

    # =====================================================
    # 7. Delete chapter
    # =====================================================

    print(
        "DELETE CHAPTER: deleting database chapter",
        flush=True,
    )

    await db.delete(chapter)

    await db.commit()

    print(
        "DELETE CHAPTER: database delete committed",
        flush=True,
    )

    # =====================================================
    # 8. Return result
    # =====================================================

    print(
        "DELETE CHAPTER: returning success",
        flush=True,
    )

    return {
        "message": "Chapter deleted successfully",
        "chapter_id": chapter_id,
        "deleted_storage_objects": deleted_storage_objects,
        "deleted_video_objects": deleted_video_objects,
    }


# =========================================================
# NOTE:
# The original file contained a second duplicate
# DELETE /{chapter_id} route below this point.
#
# It has intentionally been omitted from this diagnostic
# version because the first DELETE route already handles
# the endpoint.
# =========================================================