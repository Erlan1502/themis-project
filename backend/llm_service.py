"""
llm_service.py

Сервис интеграции с языковыми моделями:
- Google Gemini API (LLM_MODE="gemini") через официальный OpenAI-совместимый эндпоинт
- Семейство Qwen3.5 (LLM_MODE="local_qwen" / "cloud")
- Детерминированный Demo Mock Fallback (LLM_MODE="mock") для автономной демонстрации всех 10 недель.
"""

from typing import List, Dict, Any, Optional, AsyncIterator
import json
import re
import asyncio
import logging
import time
from openai import AsyncOpenAI

from backend.config import settings
from backend.models_schemas import (
    TurnSOLOProbabilities,
    AuditExtractionResult,
)
from backend.rag_service import rag_service
from backend.database import resolve_topic_id, get_course

logger = logging.getLogger("themis.llm")


class LLMService:
    def __init__(self):
        self.mode = settings.LLM_MODE
        self.client: Optional[AsyncOpenAI] = None
        self._client_loop = None
        self._circuit_breaker_until: float = 0.0
        self._init_client()

    def is_circuit_open(self) -> bool:
        """Проверяет, активен ли предохранитель (Circuit Breaker) после сбоя API."""
        return time.time() < self._circuit_breaker_until

    def trip_circuit(self, duration: float = 60.0):
        """Активирует Circuit Breaker на duration секунд."""
        self._circuit_breaker_until = time.time() + duration
        logger.warning(f"Circuit breaker tripped for {duration} seconds (until {self._circuit_breaker_until})")

    def reset_circuit(self):
        """Сбрасывает Circuit Breaker."""
        self._circuit_breaker_until = 0.0

    def _resolve_course_name(self, topic_id: str, course_name: Optional[str] = None) -> str:
        """Определяет актуальное название курса для системного промпта."""
        if course_name:
            return course_name
        try:
            topic_data = rag_service.get_topic_data(topic_id)
            course_id = topic_data.get("course_id") if topic_data else "prog_ai_2026"
            c_info = get_course(course_id or "prog_ai_2026")
            if c_info and c_info.get("title"):
                return c_info["title"]
        except Exception:
            pass
        return "Программирование для ИИ"

    def _init_client(self):
        # 1. Режим Google Gemini
        if self.mode == "gemini":
            key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""
            if key and key != "YOUR_GEMINI_API_KEY_HERE":
                try:
                    self.client = AsyncOpenAI(
                        base_url=settings.GEMINI_BASE_URL,
                        api_key=key,
                        timeout=15.0,
                        max_retries=0,
                    )
                    self.dialog_model = settings.GEMINI_MODEL
                    self.audit_model = settings.GEMINI_MODEL
                    logger.info(f"Initialized Google Gemini LLM client with model: {self.dialog_model}")
                except Exception as e:
                    logger.warning(f"Failed to initialize Gemini client: {e}. Falling back to mock mode.")
                    self.client = None
            else:
                logger.info("GEMINI_API_KEY is not set or placeholder. Running in deterministic mock mode.")
                self.client = None

        # 2. Режим локальной Qwen3.5 или стороннего OpenAI-провайдера
        elif self.mode in ("local_qwen", "cloud"):
            try:
                self.client = AsyncOpenAI(
                    base_url=settings.QWEN_BASE_URL,
                    api_key=settings.QWEN_API_KEY,
                    timeout=15.0,
                    max_retries=0,
                )
                self.dialog_model = settings.QWEN_DIALOG_MODEL
                self.audit_model = settings.QWEN_AUDIT_MODEL
            except Exception as e:
                logger.warning(f"Failed to initialize Qwen client: {e}. Falling back to mock.")
                self.client = None

        # 3. Детерминированный mock
        else:
            self.client = None

    def get_client(self) -> Optional[AsyncOpenAI]:
        if self.mode == "mock":
            return None
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if self._client_loop != loop or self.client is None:
            self._init_client()
            self._client_loop = loop
        return self.client

    async def generate_socratic_reply(
        self,
        topic_id: str,
        turn_number: int,
        student_message: str,
        history: List[Dict[str, str]],
        course_name: Optional[str] = None,
    ) -> str:
        """Генерация сократической реплики (Слой 2)."""
        client = self.get_client()
        if self.mode == "mock" or client is None or self.is_circuit_open():
            if self.is_circuit_open():
                logger.warning("Circuit breaker active, using fallback")
            return self._mock_socratic_reply(topic_id, turn_number, student_message)

        try:
            grounding_chunks = await rag_service.retrieve_chunks_async(student_message, topic_id)
            context_str = "\n\n".join([f"[{c['title']}]: {c['content']}" for c in grounding_chunks])
            effective_course = self._resolve_course_name(topic_id, course_name)

            system_prompt = (
                f"Ты — сократический ИИ-тьютор Themis Project для курса '{effective_course}' (Astana IT University). "
                "Твоя задача — не давать студенту готовых ответов, а задавать наводящие вопросы, углубляя его понимание "
                "по таксономии SOLO:\n"
                "- Шаг 1 -> выявление механизмов и причинных связей (Relational, SOLO 2);\n"
                "- Шаг 2 -> анализ компромиссов, ограничений и границ применимости (Extended Abstract, SOLO 3);\n"
                "- Шаг 3 -> стимулирование самостоятельной формулировки гипотезы или обобщения.\n"
                "Отвечай кратко, доброжелательно и по-делу (до 3-4 предложений).\n"
                f"КОНТЕКСТ УЧЕБНОЙ НЕДЕЛИ СИЛЛАБУСА:\n{context_str}"
            )

            messages = [{"role": "system", "content": system_prompt}]
            for h in history:
                messages.append(h)
            messages.append({"role": "user", "content": student_message})

            resp = await client.chat.completions.create(
                model=self.dialog_model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
                timeout=10.0,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            self.trip_circuit(60.0)
            logger.error(f"Error calling live LLM dialog service: {e}. Circuit breaker tripped. Falling back to mock.")
            return self._mock_socratic_reply(topic_id, turn_number, student_message)

    async def generate_socratic_reply_stream(
        self,
        topic_id: str,
        turn_number: int,
        student_message: str,
        history: List[Dict[str, str]],
        course_name: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Потоковая генерация сократической реплики (Слой 2).
        Поддерживает SSE-стриминг токенов как в реальном режиме (Gemini/OpenAI stream=True),
        так и в автономном mock-режиме (потоковая выдача детерминированных слов).
        """
        client = self.get_client()
        if self.mode == "mock" or client is None or self.is_circuit_open():
            if self.is_circuit_open():
                logger.warning("Circuit breaker active, using fallback")
            async for chunk in self._mock_socratic_reply_stream(topic_id, turn_number, student_message):
                yield chunk
            return

        yielded_chars: int = 0
        try:
            grounding_chunks = await rag_service.retrieve_chunks_async(student_message, topic_id)
            context_str = "\n\n".join([f"[{c['title']}]: {c['content']}" for c in grounding_chunks])
            effective_course = self._resolve_course_name(topic_id, course_name)

            system_prompt = (
                f"Ты — сократический ИИ-тьютор Themis Project для курса '{effective_course}' (Astana IT University). "
                "Твоя задача — не давать студенту готовых ответов, а задавать наводящие вопросы, углубляя его понимание "
                "по таксономии SOLO:\n"
                "- Шаг 1 -> выявление механизмов и причинных связей (Relational, SOLO 2);\n"
                "- Шаг 2 -> анализ компромиссов, ограничений и границ применимости (Extended Abstract, SOLO 3);\n"
                "- Шаг 3 -> стимулирование самостоятельной формулировки гипотезы или обобщения.\n"
                "Отвечай кратко, доброжелательно и по-делу (до 3-4 предложений).\n"
                f"КОНТЕКСТ УЧЕБНОЙ НЕДЕЛИ СИЛЛАБУСА:\n{context_str}"
            )

            messages = [{"role": "system", "content": system_prompt}]
            for h in history:
                messages.append(h)
            messages.append({"role": "user", "content": student_message})

            response_stream = await client.chat.completions.create(
                model=self.dialog_model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
                stream=True,
                timeout=10.0,
            )
            async for chunk in response_stream:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yielded_chars += len(delta)
                        yield delta
        except Exception as e:
            self.trip_circuit(60.0)
            logger.error(f"Error calling live LLM dialog stream service: {e}. Circuit breaker tripped.")
            if yielded_chars == 0:
                logger.info("No tokens yielded yet, falling back to mock stream.")
                async for chunk in self._mock_socratic_reply_stream(topic_id, turn_number, student_message):
                    yield chunk
            else:
                logger.warning(f"Stream interrupted after {yielded_chars} chars. Appending break marker.")
                yield " ... [связь прервана]"

    async def extract_audit_evidence(
        self,
        topic_id: str,
        dialog_turns: List[Dict[str, str]],
        course_name: Optional[str] = None,
    ) -> AuditExtractionResult:
        """Извлечение доказательств аудита по протоколу Evidence-First (Слой 3A)."""
        client = self.get_client()
        if self.mode == "mock" or client is None or self.is_circuit_open():
            if self.is_circuit_open():
                logger.warning("Circuit breaker active, using fallback")
            return self._mock_audit_extraction(topic_id, dialog_turns)

        try:
            glossary = rag_service.get_glossary(topic_id)
            turns_text = "\n".join([
                f"Шаг {i+1} [Студент]: {t.get('student', '')}\n[Тьютор]: {t.get('system', '')}"
                for i, t in enumerate(dialog_turns)
            ])
            effective_course = self._resolve_course_name(topic_id, course_name)

            system_prompt = (
                f"Ты — эксперт психометрического аудита Themis Project по силлабусу '{effective_course}'. "
                "Проанализируй диалог студента по протоколу EVIDENCE-FIRST. "
                "1. Сначала извлеки прямые цитаты студента (student_quotes).\n"
                "2. Выдели освоенные концепты из глоссария темы (mastered_concepts).\n"
                "3. Определи, проявил ли студент исследовательскую инициативу 3-го уровня (socratic_initiative: bool).\n"
                "4. Сформулируй краткое обоснование (pedagogical_justification).\n"
                "5. Только в конце оцени распределение SOLO [p1, p2, p3] для каждого шага диалога.\n"
                "Верни валидный JSON:\n"
                "{\n"
                '  "on_topic": true,\n'
                '  "student_quotes": ["..."],\n'
                '  "mastered_concepts": ["..."],\n'
                '  "socratic_initiative": true,\n'
                '  "pedagogical_justification": "...",\n'
                '  "turns_probabilities": [\n'
                '    {"turn_number": 1, "p1": 0.9, "p2": 0.1, "p3": 0.0},\n'
                '    {"turn_number": 2, "p1": 0.0, "p2": 0.85, "p3": 0.15},\n'
                '    {"turn_number": 3, "p1": 0.0, "p2": 0.05, "p3": 0.95}\n'
                "  ]\n"
                "}\n"
                f"ГЛОССАРИЙ ТЕМЫ: {glossary}"
            )

            resp = await client.chat.completions.create(
                model=self.audit_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"ДИАЛОГ СТУДЕНТА:\n{turns_text}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=3000,
                timeout=15.0,
            )
            content = resp.choices[0].message.content.strip()
            # Извлекаем JSON-объект, отсекая комментарии или markdown-блоки
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                content = json_match.group(0)
            elif content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)
            data = json.loads(content)
            result = AuditExtractionResult.model_validate(data)

            # Детерминированная валидация по глоссарию темы и тексту реплик студента
            from backend.similarity_service import similarity_service
            full_student_text = " ".join([t.get("student", "") for t in dialog_turns])

            verified_concepts = []
            for c in result.mastered_concepts:
                is_in_glossary = any(
                    similarity_service.match_concept(g, c) or similarity_service.match_concept(c, g)
                    for g in glossary
                )
                if is_in_glossary and similarity_service.match_concept(c, full_student_text):
                    verified_concepts.append(c)

            for g in glossary:
                if g not in verified_concepts and similarity_service.match_concept(g, full_student_text):
                    verified_concepts.append(g)

            result.mastered_concepts = verified_concepts[:6]
            return result
        except Exception as e:
            self.trip_circuit(60.0)
            logger.error(f"Error calling live LLM audit extraction: {e}. Circuit breaker tripped. Falling back to mock.")
            return self._mock_audit_extraction(topic_id, dialog_turns)

    # -----------------------------------------------------------------
    # ДЕТЕРМИНИРОВАННЫЙ MOCK-КОНТУР ДЛЯ ДЕМО ВСЕХ 10 НЕДЕЛЬ
    # -----------------------------------------------------------------
    def _mock_socratic_reply(self, topic_id: str, turn_number: int, student_message: str) -> str:
        # Канонический Use Case Недели 9 / topic_05_regularization
        if "topic_05" in topic_id or "week_09" in topic_id:
            if turn_number == 1:
                return (
                    "Отлично подмечено! Ты верно связал ко-адаптацию весов с переобучением. "
                    "А как именно механизм Dropout разрушает эту нежелательную взаимозависимость между нейронами на уровне градиентов?"
                )
            elif turn_number == 2:
                return (
                    "Именно так! Случайное зануление заставляет нейроны обучаться устойчивым признакам без опоры на соседей. "
                    "А теперь подумай: есть ли экстремальный предел у этой техники? "
                    "Что произойдет, если мы выкрутим регуляризацию на максимум, например, выключим 80% нейронов?"
                )
            else:
                return (
                    "Отличная постановка проблемы! Ты затронул фундаментальный компромисс между регуляризацией "
                    "и эффективной емкостью (capacity) сети при p=0.8. Как этот порог зависит от ширины скрытого слоя?"
                )

        # Обобщенный сократический тьютор для остальных недель силлабуса
        topic_info = rag_service.get_topic_data(topic_id)
        topic_title = topic_info["title"] if topic_info else "данной теме"

        if turn_number == 1:
            return (
                f"Интересная мысль по материалу {topic_title}! Ты точно описал базовое явление. "
                "А какой физический или вычислительный механизм лежит в его основе? Попробуй объяснить причинно-следственную связь."
            )
        elif turn_number == 2:
            return (
                "Хорошее углубление в механизмы! Теперь давай посмотрим на границы применимости. "
                "В каких реальных сценариях или при каких экстремальных входных данных этот подход перестанет эффективно работать?"
            )
        else:
            return (
                "Превосходное системное обобщение! Ты связал базовые концепты с архитектурными компромиссами. "
                "Твой ответ полностью охватывает ключевые аспекты темы и передан на аналитический аудит преподавателю."
            )

    async def _mock_socratic_reply_stream(
        self,
        topic_id: str,
        turn_number: int,
        student_message: str
    ) -> AsyncIterator[str]:
        """Потоковая выдача детерминированного сократического ответа частями."""
        reply = self._mock_socratic_reply(topic_id, turn_number, student_message)
        words = reply.split(" ")
        for i, word in enumerate(words):
            chunk = word if i == 0 else " " + word
            yield chunk
            await asyncio.sleep(0.01)

    def _mock_audit_extraction(self, topic_id: str, dialog_turns: List[Dict[str, str]]) -> AuditExtractionResult:
        full_text = " ".join([t.get("student", "") for t in dialog_turns])

        # Канонический Use Case Студента К. (80%, underfitting, емкость) - ТОЛЬКО для Недели 9 / регуляризации
        resolved = resolve_topic_id(topic_id)
        if resolved in ("week_09_deep_learning", "topic_05_regularization") and (
            "80%" in full_text or "underfitting" in full_text.lower() or "емкост" in full_text.lower()
        ):
            extracted_quotes = [t.get("student", "") for t in dialog_turns if t.get("student")]
            if not extracted_quotes:
                extracted_quotes = [
                    "Переобучение происходит, когда веса подстраиваются под шум выборки, создавая избыточную ко-адаптацию (co-adaptation) нейронов.",
                    "Dropout случайным образом обнуляет активации с вероятностью p, обеспечивая регуляризацию.",
                    "Если Dropout так эффективен, почему бы нам не выключать 80% нейронов для максимальной регуляризации? "
                    "В какой момент этот компромисс (dropout rate trade-off) сломает обучение и вызовет потерю емкости сети (model capacity, underfitting)?",
                ]
            return AuditExtractionResult(
                on_topic=True,
                student_quotes=extracted_quotes,
                mastered_concepts=[
                    "co-adaptation",
                    "model capacity",
                    "dropout rate trade-off",
                    "underfitting",
                ],
                socratic_initiative=True,
                pedagogical_justification=(
                    "Студент самостоятельно исследовал поведение гиперпараметра на экстремальных границах, "
                    "связав регуляризацию с потерей емкости сети (underfitting) и шириной слоя."
                ),
                turns_probabilities=[
                    TurnSOLOProbabilities(turn_number=1, p1=0.90, p2=0.10, p3=0.00),
                    TurnSOLOProbabilities(turn_number=2, p1=0.00, p2=0.85, p3=0.15),
                    TurnSOLOProbabilities(turn_number=3, p1=0.00, p2=0.05, p3=0.95),
                ],
            )

        # Адаптивное детерминированное извлечение для других недель силлабуса:
        # Извлекаем ТОЛЬКО термины, реально упомянутые студентом. Никакой фейковой подстановки glossary[:3]!
        glossary = rag_service.get_glossary(topic_id)
        quotes = [t.get("student", "") for t in dialog_turns if t.get("student")]
        from backend.similarity_service import similarity_service
        found_concepts = [
            c for c in glossary
            if similarity_service.match_concept(c, full_text)
        ][:6]

        has_substance = len(found_concepts) > 0 or len(full_text.split()) >= 15

        return AuditExtractionResult(
            on_topic=has_substance,
            student_quotes=quotes,
            mastered_concepts=found_concepts,
            socratic_initiative=len(dialog_turns) >= 3 and len(found_concepts) >= 2,
            pedagogical_justification=(
                f"Студент продемонстрировал владение понятиями темы ({topic_id}): {', '.join(found_concepts)}."
                if found_concepts
                else f"Студент завершил сессию по теме ({topic_id}), специфические термины глоссария не зафиксированы."
            ),
            turns_probabilities=[
                TurnSOLOProbabilities(turn_number=1, p1=0.75, p2=0.25, p3=0.00),
                TurnSOLOProbabilities(turn_number=2, p1=0.10, p2=0.70, p3=0.20),
                TurnSOLOProbabilities(turn_number=3, p1=0.05, p2=0.25, p3=0.70),
            ],
        )


llm_service = LLMService()
