from fastapi import FastAPI, HTTPException
from typing import List
import asyncio
from .benchmark import SearchValidator, SearchMethod
from pydantic import BaseModel

app = FastAPI(title="Search Validation Service")

DEFAULT_QUERIES = [
    "космические путешествия",
    "Побег из Шоушенка",
    "Крёстный отец",
    "Тёмный рыцарь",
    "Криминальное чтиво",
    "Властелин колец: Возвращение короля",
    "Бойцовский клуб",
    "Форрест Гамп",
    "Начало",
    "Матрица",
    "Славные парни",
    "Империя наносит ответный удар",
    "Пролетая над гнездом кукушки",
    "Семь самураев",
    "Унесённые призраками",
    "Город Бога",
    "Молчание ягнят",
    "Эта замечательная жизнь",
    "Жизнь прекрасна",
    "Подозрительные лица",
]

class ValidationRequest(BaseModel):
    queries: List[str]
    base_url: str = "http://127.0.0.1:8000"

@app.post("/validate")
async def run_validation(request: ValidationRequest):
    """Запуск валидации с пользовательскими запросами"""
    try:
        validator = SearchValidator(base_url=request.base_url)
        results_path = await validator.validate_queries(request.queries)
        return {
            "status": "success",
            "message": "Валидация успешно завершена",
            "results_path": str(results_path)
        }
    except Exception as e:
        logger.error(f"Ошибка валидации: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при выполнении валидации: {str(e)}"
        )

@app.post("/validate/default")
async def run_default_validation():
    """Запуск валидации с предустановленными запросами"""
    try:
        validator = SearchValidator()
        await validator.validate_queries(DEFAULT_QUERIES)
        return {
            "status": "success",
            "message": "Валидация с предустановленными запросами завершена",
            "queries_used": DEFAULT_QUERIES,
            "results_path": str(validator.results_dir)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при выполнении валидации: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    return {"status": "ok"}