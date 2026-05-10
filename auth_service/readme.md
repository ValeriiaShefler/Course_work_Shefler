# Auth Service

## Задачи сервиса
- Регистрация новых пользователей
- Аутентификация (логин)
- Выдача JWT токенов
- Проверка валидности JWT токенов для других сервисов
- Управление профилем: смена email, username, пароля
- Удаление аккаунта с подтверждением пароля

## Межсервисное взаимодействие

Task Service обращается к эндпоинту `GET /verify` для проверки JWT-токенов. Сервис не хранит состояние сессий — вся информация закодирована в самом токене.

## Структура базы данных

    CREATE TABLE users (  
        id SERIAL PRIMARY KEY,  
        email VARCHAR(255) UNIQUE NOT NULL,  
        username VARCHAR(100) UNIQUE NOT NULL,  
        password_hash VARCHAR(255) NOT NULL,  
        avatar TEXT,  
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  
    );  

## Переменные окружения, в том числе секретный JWT ключ, уникальный для каждого развертывания

DATABASE_URL=postgresql://  postgres:postgres123@postgres:5432/taskmanager  
JWT_SECRET_KEY=your-secret-key-change-this  
JWT_ALGORITHM=HS256  
JWT_EXPIRE_MINUTES=60  
PORT=8001  

## Подготовка к запуску  

Перед запуском необходимо обязательно скопируйте файл с примером переменных окружения .env.example ф файл .env в папке auth_service, например, воспользовавшись командой:  
    
    cp .env.example .env  

Также необходимо обязательно сгенерировать свой уникальный с екрестный ключ и заменить JWT_SECRET_KEY в .env:  

    вариант для Linux/Mac: openssl rand -hex 32

    вариант для Python: python -c "import secrets; print(secrets.token_urlsafe(32))"  

При необходимости можно отредактировать и другие переменные  

## Запуск сервиса  
1. Через docker-compose из корня проекта (docker-compose версии от 2.x и выше):  

    docker-compose up --build  

2. Или же локально:  

    cd auth_service
    pip install -r requirements.txt
    uvicorn app:app --host 0.0.0.0 --port 8001 --reload

## API Endpoints

1. POST 	/register            регистрация  
2. POST     /login               авторизация  
3. GET      /verify              проверка токена (для других сервисов)  
4. GET      /me                  информация о себе  
5. PUT      /change-email        смена почты  
6. PUT      /change-username     смена никнейма  
7. PUT      /change-password     cмена пароля  
8. DELETE   /delete-account      удаление аккаунта  
9. GET     	/health              проверка здоровья сервиса  

## Доступ к API  

1. Через Swagger UI (интерактивная документация)

    В браузере открыть ссылку: http://localhost:8001/docs  

2. Через curl. Рассматрим примеры запросов:

    2.1 Регистрация:  

        curl -X POST http://localhost:8001/register \
            -H "Content-Type: application/json" \
            -d '{
                "username": "ivan",
                "email": "ivan@example.com",
                "password": "123456",
                "avatar": ""
            }'

    2.2 Авторизация:  

        curl -X POST http://localhost:8001/login \
            -H "Content-Type: application/json" \
            -d '{"email":"ivan@example.com","password":"123456"}'

    2.3 Смена никнейма (требуется токен):  
    
        curl -X PUT http://localhost:8001/change-username \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer <ваш_токен>" \
            -d '{"username":"ivan123"}'  

    2.4 Удаление аккаунта (требуется токен и пароль):

        curl -X DELETE http://localhost:8001/delete-account \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer <ваш_токен>" \
            -d '{"password":"123456"}'  

3. Через веб-клиент о чем подробнее в readme.md в корне проекта  

## Файловая структура  

auth_service/  
├── app.py              # основной код сервиса  
├── requirements.txt    # зависимости Python  
├── Dockerfile          # сборка Docker-образа  
├── .env.example        # пример переменных окружения  
└── readme.md           # документация    

## Requirements  

    fastapi==0.104.1  
    uvicorn==0.24.0  
    python-jose[cryptography]==3.3.0  
    bcrypt==4.1.2  
    asyncpg==0.29.0  
    python-dotenv==1.0.0  
    email-validator==2.1.0  
    httpx==0.25.1  

В случае, если вам необходимо проверить работоспособность системы, необходимо отправить запрос curl http://localhost:8001/health и ждать ответ {"status":"ok"}.