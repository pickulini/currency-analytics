FROM python:3.10-slim

WORKDIR /app

# Устанавливаем зависимости системы (если нужны, но здесь нет)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Создаём папку для данных (пользователи и отчёты)
RUN mkdir -p data/reports

# Открываем порт, который слушает Flask
EXPOSE 5000

# Запускаем приложение
CMD ["python", "app.py"]
