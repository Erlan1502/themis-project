"""
test_v2_regression_suite.py

Полный регрессионный тестовый набор Themis Project v2.0 (Шаг 6).
Покрывает 8 ключевых архитектурных и математических сценариев:
1. Тест устойчивости Vector Store (SentenceTransformer failure, 1024-dim L2 hash fallback, защита от InvalidDimensionException).
2. Тест когорты с отрицательной медианой (mu_eff = max(0, median) == 0.0, положительные sigma_thresholds, защита от ложного z_score > 3.0 при шуме +0.5).
3. Тест инвариантности когорты после рестарта БД (median_delta == 2.5, mad == 3.8, robust_sigma == 5.63, стабильность WATCHLIST/HIGH_DISCREPANCY, отсутствие обрушения в 57.4).
4. Тест обнуления галлюцинированных концептов вне глоссария (mastered_concepts -> [], k_density -> floor 0.75).
5. Тест мульти-курсовой и мульти-темной изоляции (отсутствие затирания Недели 9 при прохождении Недели 1 или другого курса).
6. Тест гостевого входа TMA с последующей привязкой по QR-коду без IntegrityError (слияние временного профиля stud_tg_<id>).
7. Тест Circuit Breaker (<0.1s fallback) и восстановления из AUDITING при сбое LLM.
8. Тест транслитерации русскоязычных лекций (уникальные topic_id на одной неделе) и защиты от битых/устаревших .ppt/.doc (ValueError).
"""

import math
import time
import pytest
from unittest.mock import AsyncMock, patch

from backend.main import (
    reset_database,
    db_records,
    db_sessions,
    get_record,
    get_topic_records,
    get_or_create_record,
    run_background_audit,
    audit_broadcaster,
    sync_records_to_sqlite,
    CANONICAL_COURSE_ID,
    CANONICAL_TOPIC_ID,
)
from backend.models_schemas import (
    StudentAuditRecord,
    AuditExtractionResult,
    TurnSOLOProbabilities,
)
from backend.math_engine import ThemisMathEngine
from backend.vector_store import BgeM3EmbeddingFunction, ThemisVectorStore
from backend.seed_data import get_canonical_benchmark_stud_k, get_canonical_seed_records
from backend.database import (
    get_connection,
    get_student_identity,
    get_student_identity_by_telegram_id,
    create_telegram_binding_token,
    link_telegram_identity,
    save_session,
    get_session,
    update_session_status,
)
from backend.tma_auth import get_or_create_telegram_student
from backend.llm_service import llm_service
from backend.ingestion_service import ingestion_service
from backend.markdown_converter import markdown_converter


@pytest.fixture(autouse=True)
def clean_database():
    """Сбрасывает базу данных в чистое каноническое состояние перед каждым тестом."""
    reset_database(load_from_db_if_exists=False)
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE student_identities SET telegram_id = NULL, telegram_username = NULL WHERE student_id LIKE 'stud_aai_%'")
    c.execute("DELETE FROM student_identities WHERE student_id LIKE 'stud_tg_%'")
    conn.commit()
    conn.close()
    yield


# ============================================================================
# 1. ТЕСТ УСТОЙЧИВОСТИ VECTOR STORE (HNSW & 1024-DIM RESILIENCE)
# ============================================================================

def test_vector_store_resilience_and_degraded_hash_mode(monkeypatch):
    """
    1. Симуляция недоступности SentenceTransformer (через monkeypatch/mock на _get_model).
    2. Проверка, что BgeM3EmbeddingFunction генерирует 1024-мерные оффлайн хэш-векторы с L2-нормой 1.0 и флагом is_degraded=True.
    3. Проверка, что на 1024-мерной ChromaDB коллекции add_slides не падает с InvalidDimensionException,
       корректно возвращает 0 в деградированном режиме, а search_relevant_slides работает без исключений.
    """
    fn = BgeM3EmbeddingFunction()

    # Симулируем недоступность SentenceTransformer (ошибка сети и локального кэша)
    def fake_get_model(self):
        self._model = None
        self.is_degraded = True
        return None

    monkeypatch.setattr(BgeM3EmbeddingFunction, "_get_model", fake_get_model)

    # Проверяем вызов генерации эмбеддингов
    docs = [
        "Механизм регуляризации Dropout в глубоких нейросетях",
        "Предотвращение ко-адаптации весов и переобучения",
    ]
    vectors = fn(docs)

    assert fn.is_degraded is True
    assert len(vectors) == 2
    for vec in vectors:
        assert len(vec) == 1024, f"Ожидалась размерность 1024, получено {len(vec)}"
        l2_norm = math.sqrt(sum(x * x for x in vec))
        assert abs(l2_norm - 1.0) < 1e-5, f"L2 норма вектора должна быть 1.0, получено {l2_norm}"

    # Проверяем векторное хранилище ThemisVectorStore
    store = ThemisVectorStore()
    monkeypatch.setattr(store.embedding_fn, "_get_model", fake_get_model)
    store.embedding_fn.is_degraded = True

    # add_slides не должен падать с InvalidDimensionException, должен безопасно вернуть 0 во избежание порчи HNSW индекса
    added_count = store.add_slides(
        topic_id="week_09_deep_learning",
        week_number=9,
        slides_data=[{"title": "Slide 1", "text": "Тестовый слайд"}],
        course_id="prog_ai_2026",
    )
    assert added_count == 0

    # search_relevant_slides должен работать без исключений
    search_results = store.search_relevant_slides(
        query="Dropout regularization",
        topic_id="week_09_deep_learning",
        course_id="prog_ai_2026",
        top_k=2,
    )
    assert isinstance(search_results, list)


# ============================================================================
# 2. ТЕСТ КОГОРТЫ С ОТРИЦАТЕЛЬНОЙ МЕДИАНОЙ (NEGATIVE MEDIAN & MU_EFF)
# ============================================================================

def test_negative_median_cohort_effective_center_and_thresholds():
    """
    1. Создать когорту студентов, где у большинства G_prof > S_depth (raw_median < 0, например -10.0).
    2. Проверить, что effective center mu_eff = max(0.0, raw_median) равен 0.0.
    3. Проверить, что пороги +1σ, +2σ, +3σ остаются строго положительными (> 0).
    4. Проверить, что студент со случайным шумом дельты +0.5 не получает ложный z_score > 3.0 и классифицируется в NORMAL (зеленая зона).
    """
    engine = ThemisMathEngine()

    # Когорта, где у большинства очные оценки выше ИИ (G_prof > S_depth)
    records = [
        StudentAuditRecord(student_id="s1", in_class_grade=90.0, ai_depth_score=75.0, session_status="COMPLETED", turns_count=3),  # delta = -15
        StudentAuditRecord(student_id="s2", in_class_grade=88.0, ai_depth_score=76.0, session_status="COMPLETED", turns_count=3),  # delta = -12
        StudentAuditRecord(student_id="s3", in_class_grade=85.0, ai_depth_score=75.0, session_status="COMPLETED", turns_count=3),  # delta = -10
        StudentAuditRecord(student_id="s4", in_class_grade=82.0, ai_depth_score=74.0, session_status="COMPLETED", turns_count=3),  # delta = -8
        StudentAuditRecord(student_id="s5", in_class_grade=80.0, ai_depth_score=75.0, session_status="COMPLETED", turns_count=3),  # delta = -5
        # Студент со случайным шумом дельты +0.5 балла
        StudentAuditRecord(student_id="s_noise", in_class_grade=80.0, ai_depth_score=80.5, session_status="COMPLETED", turns_count=3),  # delta = +0.5
    ]

    summary = engine.compute_cohort_discrepancy(records)

    # 1. raw_median < 0
    assert summary["raw_median_delta"] < 0.0
    assert summary["median_delta"] < 0.0

    # 2. mu_eff равен 0.0
    assert summary["mu_eff"] == 0.0

    # 3. Пороги +1σ, +2σ, +3σ остаются строго положительными
    assert summary["sigma_thresholds"]["plus_1_sigma"] > 0.0
    assert summary["sigma_thresholds"]["plus_2_sigma"] > 0.0
    assert summary["sigma_thresholds"]["plus_3_sigma"] > 0.0
    assert summary["robust_sigma"] >= engine.sigma_min  # >= 4.0

    # 4. Студент s_noise со случайным шумом +0.5 не получает ложный z_score > 3.0 и классифицируется в NORMAL
    s_noise = next(r for r in records if r.student_id == "s_noise")
    assert s_noise.rectified_delta == 0.5
    assert s_noise.z_score < 1.0  # z_val = 0.5 / 4.0 = 0.12 << 3.0
    assert s_noise.zone == "NORMAL"


# ============================================================================
# 3. ТЕСТ ИНВАРИАНТНОСТИ КОГОРТЫ ПОСЛЕ РЕСТАРТА БД
# ============================================================================

def test_cohort_invariance_after_db_restart():
    """
    1. Вызвать reset_database(load_from_db_if_exists=False) — получить канонический сид.
    2. Добавить Студента К. и проверить метрики: median_delta == 2.5, mad == 3.8, robust_sigma == 5.63.
    3. Вызвать reset_database(load_from_db_if_exists=True) (симуляция рестарта сервера и перезагрузки из SQLite).
    4. Проверить, что метрики когорты остаются в точности median_delta == 2.5, mad == 3.8, robust_sigma == 5.63,
       stud_aai_010 и stud_aai_011 остаются в WATCHLIST, stud_aai_042 остается в HIGH_DISCREPANCY,
       а S_depth фоновых студентов не обрушивается до 57.4.
    """
    # 1. Холодный канонический сид
    reset_database(load_from_db_if_exists=False)

    # Добавляем канонического Студента К. в активную ведомость и синхронизируем в SQLite
    stud_k = get_canonical_benchmark_stud_k()
    db_records[(stud_k.student_id, CANONICAL_COURSE_ID, CANONICAL_TOPIC_ID)] = stud_k
    sync_records_to_sqlite()

    # Проверяем метрики канонической когорты (12 студентов)
    summary_before = db_records.recompute_topic_cohort(CANONICAL_COURSE_ID, CANONICAL_TOPIC_ID)
    assert summary_before["median_delta"] == 2.5
    assert summary_before["mad"] == 3.8
    assert summary_before["robust_sigma"] == 5.63

    # 2. Симуляция рестарта сервера: загрузка состояния из SQLite
    reset_database(load_from_db_if_exists=True)

    summary_after = db_records.recompute_topic_cohort(CANONICAL_COURSE_ID, CANONICAL_TOPIC_ID)
    assert summary_after["median_delta"] == 2.5
    assert summary_after["mad"] == 3.8
    assert summary_after["robust_sigma"] == 5.63

    # 3. Проверка зон и сохранности фоновых студентов
    rec_010 = db_records.get_record("stud_aai_010", CANONICAL_COURSE_ID, CANONICAL_TOPIC_ID)
    rec_011 = db_records.get_record("stud_aai_011", CANONICAL_COURSE_ID, CANONICAL_TOPIC_ID)
    rec_042 = db_records.get_record("stud_aai_042", CANONICAL_COURSE_ID, CANONICAL_TOPIC_ID)

    assert rec_010 is not None
    assert rec_010.zone == "WATCHLIST"
    assert rec_010.ai_depth_score != 57.4

    assert rec_011 is not None
    assert rec_011.zone == "WATCHLIST"
    assert rec_011.ai_depth_score != 57.4

    assert rec_042 is not None
    assert rec_042.zone == "HIGH_DISCREPANCY"
    assert rec_042.ai_depth_score == 93.5

    # Ни у одного из 12 студентов S_depth не обрушился в 57.4
    topic_records = db_records.get_topic_records(CANONICAL_COURSE_ID, CANONICAL_TOPIC_ID)
    completed_records = [r for r in topic_records if r.session_status == "COMPLETED"]
    assert len(completed_records) == 12
    for r in completed_records:
        assert r.ai_depth_score != 57.4, f"Студент {r.student_id} обрушился в 57.4!"


# ============================================================================
# 4. ТЕСТ ОБНУЛЕНИЯ ГАЛЛЮЦИНИРОВАННЫХ КОНЦЕПТОВ ВНЕ ГЛОССАРИЯ
# ============================================================================

def test_hallucinated_concepts_cleared_outside_glossary():
    """
    1. Создать запись студента с концептами, которых нет в глоссарии темы (например, ["hallucination_1", "quantum_flux"]).
    2. Прогнать через compute_individual_depth.
    3. Проверить, что record.extraction.mastered_concepts очищен до [], а K_density опустился до минимального порога 0.75.
    """
    engine = ThemisMathEngine()

    extraction = AuditExtractionResult(
        on_topic=True,
        student_quotes=["Я использовал квантовые флуктуации и теорию струн для обучения модели."],
        mastered_concepts=["hallucination_1", "quantum_flux"],
        socratic_initiative=False,
        pedagogical_justification="Галлюцинированные термины вне темы регуляризации.",
        turns_probabilities=[
            TurnSOLOProbabilities(turn_number=1, p1=0.7, p2=0.3, p3=0.0),
            TurnSOLOProbabilities(turn_number=2, p1=0.2, p2=0.6, p3=0.2),
            TurnSOLOProbabilities(turn_number=3, p1=0.1, p2=0.4, p3=0.5),
        ],
    )

    record = StudentAuditRecord(
        student_id="stud_hallucinated_test",
        course_id=CANONICAL_COURSE_ID,
        topic_id="week_09_deep_learning",
        in_class_grade=75.0,
        session_status="COMPLETED",
        turns_count=3,
        total_tokens=150,
        extraction=extraction,
    )

    engine.compute_individual_depth(record)

    # mastered_concepts очищен до []
    assert record.extraction.mastered_concepts == []
    # K_density опустился до минимального порога floor = 0.75
    assert record.k_density == 0.75
    assert record.k_density == engine.density_floor


# ============================================================================
# 5. ТЕСТ МУЛЬТИ-КУРСОВОЙ И МУЛЬТИ-ТЕМНОЙ ИЗОЛЯЦИИ
# ============================================================================

def test_multi_course_and_multi_topic_isolation():
    """
    1. Один и тот же студент (например, stud_aai_042) проходит сократический диалог на двух разных неделях/темах
       (например, week_09_deep_learning и week_01_tools_python).
    2. Проверить, что данные Недели 9 НЕ затираются данными Недели 1.
    3. Проверить, что get_record / get_topic_records возвращают изолированные записи для соответствующих недель/курсов.
    """
    # Задаем эталонного Студента К. на Неделе 9
    stud_k_w9 = get_canonical_benchmark_stud_k()
    stud_k_w9.topic_id = "week_09_deep_learning"
    db_records[("stud_aai_042", CANONICAL_COURSE_ID, "week_09_deep_learning")] = stud_k_w9
    db_records.recompute_topic_cohort(CANONICAL_COURSE_ID, "week_09_deep_learning")

    # Инициализируем запись того же студента на Неделе 1
    rec_w1 = get_or_create_record(
        student_id="stud_aai_042",
        course_id=CANONICAL_COURSE_ID,
        topic_id="week_01_tools_python"
    )
    assert rec_w1.session_status == "OPTED_OUT"
    assert rec_w1.ai_depth_score is None

    # Симулируем прохождение диалога на Неделе 1
    rec_w1.session_status = "COMPLETED"
    rec_w1.turns_count = 3
    rec_w1.ai_depth_score = 78.5
    rec_w1.raw_delta = 8.5
    rec_w1.rectified_delta = 8.5

    # Сохраняем в реестр
    db_records[("stud_aai_042", CANONICAL_COURSE_ID, "week_01_tools_python")] = rec_w1

    # Проверяем изоляцию через get_record
    w9_check = get_record("stud_aai_042", CANONICAL_COURSE_ID, "week_09_deep_learning")
    w1_check = get_record("stud_aai_042", CANONICAL_COURSE_ID, "week_01_tools_python")

    assert w9_check is not None
    assert w1_check is not None

    # Неделя 9 осталась полностью неизменной
    assert w9_check.ai_depth_score == 93.5
    assert w9_check.rectified_delta == 23.5
    assert w9_check.zone == "HIGH_DISCREPANCY"
    assert w9_check.topic_id == "week_09_deep_learning"

    # Неделя 1 имеет свои собственные данные
    assert w1_check.ai_depth_score == 78.5
    assert w1_check.rectified_delta == 8.5
    assert w1_check.topic_id == "week_01_tools_python"

    # Проверяем изоляцию списков get_topic_records
    topic_w9_records = get_topic_records(CANONICAL_COURSE_ID, "week_09_deep_learning")
    topic_w1_records = get_topic_records(CANONICAL_COURSE_ID, "week_01_tools_python")

    assert any(r.student_id == "stud_aai_042" and r.ai_depth_score == 93.5 for r in topic_w9_records)
    assert any(r.student_id == "stud_aai_042" and r.ai_depth_score == 78.5 for r in topic_w1_records)


# ============================================================================
# 6. ТЕСТ ГОСТЕВОГО ВХОДА TMA С ПОСЛЕДУЮЩЕЙ QR-ПРИВЯЗКОЙ БЕЗ INTEGRITYERROR
# ============================================================================

def test_tma_guest_login_and_subsequent_qr_binding_no_integrity_error():
    """
    1. Вызвать get_or_create_telegram_student(telegram_id=999888, username="test_guest") — создается профиль stud_tg_999888.
    2. Создать QR токен привязки для stud_aai_042.
    3. Вызвать link_telegram_identity("stud_aai_042", 999888, "test_guest").
    4. Проверить, что вызов завершился успешно (True) без sqlite3.IntegrityError, а telegram_id привязался к stud_aai_042.
    """
    tg_guest_user = {
        "id": 999888,
        "first_name": "Гость",
        "last_name": "Жюри",
        "username": "test_guest",
    }

    # 1. Zero-Friction гостевой вход в TMA
    guest_student_id = get_or_create_telegram_student(tg_guest_user)
    assert guest_student_id == "stud_tg_999888"

    ident_guest = get_student_identity_by_telegram_id(999888)
    assert ident_guest is not None
    assert ident_guest["student_id"] == "stud_tg_999888"

    # 2. Создаем QR токен привязки для целевого студента stud_aai_042
    token_info = create_telegram_binding_token("stud_aai_042")
    assert token_info["token"].startswith("bind_")
    assert token_info["student_id"] == "stud_aai_042"

    # 3. Сканирование QR и привязка Telegram ID
    # Ранее это падало с sqlite3.IntegrityError: UNIQUE constraint failed: student_identities.telegram_id
    success = link_telegram_identity(
        student_id="stud_aai_042",
        telegram_id=999888,
        telegram_username="test_guest",
    )
    assert success is True

    # 4. Проверяем, что telegram_id теперь успешно принадлежит stud_aai_042
    ident_target = get_student_identity("stud_aai_042")
    assert ident_target is not None
    assert ident_target["telegram_id"] == 999888
    assert ident_target["telegram_username"] == "test_guest"

    # А временный профиль stud_tg_999888 больше не конфликтует
    ident_old_guest = get_student_identity("stud_tg_999888")
    assert ident_old_guest is None or ident_old_guest.get("telegram_id") is None


# ============================================================================
# 7. ТЕСТ CIRCUIT BREAKER И ВОССТАНОВЛЕНИЯ ИЗ СТАТУСА AUDITING
# ============================================================================

@pytest.mark.anyio
async def test_circuit_breaker_and_auditing_failure_recovery():
    """
    1. Проверить, что при сбое/таймауте LLM включается Circuit Breaker (is_circuit_open() == True),
       и повторный вызов занимает менее 0.1 секунды за счет мгновенного fallback.
    2. Проверить, что если в run_background_audit происходит ошибка (например, сбой экстракции),
       сессия студента не зависает в 'AUDITING', а корректно переводится в 'COMPLETED' с fallback экстракцией и рассылкой SSE.
    """
    # Часть 1: Circuit Breaker
    llm_service.reset_circuit()
    assert llm_service.is_circuit_open() is False

    # Активируем Circuit Breaker
    llm_service.trip_circuit(duration=60.0)
    assert llm_service.is_circuit_open() is True

    # Повторный вызов должен сработать мгновенно (< 0.1 сек) через детерминированный fallback
    t0 = time.perf_counter()
    reply = await llm_service.generate_socratic_reply(
        topic_id="week_09_deep_learning",
        turn_number=1,
        student_message="Dropout случайным образом зануляет нейроны.",
        history=[],
    )
    dt = time.perf_counter() - t0

    assert dt < 0.1, f"Fallback Circuit Breaker занял слишком много времени: {dt:.4f}s (должен < 0.1s)"
    assert len(reply) > 0
    llm_service.reset_circuit()

    # Часть 2: Восстановление из статуса AUDITING при сбое фонового аудита
    test_sid = "stud_cb_recovery_01"
    sess_id = "sess_cb_recovery_01"

    # Создаем запись студента в статусе AUDITING
    rec = get_or_create_record(test_sid, CANONICAL_COURSE_ID, CANONICAL_TOPIC_ID)
    rec.session_status = "AUDITING"
    rec.turns_count = 3
    db_records[(test_sid, CANONICAL_COURSE_ID, CANONICAL_TOPIC_ID)] = rec

    # Создаем сессию в SQLite и памяти
    save_session(
        session_id=sess_id,
        student_id=test_sid,
        course_id=CANONICAL_COURSE_ID,
        topic_id=CANONICAL_TOPIC_ID,
        status="AUDITING",
    )
    db_sessions[sess_id] = {
        "student_id": test_sid,
        "course_id": CANONICAL_COURSE_ID,
        "topic_id": CANONICAL_TOPIC_ID,
        "turns": [],
        "active": True,
    }

    # Имитируем падение extract_audit_evidence (например, сетевая ошибка или таймаут)
    async def mock_extract_fail(*args, **kwargs):
        raise RuntimeError("Сетевой сбой при извлечении аудита")

    with patch.object(llm_service, "extract_audit_evidence", side_effect=mock_extract_fail):
        # Запускаем фоновый аудит
        await run_background_audit(
            student_id=test_sid,
            topic_id=CANONICAL_TOPIC_ID,
            dialog_turns=[
                {"student": "Dropout регуляризует сеть.", "system": "Как именно?"},
                {"student": "Предотвращает ко-адаптацию весов.", "system": "Отлично!"},
                {"student": "На тесте мы масштабируем веса.", "system": "Верно."},
            ],
            session_id=sess_id,
        )

    # Проверяем, что статус сессии не завис в 'AUDITING', а переведен в 'COMPLETED'
    updated_rec = get_record(test_sid, CANONICAL_COURSE_ID, CANONICAL_TOPIC_ID)
    assert updated_rec is not None
    assert updated_rec.session_status == "COMPLETED"
    assert updated_rec.extraction is not None
    assert updated_rec.ai_depth_score is not None

    sess_row = get_session(sess_id)
    assert sess_row is not None
    assert sess_row["status"] == "COMPLETED"


# ============================================================================
# 8. ТЕСТ ТРАНСЛИТЕРАЦИИ РУССКОЯЗЫЧНЫХ ЛЕКЦИЙ И ЗАЩИТЫ ОТ БИТЫХ ФАЙЛОВ
# ============================================================================

def test_cyrillic_transliteration_and_corrupted_file_rejection():
    """
    1. Проверить, что auto_structure_topic для двух русских названий на одной неделе
       (например, «Трансформеры» и «Ансамбли моделей») генерирует разные, уникальные topic_id.
    2. Проверить, что при попытке загрузить битый/устаревший .ppt или .doc конвертер возвращает ValueError.
    """
    # 1. Транслитерация русскоязычных лекций на одной неделе (Неделя 11)
    meta_transformers = ingestion_service.auto_structure_topic(
        markdown_text="# Лекция: Архитектура Трансформеры и механизм внимания Self-Attention\nКонтент лекции...",
        filename="lecture_transformers.md",
        week_number=11,
        topic_name="Трансформеры",
    )

    meta_ensembles = ingestion_service.auto_structure_topic(
        markdown_text="# Лекция: Ансамбли моделей, бэггинг и градиентный бустинг\nКонтент лекции...",
        filename="lecture_ensembles.md",
        week_number=11,
        topic_name="Ансамбли моделей",
    )

    # Проверяем, что сгенерированные topic_id уникальны и не затирают друг друга
    assert meta_transformers["topic_id"] != meta_ensembles["topic_id"]
    assert "week_11" in meta_transformers["topic_id"]
    assert "week_11" in meta_ensembles["topic_id"]

    # Проверяем, что в slug присутствует читаемая транслитерация
    assert "transform" in meta_transformers["topic_id"].lower()
    assert "ansambl" in meta_ensembles["topic_id"].lower()

    # 2. Защита от устаревших бинарных форматов .ppt и .doc
    with pytest.raises(ValueError) as excinfo_ppt:
        markdown_converter.convert_file("old_lecture.ppt")
    assert "не поддерживается" in str(excinfo_ppt.value).lower() or "pptx" in str(excinfo_ppt.value).lower()

    with pytest.raises(ValueError) as excinfo_doc:
        markdown_converter.convert_file("old_document.doc")
    assert "не поддерживается" in str(excinfo_doc.value).lower() or "docx" in str(excinfo_doc.value).lower()
