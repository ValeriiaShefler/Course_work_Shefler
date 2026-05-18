# точка входа Auth Service

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router

app = FastAPI(title="Auth Service")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Подключаем роутер
app.include_router(router)


@app.on_event("startup")
async def startup():
    print("Starting Auth Service...")
    print("Auth Service started successfully")


@app.on_event("shutdown")
async def shutdown():
    print("Shutting down...")