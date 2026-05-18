# конфигурация сервиса аутентификации

import os
from dotenv import load_dotenv

load_dotenv()

class AuthConfig:
    
    #валидация пароля
    MIN_PASSWORD_LENGTH = int(os.getenv("MIN_PASSWORD_LENGTH", "6"))
    MIN_USERNAME_LENGTH = int(os.getenv("MIN_USERNAME_LENGTH", "3"))
    
    # JWT настройки
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-me")
    ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    
    # База данных
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    #сообщения об ошибках
    ERROR_MESSAGES = {
        "password_too_short": f"Пароль должен быть не менее {MIN_PASSWORD_LENGTH} символов",
        "username_too_short": f"Никнейм должен быть не менее {MIN_USERNAME_LENGTH} символов",
        "invalid_email": "Неверный формат email",
        "email_exists": "Email уже зарегистрирован",
        "username_exists": "Никнейм уже занят",
        "invalid_credentials": "Неверный email или пароль",
        "invalid_token": "Неверный или просроченный токен",
        "user_not_found": "Пользователь не найден",
    }


config = AuthConfig()