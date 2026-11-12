"""
test_api.py

Интеграционные тесты для REST API Themis Project (v2.0).
Проверяют контракты всех 5 основных эндпоинтов + сброс демо.
"""

import pytest
from starlette.testclient import TestClient
from backend.main import app, reset_database


@pytest.fixture(autouse=True)
def setup_db():
    reset_database()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_session_start(client):
    """Тест эндпоинта 1: инициализация сессии."""
    resp = client.post("/api/v1/session/start", json={
        "student_id": "stud_aai_042",
        "course_id": "prog_ai_2026",
        "topic_id": "topic_05_regularization",
        "force_open": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["status"] == "ACTIVE"
    assert "Добровольная сессия Themis Project" in data["policy_notice"]
    assert "ко-адаптации признаков" in data["initial_prompt"]


def test_dialog_turns_and_audit_trigger(client):
    """
    Тест эндпоинта 2: прохождение 3 шагов сократического диалога
    и автоматический триггер Слоев 3A и 3B.
    """
    # 1. Старт сессии
    start_resp = client.post("/api/v1/session/start", json={
        "student_id": "stud_live_test",
        "course_id": "prog_ai_2026",
        "topic_id": "topic_05_regularization",
    })
    sess_id = start_resp.json()["session_id"]

    # 2. Шаг 1
    t1_resp = client.post("/api/v1/dialog/turn", json={
        "session_id": sess_id,
        "student_message": "Переобучение связано с тем, что веса подстраиваются под шум и возникает ко-адаптация.",
        "paste_detected": False,
        "typing_duration_ms": 12000,
    })
    assert t1_resp.status_code == 200
    assert t1_resp.json()["turn_number"] == 1
    assert "LOW" in t1_resp.json()["session_confidence"]

    # 3. Шаг 2
    t2_resp = client.post("/api/v1/dialog/turn", json={
        "session_id": sess_id,
        "student_message": "Dropout зануляет случайные нейроны при обучении, поэтому веса не могут ко-адаптироваться.",
        "paste_detected": False,
        "typing_duration_ms": 15000,
    })
    assert t2_resp.status_code == 200
    assert t2_resp.json()["turn_number"] == 2

    # 4. Шаг 3 (с канонической репликой Студента К.)
    t3_resp = client.post("/api/v1/dialog/turn", json={
        "session_id": sess_id,
        "student_message": "Если Dropout так эффективен, почему бы нам не выключать 80% нейронов для максимальной регуляризации? В какой момент это сломает обучение и вызовет потерю емкости сети (underfitting)?",
        "paste_detected": False,
        "typing_duration_ms": 24000,
    })
    assert t3_resp.status_code == 200
    assert t3_resp.json()["turn_number"] == 3
    assert "HIGH" in t3_resp.json()["session_confidence"]


def test_sync_in_class_grades(client):
    """Тест эндпоинта 3: синхронизация очных оценок преподавателя."""
    sync_resp = client.post("/api/v1/sync/in-class-grades", json={
        "course_id": "prog_ai_2026",
        "topic_id": "topic_05_regularization",
        "records": [
            {"student_id": "stud_aai_042", "in_class_grade": 70.0},
            {"student_id": "stud_aai_015", "in_class_grade": 88.0},
        ]
    })
    assert sync_resp.status_code == 200
    data = sync_resp.json()
    assert data["status"] == "SUCCESS"
    assert data["synced_count"] == 2
    assert "cohort_summary" in data


def test_dashboard(client):
    """
    Тест эндпоинта 4: получение дашборда когорты.
    Инварианты: 28 студентов, 12 completed, 16 opted_out/incomplete,
    median=2.5, mad=3.8, sigma=5.63, alerts: green=9, yellow=2, red=0, purple=1.
    """
    resp = client.get("/api/v1/audit/dashboard?topic_id=topic_05_regularization")
    assert resp.status_code == 200
    data = resp.json()
    assert data["project"] == "Themis Project"
    assert data["total_students"] == 28
    assert data["sessions_completed"] == 12
    assert data["opted_out_or_incomplete"] == 16
    assert data["distribution"]["median_delta"] == 2.5
    assert data["distribution"]["mad"] == 3.8
    assert data["distribution"]["robust_sigma"] == 5.63
    assert data["distribution"]["sigma_thresholds"]["plus_1_sigma"] == 8.13
    assert data["distribution"]["sigma_thresholds"]["plus_2_sigma"] == 13.77
    assert data["distribution"]["sigma_thresholds"]["plus_3_sigma"] == 19.40

    assert data["alerts_count"]["green"] == 9
    assert data["alerts_count"]["yellow"] == 2
    assert data["alerts_count"]["red"] == 0
    assert data["alerts_count"]["purple"] == 1
    assert len(data["students"]) == 28


def test_report_stud_k(client):
    """
    Тест эндпоинта 5: AI Discrepancy Report для Студента К.
    Инварианты: grade=70.0, ai_depth_score=93.5, delta=23.5, z_score=3.73, zone=HIGH_DISCREPANCY.
    """
    resp = client.get("/api/v1/audit/report/stud_aai_042?topic_id=topic_05_regularization")
    assert resp.status_code == 200
    data = resp.json()
    assert data["student_id"] == "stud_aai_042"
    assert data["in_class_grade"] == 70.0
    assert data["ai_depth_score"] == 93.5
    assert data["rectified_delta"] == 23.5
    assert data["z_score"] == 3.73
    assert data["zone"] == "HIGH_DISCREPANCY"
    assert "93.5" in data["non_credit_notice"]
    assert data["solo_analysis"]["dominant_level"] == "Extended Abstract (SOLO Level 3)"
    assert data["solo_analysis"]["aggregated_probabilities"]["p1"] == 0.05
    assert data["solo_analysis"]["aggregated_probabilities"]["p2"] == 0.15
    assert data["solo_analysis"]["aggregated_probabilities"]["p3"] == 0.80
    assert data["solo_analysis"]["e_d_squared"] == 7.85
    assert len(data["evidence"]["student_quotes"]) >= 1
    assert "underfitting" in data["evidence"]["mastered_concepts"]
    assert data["evidence"]["telemetry_clean"] is True


def test_demo_reset(client):
    """Тест эндпоинта 6: сброс демо-данных."""
    resp = client.post("/api/v1/demo/reset")
    assert resp.status_code == 200
    assert resp.json()["status"] == "SUCCESS"

