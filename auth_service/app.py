#микросервис аутентификации для:
#1. регистрации
#2. аутентификации с выдачей JWT токена
#3. проверкой валидности JWT токенов для других сервисов
#4. управления профилем, в том числе сменой почты, никнейма, пароля и удаления аккаунта
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware # для кросс-доменных запросов с веб-клиента
from pydantic import BaseModel
from typing import Optional
import asyncpg
import os
import asyncio
from dotenv import load_dotenv
from jose import JWTError, jwt
from datetime import datetime, timedelta
import bcrypt

load_dotenv()

app = FastAPI(title="Auth Service")
security = HTTPBearer() #схема для Bearer токенов

# разрешаем запросы с любых источников, чтобы веб-клиент (http://localhost:3000) мог обращаться к API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT настройки
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

#пул соединения с бд
db_pool = None

#модели для валидации запросов и ответов
#регистрация
class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    avatar: Optional[str] = None

#авторизация
class UserLogin(BaseModel):
    email: str
    password: str

#ответ на регистрацию или валидацию
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    avatar: Optional[str] = None

#ответ при проверке токена для других сервисов
class VerifyResponse(BaseModel):
    valid: bool
    user_id: Optional[int] = None
    username: Optional[str] = None
    avatar: Optional[str] = None

#смена почты
class ChangeEmailRequest(BaseModel):
    email: str

#смена никнейма
class ChangeUsernameRequest(BaseModel):
    username: str

#смена пароля
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    avatar: Optional[str] = None

#Хеширование пароля с помощью bcrypt
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

#проверка пароля
def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

#запуск
@app.on_event("startup")
async def startup():
    global db_pool
    print("Starting Auth Service...")
    
    database_url = os.getenv("DATABASE_URL")
    print(f"Connecting to: {database_url}")
    # повторяем попытки подключения к БД (ждём пока PostgreSQL запустится)
    for attempt in range(15):
        try:
            db_pool = await asyncpg.create_pool(database_url, min_size=1, max_size=5)
            async with db_pool.acquire() as conn:
                #если таблицы еще нет, то создаем ее
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(255) UNIQUE NOT NULL,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        avatar TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("Users table ready")
                print("Auth Service started successfully")
            return
        except Exception as e:
            print(f" Attempt {attempt + 1}/15 failed: {e}")
            await asyncio.sleep(3)
    
    raise Exception("Could not connect to database after 15 attempts")

#остановка сервиса
@app.on_event("shutdown")
async def shutdown():
    if db_pool:
        await db_pool.close()

# эндпоинты
@app.post("/register", response_model=TokenResponse)
async def register(user: UserRegister):
    print(f"Registration attempt: {user.email}")
    
    #валидация:
    # - проверяет почту и длину пароля (не меньше 6 символов)
    # - проверяет уникальность почты и никнейма 
    # - хешируется пароль
    # - сохраняет данные в базу
    # - возвращает JWT токен
    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    if len(user.username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
    if "@" not in user.email or "." not in user.email:
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    try:
        async with db_pool.acquire() as conn:
            #проверка на существование
            existing = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1 OR username = $2",
                user.email, user.username
            )
            if existing:
                raise HTTPException(status_code=400, detail="Email or username already exists")
            
            # создание пользователя
            password_hash = hash_password(user.password)
            new_user = await conn.fetchrow(
                "INSERT INTO users (email, username, password_hash, avatar) VALUES ($1, $2, $3, $4) RETURNING id",
                user.email, user.username, password_hash, user.avatar
            )
            
            #создание токена
            token = create_access_token({
                "sub": str(new_user["id"]), # subject это ID пользователя
                "username": user.username
            })
            
            print(f"User registered: {user.username} (id: {new_user['id']})")
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "user_id": new_user["id"],
                "username": user.username,
                "avatar": user.avatar
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

#авторизация пользователя (проверяем почту и пароль, возвращая JWT токен для запросов)
@app.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    print(f"Login attempt: {user.email}")
    
    try:
        async with db_pool.acquire() as conn:
            db_user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", user.email)
            if not db_user:
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            if not verify_password(user.password, db_user["password_hash"]):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            
            token = create_access_token({
                "sub": str(db_user["id"]),
                "username": db_user["username"]
            })
            
            print(f"User logged in: {db_user['username']}")
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "user_id": db_user["id"],
                "username": db_user["username"],
                "avatar": db_user["avatar"]
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

#проверка JWT токена (в том числе срока годности и подписи, а при валдиности возвращает id пользователя и юзернейм)
@app.get("/verify", response_model=VerifyResponse)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            return {"valid": False, "user_id": None, "username": None, "avatar": None}
        
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, username, avatar FROM users WHERE id = $1",
                int(user_id)
            )
            if not user:
                return {"valid": False, "user_id": None, "username": None, "avatar": None}
        
        return {
            "valid": True,
            "user_id": user["id"],
            "username": user["username"],
            "avatar": user["avatar"]
        }
    except jwt.ExpiredSignatureError:
        return {"valid": False, "user_id": None, "username": None, "avatar": None}
    except jwt.JWTError:
        return {"valid": False, "user_id": None, "username": None, "avatar": None}
    except Exception as e:
        print(f"Verify error: {e}")
        return {"valid": False, "user_id": None, "username": None, "avatar": None}

#получение информации о текущем пользователе
@app.get("/me", response_model=UserResponse)
async def get_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, username, avatar FROM users WHERE id = $1",
                int(user_id)
            )
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            return {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"],
                "avatar": user["avatar"]
            }
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

#смена почты с затебованием токена
@app.put("/change-email")
async def change_email(
    request: ChangeEmailRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if "@" not in request.email or "." not in request.email:
            raise HTTPException(status_code=400, detail="Invalid email format")
        
        async with db_pool.acquire() as conn:
            #проверяем, не занят ли email
            existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1 AND id != $2", request.email, int(user_id))
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use")
            
            await conn.execute("UPDATE users SET email = $1 WHERE id = $2", request.email, int(user_id))
            return {"message": "Email updated successfully"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# смена никнейма с затребованием токена
@app.put("/change-username")
async def change_username(
    request: ChangeUsernameRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if len(request.username) < 3:
            raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
        
        async with db_pool.acquire() as conn:
            # Проверяем, не занят ли никнейм
            existing = await conn.fetchrow("SELECT id FROM users WHERE username = $1 AND id != $2", request.username, int(user_id))
            if existing:
                raise HTTPException(status_code=400, detail="Username already in use")
            
            await conn.execute("UPDATE users SET username = $1 WHERE id = $2", request.username, int(user_id))
            
            # обновляем токен с новым username
            new_token = create_access_token({
                "sub": str(user_id),
                "username": request.username
            })
            
            return {"message": "Username updated successfully", "access_token": new_token}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

#смена пароля пользователя с затребованием текущего пароля
@app.put("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Сменить пароль пользователя"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if len(request.new_password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        async with db_pool.acquire() as conn:
            #проверяем текущий пароль
            user = await conn.fetchrow("SELECT password_hash FROM users WHERE id = $1", int(user_id))
            if not verify_password(request.current_password, user["password_hash"]):
                raise HTTPException(status_code=401, detail="Current password is incorrect")
            
            # обновляем пароль
            new_hash = hash_password(request.new_password)
            await conn.execute("UPDATE users SET password_hash = $1 WHERE id = $2", new_hash, int(user_id))
            return {"message": "Password updated successfully"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

#удалерие аккаунта пользователя
@app.delete("/delete-account")
async def delete_account(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    try:
        body = await request.json()
        password = body.get("password")
        
        if not password:
            raise HTTPException(status_code=400, detail="Password required")
        
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow("SELECT password_hash FROM users WHERE id = $1", int(user_id))
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            if not verify_password(password, user["password_hash"]):
                raise HTTPException(status_code=401, detail="Invalid password")
            
            await conn.execute("DELETE FROM users WHERE id = $1", int(user_id))
            
            return {"message": "Account deleted successfully"}
            
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        print(f"Delete account error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}