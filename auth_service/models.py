# Pydantic модели для валидации данных
from pydantic import BaseModel, EmailStr
from typing import Optional


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    avatar: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    avatar: Optional[str] = None


class VerifyResponse(BaseModel):
    #ответ при проверке токена (для других сервисов)
    valid: bool
    user_id: Optional[int] = None
    username: Optional[str] = None
    avatar: Optional[str] = None


class ChangeEmailRequest(BaseModel):
    email: EmailStr


class ChangeUsernameRequest(BaseModel):
    username: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    avatar: Optional[str] = None