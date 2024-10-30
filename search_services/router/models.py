from pydantic import BaseModel, Field, validator
from typing import List, Dict, Union
from enum import IntEnum

class SearchMethod(IntEnum):
    FULLTEXT = 1
    VECTOR = 2
    HYBRID = 3

class RouterRequest(BaseModel):
    query: str = Field(..., description="Поисковый запрос")
    top_k: int = Field(..., ge=3, le=21, description="Количество результатов")
    method: SearchMethod = Field(..., description="Метод поиска: 1-полнотекстовый, 2-векторный, 3-гибридный")

class SearchResult(BaseModel):
    movie_id: str
    score: float
    content: str
    source: str = Field(description="Источник результата: fulltext/vector/hybrid")

class RouterResponse(BaseModel):
    results: List[SearchResult]
    metrics: Dict[str, Union[float, int, str]]