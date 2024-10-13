# Используем образ для FastAPI
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.11-slim

# Копируем файл зависимостей
COPY requirements.txt /app/requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r /app/requirements.txt

# Копируем весь исходный код проекта в контейнер
COPY . /app

# Устанавливаем рабочую директорию
WORKDIR /app

# Указываем команду для запуска приложения FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
