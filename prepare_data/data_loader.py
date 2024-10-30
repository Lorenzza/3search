import os
import pickle
from pathlib import Path

def load_index_and_documents():
    """Загрузка индекса и документов"""
    # Определение путей к файлам
    data_dir = Path("D:/_DS/test_q/transneft/data")
    index_path = data_dir / "vector_index.pkl"
    documents_path = data_dir / "documents.pkl"

    if not index_path.exists():
        raise FileNotFoundError(f"Индекс не найден: {index_path}")
    if not documents_path.exists():
        raise FileNotFoundError(f"Документы не найдены: {documents_path}")

    # Загрузка индекса FAISS
    with open(index_path, "rb") as f:
        index = pickle.load(f)

    # Загрузка документов
    with open(documents_path, "rb") as f:
        documents = pickle.load(f)

    return index, documents