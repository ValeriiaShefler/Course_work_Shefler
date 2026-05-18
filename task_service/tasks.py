#CRUD операции с задачами
from database import get_connection, close_connection
from typing import List, Optional


async def get_user_tasks(user_id: int) -> List[dict]:
    conn = await get_connection()
    try:
        rows = await conn.fetch(
            "SELECT id, user_id, title, description, status, created_at FROM tasks WHERE user_id = $1 ORDER BY created_at DESC",
            user_id
        )
        return [dict(row) for row in rows]
    finally:
        await close_connection(conn)


async def get_task_by_id(task_id: int, user_id: int) -> Optional[dict]:
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "SELECT id, user_id, title, description, status, created_at FROM tasks WHERE id = $1 AND user_id = $2",
            task_id, user_id
        )
        return dict(row) if row else None
    finally:
        await close_connection(conn)


async def create_task(user_id: int, title: str, description: Optional[str] = None) -> dict:
    conn = await get_connection()
    try:
        row = await conn.fetchrow(
            "INSERT INTO tasks (user_id, title, description) VALUES ($1, $2, $3) RETURNING id, user_id, title, description, status, created_at",
            user_id, title, description
        )
        return dict(row)
    finally:
        await close_connection(conn)


async def update_task(task_id: int, user_id: int, title: Optional[str] = None, 
                      description: Optional[str] = None, status: Optional[str] = None) -> Optional[dict]:
    conn = await get_connection()
    try:
        # Проверка прав доступа
        existing = await conn.fetchrow(
            "SELECT id FROM tasks WHERE id = $1 AND user_id = $2",
            task_id, user_id
        )
        if not existing:
            return None
        
        # Динамическое построение UPDATE запроса
        updates = []
        values = []
        if title is not None:
            updates.append(f"title = ${len(values) + 3}")
            values.append(title)
        if description is not None:
            updates.append(f"description = ${len(values) + 3}")
            values.append(description)
        if status is not None:
            updates.append(f"status = ${len(values) + 3}")
            values.append(status)
        
        if updates:
            query = f"""
                UPDATE tasks 
                SET {", ".join(updates)}
                WHERE id = $1 AND user_id = $2
                RETURNING id, user_id, title, description, status, created_at
            """
            row = await conn.fetchrow(query, task_id, user_id, *values)
            return dict(row) if row else None
        else:
            return await get_task_by_id(task_id, user_id)
    finally:
        await close_connection(conn)


async def delete_task(task_id: int, user_id: int) -> bool:
    conn = await get_connection()
    try:
        result = await conn.execute(
            "DELETE FROM tasks WHERE id = $1 AND user_id = $2",
            task_id, user_id
        )
        return result != "DELETE 0"
    finally:
        await close_connection(conn)


async def delete_all_user_tasks(user_id: int) -> bool:
    conn = await get_connection()
    try:
        await conn.execute("DELETE FROM tasks WHERE user_id = $1", user_id)
        return True
    finally:
        await close_connection(conn)