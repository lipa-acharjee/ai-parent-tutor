import asyncio
from sqlalchemy import text
from app.db.database import engine

async def main():
    async with engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'shared_videos'
                ORDER BY ordinal_position
            """)
        )

        print("Shared videos table columns:")
        for row in result:
            print("-", row[0])

    await engine.dispose()

asyncio.run(main())
