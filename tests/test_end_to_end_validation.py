"""
test_end_to_end_validation.py

Шаг 7. Сквозная валидация и комплексное тестирование Themis Project:
1. Мульти-курсовая изоляция (Multi-course & Topic Isolation):
   - Изоляция двух разных курсов: prog_ai_2026 и course_stats_2026.
   - Загрузка тем, чанков в ChromaDB и записей студентов в SQLite для обоих курсов.
   - Проверка полной изоляции дашборда, силлабуса, ведомостей и RAG-поиска (нулевое пересечение контекстов).
2. Сквозной пайплайн End-to-End (Data Lineage):
   - Ingest материалов -> Markdown-нормализация -> Семантический чанкер с breadcrumbs -> ChromaDB HNSW BGE-M3.
   - 3 шага сократического диалога через /api/v1/dialog/turn/stream -> немедленный AUDITING статус.
   - Фоновый психометрический расчет Слоя 3A/3B (ThemisMathEngine) -> сохранение в student_audits SQLite ->
     push-событие в SSE /api/v1/events/audit-stream -> появление студента на дашборде.
3. Комплексная проверка всех продуктовых и математических инвариантов:
   - Инвариант 1: Добровольность «Цифрового пандуса» (POST /api/v1/session/opt-out -> OPTED_OUT, G_prof сохранена, Z=0).
   - Инвариант 2: Некредитный статус S_depth (аналитическая оценка не заменяет G_prof без решения преподавателя).
   - Инвариант 3: Односторонняя положительная ректификация Delta^+ = max(0, S_depth - G_prof) и Zero Downward Penalty
     (запрет занижения оценки, 400 Bad Request при new_grade < G_prof, Delta^+=0 и Z^+=0 при S_depth <= G_prof).
   - Инвариант 4: Робастная статистика когорты (Median, MAD, sigma_rob = 1.4826 * MAD, зоны NORMAL, WATCHLIST, AUDIT_TRIGGER, HIGH_DISCREPANCY).
"""

import json
import time
import pytest
import numpy as np
from starlette.testclient import TestClient

from backend.main import (
    app,
    reset_database,
    db_records,
    db_sessions,
    engine,
    sync_records_to_sqlite,
    run_background_audit,
    audit_broadcaster,
)
from backend.models_schemas import (
    StudentAuditRecord,
    AuditExtractionResult,
    TurnSOLOProbabilities,
)
from backend.database import (
    get_connection,
    save_course,
    save_syllabus_week,
    save_lecture_glossary,
    save_student_audit,
    get_courses,
    get_syllabus_weeks,
    get_lecture_glossary,
    get_all_student_audits,
    get_student_audit,
)
from backend.vector_store import vector_store
from backend.rag_service import rag_service
from backend.markdown_converter import clean_markdown_text
from backend.chunker import smart_chunk_markdown
from backend.llm_service import llm_service
from backend.config import settings


@pytest.fixture(autouse=True)
def setup_db():
    reset_database(load_from_db_if_exists=False)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def parse_sse_events(raw_text: str):
    """Парсинг SSE payload (Server-Sent Events) из текстового ответа."""
    events = []
    for line in raw_text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            payload_str = line[len("data:"):].strip()
            if payload_str:
                try:
                    events.append(json.loads(payload_str))
                except Exception:
                    pass
    return events


# =====================================================================
# 1. МУЛЬТИ-КУРСОВАЯ ИЗОЛЯЦИЯ (Multi-course & Topic Isolation)
# =====================================================================

def test_multi_course_metadata_and_rag_isolation():
    """
    Проверка строгой изоляции между двумя курсами:
    Курс А: prog_ai_2026 ('Программирование для ИИ')
    Курс Б: course_stats_2026 ('Прикладная математическая статистика')
    
    1. Регистрация метаданных, силлабусов и глоссариев в SQLite.
    2. Индексация чанков в ChromaDB с фильтрацией по course_id и topic_id.
    3. Проверка, что RAG-поиск по Курсу Б возвращает ТОЛЬКО материалы Курса Б
       и ни при каких запросах не отдает чанки Курса А, и наоборот.
    """
    course_a = "prog_ai_2026"
    course_b = "course_stats_2026"

    # 1. Регистрация нового курса Б в SQLite
    save_course(
        course_id=course_b,
        title="Прикладная математическая статистика",
        instructor="Проф. Алиев С.К.",
        description="Курс по теории вероятностей и проверке статистических гипотез"
    )

    # Добавляем неделю в силлабус курса Б
    save_syllabus_week(
        course_id=course_b,
        topic_id="week_01_prob_theory",
        week_number=1,
        title="Неделя 1. Случайные величины и ЦПТ",
        topic_name="Теория вероятностей",
        initial_prompt="Как вы понимаете формулировку Центральной предельной теоремы?",
        chunks_count=2
    )

    # Добавляем глоссарий для курса Б
    stats_glossary = [
        "центральная предельная теорема",
        "критерий стьюдента",
        "p-value",
        "уровень значимости",
        "ковариация",
    ]
    save_lecture_glossary(
        course_id=course_b,
        topic_id="week_01_prob_theory",
        terms=stats_glossary
    )

    # 2. Индексация изолированных чанков в ChromaDB
    stats_slides = [
        {
            "slide_number": 1,
            "title": "Центральная предельная теорема (ЦПТ)",
            "text": (
                "Центральная предельная теорема утверждает, что сумма достаточно большого "
                "количества слабо зависимых случайных величин имеет распределение, близкое к нормальному."
            ),
            "bullet_points": ["Сумма случайных величин", "Сходимость к нормальному закону N(mu, sigma^2)"],
        },
        {
            "slide_number": 2,
            "title": "Критерий Стьюдента и p-value",
            "text": (
                "t-критерий Стьюдента используется для проверки гипотез о равенстве средних значений "
                "двух генеральных совокупностей при неизвестной дисперсии. p-value определяет вероятность ошибки первого рода."
            ),
            "bullet_points": ["t-статистика", "Степени свободы", "Критическая область p-value < alpha"],
        }
    ]

    vector_store.add_slides(
        topic_id="week_01_prob_theory",
        week_number=1,
        slides_data=stats_slides,
        course_id=course_b,
        delete_old=True
    )

    # 3. Проверка RAG-поиска для курса Б
    results_stats = vector_store.search_relevant_slides(
        query="распределение случайных величин p-value и критерий Стьюдента",
        topic_id="week_01_prob_theory",
        course_id=course_b,
        top_k=2
    )
    assert len(results_stats) > 0
    for r in results_stats:
        assert r["metadata"]["course_id"] == course_b
        assert r["metadata"]["topic_id"] == "week_01_prob_theory"
        # Чанки курса А (Dropout, нейронные сети) не должны присутствовать
        assert "dropout" not in r["text"].lower()

    # 4. Проверка RAG-поиска для курса А (prog_ai_2026)
    results_ai = vector_store.search_relevant_slides(
        query="регуляризация нейросети Dropout ко-адаптация",
        topic_id="week_09_deep_learning",
        course_id=course_a,
        top_k=2
    )
    assert len(results_ai) > 0
    for r in results_ai:
        assert r["metadata"]["course_id"] == course_a
        # Чанки курса Б (p-value, критерий Стьюдента) не должны присутствовать
        assert "стьюдент" not in r["text"].lower()
        assert "p-value" not in r["text"].lower()


def test_multi_course_syllabus_and_dashboard_isolation(client):
    """
    Проверка мульти-курсовой изоляции на уровне REST API:
    1. GET /api/v1/courses отдает оба курса.
    2. GET /api/v1/syllabus/weeks фильтрует недели строго по запрошенному course_id.
    3. GET /api/v1/audit/dashboard отдает когорту и робастную статистику
       строго для запрошенного course_id и topic_id, без утечки студентов чужого курса.
    """
    course_a = "prog_ai_2026"
    course_b = "course_stats_2026"

    # Регистрация курса Б и его темы
    save_course(
        course_id=course_b,
        title="Прикладная математическая статистика",
        instructor="Проф. Алиев С.К.",
        description="Курс по статистике"
    )
    save_syllabus_week(
        course_id=course_b,
        topic_id="week_01_prob_theory",
        week_number=1,
        title="Неделя 1. Случайные величины",
        topic_name="Теория вероятностей",
        initial_prompt="Каковы условия применимости ЦПТ?",
        chunks_count=2
    )
    rag_service.reload()

    # Добавляем двух студентов курса Б в db_records
    rec_b1 = StudentAuditRecord(
        student_id="stud_stat_101",
        course_id=course_b,
        topic_id="week_01_prob_theory",
        student_name="Касымов Даурен",
        group_id="group_stat",
        in_class_grade=60.0,
        session_status="COMPLETED",
        turns_count=3,
        total_tokens=150,
        ai_depth_score=88.0,
        raw_delta=28.0,
        rectified_delta=28.0,
        z_score=3.2,
        zone="HIGH_DISCREPANCY",
        telemetry_clean=True,
    )
    rec_b2 = StudentAuditRecord(
        student_id="stud_stat_102",
        course_id=course_b,
        topic_id="week_01_prob_theory",
        student_name="Омарова Алия",
        group_id="group_stat",
        in_class_grade=82.0,
        session_status="COMPLETED",
        turns_count=3,
        total_tokens=140,
        ai_depth_score=75.0,
        raw_delta=-7.0,
        rectified_delta=0.0,
        z_score=0.0,
        zone="NORMAL",
        telemetry_clean=True,
    )
    db_records[rec_b1.student_id] = rec_b1
    db_records[rec_b2.student_id] = rec_b2
    sync_records_to_sqlite()

    # 1. Проверка GET /api/v1/courses
    resp_courses = client.get("/api/v1/courses")
    assert resp_courses.status_code == 200
    courses_list = resp_courses.json()
    course_ids = [c["course_id"] for c in courses_list]
    assert course_a in course_ids
    assert course_b in course_ids

    # 2. Проверка GET /api/v1/syllabus/weeks?course_id=...
    resp_weeks_b = client.get(f"/api/v1/syllabus/weeks?course_id={course_b}")
    assert resp_weeks_b.status_code == 200
    weeks_b = resp_weeks_b.json()
    assert len(weeks_b) == 1
    assert weeks_b[0]["topic_id"] == "week_01_prob_theory"

    resp_weeks_a = client.get(f"/api/v1/syllabus/weeks?course_id={course_a}")
    assert resp_weeks_a.status_code == 200
    weeks_a = resp_weeks_a.json()
    assert len(weeks_a) >= 9
    assert all(w["topic_id"] != "week_01_prob_theory" for w in weeks_a)

    # 3. Проверка дашборда для курса Б
    resp_dash_b = client.get(f"/api/v1/audit/dashboard?course_id={course_b}&topic_id=week_01_prob_theory")
    assert resp_dash_b.status_code == 200
    dash_b = resp_dash_b.json()
    assert dash_b["total_students"] == 2
    dash_b_student_ids = [s["student_id"] for s in dash_b["students"]]
    assert "stud_stat_101" in dash_b_student_ids
    assert "stud_stat_102" in dash_b_student_ids
    # Студент К. из курса А не должен присутствовать на дашборде курса Б
    assert "stud_aai_042" not in dash_b_student_ids

    # 4. Проверка дашборда для курса А
    resp_dash_a = client.get(f"/api/v1/audit/dashboard?course_id={course_a}&topic_id=week_09_deep_learning")
    assert resp_dash_a.status_code == 200
    dash_a = resp_dash_a.json()
    dash_a_student_ids = [s["student_id"] for s in dash_a["students"]]
    assert "stud_aai_042" in dash_a_student_ids
    assert "stud_stat_101" not in dash_a_student_ids
    assert "stud_stat_102" not in dash_a_student_ids

    # 5. Проверка запросов SQLite get_all_student_audits с фильтрацией
    audits_b = get_all_student_audits(course_id=course_b)
    assert len(audits_b) == 2
    assert {a["student_id"] for a in audits_b} == {"stud_stat_101", "stud_stat_102"}


# =====================================================================
# 2. СКВОЗНОЙ ПАЙПЛАЙН END-TO-END (Data Lineage)
# =====================================================================

def test_end_to_end_data_lineage_and_streaming_audit(client, monkeypatch):
    """
    Полный сквозной тест Data Lineage от документа до дашборда:
    1. Исходный текст лекции -> Markdown-нормализация -> Семантический чанкер с breadcrumbs -> ChromaDB.
    2. Старт сессии -> 3 шага сократического диалога через POST /api/v1/dialog/turn/stream.
    3. На 3-м шаге: мгновенная отдача ответа со статусом AUDITING.
    4. Фоновый асинхронный расчет Слоя 3A (экстракция) и Слоя 3B (ThemisMathEngine).
    5. Обновление статуса в COMPLETED, вычисление S_depth, Delta^+, Z-score.
    6. Сохранение в SQLite student_audits и появление студента на дашборде.
    """
    # Переводим LLM в детерминированный mock-режим для мгновенного и предсказуемого выполнения
    monkeypatch.setattr(llm_service, "mode", "mock")
    monkeypatch.setattr(settings, "LLM_MODE", "mock")

    student_id = "stud_e2e_lineage_k"
    course_id = "prog_ai_2026"
    topic_id = "week_09_deep_learning"

    # Шаг 1: Подготовка документа, очистка и семантический чанкинг
    raw_lecture_markdown = (
        "# Лекция 9. Регуляризация нейронных сетей\n\n"
        "## Механизм Dropout и ко-адаптация\n\n"
        "Метод Dropout случайным образом зануляет активации нейронов с вероятностью p.\n"
        "Это предотвращает взаимную ко-адаптацию весов (co-adaptation) и заставляет каждый нейрон "
        "формировать устойчивые признаки независимо от соседних.\n\n"
        "| Гиперпараметр | Типичное значение | Назначение |\n"
        "|---|---|---|\n"
        "| p (dropout rate) | 0.2 - 0.5 | Вероятность зануления |\n"
        "| weight_decay | 1e-4 | L2-регуляризация |\n\n"
        "При слишком высоком p (например, 80%) возникает недостаточная емкость сети (underfitting).\n\n"
        "```python\n"
        "import torch.nn as nn\n"
        "layer = nn.Dropout(p=0.5)\n"
        "```\n"
    )

    cleaned_md = clean_markdown_text(raw_lecture_markdown)
    assert "# Лекция 9" in cleaned_md
    assert "| Гиперпараметр |" in cleaned_md

    # Семантический чанкинг с инжекцией контекстных хлебных крошек
    chunks = smart_chunk_markdown(
        markdown_text=cleaned_md,
        course_id=course_id,
        topic_id=topic_id,
        week_number=9,
        topic_name="Глубокое обучение и регуляризация",
        course_title="Программирование для ИИ"
    )
    assert len(chunks) >= 1
    # Проверяем наличие breadcrumbs в тексте чанка
    first_chunk_text = chunks[0]["text"]
    assert "[Курс: Программирование для ИИ" in first_chunk_text
    assert "Тема: Глубокое обучение и регуляризация" in first_chunk_text

    # Шаг 2: Инициализация сессии студента
    start_resp = client.post("/api/v1/session/start", json={
        "student_id": student_id,
        "course_id": course_id,
        "topic_id": topic_id,
        "force_open": True,
    })
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    session_id = start_data["session_id"]
    assert start_data["status"] == "ACTIVE"
    assert "Добровольная сессия" in start_data["policy_notice"]

    # Шаг 3: Сократический диалог через SSE /turn/stream (Шаг 1)
    s1_resp = client.post("/api/v1/dialog/turn/stream", json={
        "session_id": session_id,
        "student_message": "Переобучение связано с тем, что веса нейронов подстраиваются под шум и возникает ко-адаптация.",
        "typing_duration_ms": 12000,
    })
    assert s1_resp.status_code == 200
    events_s1 = parse_sse_events(s1_resp.text)
    event_types_s1 = [e.get("type") for e in events_s1]
    assert "sources" in event_types_s1
    assert "delta" in event_types_s1
    assert "done" in event_types_s1
    done_s1 = next(e for e in events_s1 if e.get("type") == "done")["turn_response"]
    assert done_s1["turn_number"] == 1
    assert done_s1["session_status"] == "INCOMPLETE_IGNORED"

    # Шаг 4: Сократический диалог (Шаг 2)
    s2_resp = client.post("/api/v1/dialog/turn/stream", json={
        "session_id": session_id,
        "student_message": "Dropout зануляет случайные нейроны при обучении, моделируя ансамбль подсетей.",
        "typing_duration_ms": 14000,
    })
    assert s2_resp.status_code == 200
    events_s2 = parse_sse_events(s2_resp.text)
    done_s2 = next(e for e in events_s2 if e.get("type") == "done")["turn_response"]
    assert done_s2["turn_number"] == 2
    assert done_s2["session_status"] == "INCOMPLETE_IGNORED"

    # Шаг 5: Сократический диалог (Шаг 3 — триггер аудита)
    # Используем ключевые фразы Студента К. (80%, underfitting, емкость)
    s3_resp = client.post("/api/v1/dialog/turn/stream", json={
        "session_id": session_id,
        "student_message": (
            "Если Dropout так эффективен, почему бы нам не выключать 80% нейронов для максимальной регуляризации? "
            "В какой момент это сломает обучение и вызовет потерю емкости сети (underfitting)?"
        ),
        "typing_duration_ms": 25000,
    })
    assert s3_resp.status_code == 200
    events_s3 = parse_sse_events(s3_resp.text)
    done_s3 = next(e for e in events_s3 if e.get("type") == "done")["turn_response"]
    assert done_s3["turn_number"] == 3
    # Студент немедленно получает статус AUDITING
    assert done_s3["session_status"] == "AUDITING"

    # Шаг 6: Проверка завершения фонового расчета психометрического ядра
    for _ in range(30):
        rec = db_records.get(student_id)
        if rec and rec.session_status == "COMPLETED" and rec.ai_depth_score is not None:
            break
        time.sleep(0.1)

    rec = db_records[student_id]
    assert rec.session_status == "COMPLETED"
    assert rec.ai_depth_score is not None
    # Канонический балл Студента К. — 93.5
    assert rec.ai_depth_score >= 90.0
    assert rec.rectified_delta > 0.0
    assert rec.extraction is not None
    assert "underfitting" in rec.extraction.mastered_concepts

    # Шаг 7: Проверка сохранения в SQLite student_audits
    saved_audit = get_student_audit(student_id=student_id, course_id=course_id, topic_id=topic_id)
    assert saved_audit is not None
    assert saved_audit["session_status"] == "COMPLETED"
    assert saved_audit["ai_depth_score"] == rec.ai_depth_score

    # Шаг 8: Проверка появления студента на дашборде
    resp_dash = client.get(f"/api/v1/audit/dashboard?course_id={course_id}&topic_id={topic_id}")
    assert resp_dash.status_code == 200
    dash_data = resp_dash.json()
    student_entries = [s for s in dash_data["students"] if s["student_id"] == student_id]
    assert len(student_entries) == 1
    st_entry = student_entries[0]
    assert st_entry["ai_depth_score"] == rec.ai_depth_score
    assert st_entry["rectified_delta"] == rec.rectified_delta
    assert st_entry["zone"] in ("HIGH_DISCREPANCY", "AUDIT_TRIGGER")


# =====================================================================
# 3. КОМПЛЕКСНАЯ ПРОВЕРКА ПРОДУКТОВЫХ И МАТЕМАТИЧЕСКИХ ИНВАРИАНТОВ
# =====================================================================

def test_invariant_1_digital_ramp_opt_out(client):
    """
    Инвариант 1: Добровольность «Цифрового пандуса» (UDL Principle):
    - Студент начинает сократическую сессию.
    - В любой момент отправляет запрос POST /api/v1/session/opt-out.
    - Статус фиксируется как OPTED_OUT.
    - Очная оценка G_prof сохраняется в 100% объеме без штрафов.
    - Z-score = 0.0, Rectified Delta = 0.0, ai_depth_score = None, zone = NO_SIGNAL.
    - Сессия закрывается, активный статус удаляется.
    """
    student_id = "stud_ramp_optout_test"
    course_id = "prog_ai_2026"
    topic_id = "week_09_deep_learning"
    expected_grade = 78.0

    # Создаем запись студента с очной оценкой 78.0
    rec = StudentAuditRecord(
        student_id=student_id,
        course_id=course_id,
        topic_id=topic_id,
        student_name="Студент Пандус",
        group_id="group_1",
        in_class_grade=expected_grade,
        session_status="INCOMPLETE_IGNORED",
        turns_count=1,
        total_tokens=40,
    )
    db_records[student_id] = rec
    sync_records_to_sqlite()

    # Стартуем сессию
    start_resp = client.post("/api/v1/session/start", json={
        "student_id": student_id,
        "course_id": course_id,
        "topic_id": topic_id,
        "force_open": True,
    })
    assert start_resp.status_code == 200
    session_id = start_resp.json()["session_id"]
    assert session_id in db_sessions

    # Добровольный отказ студента
    opt_resp = client.post("/api/v1/session/opt-out", json={
        "student_id": student_id,
        "session_id": session_id,
    })
    assert opt_resp.status_code == 200
    opt_data = opt_resp.json()

    assert opt_data["status"] == "OPTED_OUT"
    assert opt_data["in_class_grade"] == expected_grade
    assert opt_data["ai_depth_score"] is None
    assert opt_data["rectified_delta"] == 0.0
    assert opt_data["zone"] == "NO_SIGNAL"

    # Проверяем состояние в БД и оперативной памяти
    rec_after = db_records[student_id]
    assert rec_after.session_status == "OPTED_OUT"
    assert rec_after.in_class_grade == expected_grade
    assert rec_after.ai_depth_score is None
    assert rec_after.rectified_delta == 0.0
    assert rec_after.z_score == 0.0
    assert rec_after.zone == "NO_SIGNAL"
    assert session_id not in db_sessions


def test_invariant_2_non_credit_diagnostic_status(client):
    """
    Инвариант 2: Некредитный диагностический статус S_depth:
    - Аналитическая оценка S_depth служит только сигналом для преподавателя и НЕ заменяет
      очную оценку G_prof автоматически.
    - До явного решения преподавателя через /api/v1/audit/decision очная оценка остается нетронутой.
    - При решении REJECT или KEEP_CURRENT очная оценка также не изменяется.
    """
    student_id = "stud_non_credit_test"
    course_id = "prog_ai_2026"
    topic_id = "week_09_deep_learning"
    initial_grade = 70.0
    diagnostic_depth = 91.5

    # Студент прошел сессию, получен высокий диагностический балл 91.5
    rec = StudentAuditRecord(
        student_id=student_id,
        course_id=course_id,
        topic_id=topic_id,
        student_name="Студент Диагностика",
        group_id="group_1",
        in_class_grade=initial_grade,
        session_status="COMPLETED",
        turns_count=3,
        total_tokens=180,
        ai_depth_score=diagnostic_depth,
        raw_delta=21.5,
        rectified_delta=21.5,
        z_score=2.8,
        zone="AUDIT_TRIGGER",
        telemetry_clean=True,
    )
    db_records[student_id] = rec
    sync_records_to_sqlite()

    # Проверяем, что в дашборде in_class_grade ВСЕ ЕЩЕ 70.0 (некредитный статус)
    dash_resp = client.get(f"/api/v1/audit/dashboard?course_id={course_id}&topic_id={topic_id}")
    student_entry = next(s for s in dash_resp.json()["students"] if s["student_id"] == student_id)
    assert student_entry["in_class_grade"] == initial_grade
    assert student_entry["ai_depth_score"] == diagnostic_depth

    # Преподаватель решает сохранить текущую оценку (REJECT)
    reject_resp = client.post("/api/v1/audit/decision", json={
        "student_id": student_id,
        "course_id": course_id,
        "topic_id": topic_id,
        "action": "REJECT",
        "comment": "Ответы поверхностные, сохраняем очный балл",
    })
    assert reject_resp.status_code == 200
    reject_data = reject_resp.json()
    assert reject_data["action"] == "REJECT"
    assert reject_data["previous_grade"] == initial_grade
    assert reject_data["updated_grade"] == initial_grade
    assert db_records[student_id].in_class_grade == initial_grade


def test_invariant_3_positive_rectification_and_zero_downward_penalty(client):
    """
    Инвариант 3: Односторонняя положительная ректификация и Zero Downward Penalty:
    1. Delta^+ = max(0, S_depth - G_prof):
       - Если S_depth <= G_prof, то Delta^+ = 0.0, Z = 0.0, зона NORMAL.
       - Система фиксирует 'Согласие каналов', занижение исключено регламентом.
    2. Zero Downward Penalty на уровне API:
       - При попытке преподавателя или системы выставить new_grade < G_prof
         API возвращает 400 Bad Request с сообщением 'Themis policy violation: grade cannot be revised downward'.
       - При попытке применить ACCEPT_RECTIFICATION к студенту с S_depth < G_prof
         без указания валидной повышенной оценки API возвращает 400 Bad Request.
    """
    course_id = "prog_ai_2026"
    topic_id = "week_09_deep_learning"

    # Случай А: Студент с высокой очной оценкой G_prof = 85.0 и меньшим S_depth = 78.0
    stud_high_in_class = "stud_downward_protect"
    rec_high = StudentAuditRecord(
        student_id=stud_high_in_class,
        course_id=course_id,
        topic_id=topic_id,
        student_name="Студент Высокий Балл",
        group_id="group_1",
        in_class_grade=85.0,
        session_status="COMPLETED",
        turns_count=3,
        total_tokens=150,
        ai_depth_score=78.0,
        raw_delta=-7.0,
        rectified_delta=0.0,  # Односторонняя ректификация: max(0, -7.0) = 0.0
        z_score=0.0,
        zone="NORMAL",
        telemetry_clean=True,
        extraction=AuditExtractionResult(
            on_topic=True,
            student_quotes=["Dropout случайным образом отключает нейроны."],
            mastered_concepts=["dropout", "regularization"],
            socratic_initiative=False,
            pedagogical_justification="Базовое понимание регуляризации.",
            turns_probabilities=[
                TurnSOLOProbabilities(turn_number=1, p1=0.8, p2=0.2, p3=0.0),
                TurnSOLOProbabilities(turn_number=2, p1=0.5, p2=0.5, p3=0.0),
                TurnSOLOProbabilities(turn_number=3, p1=0.4, p2=0.6, p3=0.0),
            ]
        ),
    )
    db_records[stud_high_in_class] = rec_high
    sync_records_to_sqlite()

    # 1. Проверяем отчет аудита: согласие каналов
    rep_resp = client.get(f"/api/v1/audit/report/{stud_high_in_class}?topic_id={topic_id}&course_id={course_id}")
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()
    assert rep_data["zone"] == "NORMAL"
    assert rep_data["rectified_delta"] == 0.0
    assert "Согласие каналов" in rep_data["recommended_action"]
    assert "вмешательство не требуется" in rep_data["recommended_action"]
    assert "сниз" not in rep_data["recommended_action"].lower()

    # 2. Попытка преподавателя занизить оценку до 78.0 (Zero Downward Penalty)
    downgrade_resp = client.post("/api/v1/audit/decision", json={
        "student_id": stud_high_in_class,
        "course_id": course_id,
        "topic_id": topic_id,
        "action": "ACCEPT_RECTIFICATION",
        "new_grade": 78.0,  # 78.0 < 85.0 -> ЗАПРЕЩЕНО
    })
    assert downgrade_resp.status_code == 400
    assert "cannot be revised downward" in downgrade_resp.json()["detail"].lower()
    # Оценка в БД осталась 85.0
    assert db_records[stud_high_in_class].in_class_grade == 85.0

    # 3. Попытка автоматической ректификации без указания new_grade при S_depth < G_prof
    auto_rect_resp = client.post("/api/v1/audit/decision", json={
        "student_id": stud_high_in_class,
        "course_id": course_id,
        "topic_id": topic_id,
        "action": "ACCEPT_RECTIFICATION",
    })
    assert auto_rect_resp.status_code == 400
    assert "cannot be revised downward" in auto_rect_resp.json()["detail"].lower()
    assert db_records[stud_high_in_class].in_class_grade == 85.0

    # 4. Валидное повышение оценки (ACCEPT_RECTIFICATION с new_grade >= previous_grade)
    valid_up_resp = client.post("/api/v1/audit/decision", json={
        "student_id": stud_high_in_class,
        "course_id": course_id,
        "topic_id": topic_id,
        "action": "ACCEPT_RECTIFICATION",
        "new_grade": 88.0,
        "comment": "Студент продемонстрировал глубокое понимание на устном блице",
    })
    assert valid_up_resp.status_code == 200
    assert valid_up_resp.json()["updated_grade"] == 88.0
    assert db_records[stud_high_in_class].in_class_grade == 88.0


def test_invariant_4_robust_cohort_statistics():
    """
    Инвариант 4: Робастная статистика когорты ThemisMathEngine (Слой 3B):
    - Медиана сырых расхождений (raw_delta).
    - Медианное абсолютное отклонение: MAD = median(|Delta_i - Median_Delta|).
    - Робастное стандартное отклонение: sigma_rob = max(sigma_min, 1.4826 * MAD).
    - Правильность отнесения студентов к 4 зонам риска:
      * NORMAL: Delta^+ <= 0.0 или Z < 1.0 (или Delta^+ < 10.0)
      * WATCHLIST: Z >= 1.0 и Delta^+ >= 10.0 (+1 sigma)
      * AUDIT_TRIGGER: Z >= 2.0 и Delta^+ >= 15.0 (+2 sigma)
      * HIGH_DISCREPANCY (Purple): Z >= 3.0 и Delta^+ >= 20.0 (+3 sigma)
    """
    test_engine = engine

    # Создаем контролируемую когорту с каноническими дельтами
    # Медиана сырых дельт около 2.0, MAD около 3.0 -> sigma_rob = max(4.0, 1.4826 * 3.0) = 4.45
    records = [
        StudentAuditRecord(student_id="s_norm_01", in_class_grade=85.0, ai_depth_score=80.0, session_status="COMPLETED", turns_count=3),  # delta = -5 (rect = 0)
        StudentAuditRecord(student_id="s_norm_02", in_class_grade=80.0, ai_depth_score=80.0, session_status="COMPLETED", turns_count=3),  # delta = 0 (rect = 0)
        StudentAuditRecord(student_id="s_norm_03", in_class_grade=75.0, ai_depth_score=76.0, session_status="COMPLETED", turns_count=3),  # delta = +1 (rect = 1)
        StudentAuditRecord(student_id="s_norm_04", in_class_grade=74.0, ai_depth_score=76.0, session_status="COMPLETED", turns_count=3),  # delta = +2 (rect = 2)
        StudentAuditRecord(student_id="s_norm_05", in_class_grade=72.0, ai_depth_score=75.0, session_status="COMPLETED", turns_count=3),  # delta = +3 (rect = 3)
        StudentAuditRecord(student_id="s_norm_06", in_class_grade=70.0, ai_depth_score=74.0, session_status="COMPLETED", turns_count=3),  # delta = +4 (rect = 4)
        StudentAuditRecord(student_id="s_watch_01", in_class_grade=70.0, ai_depth_score=81.0, session_status="COMPLETED", turns_count=3), # delta = +11 (rect = 11)
        StudentAuditRecord(student_id="s_trig_01", in_class_grade=70.0, ai_depth_score=86.0, session_status="COMPLETED", turns_count=3),  # delta = +16 (rect = 16)
        StudentAuditRecord(student_id="s_purple_01", in_class_grade=70.0, ai_depth_score=94.0, session_status="COMPLETED", turns_count=3), # delta = +24 (rect = 24)
        StudentAuditRecord(student_id="s_opted_out", in_class_grade=75.0, ai_depth_score=None, session_status="OPTED_OUT", turns_count=0), # OPTED_OUT
    ]

    summary = test_engine.compute_cohort_discrepancy(records)

    # 1. Проверяем базовые робастные статистики
    assert "median_delta" in summary
    assert "mad" in summary
    assert "robust_sigma" in summary
    assert summary["robust_sigma"] >= test_engine.sigma_min

    # Ручной расчет для сверки
    raw_deltas = [-5.0, 0.0, 1.0, 2.0, 3.0, 4.0, 11.0, 16.0, 24.0]
    expected_median = float(np.median(raw_deltas))
    expected_mad = float(np.median(np.abs(np.array(raw_deltas) - expected_median)))
    expected_sigma = max(test_engine.sigma_min, 1.4826 * expected_mad)

    assert abs(summary["median_delta"] - expected_median) < 0.05
    assert abs(summary["mad"] - expected_mad) < 0.05
    assert abs(summary["robust_sigma"] - expected_sigma) < 0.05

    # 2. Проверяем пороги сигм
    thresh = summary["sigma_thresholds"]
    assert thresh["plus_1_sigma"] == round(expected_median + 1.0 * expected_sigma, 2)
    assert thresh["plus_2_sigma"] == round(expected_median + 2.0 * expected_sigma, 2)
    assert thresh["plus_3_sigma"] == round(expected_median + 3.0 * expected_sigma, 2)

    # 3. Проверка классификации по зонам
    rec_by_id = {r.student_id: r for r in records}

    # Студенты с отрицательной или нулевой дельтой строго в NORMAL с Z=0
    assert rec_by_id["s_norm_01"].rectified_delta == 0.0
    assert rec_by_id["s_norm_01"].z_score == 0.0
    assert rec_by_id["s_norm_01"].zone == "NORMAL"

    assert rec_by_id["s_norm_02"].rectified_delta == 0.0
    assert rec_by_id["s_norm_02"].z_score == 0.0
    assert rec_by_id["s_norm_02"].zone == "NORMAL"

    # Небольшие дельты (< 10) остаются в NORMAL
    assert rec_by_id["s_norm_03"].zone == "NORMAL"
    assert rec_by_id["s_norm_04"].zone == "NORMAL"
    assert rec_by_id["s_norm_05"].zone == "NORMAL"
    assert rec_by_id["s_norm_06"].zone == "NORMAL"

    # Студент в зоне WATCHLIST (+1 sigma, delta >= 10)
    assert rec_by_id["s_watch_01"].rectified_delta == 11.0
    assert rec_by_id["s_watch_01"].z_score >= 1.0
    assert rec_by_id["s_watch_01"].zone == "WATCHLIST"

    # Студент в зоне AUDIT_TRIGGER (+2 sigma, delta >= 15)
    assert rec_by_id["s_trig_01"].rectified_delta == 16.0
    assert rec_by_id["s_trig_01"].z_score >= 2.0
    assert rec_by_id["s_trig_01"].zone == "AUDIT_TRIGGER"

    # Студент в зоне HIGH_DISCREPANCY (+3 sigma, delta >= 20, Purple)
    assert rec_by_id["s_purple_01"].rectified_delta == 24.0
    assert rec_by_id["s_purple_01"].z_score >= 3.0
    assert rec_by_id["s_purple_01"].zone == "HIGH_DISCREPANCY"

    # Студент OPTED_OUT не имеет сигнала
    assert rec_by_id["s_opted_out"].z_score == 0.0
    assert rec_by_id["s_opted_out"].zone == "NO_SIGNAL"

    # Проверка счетчиков алертов в сводке
    alerts = summary["alerts_count"]
    assert alerts["green"] >= 6
    assert alerts["yellow"] == 1
    assert alerts["red"] == 1
    assert alerts["purple"] == 1
