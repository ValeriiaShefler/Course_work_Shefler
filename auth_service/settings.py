# вместо глобальных переменных
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    #настройки сервиса с валидацией типов
    
    # база данных
    DATABASE_URL: str
    
    #JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    
    # валидация
    MIN_PASSWORD_LENGTH: int = 6
    MIN_USERNAME_LENGTH: int = 3
    
    # сервер
    PORT: int = 8001
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()