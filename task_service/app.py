#микросервис управления задачами для:
#1. создание, чтение, обновление, удаление записей
#2. проверка аутентификации (межсервисное взаимодействие)
#3. проверкой валидности JWT токенов для других сервисов
#4. просмотр и изолция данных пользователя (от других пользователей)
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncpg
import os
import asyncio
from dotenv import load_dotenv
import httpx
from datetime import datetime

load_dotenv()

app = FastAPI(title="Task Service")
security = HTTPBearer()

# настройки для веб клиента
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#глобальные переменные 
db_pool = None
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8001")

#модель создания задачи
class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None

#модель обновления задачи
class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

#ответ при работе с задачами
class TaskResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    status: str
    created_at: datetime

#запуск сервиса и подключение к БД с созданием таблицы
@app.on_event("startup")
async def startup():
    global db_pool
    print("Starting Task Service...")
    
    #повторяем попытки подключения (ждём PostgreSQL)
    for attempt in range(15):
        try:
            db_pool = await asyncpg.create_pool(os.getenv("DATABASE_URL"), min_size=1, max_size=5)
            async with db_pool.acquire() as conn:
                #создаём таблицу tasks, если её нет
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        description TEXT,
                        status VARCHAR(50) DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("Tasks table ready")
                print("Task Service started successfully")
            return
        except Exception as e:
            print(f"Attempt {attempt + 1}/15 failed: {e}")
            await asyncio.sleep(3)
    
    raise Exception("Could not connect to database")

@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()

# вспомогательные функции
#вызываем auth service для проверки токена, ведь task task не проверяет JWT самостоятельно
async def verify_token(token: str) -> dict:
    for attempt in range(5):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{AUTH_SERVICE_URL}/verify",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            print(f"Auth service connection attempt {attempt + 1}/5 failed: {e}")
            await asyncio.sleep(2)
    
    raise HTTPException(status_code=401, detail="Authentication failed")

#получение текущего пользователя их токена
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    return await verify_token(credentials.credentials)

#получение всех задач пользователя с сортировкой по дате создания
@app.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(user: dict = Depends(get_current_user)):
    if not user.get("valid"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM tasks WHERE user_id = $1 ORDER BY created_at DESC",
            user["user_id"]
        )
        return [dict(row) for row in rows]

#создание новой задачи
@app.post("/tasks", response_model=TaskResponse)
async def create_task(
    task: TaskCreate,
    user: dict = Depends(get_current_user)
):
    if not user.get("valid"):
        raise HTTPException(status_code=401, detail="Invalid token")
    if not task.title or len(task.title.strip()) == 0:
        raise HTTPException(status_code=400, detail="Title is required")
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO tasks (user_id, title, description) VALUES ($1, $2, $3) RETURNING *",
            user["user_id"], task.title, task.description
        )
        return dict(row)

#получение задачи по айди
@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, user: dict = Depends(get_current_user)):
    if not user.get("valid"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM tasks WHERE id = $1 AND user_id = $2",
            task_id, user["user_id"]
        )
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
        return dict(row)

#обновить задачу
@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task_update: TaskUpdate, user: dict = Depends(get_current_user)):
    if not user.get("valid"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    async with db_pool.acquire() as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM tasks WHERE id = $1 AND user_id = $2",
            task_id, user["user_id"]
        )
        if not existing:
            raise HTTPException(status_code=404, detail="Task not found")
        
        updates = []
        values = []
        if task_update.title is not None:
            updates.append(f"title = ${len(values) + 3}")
            values.append(task_update.title)
        if task_update.description is not None:
            updates.append(f"description = ${len(values) + 3}")
            values.append(task_update.description)
        if task_update.status is not None:
            if task_update.status not in ["pending", "in_progress", "completed"]:
                raise HTTPException(status_code=400, detail="Invalid status")
            updates.append(f"status = ${len(values) + 3}")
            values.append(task_update.status)
        
        if updates:
            query = f"""
                UPDATE tasks 
                SET {", ".join(updates)}
                WHERE id = $1 AND user_id = $2
                RETURNING *
            """
            row = await conn.fetchrow(query, task_id, user["user_id"], *values)
            return dict(row)
        else:
            row = await conn.fetchrow("SELECT * FROM tasks WHERE id = $1", task_id)
            return dict(row)

#удаление задачи по айди
@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, user: dict = Depends(get_current_user)):
    if not user.get("valid"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    async with db_pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM tasks WHERE id = $1 AND user_id = $2",
            task_id, user["user_id"]
        )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Task not found")
        return {"message": "Task deleted successfully"}

#удаление всех задач (автоматически происходит при удалении пользователя)
@app.delete("/tasks/delete-all")
async def delete_all_user_tasks(user: dict = Depends(get_current_user)):
    """Удалить все задачи пользователя (при удалении аккаунта)"""
    if not user.get("valid"):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM tasks WHERE user_id = $1", user["user_id"])
        return {"message": "All tasks deleted successfully"}

@app.get("/health")
async def health():
    return {"status": "ok"}