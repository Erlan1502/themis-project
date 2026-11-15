"""
test_group_and_session.py

Тестирование функционала Группы 1 (20 студентов, каждый как отдельный инстанс)
и механизмов персистентного сохранения/восстановления сессий диалога.
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


def test_group_1_has_exactly_20_distinct_students(client):
    """Проверка, что Группа 1 содержит ровно 20 студентов, каждый представлен отдельным инстансом."""
    resp = client.get("/api/v1/students?group_id=group_1")
    assert resp.status_code == 200
    students = resp.json()
    assert len(students) == 20, f"Ожидалось 20 студентов, получено {len(students)}"

    # Все ID уникальны и принадлежат group_1
    student_ids = [s["student_id"] for s in students]
    assert len(set(student_ids)) == 20
    for s in students:
        assert s["group_id"] == "group_1"
        assert s["display_name"] is not None
        assert s["in_class_grade"] is not None

    # Главные представители
    assert "stud_aai_042" in student_ids  # Студент К.
    assert "stud_aai_015" in student_ids  # София Михайлова (Incomplete)
    assert "stud_aai_025" in student_ids  # Ксения Макарова (Opted-out)


def test_session_restoration_for_student_k(client):
    """Проверка восстановления активной сессии для Студента К."""
    resp = client.get("/api/v1/session/active/stud_aai_042")
    assert resp.status_code == 200
    data = resp.json()
    assert data["found"] is True
    assert data["session_id"] is not None
    assert data["status"] == "COMPLETED"
    assert len(data["turns"]) == 3
    assert data["turns_count"] == 3


def test_session_restoration_for_incomplete_student(client):
    """Проверка восстановления сессии для студента со статусом INCOMPLETE (София Михайлова)."""
    resp = client.get("/api/v1/session/active/stud_aai_015")
    assert resp.status_code == 200
    data = resp.json()
    assert data["found"] is True
    assert len(data["turns"]) == 1
    assert data["status"] == "ACTIVE"


def test_session_for_opted_out_student(client):
    """Проверка статуса для студента без сессии (Opted-Out)."""
    resp = client.get("/api/v1/session/active/stud_aai_020")
    assert resp.status_code == 200
    data = resp.json()
    assert data["found"] is False
    assert len(data["turns"]) == 0


def test_dashboard_group_1_distribution_math(client):
    """
    Проверка математических инвариантов Группы 1:
    Все 12 completed сессий находятся в Группе 1,
    поэтому median=2.5, mad=3.8, robust_sigma=5.63 сохраняются в точности по 'Документация.md'.
    """
    resp = client.get("/api/v1/audit/dashboard?group_id=group_1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_students"] == 20
    assert data["sessions_completed"] == 12
    assert data["opted_out_or_incomplete"] == 8
    assert data["distribution"]["median_delta"] == 2.5
    assert data["distribution"]["mad"] == 3.8
    assert data["distribution"]["robust_sigma"] == 5.63
    assert data["alerts_count"]["purple"] == 1
    assert data["alerts_count"]["yellow"] == 2
    assert data["alerts_count"]["green"] == 9

