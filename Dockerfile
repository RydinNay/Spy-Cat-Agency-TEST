FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Копируем весь проект
COPY . .

# Копируем скрипт только для создания суперюзера
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Команда запуска: сначала миграции, затем runserver
CMD python manage.py makemigrations && \
    python manage.py migrate --noinput && \
    /entrypoint.sh && \
    python manage.py runserver 0.0.0.0:8000
