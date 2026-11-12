"""
seed_data.py

Канонический набор данных для демонстрации Themis Project (v2.0).
Курс: prog_ai_2026 ("Programming AI")
Тема: topic_05_regularization ("Regularization & Dropout Dynamics")

Когорта из 28 студентов:
- 14 студентов со статусом OPTED_OUT (не заходили в бот, очные оценки 78–95 без изменений).
- 2 студента со статусом INCOMPLETE_IGNORED (случайный вход, 1 реплика, Delta_pos = 0.0).
- 12 студентов со статусом COMPLETED (полная сессия из 3 реплик):
    * 9 студентов в зоне NORMAL (Green)
    * 2 студента в зоне WATCHLIST (Yellow)
    * 1 студент в зоне HIGH_DISCREPANCY (Purple) — Студент К. (stud_aai_042)
"""

from typing import List, Dict, Any
from backend.models_schemas import (
    StudentAuditRecord,
    AuditExtractionResult,
    TurnSOLOProbabilities,
)
from backend.math_engine import ThemisMathEngine


def get_canonical_seed_records() -> List[StudentAuditRecord]:
    records: List[StudentAuditRecord] = []

    # 1. Студент К. (stud_aai_042) — главный герой сценария (Use Case)
    extraction_stud_k = AuditExtractionResult(
        on_topic=True,
        student_quotes=[
            "Если Dropout так эффективен, почему бы нам не выключать 80% нейронов для максимальной регуляризации? "
            "В какой момент это сломает обучение и вызовет потерю емкости сети (underfitting)?"
        ],
        mastered_concepts=[
            "co-adaptation",
            "model capacity",
            "dropout rate trade-off",
            "underfitting"
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
        ]
    )

    stud_k = StudentAuditRecord(
        student_id="stud_aai_042",
        in_class_grade=70.0,
        session_status="COMPLETED",
        turns_count=3,
        total_tokens=180,
        extraction=extraction_stud_k,
        telemetry_clean=True,
    )
    # Предварительный расчет глубины
    ThemisMathEngine().compute_individual_depth(stud_k)

    # 2. Остальные 11 завершенных сессий с точными дельтами:
    # deltas: [-3.2, -1.5, -1.3, 0.4, 1.1, 2.0, 3.0, 4.2, 6.3, 11.0, 13.2]
    # При добавлении stud_k (delta = +23.5) медиана массива равна ровно 2.5, а MAD = 3.8.
    other_completed_configs = [
        # (id, in_class, raw_delta, concepts_count, tokens, initiative, quotes, justification)
        ("stud_aai_001", 85.0, -3.2, 3, 160, False, ["Dropout отключает случайные нейроны."], "Базовое понимание Dropout."),
        ("stud_aai_002", 82.0, -1.5, 3, 140, False, ["Это снижает зависимость нейронов друг от друга."], "Понимание снижения ко-адаптации."),
        ("stud_aai_003", 79.0, -1.3, 3, 150, False, ["На тесте все веса умножаются на p."], "Знание процедуры инференса (inverted dropout)."),
        ("stud_aai_004", 75.0, 0.4, 3, 170, False, ["L2-регуляризация штрафует большие веса."], "Сравнение с L2/Weight decay."),
        ("stud_aai_005", 78.0, 1.1, 4, 180, False, ["Dropout можно интерпретировать как ансамблирование подсетей."], "Связь с ансамблевыми методами."),
        ("stud_aai_006", 81.0, 2.0, 4, 160, False, ["Шум во время обучения мешает ко-адаптации."], "Физическая интуиция регуляризации."),
        ("stud_aai_007", 76.0, 3.0, 4, 190, False, ["При слишком высоком p сеть недообучается."], "Осознание риска underfitting."),
        ("stud_aai_008", 72.0, 4.2, 4, 175, False, ["Dropout обычно не применяют к сверточным слоям с 1x1 фильтрами."], "Понимание специфики для CNN."),
        ("stud_aai_009", 74.0, 6.3, 4, 185, False, ["Разреживание активаций стабилизирует скрытые представления."], "Углубленный ответ уровня Relational."),
        # 2 студента в WATCHLIST (желтая зона)
        ("stud_aai_010", 73.0, 11.0, 4, 190, False, ["Проблема внутреннего ковариантного сдвига и как Dropout взаимодействует с BatchNorm."], "Студент затронул тонкий конфликт между Dropout и Batch Normalization."),
        ("stud_aai_011", 71.0, 13.2, 4, 195, False, ["Масштабирование градиентов при Inverted Dropout сохраняет масштаб функции активации."], "Глубокий анализ масштабирования дисперсии активаций."),
    ]

    for sid, in_class, raw_d, n_c, tokens, init, quotes, just in other_completed_configs:
        depth_score = round(in_class + raw_d, 1)
        # Формируем реалистичную экстракцию
        ext = AuditExtractionResult(
            on_topic=True,
            student_quotes=quotes,
            mastered_concepts=["dropout", "regularization", "co-adaptation"][:n_c],
            socratic_initiative=init,
            pedagogical_justification=just,
            turns_probabilities=[
                TurnSOLOProbabilities(turn_number=1, p1=0.7, p2=0.3, p3=0.0),
                TurnSOLOProbabilities(turn_number=2, p1=0.2, p2=0.6, p3=0.2),
                TurnSOLOProbabilities(turn_number=3, p1=0.1, p2=0.4, p3=0.5),
            ]
        )
        rec = StudentAuditRecord(
            student_id=sid,
            in_class_grade=in_class,
            session_status="COMPLETED",
            turns_count=3,
            total_tokens=tokens,
            extraction=ext,
            ai_depth_score=depth_score,
            telemetry_clean=True,
        )
        records.append(rec)

    # Добавляем stud_k к completed (всего 12)
    records.append(stud_k)

    # 3. Два студента со статусом INCOMPLETE_IGNORED (случайный вход)
    incomplete_configs = [
        ("stud_aai_015", 88.0, 1, 35, ["Что такое регуляризация?"]),
        ("stud_aai_019", 84.0, 1, 28, ["Я зашел проверить ссылку"]),
    ]
    for sid, in_class, turns, tokens, quotes in incomplete_configs:
        rec = StudentAuditRecord(
            student_id=sid,
            in_class_grade=in_class,
            session_status="INCOMPLETE_IGNORED",
            turns_count=turns,
            total_tokens=tokens,
            extraction=AuditExtractionResult(
                on_topic=True,
                student_quotes=quotes,
                mastered_concepts=[],
                socratic_initiative=False,
                pedagogical_justification="Сессия не завершена (менее 2 реплик). Игнорируется аналитическим ядром.",
                turns_probabilities=[
                    TurnSOLOProbabilities(turn_number=1, p1=1.0, p2=0.0, p3=0.0)
                ]
            ),
            ai_depth_score=None,
            telemetry_clean=True,
        )
        records.append(rec)

    # 4. 14 студентов со статусом OPTED_OUT (не пользовались ботом)
    opted_out_grades = [
        ("stud_aai_020", 94.0),
        ("stud_aai_021", 91.0),
        ("stud_aai_022", 89.0),
        ("stud_aai_023", 88.0),
        ("stud_aai_024", 86.0),
        ("stud_aai_025", 92.0),
        ("stud_aai_026", 95.0),
        ("stud_aai_027", 85.0),
        ("stud_aai_028", 83.0),
        ("stud_aai_029", 80.0),
        ("stud_aai_030", 79.0),
        ("stud_aai_031", 90.0),
        ("stud_aai_032", 87.0),
        ("stud_aai_033", 82.0),
    ]
    for sid, in_class in opted_out_grades:
        rec = StudentAuditRecord(
            student_id=sid,
            in_class_grade=in_class,
            session_status="OPTED_OUT",
            turns_count=0,
            total_tokens=0,
            extraction=None,
            ai_depth_score=None,
            telemetry_clean=True,
        )
        records.append(rec)

    # Выполняем когортный расчет (Этап 3B)
    engine = ThemisMathEngine()
    engine.compute_cohort_discrepancy(records)

    return records


# Словарь метаданных студентов для обогащения UI (имена, аватары)
STUDENT_NAMES_MAP = {
    "stud_aai_042": "Студент К. (Анонимный аудит)",
    "stud_aai_001": "Алексей Смирнов",
    "stud_aai_002": "Айгерим Тулегенова",
    "stud_aai_003": "Даниил Морозов",
    "stud_aai_004": "Екатерина Волкова",
    "stud_aai_005": "Жандос Касымов",
    "stud_aai_006": "Иван Новиков",
    "stud_aai_007": "Мария Федорова",
    "stud_aai_008": "Нурлан Сапаров",
    "stud_aai_009": "Ольга Васильева",
    "stud_aai_010": "Павел Ковалев",
    "stud_aai_011": "Руслан Ахметов",
    "stud_aai_015": "София Михайлова",
    "stud_aai_019": "Тимур Исаев",
    "stud_aai_020": "Александр Попов",
    "stud_aai_021": "Виктория Лебедева",
    "stud_aai_022": "Дмитрий Козлов",
    "stud_aai_023": "Елена Соколова",
    "stud_aai_024": "Игорь Павлов",
    "stud_aai_025": "Ксения Макарова",
    "stud_aai_026": "Максим Семенов",
    "stud_aai_027": "Наталья Голубева",
    "stud_aai_028": "Олег Виноградов",
    "stud_aai_029": "Полина Богданова",
    "stud_aai_030": "Роман Воробьев",
    "stud_aai_031": "Светлана Медведева",
    "stud_aai_032": "Татьяна Орлова",
    "stud_aai_033": "Юрий Тарасов",
}

