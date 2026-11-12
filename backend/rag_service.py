"""
rag_service.py

Локальный RAG-сервис (Retrieval-Augmented Generation) для системы Themis Project.
Хранит и индексирует контекст силлабуса и конспекта лекции 05:
"Regularization & Dropout Dynamics" (Курс prog_ai_2026).

Обеспечивает контекстное заземление (Grounding) вопросов сократического бота.
"""

from typing import List, Dict, Any, Optional
import math
import re


# База знаний по теме занятия 05
TOPIC_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "topic_05_regularization": {
        "course_id": "prog_ai_2026",
        "topic_name": "Регуляризация и динамика Dropout в глубоких нейросетях",
        "initial_prompt": (
            "Привет! На лекции мы разобрали проблему переобучения в глубоких сетях. "
            "Подумай: почему обычное увеличение объема данных не всегда спасает от ко-адаптации признаков?"
        ),
        "glossary": [
            "overfitting",
            "co-adaptation",
            "dropout",
            "inverted dropout",
            "model capacity",
            "underfitting",
            "weight decay",
            "l2 regularization",
            "batch normalization interaction",
        ],
        "chunks": [
            {
                "id": "chunk_01_coadaptation",
                "title": "Ко-адаптация признаков и переобучение",
                "content": (
                    "В полносвязных глубоких сетях нейроны имеют тенденцию вырабатывать взаимозависимые "
                    "исправления ошибок друг друга. Это явление называется ко-адаптацией (co-adaptation). "
                    "Ко-адаптированные детекторы признаков хорошо работают на обучающей выборке, но теряют "
                    "обобщающую способность на новых данных. Даже при большом объеме данных ко-адаптация "
                    "может сохраняться в высокопараметрических моделях."
                ),
            },
            {
                "id": "chunk_02_dropout_mechanism",
                "title": "Механизм Dropout и масштабирование весов",
                "content": (
                    "Алгоритм Dropout (Srivastava et al., 2014) решает проблему ко-адаптации, "
                    "случайно исключая каждый нейрон скрытого слоя с вероятностью p (обычно 0.2-0.5) "
                    "на каждом шаге градиентного спуска. Это заставляет каждый нейрон обучаться полезным "
                    "признакам в случайных комбинациях с другими. В Inverted Dropout активации делятся на (1 - p) "
                    "во время обучения, чтобы фаза инференса оставалась детерминированной без масштабирования."
                ),
            },
            {
                "id": "chunk_03_capacity_tradeoff",
                "title": "Компромисс емкости сети и экстремальные границы регуляризации",
                "content": (
                    "При слишком сильной регуляризации (например, dropout rate p >= 0.8) эффективная емкость "
                    "сети (model capacity) резко деградирует. Потеря емкости приводит к недообучению (underfitting): "
                    "сеть теряет способность аппроксимировать целевую зависимость. Оптимальный выбор p "
                    "зависит от ширины скрытого слоя и сложности решаемой задачи."
                ),
            },
        ],
    }
}


class RAGService:
    """Сервис поиска и извлечения контекста для сократического бота."""

    def __init__(self):
        self._kb = TOPIC_KNOWLEDGE_BASE

    def get_topic_metadata(self, topic_id: str) -> Optional[Dict[str, Any]]:
        return self._kb.get(topic_id)

    def get_initial_prompt(self, topic_id: str) -> str:
        data = self._kb.get(topic_id)
        if data:
            return data["initial_prompt"]
        return "Привет! Расскажи своими словами ключевые концепты сегодняшней темы лекции."

    def get_glossary(self, topic_id: str) -> List[str]:
        data = self._kb.get(topic_id)
        if data:
            return data["glossary"]
        return []

    def retrieve_chunks(self, query: str, topic_id: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Простой и надежный лексико-семантический поиск чанков (TF-IDF / BM25 style)
        без внешних тяжелых C++ зависимостей.
        """
        topic = self._kb.get(topic_id)
        if not topic:
            return []

        chunks = topic["chunks"]
        query_words = set(re.findall(r"\w+", query.lower()))

        scored_chunks = []
        for chunk in chunks:
            text = (chunk["title"] + " " + chunk["content"]).lower()
            chunk_words = set(re.findall(r"\w+", text))
            intersection = query_words.intersection(chunk_words)
            score = len(intersection) / math.sqrt(max(1, len(chunk_words)))
            scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored_chunks[:top_k]]


# Синглтон сервиса
rag_service = RAGService()

