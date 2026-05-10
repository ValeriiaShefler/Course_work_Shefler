# Task Service

## Задачи сервиса
- CRUD операции с задачами (создание, чтение, обновление, удаление)
- Проверка аутентификации через Auth Service (межсервисное взаимодействие)
- Изоляция данных — пользователь видит только свои задачи
- Управление статусами задач (ожидает → в прогрессе → завершена)

## Межсервисное взаимодействие

Task Service обращается к эндпоинту `GET /verify` для проверки JWT-токенов. Сервис не хранит состояние сессий — вся информация закодирована в самом токене:  

    async def verify_token(token: str) -> dict:
    response = await client.get(
        f"{AUTH_SERVICE_URL}/verify",
        headers={"Authorization": f"Bearer {token}"}
    )
    return response.json()

## Структура базы данных

    CREATE TABLE tasks (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        status VARCHAR(50) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );  

## Переменные окружения

DATABASE_URL=postgresql://postgres:postgres123@postgres:5432/taskmanager  
AUTH_SERVICE_URL=http://auth_service:8001  
PORT=8002  

## Подготовка к запуску  

Перед запуском необходимо обязательно скопируйте файл с примером переменных окружения .env.example ф файл .env в папке task_service, например, воспользовавшись командой:  
    
    cp .env.example .env  

При необходимости можно отредактировать и другие переменные  

## Запуск сервиса  
1. Через docker-compose из корня проекта (docker-compose версии от 2.x и выше):  

    docker-compose up --build  

2. Или же локально:  

    cd task_service
    pip install -r requirements.txt
    uvicorn app:app --host 0.0.0.0 --port 8002 --reload

## API Endpoints

1. GET       /tasks                получить все задачи пользователя  
2. POST      /tasks                создать новую задачу  
3. GET       /tasks/{id}           получить задачу по ID  
4. PUT       /tasks/{id}           обновить задачу (любые поля)  
5. DELETE    tasks/{id}            удалить задачу  
6. DELETE    /tasks/delete-all     удалить все задачи пользователя    

При этом задачи обладают статусами:  

1. pending - ожидает выполнения (по умолчанию)  
2. in_progress - в процессе выполнения  
3. completed - задача завершена  

## Доступ к API  

1. Через Swagger UI (интерактивная документация)

    В браузере открыть ссылку: http://localhost:8002/docs  

2. Через curl. Рассматрим примеры запросов:

    2.1 Сначала нужно получить токен через Auth Service:

        curl -X POST http://localhost:8001/login \
            -H "Content-Type: application/json" \
            -d '{"email":"ivan@example.com","password":"123456"}'

    2.2 Получить все задачи по токену:  

        curl -X GET http://localhost:8002/tasks \
            -H "Authorization: Bearer <ваш_токен>"

    2.3 Создать задачу:  
    
        curl -X POST http://localhost:8002/tasks \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer <ваш_токен>" \
            -d '{"title":"Купить молоко","description":"2 литра"}'  

    2.4 Обновить задачу:

        curl -X PUT http://localhost:8002/tasks/1 \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer <ваш_токен>" \
            -d '{"status":"completed"}'  
    
    2.5 Удалить задачу:  

        curl -X DELETE http://localhost:8002/tasks/1 \
            -H "Authorization: Bearer <ваш_токен>"

3. Через веб-клиент о чем подробнее в readme.md в корне проекта  

## Файловая структура  

task_service/  
├── app.py              # основной код сервиса  
├── requirements.txt    # зависимости Python  
├── Dockerfile          # сборка Docker-образа  
├── .env.example        # пример переменных окружения  
└── readme.md           # документация    

## Requirements  

    fastapi==0.104.1
    uvicorn==0.24.0
    httpx==0.25.1
    asyncpg==0.29.0
    python-dotenv==1.0.0

В случае, если вам необходимо проверить работоспособность системы, необходимо отправить запрос curl http://localhost:8002/health и ждать ответ {"status":"ok"}.