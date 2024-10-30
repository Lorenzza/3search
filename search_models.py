from pydantic import BaseModel, Field
from typing import List, Dict, Literal
from enum import Enum

class SearchMethod(str, Enum):
    FULLTEXT = 'полнотекстовый'
    VECTOR = 'векторный'
    HYBRID = 'гибридный'

class SearchRequest(BaseModel):
    query: str = Field(..., description="Поисковый запрос")
    k: int = Field(default=10, ge=1, le=100, description="Количество результатов")
    method: SearchMethod = Field(..., description="Метод поиска")

class SearchResult(BaseModel):
    movie_id: str
    content: str
    relevance_score: float
    rank: int

class RankingMetrics(BaseModel):
    map_score: float
    ndcg_score: float
    mrr_score: float
    rprec_score: float
    precision_at_k: float
    recall_at_k: float

class ConfidenceMetrics(BaseModel):
    mean_relevance: float
    relevance_distribution: Dict[str, float]  # Гистограмма распределения
    calibration_score: float

class PerformanceMetrics(BaseModel):
    latency: float  # время выполнения в секундах

class SearchResponse(BaseModel):
    results: List[SearchResult]
    ranking_metrics: RankingMetrics
    confidence_metrics: ConfidenceMetrics
    performance_metrics: PerformanceMetrics