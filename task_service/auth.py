#проверка аутентификации через Auth Service

import httpx
from fastapi import HTTPException
from settings import settings
from config import config
import asyncio

async def verify_token(token: str) -> dict:
    #Task Service не проверяет JWT самостоятельно, а доверяет Auth Service
    
    max_retries = 5
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{settings.AUTH_SERVICE_URL}/verify",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise HTTPException(status_code=401, detail=config.ERROR_MESSAGES["invalid_token"])
        except httpx.TimeoutException:
            if attempt == max_retries - 1:
                raise HTTPException(status_code=503, detail=config.ERROR_MESSAGES["auth_service_unavailable"])
        except Exception as e:
            if attempt == max_retries - 1:
                raise HTTPException(status_code=401, detail=config.ERROR_MESSAGES["invalid_token"])
        
        await asyncio.sleep(retry_delay)
    
    raise HTTPException(status_code=401, detail=config.ERROR_MESSAGES["invalid_token"])