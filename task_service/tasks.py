#CRUD операции с задачами с использованием SQLAlchemy
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from database import Task


async def get_user_tasks(db: AsyncSession, user_id: int) -> List[dict]:
    result = await db.execute(
        select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()
    return [task.__dict__ for task in tasks]


async def get_task_by_id(db: AsyncSession, task_id: int, user_id: int) -> Optional[Task]:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_task(db: AsyncSession, user_id: int, title: str, description: Optional[str] = None) -> Task:
    task = Task(
        user_id=user_id,
        title=title,
        description=description
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def update_task(
    db: AsyncSession,
    task_id: int,
    user_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None
) -> Optional[Task]:
    task = await get_task_by_id(db, task_id, user_id)
    if not task:
        return None
    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if status is not None:
        task.status = status
    
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task_id: int, user_id: int) -> bool:
    result = await db.execute(
        delete(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    await db.commit()
    return result.rowcount > 0


async def delete_all_user_tasks(db: AsyncSession, user_id: int) -> bool:
    await db.execute(delete(Task).where(Task.user_id == user_id))
    await db.commit()
    return True