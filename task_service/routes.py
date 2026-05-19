#API эндпоинты
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from models import TaskCreate, TaskUpdate, TaskResponse
from tasks import (
    get_user_tasks, get_task_by_id, create_task,
    update_task, delete_task, delete_all_user_tasks
)
from auth import verify_token
from config import config
from database import get_db

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    token = credentials.credentials
    return await verify_token(token)


@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not user.get("valid"):
        raise HTTPException(status_code=401, detail=config.ERROR_MESSAGES["invalid_token"])
    
    tasks = await get_user_tasks(db, user["user_id"])
    return tasks


@router.post("/tasks", response_model=TaskResponse)
async def create_new_task(
    task: TaskCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not user.get("valid"):
        raise HTTPException(status_code=401, detail=config.ERROR_MESSAGES["invalid_token"])
    
    if not task.title or len(task.title.strip()) == 0:
        raise HTTPException(status_code=400, detail=config.ERROR_MESSAGES["title_required"])
    
    new_task = await create_task(db, user["user_id"], task.title, task.description)
    return new_task


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not user.get("valid"):
        raise HTTPException(status_code=401, detail=config.ERROR_MESSAGES["invalid_token"])
    
    task = await get_task_by_id(db, task_id, user["user_id"])
    if not task:
        raise HTTPException(status_code=404, detail=config.ERROR_MESSAGES["task_not_found"])
    return task


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_existing_task(
    task_id: int,
    task_update: TaskUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not user.get("valid"):
        raise HTTPException(status_code=401, detail=config.ERROR_MESSAGES["invalid_token"])
    
    # Валидация статуса
    if task_update.status and task_update.status not in config.VALID_STATUSES:
        raise HTTPException(status_code=400, detail=config.ERROR_MESSAGES["invalid_status"])
    
    updated = await update_task(
        db, task_id, user["user_id"],
        title=task_update.title,
        description=task_update.description,
        status=task_update.status
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail=config.ERROR_MESSAGES["task_not_found"])
    
    return updated


@router.delete("/tasks/{task_id}")
async def delete_existing_task(
    task_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not user.get("valid"):
        raise HTTPException(status_code=401, detail=config.ERROR_MESSAGES["invalid_token"])
    
    success = await delete_task(db, task_id, user["user_id"])
    if not success:
        raise HTTPException(status_code=404, detail=config.ERROR_MESSAGES["task_not_found"])
    
    return {"message": config.SUCCESS_MESSAGES["task_deleted"]}


@router.delete("/tasks/delete-all")
async def delete_all_tasks(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not user.get("valid"):
        raise HTTPException(status_code=401, detail=config.ERROR_MESSAGES["invalid_token"])
    
    await delete_all_user_tasks(db, user["user_id"])
    return {"message": config.SUCCESS_MESSAGES["all_tasks_deleted"]}


@router.get("/health")
async def health():
    return {"status": "ok"}