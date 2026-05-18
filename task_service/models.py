#модели валидации данных

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from config import config


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    
    def validate_status(self) -> Optional[str]:
        if self.status and self.status not in config.VALID_STATUSES:
            raise ValueError(config.ERROR_MESSAGES["invalid_status"])
        return self.status


class TaskResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: Optional[str]
    status: str
    created_at: datetime


class VerifyResponse(BaseModel):
    valid: bool
    user_id: Optional[int] = None
    username: Optional[str] = None
    avatar: Optional[str] = None