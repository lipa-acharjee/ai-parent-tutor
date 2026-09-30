import asyncio
from sqlalchemy import text
from app.db.database import engine

async def main():
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))

        tables = result.fetchall()

        print("PUBLIC TABLES:")
        if not tables:
            print("(no tables found)")
        else:
            for row in tables:
                print("-", row[0])

asyncio.run(main())
