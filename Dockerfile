# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем только необходимые файлы
COPY requirements.txt .
COPY search_services/ ./search_services/
COPY DATA/ ./DATA/
COPY run_init_services.py .
COPY run_all_services.py .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Создаем пользователя без прав root
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Открываем порты
EXPOSE 8000 8001 8002 8003

# Запускаем сервисы
CMD ["python", "run_all_services.py"]