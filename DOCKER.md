# Docker Instructions

Инструкция по развертыванию системы поиска в Docker.

## Требования

- Docker
- Docker Compose
- Свободные порты: 8000-8003

## Быстрый старт
bash
Сборка образа
docker-compose build
Запуск сервисов
docker-compose up -d
Просмотр логов
docker-compose logs -f


## Структура

- `Dockerfile` - конфигурация образа
- `docker-compose.yml` - конфигурация сервисов
- `DATA/` - индексы и данные
- `validation_results/` - результаты валидации (монтируется с хост-машины)

## Проверка работоспособности

1. Тест поиска:
bash
curl -X POST "http://localhost:8000/search" \
-H "Content-Type: application/json" \
-d '{
"query": "космические путешествия",
"top_k": 5,
"method": 1
}'

2. Запуск валидации:

bash
curl -X POST "http://localhost:8003/validate/default"


## Управление контейнером
bash
Проверка статуса
docker-compose ps
Просмотр логов
docker-compose logs -f
Остановка сервисов
docker-compose down
Перезапуск
docker-compose restart


## Мониторинг
bash
Использование ресурсов
docker stats
Логи конкретного сервиса
docker-compose logs -f search_system


## Устранение неполадок

1. Если сервисы не запускаются:
   - Проверьте, свободны ли порты 8000-8003
   - Проверьте наличие всех файлов в DATA/
   - Просмотрите логи: `docker-compose logs`

2. Если валидация не работает:
   - Убедитесь, что папка validation_results имеет правильные права
   - Проверьте логи валидатора

## Важные замечания

1. Результаты валидации сохраняются в папку `validation_results` на хост-машине
2. Все порты (8000-8003) должны быть свободны
3. При первом запуске может потребоваться время для инициализации
4. Система автоматически перезапускается при сбоях

## Безопасность

- Сервисы запускаются от непривилегированного пользователя
- Используются только необходимые порты
- Контейнер изолирован от хост-системы

## Обновление

## Устранение неполадок

1. Если сервисы не запускаются:
   - Проверьте, свободны ли порты 8000-8003
   - Проверьте наличие всех файлов в DATA/
   - Просмотрите логи: `docker-compose logs`

2. Если валидация не работает:
   - Убедитесь, что папка validation_results имеет правильные права
   - Проверьте логи валидатора

## Важные замечания

1. Результаты валидации сохраняются в папку `validation_results` на хост-машине
2. Все порты (8000-8003) должны быть свободны
3. При первом запуске может потребоваться время для инициализации
4. Система автоматически перезапускается при сбоях

## Безопасность

- Сервисы запускаются от непривилегированного пользователя
- Используются только необходимые порты
- Контейнер изолирован от хост-системы

## Обновление

## Устранение неполадок

1. Если сервисы не запускаются:
   - Проверьте, свободны ли порты 8000-8003
   - Проверьте наличие всех файлов в DATA/
   - Просмотрите логи: `docker-compose logs`

2. Если валидация не работает:
   - Убедитесь, что папка validation_results имеет правильные права
   - Проверьте логи валидатора

## Важные замечания

1. Результаты валидации сохраняются в папку `validation_results` на хост-машине
2. Все порты (8000-8003) должны быть свободны
3. При первом запуске может потребоваться время для инициализации
4. Система автоматически перезапускается при сбоях

## Безопасность

- Сервисы запускаются от непривилегированного пользователя
- Используются только необходимые порты
- Контейнер изолирован от хост-системы

## Обновление
bash
Остановка текущей версии
docker-compose down
Пересборка с обновленным кодом
docker-compose build --no-cache
Запуск новой версии
docker-compose up -d

## Особенности реализации
Использован легкий базовый образ python:3.11-slim
Минимизирован контекст сборки через .dockerignore
Многослойная сборка для оптимизации размера
Запуск от непривилегированного пользователя
Монтирование папки с результатами валидации
Автоматический перезапуск при сбоях