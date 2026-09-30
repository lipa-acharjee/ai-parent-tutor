import asyncio
from sqlalchemy import text
from app.db.database import engine

async def main():
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT current_database(), current_user, current_schema()
        """))
        row = result.fetchone()

        print("DATABASE:", row[0])
        print("USER:", row[1])
        print("SCHEMA:", row[2])

asyncio.run(main())
