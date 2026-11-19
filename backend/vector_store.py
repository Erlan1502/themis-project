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
from backend.database import resolve_topic_id

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

    def get_config(self) -> Dict[str, Any]:
        return {"model_name": self.model_name}

    def warmup(self):
        """Прогревает модель эмбеддингов BGE-M3 в памяти."""
        try:
            m = self._get_model()
            if m is not None:
                m.encode(["Themis BGE-M3 warmup probe"], normalize_embeddings=True)
                logger.info("Модель BAAI/bge-m3 успешно прогрета.")
        except Exception as e:
            logger.warning(f"Ошибка при прогреве BAAI/bge-m3: {e}")

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Загрузка модели эмбеддингов {self.model_name}...")
                self._model = SentenceTransformer(self.model_name)
                self._model.max_seq_length = 512
                logger.info(f"Модель {self.model_name} успешно загружена (max_seq_length=512).")
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

    def warmup(self):
        """
        Прогрев модели эмбеддингов BAAI/bge-m3 и HNSW-индекса в памяти.
        Вызывается при старте бэкенда для исключения задержек на первом запросе студента.
        """
        try:
            logger.info("Начало прогрева ThemisVectorStore...")
            self.embedding_fn.warmup()
            _ = self.collection.count()
            logger.info("Прогрев ThemisVectorStore успешно завершен.")
        except Exception as e:
            logger.warning(f"Ошибка при прогреве ThemisVectorStore: {e}")

    def add_slides(
        self,
        topic_id: str,
        week_number: int,
        slides_data: List[Dict[str, Any]],
        course_id: str = "prog_ai_2026"
    ) -> int:
        """
        Индексирует слайды презентации в HNSW граф.
        Каждый чанк содержит текст слайда, номер, заголовок и метаданные курса и темы.
        """
        if not slides_data:
            return 0

        resolved_topic = resolve_topic_id(topic_id)
        ids = []
        documents = []
        metadatas = []

        for slide in slides_data:
            slide_no = slide.get("slide_number", 1)
            chunk_id = f"{course_id}_{resolved_topic}_slide_{slide_no}"
            
            # Формируем семантический текст для векторного поиска
            text = f"Слайд {slide_no}: {slide.get('title', '')}\n{slide.get('text', '')}"
            if slide.get("concepts"):
                text += f"\nКлючевые концепты: {', '.join(slide['concepts'])}"

            ids.append(chunk_id)
            documents.append(text)
            metadatas.append({
                "course_id": course_id,
                "topic_id": resolved_topic,
                "week_number": week_number,
                "slide_number": slide_no,
                "title": slide.get("title", ""),
                "has_code": 1 if slide.get("has_code") else 0,
            })

        # Добавляем или обновляем в ChromaDB батчами по 100 чанков
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.upsert(
                ids=ids[i:i+batch_size],
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size]
            )
        logger.info(f"Проиндексировано {len(ids)} слайдов для курса {course_id}, темы {resolved_topic}")
        return len(ids)

    def search_relevant_slides(
        self,
        query: str,
        topic_id: Optional[str] = None,
        course_id: Optional[str] = None,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Поиск наиболее релевантных слайдов лекции по HNSW индексу
        с фильтрацией по курсу и теме.
        """
        try:
            resolved_topic = resolve_topic_id(topic_id) if topic_id else None
            conditions = []
            if course_id:
                conditions.append({"course_id": course_id})
            if resolved_topic:
                conditions.append({"topic_id": resolved_topic})

            if len(conditions) > 1:
                where_filter = {"$and": conditions}
            elif len(conditions) == 1:
                where_filter = conditions[0]
            else:
                where_filter = None

            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter
            )

            # Fallback: если при поиске с course_id ничего не найдено (старый индекс без course_id в метаданных)
            if (not results or not results["documents"] or not results["documents"][0]) and course_id and resolved_topic:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=top_k,
                    where={"topic_id": resolved_topic}
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

    def get_topic_slides_count(self, topic_id: str, course_id: Optional[str] = None) -> int:
        """Возвращает количество проиндексированных слайдов по теме."""
        try:
            resolved = resolve_topic_id(topic_id)
            if course_id:
                res = self.collection.get(where={"$and": [{"course_id": course_id}, {"topic_id": resolved}]})
            else:
                res = self.collection.get(where={"topic_id": resolved})
            return len(res["ids"]) if res and "ids" in res else 0
        except Exception:
            return 0

    def delete_topic_slides(self, topic_id: str, course_id: Optional[str] = None) -> int:
        """Удаляет чанки только для указанной темы (и курса при наличии)."""
        try:
            resolved = resolve_topic_id(topic_id)
            if course_id:
                where_cond = {"$and": [{"course_id": course_id}, {"topic_id": resolved}]}
            else:
                where_cond = {"topic_id": resolved}
            res = self.collection.get(where=where_cond)
            if res and res.get("ids"):
                self.collection.delete(ids=res["ids"])
                return len(res["ids"])
        except Exception as e:
            logger.warning(f"Ошибка при удалении чанков темы {topic_id}: {e}")
        return 0


# Синглтон векторного хранилища
vector_store = ThemisVectorStore()

