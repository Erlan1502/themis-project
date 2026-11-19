"""
test_stream_and_performance.py

Тесты для Шага 3 (Ускорение бэкенда: Warmup BGE-M3, ThreadPool и SSE-стриминг):
- Прогрев модели BAAI/bge-m3 в ThreadPool (vector_store.warmup).
- Потоковый эндпоинт POST /api/v1/dialog/turn/stream (RAG sources, delta streaming, done).
- Защита от дубликатов (Anti-Spam) в потоковом режиме.
- 3-й шаг: переход в статус AUDITING, мгновенный стрим и асинхронный аудит.
- SSE-эндпоинт GET /api/v1/events/audit-stream с live-уведомлениями преподавателя и отпиской.
- Асинхронные вызовы в ThreadPool (retrieve_chunks_async, vector_store.add_slides).
"""

import pytest
import asyncio
import json
import time
from starlette.testclient import TestClient

from backend.main import app, reset_database, db_records, audit_broadcaster
from backend.vector_store import vector_store
from backend.rag_service import rag_service


@pytest.fixture(autouse=True)
def setup_db():
    reset_database()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def parse_sse_events(raw_text: str):
    """Вспомогательная функция для парсинга SSE событий из текста ответа."""
    events = []
    lines = raw_text.splitlines()
    for line in lines:
        line = line.strip()
        if line.startswith("data:"):
            json_str = line[len("data:"):].strip()
            if json_str:
                try:
                    events.append(json.loads(json_str))
                except Exception:
                    pass
    return events


def test_vector_store_warmup():
    """Тест прогрева векторного хранилища и эмбеддингов BAAI/bge-m3."""
    vector_store.warmup()
    assert vector_store.collection is not None
    # Проверяем, что модель инициализирована и способна генерировать эмбеддинги
    assert vector_store.embedding_fn._model is not None


def test_dialog_turn_stream_turn_1(client):
    """Тест 1-го шага через POST /api/v1/dialog/turn/stream: sources, delta, done."""
    start_resp = client.post("/api/v1/session/start", json={
        "student_id": "stud_stream_test",
        "course_id": "prog_ai_2026",
        "topic_id": "week_09_deep_learning",
        "force_open": True,
    })
    assert start_resp.status_code == 200
    session_id = start_resp.json()["session_id"]

    # Отправляем 1-й шаг на стриминговый эндпоинт
    resp = client.post("/api/v1/dialog/turn/stream", json={
        "session_id": session_id,
        "student_message": "Переобучение нейросети происходит из-за ко-адаптации весов под шум выборки.",
        "typing_duration_ms": 14000,
        "paste_detected": False,
    })

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    events = parse_sse_events(resp.text)
    event_types = [e.get("type") for e in events]

    assert "sources" in event_types
    assert "delta" in event_types
    assert "done" in event_types

    # Проверяем структуру источников
    sources_event = next(e for e in events if e.get("type") == "sources")
    assert isinstance(sources_event.get("sources"), list)

    # Проверяем, что дельты содержат текст
    delta_events = [e for e in events if e.get("type") == "delta"]
    assert len(delta_events) > 0
    full_text = "".join([d.get("text", "") for d in delta_events])
    assert len(full_text) > 10

    # Проверяем финальный done объект
    done_event = next(e for e in events if e.get("type") == "done")
    turn_res = done_event.get("turn_response")
    assert turn_res["session_id"] == session_id
    assert turn_res["turn_number"] == 1
    assert turn_res["is_duplicate"] is False
    assert turn_res["session_status"] == "INCOMPLETE_IGNORED"


def test_dialog_turn_stream_anti_spam(client):
    """Тест защиты от накрутки дубликатами в потоковом режиме."""
    start_resp = client.post("/api/v1/session/start", json={
        "student_id": "stud_spam_stream",
        "course_id": "prog_ai_2026",
        "topic_id": "week_09_deep_learning",
        "force_open": True,
    })
    session_id = start_resp.json()["session_id"]

    # Шаг 1
    msg = "Ко-адаптация весов приводит к оверфиттингу и ухудшению генерализации."
    resp1 = client.post("/api/v1/dialog/turn/stream", json={
        "session_id": session_id,
        "student_message": msg,
        "typing_duration_ms": 15000,
    })
    assert resp1.status_code == 200

    # Повтор того же сообщения
    resp2 = client.post("/api/v1/dialog/turn/stream", json={
        "session_id": session_id,
        "student_message": msg,
        "typing_duration_ms": 5000,
    })
    assert resp2.status_code == 200

    events2 = parse_sse_events(resp2.text)
    done_event = next(e for e in events2 if e.get("type") == "done")
    turn_res = done_event.get("turn_response")

    assert turn_res["is_duplicate"] is True
    assert turn_res["turn_number"] == 1  # Номер шага не увеличился
    assert "ПОВТОР" in turn_res["session_confidence"]


def test_dialog_turn_stream_step_3_and_background_audit(client):
    """
    Тест 3-го шага диалога:
    - Потоковый ответ мгновенно отдает status AUDITING.
    - В фоне запускается расчет ThemisMathEngine и Evidence-First.
    - По завершении статус обновляется на COMPLETED и запись получает ai_depth_score.
    """
    start_resp = client.post("/api/v1/session/start", json={
        "student_id": "stud_stream_complete",
        "course_id": "prog_ai_2026",
        "topic_id": "topic_05_regularization",
        "force_open": True,
    })
    session_id = start_resp.json()["session_id"]

    # Шаг 1
    client.post("/api/v1/dialog/turn/stream", json={
        "session_id": session_id,
        "student_message": "Переобучение происходит, когда веса подстраиваются под специфический шум выборки, создавая избыточную ко-адаптацию нейронов.",
        "typing_duration_ms": 15000,
    })

    # Шаг 2
    client.post("/api/v1/dialog/turn/stream", json={
        "session_id": session_id,
        "student_message": "Dropout случайным образом обнуляет активации нейронов с вероятностью p во время прямого прохода. Это заставляет каждый нейрон обучаться полезным признакам независимо от соседей, имитируя ансамбль подсетей.",
        "typing_duration_ms": 18000,
    })

    # Шаг 3
    resp3 = client.post("/api/v1/dialog/turn/stream", json={
        "session_id": session_id,
        "student_message": "Если Dropout так эффективен, почему бы нам не выключать 80% нейронов для максимальной регуляризации? В какой момент это сломает обучение и вызовет потерю емкости сети (underfitting)?",
        "typing_duration_ms": 22000,
    })
    assert resp3.status_code == 200

    events3 = parse_sse_events(resp3.text)
    done_event = next(e for e in events3 if e.get("type") == "done")
    turn_res = done_event.get("turn_response")

    # Студент сразу получает статус AUDITING
    assert turn_res["turn_number"] == 3
    assert turn_res["session_status"] == "AUDITING"
    assert "AUDITING" in turn_res["session_confidence"]

    # Даем фоновой асинхронной задаче завершиться (до 2 секунд)
    for _ in range(20):
        rec = db_records.get("stud_stream_complete")
        if rec and rec.session_status == "COMPLETED" and rec.ai_depth_score is not None:
            break
        time.sleep(0.1)

    rec = db_records["stud_stream_complete"]
    assert rec.session_status == "COMPLETED"
    assert rec.extraction is not None
    assert rec.ai_depth_score is not None
    assert rec.ai_depth_score >= 70.0
    assert rec.zone in ("HIGH_DISCREPANCY", "AUDIT_TRIGGER", "WATCHLIST", "NORMAL")


def test_audit_stream_sse_endpoint(client):
    """
    Тест SSE-эндпоинта уведомлений преподавателя GET /api/v1/events/audit-stream:
    - Подключение к потоку;
    - Получение connected события;
    - Получение audit_completed при бродкасте;
    - Безопасная отписка очереди.
    """
    initial_sub_count = len(audit_broadcaster._subscribers)

    with client.stream("GET", "/api/v1/events/audit-stream") as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        assert len(audit_broadcaster._subscribers) == initial_sub_count + 1

        lines = resp.iter_lines()
        first_line = next(lines)
        while not first_line.startswith("data:"):
            first_line = next(lines)
        connected_data = json.loads(first_line[len("data:"):].strip())
        assert connected_data["type"] == "connected"

        # Симулируем событие завершения аудита через broadcast
        test_payload = {
            "type": "audit_completed",
            "student_id": "stud_broadcast_test",
            "record": {
                "student_id": "stud_broadcast_test",
                "in_class_grade": 70.0,
                "ai_depth_score": 92.5,
                "rectified_delta": 22.5,
                "z_score": 3.1,
                "zone": "HIGH_DISCREPANCY",
                "session_status": "COMPLETED",
            }
        }
        # Запускаем отправку в event loop
        asyncio.run(audit_broadcaster.broadcast(test_payload))

        # Читаем следующее событие
        second_line = next(lines)
        while not second_line.startswith("data:"):
            second_line = next(lines)
        audit_event = json.loads(second_line[len("data:"):].strip())
        assert audit_event["type"] == "audit_completed"
        assert audit_event["student_id"] == "stud_broadcast_test"
        assert audit_event["record"]["ai_depth_score"] == 92.5

    # После закрытия стрима подписчик должен быть удален
    assert len(audit_broadcaster._subscribers) == initial_sub_count


def test_async_threadpool_operations():
    """Тест неблокирующего вызова retrieve_chunks_async."""
    chunks = asyncio.run(rag_service.retrieve_chunks_async(
        query="регуляризация Dropout ко-адаптация нейронов",
        topic_id="week_09_deep_learning",
        top_k=2
    ))
    assert isinstance(chunks, list)
