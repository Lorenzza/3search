from sentence_transformers import SentenceTransformer
import numpy as np
from pathlib import Path
from sklearn.preprocessing import normalize
import pickle
import faiss
import argparse
import json
from typing import Dict

class VectorIndexer:
    def __init__(self):
        self.model = None
        self.initialize_model()

    def initialize_model(self):
        """Инициализация модели"""
        try:
            model_name = 'distiluse-base-multilingual-cased-v2'
            print(f"Загрузка модели: {model_name}")
            self.model = SentenceTransformer(model_name)
            print(f"Размерность модели: {self.model.get_sentence_embedding_dimension()}")
        except Exception as e:
            print(f"Ошибка при инициализации модели: {str(e)}")
            raise

    def create_index(self, base_path: str = r"D:\_DS\test_q\transneft\DATA\RAW\dataset") -> Dict:
        """Создание векторного индекса"""
        try:
            base_path = Path(base_path)
            folders = ["neg", "neu", "pos"]
            documents = []
            vectors = []

            print("Начало обработки документов...")
            # Сбор и векторизация документов
            for folder in folders:
                folder_path = base_path / folder
                print(f"Обработка папки: {folder}")
                for file_path in folder_path.glob("*.txt"):
                    with open(file_path, "r", encoding="utf-8") as file:
                        content = file.read()
                        movie_id, review_id = file_path.stem.split('-')
                        documents.append({
                            "movie_id": movie_id,
                            "review_id": review_id,
                            "sentiment": folder,
                            "content": content
                        })
                        vector = self.model.encode([content])[0]
                        vectors.append(vector)

            print("Векторизация завершена")
            
            # Преобразование и нормализация векторов
            vectors = np.array(vectors).astype('float32')
            normalized_vectors = normalize(vectors)
            
            # Создание индекса
            dimension = normalized_vectors.shape[1]
            index = faiss.IndexFlatIP(dimension)
            index.add(normalized_vectors)

            # Сохранение индекса
            output_path = Path("D:/_DS/test_q/transneft/data")
            output_path.mkdir(parents=True, exist_ok=True)
            
            with open(output_path / "vector_index.pkl", "wb") as f:
                pickle.dump(index, f)

            print(f"Индекс сохранен в: {output_path / 'vector_index.pkl'}")

            details = {
                "status": "success",
                "message": "Индекс успешно создан и сохранен",
                "details": {
                    "dimension": dimension,
                    "num_vectors": len(vectors),
                    "index_type": type(index).__name__
                }
            }

            # Сохраняем информацию об индексе
            with open(output_path / "index_info.json", "w", encoding="utf-8") as f:
                json.dump(details, f, ensure_ascii=False, indent=2)

            return details

        except Exception as e:
            print(f"Ошибка при создании индекса: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Создание векторного индекса')
    parser.add_argument(
        '--path', 
        type=str, 
        default=r"D:\_DS\test_q\transneft\DATA\RAW\dataset",
        help='Путь к директории с данными'
    )

    args = parser.parse_args()
    
    try:
        indexer = VectorIndexer()
        result = indexer.create_index(args.path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"Ошибка: {e}")
        exit(1)

if __name__ == "__main__":
    main()