class TaskConfig:
   
    # Статусы задач
    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    
    #допустимые статусы
    VALID_STATUSES = [STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_COMPLETED]
    
    #сообщения об ошибках
    ERROR_MESSAGES = {
        "invalid_token": "Неверный или просроченный токен",
        "task_not_found": "Задача не найдена",
        "title_required": "Название задачи обязательно",
        "invalid_status": f"Неверный статус. Допустимые: {', '.join(VALID_STATUSES)}",
        "auth_service_unavailable": "Сервис аутентификации недоступен",
    }
    
    # сообщения об успехе
    SUCCESS_MESSAGES = {
        "task_deleted": "Задача успешно удалена",
        "all_tasks_deleted": "Все задачи успешно удалены",
    }


config = TaskConfig()