import asyncpg
from config import DB_CONFIG

pool = None


async def init_db():
    global pool
    pool = await asyncpg.create_pool(**DB_CONFIG)


async def save_application(data, text):
    if pool is None:
        raise RuntimeError("DB not initialized")

    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO applications 
            (name, age, contact, instagram, telegram, application_text)
            VALUES ($1, $2, $3, $4, $5, $6)
        """,
        data.get("name"),
        data.get("age"),
        data.get("contact"),
        data.get("instagram"),
        data.get("telegram"),
        text
        )


async def get_applications(limit=10):
    if pool is None:
        raise RuntimeError("DB not initialized")

    async with pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM applications
            ORDER BY id DESC
            LIMIT $1
        """, limit)