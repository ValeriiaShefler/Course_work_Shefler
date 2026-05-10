# ShV Manager — микросервисное приложение для управления задачами

## О проекте

Веб-приложение для управления задачами, построенное по **микросервисной архитектуре**. Пользователи могут создавать задачи, менять их статус, редактировать и удалять. Приложение поддерживает регистрацию, аутентификацию, управление профилем и тёмную тему.

## Архитектура проекта

Проект состоит из трёх основных компонентов:

| Компонент | Технологии | Порт | Описание |
|-----------|------------|------|----------|
| **Auth Service** | Python + FastAPI + JWT | 8001 | Регистрация, логин, выдача/проверка JWT, управление профилем |
| **Task Service** | Python + FastAPI + PostgreSQL | 8002 | CRUD операции с задачами, статусы, фильтрация |
| **PostgreSQL** | PostgreSQL 15 | 5432 | Общая база данных (таблицы users и tasks) |
| **Web Client** | HTML + CSS + JavaScript | 3000 | Полноценный веб-интерфейс |

## Структура проекта:  

Course_work_Shefler/  
│  
├── docker-compose.yml          # Оркестрация всех сервисов  
├── .env.example                # Пример переменных для Docker  
├── .gitignore                  # Исключения для git  
├── README.md                   # Документация веб-клиента  
│  
├── auth_service/               # Сервис аутентификации  
│   ├── app.py                  # Код сервиса  
│   ├── requirements.txt        # Зависимости Python  
│   ├── Dockerfile              # Сборка Docker-образа  
│   ├── .env.example            # Пример переменных окружения  
│   └── README.md               # Документация сервиса  
│  
├── task_service/               # Сервис управления задачами  
│   ├── app.py                  # Код сервиса   
│   ├── requirements.txt        # Зависимости Python  
│   ├── Dockerfile              # Сборка Docker-образа  
│   ├── .env.example            # Пример переменных окружения  
│   └── README.md               # Документация сервиса  
│  
└── web_client/                 # Веб-интерфейс  
    ├── index.html              # Стартовая страница  
    ├── login.html              # Страница входа  
    ├── register.html           # Регистрация  
    ├── tasks.html              # Главная (список задач)  
    ├── profile.html            # Настройки профиля  
    └── style.css               # Единый файл стилей     

## Запуск приложения

1. Склонируйет репозиторий:

    git clone https://github.com/ValeriiaShefler/Course_work_Shefler.git  
    cd Course_work_Shefler  

2. Скопируйте примеры переменных окружения в файлы env.:  

    cp .env.example .env
    cp auth_service/.env.example auth_service/.env
    cp task_service/.env.example task_service/.env

3. Обязательно сгенерируйте свой JWT_SECRET_KEY, например в PowerShell:  

    python -c "import secrets; print(secrets.token_urlsafe(32))"   

И вставьте полученный ключ в файл auth_service/.env  

4. Запустите микросервисы (docker-compose версии от 2.x и выше):  

    docker-compose up --build  

5. Запустите веб клиент в новом окне терминала:  

    cd web_client  
    python -m http.server 3000  

6. В браузере откройте http://localhost:3000  

Более подробно о каждом сервисе и средствах разработчика можно узнать в файлах readme.md в соотвествующих папках auth_service/ и task_service/

