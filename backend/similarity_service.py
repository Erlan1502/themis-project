"""
similarity_service.py

Модуль семантического анализа и детекции повторов/перефразирований (Anti-Spam & Repetition Guard).
Предотвращает накрутку баллов и рост уверенности C_sample при повторной отправке
одного и того же вопроса или поверхностном перефразировании без добавления нового когнитивного смысла.
"""

from typing import List, Tuple, Dict, Any
import re
import math


class SemanticSimilarityService:
    def __init__(self, repetition_threshold: float = 0.55):
        self.repetition_threshold = repetition_threshold

    def _stem(self, word: str) -> str:
        """Легковесный стемминг для нормализации русских и английских флексий."""
        w = word.lower().replace("ё", "е")
        if len(w) <= 3:
            return w
        endings = [
            "ейший", "айший", "иями", "ями", "ами", "ьми",
            "ного", "ному", "ными", "ных", "ного", "ному",
            "вать", "ение", "ения", "ению", "ением",
            "ация", "ации", "ацию", "ацией",
            "ным", "ная", "ное", "ные", "ной", "ную", "ных",
            "ого", "ему", "ому", "его", "ыми",
            "ете", "ите", "ешь", "ишь",
            "ет", "ут", "ют", "ит", "ат", "ят", "ло", "ла", "ли", "но",
            "ов", "ев", "ей", "ям", "ам", "ах", "ях", "ую", "юю", "ые", "ой", "ей",
            "а", "е", "и", "й", "о", "у", "ы", "ь", "я", "s", "ed", "ing"
        ]
        for end in endings:
            if w.endswith(end) and len(w) - len(end) >= 3:
                return w[:-len(end)]
        return w

    def _tokenize(self, text: str) -> List[str]:
        """Токенизация и стемминг русских и латинских слов."""
        text_clean = text.lower().replace("ё", "е")
        raw_tokens = re.findall(r"[а-яa-z0-9]{3,}", text_clean)
        # Отсекаем базовые стоп-слова
        stop_words = {
            "что", "как", "это", "для", "или", "если", "при", "где", "чем",
            "так", "все", "она", "оно", "они", "был", "быть", "есть", "нас",
            "вам", "его", "еще", "уже", "без", "под", "над", "про", "тот"
        }
        tokens = [t for t in raw_tokens if t not in stop_words]
        return [self._stem(t) for t in tokens]

    def _char_ngrams(self, text: str, n: int = 3) -> set:
        """Символьные n-граммы для учета опечаток и словоформ (стемминг-эффект)."""
        text_clean = re.sub(r"\s+", " ", text.lower().strip())
        if len(text_clean) < n:
            return {text_clean}
        return {text_clean[i:i+n] for i in range(len(text_clean) - n + 1)}

    def calculate_similarity(self, text_a: str, text_b: str) -> float:
        """
        Гибридное вычисление семантического сходства двух реплик:
        1. Векторное косинусное сходство по лексемам (TF-IDF style).
        2. Коэффициент Жаккара по символьным триграммам (устойчивость к флексиям).
        """
        # Точное или почти точное совпадение
        clean_a = re.sub(r"\s+", " ", text_a.strip().lower())
        clean_b = re.sub(r"\s+", " ", text_b.strip().lower())
        if clean_a == clean_b:
            return 1.0

        tokens_a = self._tokenize(text_a)
        tokens_b = self._tokenize(text_b)

        if not tokens_a or not tokens_b:
            # Сравнение по n-граммам
            ng_a = self._char_ngrams(text_a)
            ng_b = self._char_ngrams(text_b)
            return len(ng_a & ng_b) / max(1, len(ng_a | ng_b))

        # 1. Cosine similarity по токенам
        freq_a: Dict[str, int] = {}
        freq_b: Dict[str, int] = {}
        for t in tokens_a:
            freq_a[t] = freq_a.get(t, 0) + 1
        for t in tokens_b:
            freq_b[t] = freq_b.get(t, 0) + 1

        all_words = set(freq_a.keys()) | set(freq_b.keys())
        dot_product = sum(freq_a.get(w, 0) * freq_b.get(w, 0) for w in all_words)
        norm_a = math.sqrt(sum(v * v for v in freq_a.values()))
        norm_b = math.sqrt(sum(v * v for v in freq_b.values()))
        cosine_sim = dot_product / (norm_a * norm_b) if norm_a * norm_b > 0 else 0.0

        # 2. Jaccard similarity по символьным триграммам
        ng_a = self._char_ngrams(text_a)
        ng_b = self._char_ngrams(text_b)
        jaccard_sim = len(ng_a & ng_b) / max(1, len(ng_a | ng_b))

        # Взвешенное сходство
        combined_sim = 0.65 * cosine_sim + 0.35 * jaccard_sim
        return round(combined_sim, 3)

    def check_repetition(
        self,
        new_message: str,
        previous_messages: List[str]
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Проверяет, является ли новое сообщение повторением или перефразированием
        ранее отправленных сообщений в текущей сессии.
        
        Возвращает: (is_duplicate: bool, max_similarity: float, matched_message: Optional[str])
        """
        if not previous_messages:
            return False, 0.0, None

        max_sim = 0.0
        matched_msg = None

        for prev in previous_messages:
            sim = self.calculate_similarity(new_message, prev)
            if sim > max_sim:
                max_sim = sim
                matched_msg = prev

        is_dup = max_sim >= self.repetition_threshold
        return is_dup, max_sim, matched_msg


similarity_service = SemanticSimilarityService()
