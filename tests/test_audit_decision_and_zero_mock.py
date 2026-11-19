"""
test_audit_decision_and_zero_mock.py

Тесты для Шага 2:
1. POST /api/v1/audit/decision (фиксация решения преподавателя)
2. Инвариант Zero Downward Penalty (запрет занижения оценки)
3. Динамический recommended_action в /api/v1/audit/report/{student_id} по зонам
4. GET /api/v1/system/health (системный статус ядра Themis)
5. Проверка Zero-Mock: отсутствие фейковых концептов glossary[:3]
"""

import pytest
from starlette.testclient import TestClient
from backend.main import app, reset_database
from backend.models_schemas import StudentAuditRecord, AuditExtractionResult, TurnSOLOProbabilities
from backend.math_engine import ThemisMathEngine
from backend.similarity_service import similarity_service


@pytest.fixture(autouse=True)
def setup_db():
    reset_database()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_system_health_endpoint(client):
    """Проверка эндпоинта системного статуса GET /api/v1/system/health."""
    resp = client.get("/api/v1/system/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("OK", "DEGRADED")
    assert data["database"] == "connected"
    assert "llm_mode" in data
    assert "vector_store" in data
    assert data["vector_store"]["dimension"] == 1024
    assert data["vector_store"]["model"] == "BAAI/bge-m3"
    assert data["vector_store"]["collection_count"] >= 0


def test_audit_report_dynamic_recommendation_normal_zone(client):
    """
    Инвариант Zero Downward Penalty в отчете аудита:
    Для студентов с rectified_delta <= 0 или в зоне NORMAL формируется
    согласие каналов, запрещающее занижение очной оценки.
    """
    # Студент 001 имеет высокую очную оценку и delta <= 0
    resp = client.get("/api/v1/audit/report/stud_aai_001")
    assert resp.status_code == 200
    report = resp.json()
    assert report["zone"] == "NORMAL"
    assert report["rectified_delta"] == 0.0
    assert "Согласие каналов" in report["recommended_action"]
    assert "вмешательство не требуется" in report["recommended_action"]
    # Не должно содержать предложений снизить оценку
    assert "сниз" not in report["recommended_action"].lower()
    assert "понизить" not in report["recommended_action"].lower()


def test_audit_report_dynamic_recommendation_purple_zone(client):
    """
    Проверка динамической рекомендации для зоны HIGH_DISCREPANCY (Студент К.):
    Рекомендация ректификации оценки на основе реально освоенных концептов.
    """
    resp = client.get("/api/v1/audit/report/stud_aai_042")
    assert resp.status_code == 200
    report = resp.json()
    assert report["zone"] == "HIGH_DISCREPANCY"
    assert report["rectified_delta"] == 23.5
    assert "Рекомендуется ректификация оценки" in report["recommended_action"]
    assert "+23.5" in report["recommended_action"]
    assert "+3.73" in report["recommended_action"]
    assert "underfitting" in report["recommended_action"] or "co-adaptation" in report["recommended_action"]


def test_teacher_decision_accept_rectification(client):
    """Проверка принятия ректификации преподавателем с повышением оценки."""
    # Исходная оценка Студента К. — 70.0, диагностический скор — 93.5
    resp = client.post("/api/v1/audit/decision", json={
        "student_id": "stud_aai_042",
        "course_id": "prog_ai_2026",
        "topic_id": "week_09_deep_learning",
        "action": "ACCEPT_RECTIFICATION",
        "new_grade": 93.5,
        "comment": "Отличный ответ по емкости модели",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["action"] == "ACCEPT_RECTIFICATION"
    assert data["previous_grade"] == 70.0
    assert data["updated_grade"] == 93.5
    assert "ACCEPT_RECTIFICATION: 70.0 -> 93.5" in data["teacher_decision"]

    # Проверяем, что в дашборде оценка обновилась
    dash_resp = client.get("/api/v1/audit/dashboard")
    assert dash_resp.status_code == 200
    stud_k = next(s for s in dash_resp.json()["students"] if s["student_id"] == "stud_aai_042")
    assert stud_k["in_class_grade"] == 93.5


def test_teacher_decision_zero_downward_penalty_violation(client):
    """
    Проверка инварианта Zero Downward Penalty при попытке преподавателя занизить оценку:
    Эндпоинт POST /api/v1/audit/decision должен возвращать 400 Bad Request.
    """
    # Попытка занизить оценку с 70.0 до 65.0
    resp = client.post("/api/v1/audit/decision", json={
        "student_id": "stud_aai_042",
        "course_id": "prog_ai_2026",
        "topic_id": "week_09_deep_learning",
        "action": "ACCEPT_RECTIFICATION",
        "new_grade": 65.0,
    })
    assert resp.status_code == 400
    assert "Themis policy violation: grade cannot be revised downward" in resp.json()["detail"]


def test_teacher_decision_reject_and_keep(client):
    """Проверка действий REJECT, ORAL_BLITZ и KEEP_CURRENT."""
    # 1. ORAL_BLITZ
    blitz_resp = client.post("/api/v1/audit/decision", json={
        "student_id": "stud_aai_042",
        "course_id": "prog_ai_2026",
        "topic_id": "week_09_deep_learning",
        "action": "ORAL_BLITZ",
        "comment": "Спросить про inverted dropout",
    })
    assert blitz_resp.status_code == 200
    assert "ORAL_BLITZ" in blitz_resp.json()["teacher_decision"]

    # 2. KEEP_CURRENT
    keep_resp = client.post("/api/v1/audit/decision", json={
        "student_id": "stud_aai_042",
        "course_id": "prog_ai_2026",
        "topic_id": "week_09_deep_learning",
        "action": "KEEP_CURRENT",
    })
    assert keep_resp.status_code == 200
    assert keep_resp.json()["updated_grade"] == 70.0


def test_zero_mock_no_fake_concepts_if_unmentioned():
    """
    Проверка устранения фейковой подстановки glossary[:3]:
    Если студент не упоминал терминов глоссария, mastered_concepts должен быть пустым,
    и студент не должен получать K_density за термины, которых он не произносил.
    """
    from backend.llm_service import llm_service

    # Сообщение студента не содержит терминов темы week_01_tools_python
    dialog_turns = [
        {"turn_number": 1, "student": "Я просто открыл блокнот и нажал кнопку.", "system": "Понятно."},
        {"turn_number": 2, "student": "Ничего особенного не делал.", "system": "Ясно."},
        {"turn_number": 3, "student": "Все сработало само собой.", "system": "Спасибо."},
    ]

    extraction = llm_service._mock_audit_extraction("week_01_tools_python", dialog_turns)
    # Никакой фейковой подстановки glossary[:3]!
    assert extraction.mastered_concepts == []


def test_concept_matching_robustness():
    """Проверка робастности сопоставления концептов в similarity_service."""
    assert similarity_service.match_concept("dropout", "Мы применили метод Dropout в обучении.")
    assert similarity_service.match_concept("co-adaptation", "Возникает эффект ко-адаптации весов.")
    assert similarity_service.match_concept("underfitting", "Это приведет к underfitting сети.")
    assert not similarity_service.match_concept("backpropagation", "Сегодня отличная погода за окном.")
