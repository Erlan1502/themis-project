"""
test_similarity_and_anti_spam.py

Тесты для модуля выявления сходств, переформулировок и защиты от накрутки оценок дубликатами.
Также проверяет сохранение истории в SQLite базе данных.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.similarity_service import similarity_service
from backend.database import get_session, get_turns


client = TestClient(app)


def test_similarity_exact_and_rephrase():
    history = [
        "Dropout случайным образом исключает нейроны скрытых слоев во время обучения.",
    ]

    # Точный дубликат
    is_dup, sim, matched = similarity_service.check_repetition(
        "Dropout случайным образом исключает нейроны скрытых слоев во время обучения.",
        history
    )
    assert is_dup is True
    assert sim >= 0.99

    # Перефразирование (тот же смысл, изменен порядок слов)
    is_dup2, sim2, _ = similarity_service.check_repetition(
        "Во время обучения Dropout случайно выключает нейроны в скрытых слоях.",
        history
    )
    assert is_dup2 is True
    assert sim2 >= 0.62

    # Совершенно другой содержательный тезис
    is_dup3, sim3, _ = similarity_service.check_repetition(
        "При дисбалансе классов метрика ROC-AUC может быть обманчивой из-за True Negatives.",
        history
    )
    assert is_dup3 is False
    assert sim3 < 0.50


def test_anti_spam_dialog_turns_and_sqlite():
    # 1. Запуск сессии
    start_resp = client.post("/api/v1/session/start", json={
        "student_id": "stud_anti_spam_test",
        "course_id": "prog_ai_2026",
        "topic_id": "week_09_deep_learning",
        "force_open": True
    })
    assert start_resp.status_code == 200
    session_id = start_resp.json()["session_id"]

    # Проверяем запись в SQLite
    db_sess = get_session(session_id)
    assert db_sess is not None
    assert db_sess["student_id"] == "stud_anti_spam_test"

    # 2. Первый содержательный ответ
    turn1_msg = "Dropout случайным образом исключает нейроны скрытых слоев во время обучения."
    r1 = client.post("/api/v1/dialog/turn", json={
        "session_id": session_id,
        "student_message": turn1_msg,
        "paste_detected": False,
        "typing_duration_ms": 3000
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["turn_number"] == 1
    assert d1["is_duplicate"] is False

    # 3. Повтор того же самого сообщения (попытка накрутить оценку)
    r2 = client.post("/api/v1/dialog/turn", json={
        "session_id": session_id,
        "student_message": turn1_msg,
        "paste_detected": False,
        "typing_duration_ms": 1000
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["is_duplicate"] is True
    # Шаг НЕ должен увеличиться!
    assert d2["turn_number"] == 1
    assert "дублирует" in d2["system_reply"] or "⚠️" in d2["system_reply"]

    # 4. Попытка накрутить оценку легким перефразированием
    rephrased_msg = "Во время обучения Dropout случайно исключает нейроны в скрытых слоях."
    r3 = client.post("/api/v1/dialog/turn", json={
        "session_id": session_id,
        "student_message": rephrased_msg,
        "paste_detected": False,
        "typing_duration_ms": 1500
    })
    assert r3.status_code == 200
    d3 = r3.json()
    assert d3["is_duplicate"] is True
    assert d3["turn_number"] == 1

    # 5. Новый содержательный шаг (2-й уровень)
    turn2_msg = "Если мы увеличим вероятность dropout до 90%, возникнет underfitting из-за сильной потери емкости сети."
    r4 = client.post("/api/v1/dialog/turn", json={
        "session_id": session_id,
        "student_message": turn2_msg,
        "paste_detected": False,
        "typing_duration_ms": 4000
    })
    assert r4.status_code == 200
    d4 = r4.json()
    assert d4["is_duplicate"] is False
    assert d4["turn_number"] == 2

    # 6. Проверяем персистентность в SQLite
    turns = get_turns(session_id)
    assert len(turns) == 4  # 4 попытки всего
    duplicates = [t for t in turns if t["is_duplicate"]]
    assert len(duplicates) == 2
    assert duplicates[0]["similarity_score"] >= 0.99
    assert duplicates[1]["similarity_score"] >= 0.60
