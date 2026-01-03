FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание необходимых директорий
RUN mkdir -p uploads/generated uploads/user data

# Переменные окружения
ENV PORT=8080
ENV FLASK_ENV=production

# Expose порт
EXPOSE $PORT

# Команда запуска
CMD gunicorn -w 2 -b 0.0.0.0:$PORT --timeout 120 app:app
