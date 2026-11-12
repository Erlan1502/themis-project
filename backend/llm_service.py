"""
llm_service.py

Сервис интеграции с языковыми моделями семейства Qwen3.5:
- Слой 2 (Интерактивный сократический диалог): Qwen/Qwen3.5-4B
- Слой 3A (Evidence-First структурированная экстракция): Qwen/Qwen3.5-27B / 9B
- Детерминированный Demo Mock Fallback (LLM_MODE="mock") для автономной демонстрации.
"""

from typing import List, Dict, Any, Optional
import json
import logging
from openai import AsyncOpenAI

from backend.config import settings
from backend.models_schemas import (
    TurnSOLOProbabilities,
    AuditExtractionResult,
)
from backend.rag_service import rag_service

logger = logging.getLogger("themis.llm")


class LLMService:
    def __init__(self):
        self.mode = settings.LLM_MODE
        self.dialog_model = settings.QWEN_DIALOG_MODEL
        self.audit_model = settings.QWEN_AUDIT_MODEL

        # Инициализируем клиент OpenAI, если режим не mock
        self.client: Optional[AsyncOpenAI] = None
        if self.mode != "mock":
            try:
                self.client = AsyncOpenAI(
                    base_url=settings.QWEN_BASE_URL,
                    api_key=settings.QWEN_API_KEY,
                    timeout=30.0,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize AsyncOpenAI client: {e}. Falling back to mock.")
                self.mode = "mock"

    async def generate_socratic_reply(
        self,
        topic_id: str,
        turn_number: int,
        student_message: str,
        history: List[Dict[str, str]],
    ) -> str:
        """Генерация сократической реплики (Слой 2)."""
        # Если включен режим mock или если студент передает канонические фразы Студента К.
        if self.mode == "mock" or self.client is None:
            return self._mock_socratic_reply(turn_number, student_message)

        try:
            grounding_chunks = rag_service.retrieve_chunks(student_message, topic_id)
            context_str = "\n\n".join([f"[{c['title']}]: {c['content']}" for c in grounding_chunks])

            system_prompt = (
                "Ты — сократический ИИ-тьютор Themis Project по теме лекции. "
                "Твоя задача — не давать готовых ответов, а направлять студента к более глубокому уровню таксономии SOLO: "
                "Шаг 1 -> выявление механизмов (Relational); "
                "Шаг 2 -> анализ компромиссов и границ (Extended Abstract); "
                "Шаг 3 -> подведение итогов исследования.\n"
                f"КОНТЕКСТ ЗАНЯТИЯ:\n{context_str}"
            )

            messages = [{"role": "system", "content": system_prompt}]
            for h in history:
                messages.append(h)
            messages.append({"role": "user", "content": student_message})

            resp = await self.client.chat.completions.create(
                model=self.dialog_model,
                messages=messages,
                temperature=0.7,
                max_tokens=256,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error calling real LLM dialog service: {e}. Falling back to mock.")
            return self._mock_socratic_reply(turn_number, student_message)

    async def extract_audit_evidence(
        self,
        topic_id: str,
        dialog_turns: List[Dict[str, str]],
    ) -> AuditExtractionResult:
        """Извлечение доказательств аудита по протоколу Evidence-First (Слой 3A)."""
        if self.mode == "mock" or self.client is None:
            return self._mock_audit_extraction(dialog_turns)

        try:
            glossary = rag_service.get_glossary(topic_id)
            turns_text = "\n".join([
                f"Шаг {i+1} [Студент]: {t.get('student', '')}\n[Тьютор]: {t.get('system', '')}"
                for i, t in enumerate(dialog_turns)
            ])

            system_prompt = (
                "Ты — эксперт психометрического аудита Themis Project. Проанализируй сократический диалог студента. "
                "Используй протокол EVIDENCE-FIRST: сначала выдели прямые цитаты и концепты из глоссария, "
                "затем проверь наличие исследовательской инициативы 3-го уровня, сформулируй обоснование, "
                "и в конце определи пошаговые вероятности SOLO [p1, p2, p3]. "
                "Верни валидный JSON в строгом соответствии со схемой:\n"
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
                f"ДОПУСТИМЫЕ КОНЦЕПТЫ ГЛОССАРИЯ: {glossary}"
            )

            resp = await self.client.chat.completions.create(
                model=self.audit_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"ДИАЛОГ СТУДЕНТА:\n{turns_text}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1000,
            )
            content = resp.choices[0].message.content
            data = json.loads(content)
            return AuditExtractionResult.model_validate(data)
        except Exception as e:
            logger.error(f"Error calling real LLM audit extraction: {e}. Falling back to mock.")
            return self._mock_audit_extraction(dialog_turns)

    # -----------------------------------------------------------------
    # ДЕТЕРМИНИРОВАННЫЙ MOCK-КОНТУР ДЛЯ ДЕМО И IT FEST
    # -----------------------------------------------------------------
    def _mock_socratic_reply(self, turn_number: int, student_message: str) -> str:
        msg_lower = student_message.lower()

        # Реплика на шаге 1
        if turn_number == 1:
            return (
                "Отлично подмечено! Ты верно связал ко-адаптацию весов с переобучением. "
                "А как именно механизм Dropout разрушает эту нежелательную взаимозависимость между нейронами на уровне градиентов?"
            )
        # Реплика на шаге 2
        elif turn_number == 2:
            return (
                "Именно так! Случайное зануление заставляет нейроны обучаться устойчивым признакам без опоры на соседей. "
                "А теперь подумай: есть ли экстремальный предел у этой техники? "
                "Что произойдет, если мы выкрутим регуляризацию на максимум, например, выключим 80% нейронов?"
            )
        # Реплика на шаге 3 (Use Case Студента К.)
        else:
            return (
                "Отличная постановка проблемы! Ты затронул фундаментальный компромисс между регуляризацией "
                "и эффективной емкостью (capacity) сети при p=0.8. Как этот порог зависит от ширины скрытого слоя?"
            )

    def _mock_audit_extraction(self, dialog_turns: List[Dict[str, str]]) -> AuditExtractionResult:
        """Формирует каноническую экстракцию для Студента К. или адаптивную для прочих сообщений."""
        full_text = " ".join([t.get("student", "") for t in dialog_turns])

        # Если в диалоге присутствуют ключевые фразы Студента К. (80%, underfitting, емкость)
        if "80%" in full_text or "underfitting" in full_text.lower() or "емкост" in full_text.lower():
            return AuditExtractionResult(
                on_topic=True,
                student_quotes=[
                    "Если Dropout так эффективен, почему бы нам не выключать 80% нейронов для максимальной регуляризации? "
                    "В какой момент это сломает обучение и вызовет потерю емкости сети (underfitting)?"
                ],
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

        # Общий реалистичный mock для произвольного диалога
        return AuditExtractionResult(
            on_topic=True,
            student_quotes=[t.get("student", "") for t in dialog_turns if t.get("student")],
            mastered_concepts=["dropout", "regularization", "co-adaptation"],
            socratic_initiative=False,
            pedagogical_justification="Студент уверенно ответил на вопросы по механизму Dropout и ко-адаптации весов.",
            turns_probabilities=[
                TurnSOLOProbabilities(turn_number=1, p1=0.8, p2=0.2, p3=0.0),
                TurnSOLOProbabilities(turn_number=2, p1=0.1, p2=0.7, p3=0.2),
                TurnSOLOProbabilities(turn_number=3, p1=0.1, p2=0.3, p3=0.6),
            ],
        )


llm_service = LLMService()

