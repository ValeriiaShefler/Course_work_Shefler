# JWT функции: создание, проверка, хеширование паролей

from jose import jwt, JWTError
from datetime import datetime, timedelta
import bcrypt
from settings import settings


def hash_password(password: str) -> str:
    #хеширование пароля с помощью bcrypt
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": expire
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return {"valid": True, "user_id": payload.get("sub"), "username": payload.get("username")}
    except JWTError:
        return {"valid": False, "user_id": None, "username": None}