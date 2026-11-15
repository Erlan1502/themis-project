"""
seed_data.py

Канонический набор данных для демонстрации Themis Project (v2.0).
Курс: prog_ai_2026 ("Programming AI")
Тема: topic_05_regularization ("Regularization & Dropout Dynamics")

Когорта из 20 студентов (демонстрационная Группа 1):
- 6 студентов со статусом OPTED_OUT (не заходили в бот, очные оценки 86–94 без изменений).
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
}

# Идентификаторы 20 студентов, входящих в Группу 1
GROUP_1_STUDENT_IDS = [
    "stud_aai_042",  # 1. Студент К. (Purple, Completed)
    "stud_aai_001",  # 2. Алексей Смирнов (Green, Completed)
    "stud_aai_002",  # 3. Айгерим Тулегенова (Green, Completed)
    "stud_aai_003",  # 4. Даниил Морозов (Green, Completed)
    "stud_aai_004",  # 5. Екатерина Волкова (Green, Completed)
    "stud_aai_005",  # 6. Жандос Касымов (Green, Completed)
    "stud_aai_006",  # 7. Иван Новиков (Green, Completed)
    "stud_aai_007",  # 8. Мария Федорова (Green, Completed)
    "stud_aai_008",  # 9. Нурлан Сапаров (Green, Completed)
    "stud_aai_009",  # 10. Ольга Васильева (Green, Completed)
    "stud_aai_010",  # 11. Павел Ковалев (Yellow, Completed)
    "stud_aai_011",  # 12. Руслан Ахметов (Yellow, Completed)
    "stud_aai_015",  # 13. София Михайлова (Incomplete, Ignored)
    "stud_aai_019",  # 14. Тимур Исаев (Incomplete, Ignored)
    "stud_aai_020",  # 15. Александр Попов (Opted-Out)
    "stud_aai_021",  # 16. Виктория Лебедева (Opted-Out)
    "stud_aai_022",  # 17. Дмитрий Козлов (Opted-Out)
    "stud_aai_023",  # 18. Елена Соколова (Opted-Out)
    "stud_aai_024",  # 19. Игорь Павлов (Opted-Out)
    "stud_aai_025",  # 20. Ксения Макарова (Opted-Out)
]


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
        group_id="group_1",
        student_name=STUDENT_NAMES_MAP["stud_aai_042"],
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
            group_id="group_1",
            student_name=STUDENT_NAMES_MAP.get(sid, sid),
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
            group_id="group_1",
            student_name=STUDENT_NAMES_MAP.get(sid, sid),
        )
        records.append(rec)

    # 4. 6 студентов со статусом OPTED_OUT (не пользовались ботом, очные оценки 86-94):
    # Входят в единую демонстрационную Группу 1 (stud_aai_020 .. stud_aai_025, ровно 20 студентов в когорте).
    opted_out_grades = [
        ("stud_aai_020", 94.0, "group_1"),
        ("stud_aai_021", 91.0, "group_1"),
        ("stud_aai_022", 89.0, "group_1"),
        ("stud_aai_023", 88.0, "group_1"),
        ("stud_aai_024", 86.0, "group_1"),
        ("stud_aai_025", 92.0, "group_1"),
    ]
    for sid, in_class, gid in opted_out_grades:
        rec = StudentAuditRecord(
            student_id=sid,
            in_class_grade=in_class,
            session_status="OPTED_OUT",
            turns_count=0,
            total_tokens=0,
            extraction=None,
            ai_depth_score=None,
            telemetry_clean=True,
            group_id=gid,
            student_name=STUDENT_NAMES_MAP.get(sid, sid),
        )
        records.append(rec)

    # Выполняем когортный расчет (Этап 3B)
    engine = ThemisMathEngine()
    engine.compute_cohort_discrepancy(records)

    return records


def get_group_records(group_id: str = "group_1") -> List[StudentAuditRecord]:
    """Возвращает список студентов конкретной группы (по умолчанию Группа 1: 20 студентов)."""
    all_records = get_canonical_seed_records()
    return [r for r in all_records if r.group_id == group_id]


def seed_sqlite_dialogs():
    """Сохранение канонических сессий Студента К. и Софии Михайловой в SQLite."""
    try:
        from backend.database import save_session, save_turn, get_session

        # Проверяем, есть ли уже сессия stud_k в БД
        if not get_session("sess_canonical_stud_k"):
            sess_k_id = "sess_canonical_stud_k"
            save_session(sess_k_id, "stud_aai_042", "prog_ai_2026", "topic_05_regularization", "COMPLETED")
            save_turn(
                session_id=sess_k_id,
                turn_number=1,
                student_message="Переобучение происходит, когда веса подстраиваются под специфический шум выборки, создавая избыточную ко-адаптацию нейронов.",
                system_reply="Отлично. Ты упомянул ко-адаптацию нейронов. Каким именно математическим механизмом метод Dropout предотвращает эту ко-адаптацию в процессе обратного распространения ошибки?",
                similarity_score=0.15,
                is_duplicate=False,
                typing_duration_ms=18000,
                paste_detected=False,
            )
            save_turn(
                session_id=sess_k_id,
                turn_number=2,
                student_message="Dropout случайным образом обнуляет активации нейронов с вероятностью p во время прямого прохода. Это заставляет каждый нейрон обучаться полезным признакам независимо от соседей, имитируя ансамбль подсетей.",
                system_reply="Глубокое понимание ансамблевой природы Dropout. А что происходит на экстремальных границах? Например, при слишком высокой вероятности отключения нейронов?",
                similarity_score=0.22,
                is_duplicate=False,
                typing_duration_ms=21000,
                paste_detected=False,
            )
            save_turn(
                session_id=sess_k_id,
                turn_number=3,
                student_message="Если Dropout так эффективен, почему бы нам не выключать 80% нейронов для максимальной регуляризации? В какой момент это сломает обучение и вызовет потерю емкости сети (underfitting)?",
                system_reply="Блестящий исследовательский вопрос! Отключение 80% нейронов катастрофически снижает эффективную емкость сети (model capacity), вызывая недообучение (underfitting). Баланс между регуляризацией и емкостью — фундаментальный компромисс глубокого обучения.",
                similarity_score=0.18,
                is_duplicate=False,
                typing_duration_ms=25000,
                paste_detected=False,
            )

        if not get_session("sess_canonical_stud_015"):
            sess_sofia_id = "sess_canonical_stud_015"
            save_session(sess_sofia_id, "stud_aai_015", "prog_ai_2026", "topic_05_regularization", "INCOMPLETE_IGNORED")
            save_turn(
                session_id=sess_sofia_id,
                turn_number=1,
                student_message="Что такое регуляризация?",
                system_reply="Регуляризация — это совокупность методов, предотвращающих переобучение модели. Попробуй объяснить своими словами: почему нейросеть начинает запоминать шум?",
                similarity_score=0.10,
                is_duplicate=False,
                typing_duration_ms=5000,
                paste_detected=False,
            )
    except Exception as e:
        print(f"Warning seeding SQLite dialogs: {e}")

