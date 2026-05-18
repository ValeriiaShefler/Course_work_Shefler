import asyncio
from database import get_connection, close_connection
from auth import hash_password, verify_password


async def get_user_by_email(email: str):
    conn = await get_connection()
    try:
        return await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
    finally:
        await close_connection(conn)


async def get_user_by_username(username: str):
    conn = await get_connection()
    try:
        return await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
    finally:
        await close_connection(conn)


async def get_user_by_id(user_id: int):
    conn = await get_connection()
    try:
        return await conn.fetchrow("SELECT id, email, username, avatar FROM users WHERE id = $1", user_id)
    finally:
        await close_connection(conn)


async def create_user(email: str, username: str, password: str, avatar: str = None):
    conn = await get_connection()
    try:
        password_hash = hash_password(password)
        return await conn.fetchrow(
            "INSERT INTO users (email, username, password_hash, avatar) VALUES ($1, $2, $3, $4) RETURNING id",
            email, username, password_hash, avatar
        )
    finally:
        await close_connection(conn)


async def update_user_email(user_id: int, email: str):
    conn = await get_connection()
    try:
        await conn.execute("UPDATE users SET email = $1 WHERE id = $2", email, user_id)
    finally:
        await close_connection(conn)


async def update_user_username(user_id: int, username: str):
    conn = await get_connection()
    try:
        await conn.execute("UPDATE users SET username = $1 WHERE id = $2", username, user_id)
    finally:
        await close_connection(conn)


async def update_user_password(user_id: int, new_password: str):
    conn = await get_connection()
    try:
        new_hash = hash_password(new_password)
        await conn.execute("UPDATE users SET password_hash = $1 WHERE id = $2", new_hash, user_id)
    finally:
        await close_connection(conn)


async def delete_user(user_id: int):
    conn = await get_connection()
    try:
        await conn.execute("DELETE FROM users WHERE id = $1", user_id)
    finally:
        await close_connection(conn)


async def check_email_exists(email: str, exclude_user_id: int = None):
    conn = await get_connection()
    try:
        if exclude_user_id:
            return await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1 AND id != $2",
                email, exclude_user_id
            )
        return await conn.fetchrow("SELECT id FROM users WHERE email = $1", email)
    finally:
        await close_connection(conn)


async def check_username_exists(username: str, exclude_user_id: int = None):
    conn = await get_connection()
    try:
        if exclude_user_id:
            return await conn.fetchrow(
                "SELECT id FROM users WHERE username = $1 AND id != $2",
                username, exclude_user_id
            )
        return await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
    finally:
        await close_connection(conn)