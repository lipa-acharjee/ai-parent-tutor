from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chunk

from app.ai.models import embedding_provider


# =========================================================
# ADD CHUNKS
# =========================================================

async def add_chunks(
    db: AsyncSession,
    chapter_id: str,
    chunks: list[tuple[int | None, str]],
):
    print("RAG: ========================================", flush=True)
    print("RAG: add_chunks() entered", flush=True)
    print(
        f"RAG: chapter_id={chapter_id}",
        flush=True,
    )
    print(
        f"RAG: number of chunks={len(chunks)}",
        flush=True,
    )

    try:
        # -------------------------------------------------
        # 1. Validate chunks
        # -------------------------------------------------

        print(
            "RAG: STEP 1 - inspecting chunks",
            flush=True,
        )

        for index, (page, text) in enumerate(chunks):
            print(
                f"RAG: chunk {index + 1}: "
                f"page={page}, "
                f"text_length={len(text)}",
                flush=True,
            )

        print(
            "RAG: STEP 1 complete",
            flush=True,
        )

        # -------------------------------------------------
        # 2. Prepare embedding input
        # -------------------------------------------------

        print(
            "RAG: STEP 2 - preparing embedding texts",
            flush=True,
        )

        embedding_texts = [
            x[1]
            for x in chunks
        ]

        print(
            f"RAG: embedding input count={len(embedding_texts)}",
            flush=True,
        )

        for index, text in enumerate(embedding_texts):
            print(
                f"RAG: embedding input {index + 1} "
                f"length={len(text)}",
                flush=True,
            )

        print(
            "RAG: STEP 2 complete",
            flush=True,
        )

        # -------------------------------------------------
        # 3. Generate embeddings
        # -------------------------------------------------

        print(
            "RAG: STEP 3 - starting embedding generation",
            flush=True,
        )

        print(
            "RAG: calling "
            "embedding_provider.embed_documents()",
            flush=True,
        )

        vectors = embedding_provider.embed_documents(
            embedding_texts
        )

        print(
            "RAG: embedding generation completed",
            flush=True,
        )

        print(
            f"RAG: number of vectors={len(vectors)}",
            flush=True,
        )

        # -------------------------------------------------
        # 4. Inspect vectors
        # -------------------------------------------------

        print(
            "RAG: STEP 4 - inspecting vectors",
            flush=True,
        )

        for index, vector in enumerate(vectors):
            try:
                vector_length = len(vector)
            except Exception:
                vector_length = "unknown"

            print(
                f"RAG: vector {index + 1} "
                f"dimension={vector_length}",
                flush=True,
            )

        print(
            "RAG: STEP 4 complete",
            flush=True,
        )

        # -------------------------------------------------
        # 5. Create Chunk database objects
        # -------------------------------------------------

        print(
            "RAG: STEP 5 - creating Chunk objects",
            flush=True,
        )

        chunk_objects = [
            Chunk(
                chapter_id=chapter_id,
                page_number=page,
                content=text,
                embedding=vec,
            )
            for (page, text), vec in zip(
                chunks,
                vectors,
            )
        ]

        print(
            f"RAG: created "
            f"{len(chunk_objects)} Chunk objects",
            flush=True,
        )

        print(
            "RAG: STEP 5 complete",
            flush=True,
        )

        # -------------------------------------------------
        # 6. Add objects to database session
        # -------------------------------------------------

        print(
            "RAG: STEP 6 - adding Chunk objects "
            "to database session",
            flush=True,
        )

        db.add_all(chunk_objects)

        print(
            "RAG: db.add_all() completed",
            flush=True,
        )

        print(
            "RAG: STEP 6 complete",
            flush=True,
        )

        # -------------------------------------------------
        # 7. Commit database transaction
        # -------------------------------------------------

        print(
            "RAG: STEP 7 - starting database commit",
            flush=True,
        )

        await db.commit()

        print(
            "RAG: database commit completed",
            flush=True,
        )

        print(
            "RAG: STEP 7 complete",
            flush=True,
        )

        print(
            "RAG: add_chunks() completed successfully",
            flush=True,
        )

        print(
            "RAG: ========================================",
            flush=True,
        )

    except Exception as exc:

        print(
            "RAG: !!!!! EXCEPTION IN add_chunks() !!!!!",
            flush=True,
        )

        print(
            f"RAG: exception type={type(exc).__name__}",
            flush=True,
        )

        print(
            f"RAG: exception={str(exc)}",
            flush=True,
        )

        print(
            "RAG: attempting database rollback",
            flush=True,
        )

        try:
            await db.rollback()

            print(
                "RAG: database rollback completed",
                flush=True,
            )

        except Exception as rollback_exc:

            print(
                "RAG: rollback itself failed",
                flush=True,
            )

            print(
                f"RAG: rollback exception="
                f"{type(rollback_exc).__name__}: "
                f"{str(rollback_exc)}",
                flush=True,
            )

        raise


# =========================================================
# RETRIEVE
# =========================================================

async def retrieve(
    db: AsyncSession,
    chapter_id: str,
    query: str,
    k: int = 8,
):
    """
    Vector similarity search.

    Use this for targeted questions or
    concept-specific retrieval.
    """

    print(
        "RAG: retrieve() entered",
        flush=True,
    )

    print(
        f"RAG: chapter_id={chapter_id}",
        flush=True,
    )

    print(
        f"RAG: query length={len(query)}",
        flush=True,
    )

    print(
        "RAG: generating query embedding",
        flush=True,
    )

    qvec = embedding_provider.embed_query(
        query
    )

    print(
        "RAG: query embedding generated",
        flush=True,
    )

    print(
        f"RAG: query vector dimension={len(qvec)}",
        flush=True,
    )

    stmt = (
        select(Chunk)
        .where(
            Chunk.chapter_id == chapter_id
        )
        .order_by(
            Chunk.embedding.cosine_distance(
                qvec
            )
        )
        .limit(k)
    )

    print(
        "RAG: executing vector similarity query",
        flush=True,
    )

    result = await db.execute(stmt)

    chunks = list(
        result.scalars().all()
    )

    print(
        f"RAG: retrieve() returned "
        f"{len(chunks)} chunks",
        flush=True,
    )

    return chunks


# =========================================================
# RETRIEVE COMPLETE CHAPTER
# =========================================================

async def retrieve_chapter(
    db: AsyncSession,
    chapter_id: str,
):
    """
    Retrieve the complete chapter in
    textbook page order.

    This is different from vector retrieval.

    It is intended for lesson generation,
    where the AI needs to understand the
    complete chapter instead of only the
    most similar chunks.
    """

    print(
        "RAG: retrieve_chapter() entered",
        flush=True,
    )

    print(
        f"RAG: chapter_id={chapter_id}",
        flush=True,
    )

    stmt = (
        select(Chunk)
        .where(
            Chunk.chapter_id == chapter_id
        )
        .order_by(
            Chunk.page_number.asc(),
            Chunk.id.asc(),
        )
    )

    print(
        "RAG: executing complete chapter query",
        flush=True,
    )

    result = await db.execute(stmt)

    chunks = list(
        result.scalars().all()
    )

    print(
        f"RAG: retrieve_chapter() returned "
        f"{len(chunks)} chunks",
        flush=True,
    )

    return chunks


# =========================================================
# CONTEXT FROM CHUNKS
# =========================================================

def context_from_chunks(chunks):
    """
    Convert chunks into readable AI context.
    """

    print(
        "RAG: context_from_chunks() entered",
        flush=True,
    )

    print(
        f"RAG: number of chunks={len(chunks)}",
        flush=True,
    )

    context = "\n\n".join(
        f"[Page {c.page_number or '?'}]\n"
        f"{c.content}"
        for c in chunks
    )

    print(
        f"RAG: generated context length={len(context)}",
        flush=True,
    )

    return context