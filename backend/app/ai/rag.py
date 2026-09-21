from sqlalchemy import select

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chunk

from app.ai.models import embedding_provider


async def add_chunks(
    db: AsyncSession,
    chapter_id: str,
    chunks: list[tuple[int | None, str]],
):
    vectors = embedding_provider.embed_documents(
        [x[1] for x in chunks]
    )

    db.add_all(
        [
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
    )

    await db.commit()


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

    qvec = embedding_provider.embed_query(
        query
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

    return list(
        (
            await db.execute(stmt)
        ).scalars().all()
    )


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

    return list(
        (
            await db.execute(stmt)
        ).scalars().all()
    )


def context_from_chunks(chunks):
    """
    Convert chunks into readable AI context.
    """

    return "\n\n".join(
        f"[Page {c.page_number or '?'}]\n"
        f"{c.content}"
        for c in chunks
    )