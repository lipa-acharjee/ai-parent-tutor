import asyncio
from sqlalchemy import text
from app.db.database import engine

async def main():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(
                text(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname = 'public' ORDER BY tablename"
                )
            )
            tables = [row[0] for row in result.fetchall()]
            print("Tables found:", len(tables))
            for table in tables:
                print("-", table)
    except Exception as exc:
        print("Database check failed:", type(exc).__name__, str(exc))
    finally:
        await engine.dispose()

asyncio.run(main())
