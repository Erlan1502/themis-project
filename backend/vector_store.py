"""
vector_store.py

Векторное хранилище Themis Project на базе ChromaDB с HNSW-индексацией.
Обеспечивает семантический поиск по слайдам лекций и конспектам (Dense Retrieval)
с использованием мультиязычной модели эмбеддингов BAAI/bge-m3.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger("themis.vector_store")

CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_db")
os.makedirs(CHROMA_DIR, exist_ok=True)


class BgeM3EmbeddingFunction(EmbeddingFunction[Documents]):
    """
    Класс генерации эмбеддингов BAAI/bge-m3 для ChromaDB.
    Использует sentence-transformers с ленивой загрузкой весов на CPU/GPU.
    """
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        self.model_name = model_name
        self._model = None

    def name(self) -> str:
        return "bge_m3_embedding_function"

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Загрузка модели эмбеддингов {self.model_name}...")
                self._model = SentenceTransformer(self.model_name)
                logger.info(f"Модель {self.model_name} успешно загружена.")
            except Exception as e:
                logger.warning(f"Не удалось загрузить {self.model_name}: {e}. Переключение на легкую модель cointegrated/rubert-tiny2")
                try:
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer("cointegrated/rubert-tiny2")
                except Exception as ex2:
                    logger.error(f"Ошибка загрузки запасной модели: {ex2}")
                    self._model = None
        return self._model

    def __call__(self, input: Documents) -> Embeddings:
        model = self._get_model()
        if model is None:
            # Fallback к базовому хэш-вектору фиксированной размерности (если сеть недоступна)
            import hashlib
            vectors = []
            for text in input:
                vec = [0.0] * 384
                for i, token in enumerate(text.lower().split()[:384]):
                    h = int(hashlib.md5(token.encode("utf-8")).hexdigest()[:6], 16)
                    vec[i % 384] += (h % 100) / 100.0
                vectors.append(vec)
            return vectors

        embeddings = model.encode(input, normalize_embeddings=True)
        return embeddings.tolist()


class ThemisVectorStore:
    def __init__(self, persist_directory: str = CHROMA_DIR):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.embedding_fn = BgeM3EmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="themis_lecture_slides",
            metadata={"hnsw:space": "cosine"},
            embedding_function=self.embedding_fn
        )
        logger.info(f"Инициализирована коллекция ChromaDB: themis_lecture_slides (HNSW cosine)")

    def add_slides(
        self,
        topic_id: str,
        week_number: int,
        slides_data: List[Dict[str, Any]]
    ) -> int:
        """
        Индексирует слайды презентации в HNSW граф.
        Каждый чанк содержит текст слайда, номер, заголовок и метаданные темы.
        """
        if not slides_data:
            return 0

        ids = []
        documents = []
        metadatas = []

        for slide in slides_data:
            slide_no = slide.get("slide_number", 1)
            chunk_id = f"{topic_id}_slide_{slide_no}"
            
            # Формируем семантический текст для векторного поиска
            text = f"Слайд {slide_no}: {slide.get('title', '')}\n{slide.get('text', '')}"
            if slide.get("concepts"):
                text += f"\nКлючевые концепты: {', '.join(slide['concepts'])}"

            ids.append(chunk_id)
            documents.append(text)
            metadatas.append({
                "topic_id": topic_id,
                "week_number": week_number,
                "slide_number": slide_no,
                "title": slide.get("title", ""),
                "has_code": 1 if slide.get("has_code") else 0,
            })

        # Добавляем или обновляем в ChromaDB
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        logger.info(f"Проиндексировано {len(ids)} слайдов для темы {topic_id}")
        return len(ids)

    def search_relevant_slides(
        self,
        query: str,
        topic_id: Optional[str] = None,
        top_k: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Поиск наиболее релевантных слайдов лекции по HNSW индексу.
        """
        try:
            where_filter = {"topic_id": topic_id} if topic_id else None
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter
            )

            slides = []
            if results and results["documents"] and results["documents"][0]:
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0]
                ):
                    similarity = 1.0 - dist if dist is not None else 1.0
                    slides.append({
                        "text": doc,
                        "metadata": meta,
                        "similarity": round(similarity, 3)
                    })
            return slides
        except Exception as e:
            logger.error(f"Ошибка поиска в HNSW индексе: {e}")
            return []

    def get_topic_slides_count(self, topic_id: str) -> int:
        """Возвращает количество проиндексированных слайдов по теме."""
        try:
            res = self.collection.get(where={"topic_id": topic_id})
            return len(res["ids"]) if res and "ids" in res else 0
        except Exception:
            return 0


# Синглтон векторного хранилища
vector_store = ThemisVectorStore()

