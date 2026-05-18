#API эндпоинты

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from models import (
    UserRegister, UserLogin, TokenResponse,
    VerifyResponse, ChangeEmailRequest, ChangeUsernameRequest,
    ChangePasswordRequest, UserResponse
)
from users import (
    get_user_by_email, get_user_by_username, get_user_by_id, create_user,
    update_user_email, update_user_username, update_user_password,
    delete_user, check_email_exists, check_username_exists
)
from auth import create_access_token, verify_password, decode_token
from config import config

router = APIRouter()
security = HTTPBearer()


def validate_password(password: str):
    if len(password) < config.MIN_PASSWORD_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=config.ERROR_MESSAGES["password_too_short"]
        )
    return True


@router.post("/register", response_model=TokenResponse)
async def register(user: UserRegister):
    if len(user.username) < config.MIN_USERNAME_LENGTH:
        raise HTTPException(status_code=400, detail=config.ERROR_MESSAGES["username_too_short"])
    validate_password(user.password)
    
    #проверка на существование
    if await get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail=config.ERROR_MESSAGES["email_exists"])
    if await get_user_by_username(user.username):
        raise HTTPException(status_code=400, detail=config.ERROR_MESSAGES["username_exists"])
    
    # создание пользователя
    new_user = await create_user(user.email, user.username, user.password, user.avatar)
    
    #создание токена
    token = create_access_token(new_user["id"], user.username)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": new_user["id"],
        "username": user.username,
        "avatar": user.avatar
    }


@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin):
    db_user = await get_user_by_email(user.email)
    if not db_user or not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail=config.ERROR_MESSAGES["invalid_credentials"])
    
    token = create_access_token(db_user["id"], db_user["username"])
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": db_user["id"],
        "username": db_user["username"],
        "avatar": db_user["avatar"]
    }


@router.get("/verify", response_model=VerifyResponse)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    result = decode_token(credentials.credentials)
    if not result["valid"]:
        return {"valid": False, "user_id": None, "username": None, "avatar": None}
    
    user = await get_user_by_id(int(result["user_id"]))
    if not user:
        return {"valid": False, "user_id": None, "username": None, "avatar": None}
    
    return {
        "valid": True,
        "user_id": user["id"],
        "username": user["username"],
        "avatar": user["avatar"]
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    result = decode_token(credentials.credentials)
    if not result["valid"]:
        raise HTTPException(status_code=401, detail=config.ERROR_MESSAGES["invalid_token"])
    
    user = await get_user_by_id(int(result["user_id"]))
    if not user:
        raise HTTPException(status_code=404, detail=config.ERROR_MESSAGES["user_not_found"])
    
    return {
        "id": user["id"],
        "email": user["email"],
        "username": user["username"],
        "avatar": user["avatar"]
    }


@router.put("/change-email")
async def change_email(
    request: ChangeEmailRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    result = decode_token(credentials.credentials)
    if not result["valid"]:
        raise HTTPException(status_code=401, detail=config.ERROR_MESSAGES["invalid_token"])
    
    user_id = int(result["user_id"])
    
    if await check_email_exists(request.email, user_id):
        raise HTTPException(status_code=400, detail="Email already in use")
    
    await update_user_email(user_id, request.email)
    return {"message": "Почта успешно изменена"}


@router.put("/change-username")
async def change_username(
    request: ChangeUsernameRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    result = decode_token(credentials.credentials)
    if not result["valid"]:
        raise HTTPException(status_code=401, detail=config.ERROR_MESSAGES["invalid_token"])
    
    user_id = int(result["user_id"])
    
    if len(request.username) < config.MIN_USERNAME_LENGTH:
        raise HTTPException(status_code=400, detail=config.ERROR_MESSAGES["username_too_short"])
    
    if await check_username_exists(request.username, user_id):
        raise HTTPException(status_code=400, detail="Никнейм уже используется")
    
    await update_user_username(user_id, request.username)
    
    #новый токен с обновлённым username
    new_token = create_access_token(user_id, request.username)
    return {"message": "Никнейм успешно изменен", "access_token": new_token}


@router.put("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    result = decode_token(credentials.credentials)
    if not result["valid"]:
        raise HTTPException(status_code=401, detail=config.ERROR_MESSAGES["invalid_token"])
    
    user_id = int(result["user_id"])
    
    if len(request.new_password) < config.MIN_PASSWORD_LENGTH:
        raise HTTPException(status_code=400, detail=config.ERROR_MESSAGES["password_too_short"])
    
    await update_user_password(user_id, request.new_password)
    return {"message": "Пароль успешно изменен"}


@router.delete("/delete-account")
async def delete_account(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    result = decode_token(credentials.credentials)
    if not result["valid"]:
        raise HTTPException(status_code=401, detail=config.ERROR_MESSAGES["invalid_token"])
    
    user_id = int(result["user_id"])
    await delete_user(user_id)
    return {"message": "Ваш аккаунт был успешно удален"}


@router.get("/health")
async def health():
    return {"status": "ok"}