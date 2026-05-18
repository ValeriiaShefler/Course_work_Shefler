import asyncpg
from settings import settings

async def get_connection():
    conn = await asyncpg.connect(settings.DATABASE_URL)
    return conn

async def close_connection(conn):
    await conn.close()