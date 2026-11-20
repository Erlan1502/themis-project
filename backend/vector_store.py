"""
vector_store.py

Векторное хранилище Themis Project на базе ChromaDB с HNSW-индексацией.
Обеспечивает семантический поиск по слайдам лекций и конспектам (Dense Retrieval)
с использованием мультиязычной модели эмбеддингов BAAI/bge-m3.
"""

import os
import math
import hashlib
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
    Поддерживает локальный кэш и детерминированный 1024-мерный оффлайн хэш-эмбеддер.
    """
    def __init__(self, model_name: str = "BAAI/bge-m3"):
        self.model_name = model_name
        self.dimension: int = 1024
        self.is_degraded: bool = False
        self._model = None

    def name(self) -> str:
        return "bge_m3_embedding_function"

    def get_config(self) -> Dict[str, Any]:
        return {"model_name": self.model_name}

    def get_status(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "is_degraded": self.is_degraded,
            "model": self.model_name if not self.is_degraded else "offline_hash_1024",
        }

    def warmup(self):
        """Прогревает модель эмбеддингов BGE-M3 в памяти."""
        try:
            m = self._get_model()
            if m is not None:
                m.encode(["Themis BGE-M3 warmup probe"], normalize_embeddings=True)
                logger.info("Модель BAAI/bge-m3 успешно прогрета.")
            else:
                logger.info("BgeM3EmbeddingFunction работает в деградированном оффлайн-режиме (1024-dim hash).")
        except Exception as e:
            logger.warning(f"Ошибка при прогреве BAAI/bge-m3: {e}")
            self._model = None
            self.is_degraded = True

    def _get_model(self):
        if self._model is None and not self.is_degraded:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Загрузка модели эмбеддингов {self.model_name}...")
                self._model = SentenceTransformer(self.model_name)
                self._model.max_seq_length = 512
                self.is_degraded = False
                logger.info(f"Модель {self.model_name} успешно загружена (max_seq_length=512).")
            except Exception as e:
                logger.warning(
                    f"Не удалось загрузить {self.model_name} из сети: {e}. "
                    "Попытка загрузки из локального дискового кэша..."
                )
                try:
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer(self.model_name, local_files_only=True)
                    self._model.max_seq_length = 512
                    self.is_degraded = False
                    logger.info(f"Модель {self.model_name} успешно загружена из локального кэша.")
                except Exception as ex_cache:
                    logger.error(
                        f"Не удалось загрузить {self.model_name} из локального кэша: {ex_cache}. "
                        "Переключение в деградированный оффлайн-режим (1024-dim hash)."
                    )
                    self._model = None
                    self.is_degraded = True
        return self._model

    def __call__(self, input: Documents) -> Embeddings:
        model = self._get_model()
        if model is None or self.is_degraded:
            # Детерминированный оффлайн хэш-эмбеддер строго размерности 1024 с L2-нормализацией
            vectors: Embeddings = []
            for text in input:
                vec = [0.0] * 1024
                tokens = text.lower().split()[:1024]
                for i, token in enumerate(tokens):
                    h = int(hashlib.md5(token.encode("utf-8")).hexdigest()[:6], 16)
                    vec[i % 1024] += (h % 100) / 100.0
                norm = math.sqrt(sum(x * x for x in vec))
                if norm > 0.0:
                    vec = [x / norm for x in vec]
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

    @property
    def is_degraded(self) -> bool:
        return self.embedding_fn.is_degraded

    @property
    def dimension(self) -> int:
        return 1024

    def get_status(self) -> Dict[str, Any]:
        return self.embedding_fn.get_status()

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

    def delete_topic_chunks(self, topic_id: str, course_id: str = "prog_ai_2026") -> int:
        """
        Селективное удаление старых чанков только этой пары (course_id, topic_id)
        перед повторной или инкрементальной индексацией.
        """
        try:
            resolved = resolve_topic_id(topic_id)
            self.collection.delete(where={"$and": [{"course_id": course_id}, {"topic_id": resolved}]})
            logger.info(f"Селективно удалены старые чанки для ({course_id}, {resolved})")
            return 1
        except Exception as e:
            logger.debug(f"Удаление старых чанков ({course_id}, {topic_id}): {e}")
            return 0

    def add_slides(
        self,
        topic_id: str,
        week_number: int,
        slides_data: List[Dict[str, Any]],
        course_id: str = "prog_ai_2026",
        delete_old: bool = False
    ) -> int:
        """
        Индексирует слайды презентации или чанки Markdown в HNSW граф ChromaDB.
        Каждый чанк содержит семантический текст (с breadcrumbs), заголовок и метаданные курса и темы.
        """
        if not slides_data:
            return 0

        resolved_topic = resolve_topic_id(topic_id)

        # Проверка и ленивая инициализация эмбеддера
        if self.embedding_fn._model is None and not self.embedding_fn.is_degraded:
            self.embedding_fn._get_model()

        if self.is_degraded:
            logger.warning(
                f"Векторное хранилище работает в деградированном режиме (offline hash 1024). "
                f"Индексация слайдов для курса '{course_id}', темы '{resolved_topic}' отклонена "
                f"во избежание порчи HNSW-индекса."
            )
            return 0

        try:
            if delete_old:
                self.delete_topic_chunks(topic_id=resolved_topic, course_id=course_id)

            ids = []
            documents = []
            metadatas = []

            for idx, slide in enumerate(slides_data, start=1):
                slide_no = slide.get("slide_number", idx)
                chunk_id = slide.get("chunk_id") or f"{course_id}_{resolved_topic}_slide_{slide_no}"
                
                # Если текст уже содержит разметку и хлебные крошки от Smart Chunker
                if "text" in slide and slide["text"]:
                    text = slide["text"]
                else:
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
                    "has_table": 1 if slide.get("has_table") else 0,
                    "has_math": 1 if slide.get("has_math") else 0,
                })

            # Добавляем или обновляем в ChromaDB батчами по 100 чанков
            batch_size = 100
            for i in range(0, len(ids), batch_size):
                self.collection.upsert(
                    ids=ids[i:i+batch_size],
                    documents=documents[i:i+batch_size],
                    metadatas=metadatas[i:i+batch_size]
                )
            logger.info(f"Проиндексировано {len(ids)} чанков для курса {course_id}, темы {resolved_topic}")
            return len(ids)
        except Exception as e:
            logger.error(f"Ошибка при индексации слайдов ({course_id}, {resolved_topic}): {e}")
            return 0

    def add_chunks(
        self,
        topic_id: str,
        week_number: int,
        chunks_data: List[Dict[str, Any]],
        course_id: str = "prog_ai_2026",
        delete_old: bool = True
    ) -> int:
        """Прямой алиас для селективного добавления семантических чанков."""
        return self.add_slides(
            topic_id=topic_id,
            week_number=week_number,
            slides_data=chunks_data,
            course_id=course_id,
            delete_old=delete_old
        )

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

