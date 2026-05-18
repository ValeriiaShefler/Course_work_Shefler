from pydantic_settings import BaseSettings


class Settings(BaseSettings):
  
    DATABASE_URL: str
    AUTH_SERVICE_URL: str = "http://auth_service:8001"
    PORT: int = 8002
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()