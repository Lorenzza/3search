from pydantic import BaseModel, Field
from typing import List, Dict

class SearchRequest(BaseModel):
    query: str = Field(..., description="Поисковый запрос")
    top_k: int = Field(default=5, ge=1, le=100, description="Количество результатов")

class SearchResult(BaseModel):
    movie_id: str
    similarity: float
    content: str

class SearchResponse(BaseModel):
    results: List[SearchResult]
    ranking_metrics: Dict[str, float]

    class Config:
        arbitrary_types_allowed = True