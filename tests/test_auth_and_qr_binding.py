"""
test_auth_and_qr_binding.py

Интеграционные и модульные тесты для:
1. Таблицы учетных данных `user_credentials` (20 студентов + преподаватель).
2. Эндпоинтов авторизации:
   - POST /api/v1/auth/login
   - GET /api/v1/auth/me
   - POST /api/v1/auth/logout
3. Одноразового Deep Link и QR-кода привязки:
   - GET /api/v1/auth/telegram-qr
   - Таблицы `telegram_binding_tokens` (статусы PENDING, USED, EXPIRED).
4. Обработки `/start bind_<token>` в Telegram-боте:
   - Успешная привязка Telegram-сессии к student_id.
   - Сжигание одноразового токена (перевод в USED).
   - Защита от Replay Attack (повторное использование токена отклоняется).
   - Защита от просроченных токенов (TTL 15 минут).
   - Рассылка события `telegram_linked` в SSE AuditBroadcaster.
"""

import pytest
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from starlette.testclient import TestClient

from backend.main import app, reset_database, audit_broadcaster
from backend.database import (
    get_connection,
    get_user_credential,
    verify_password,
    get_all_user_credentials,
    create_telegram_binding_token,
    get_telegram_binding_token,
    get_student_identity,
    link_telegram_identity,
)
from backend.seed_data import GROUP_1_STUDENT_IDS


@pytest.fixture(autouse=True)
def setup_db():
    reset_database(load_from_db_if_exists=False)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_default_user_credentials_seeded():
    """Проверка, что в БД инициализированы 20 студентов и преподаватель."""
    # 1. 20 студентов через stud_01 .. stud_20
    for idx in range(1, 21):
        uname = f"stud_{idx:02d}"
        cred = get_user_credential(uname)
        assert cred is not None, f"Учетная запись {uname} не найдена"
        assert cred["role"] == "student"
        assert verify_password("themis2026", cred["password_hash"])
        assert cred["student_id"] in GROUP_1_STUDENT_IDS

    # 2. Алиасы Студента К.
    for alias in ["stud_aai_042", "student_k", "stud_05"]:
        cred = get_user_credential(alias)
        assert cred is not None, f"Алиас {alias} не найден"
        assert cred["student_id"] == "stud_aai_042"
        assert cred["role"] == "student"
        assert verify_password("themis2026", cred["password_hash"])

    # 3. Преподаватель Белощицкая С.
    teacher_cred = get_user_credential("teacher")
    assert teacher_cred is not None
    assert teacher_cred["role"] == "teacher"
    assert verify_password("themis_prof_2026", teacher_cred["password_hash"])


def test_login_student_success(client):
    """Успешный вход студента по логину stud_01."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "stud_01",
        "password": "themis2026"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "themis_sess_" in data["token"]
    assert data["role"] == "student"
    assert data["student_id"] == "stud_aai_042"
    assert "Студент К." in data["display_name"]
    assert isinstance(data["is_telegram_linked"], bool)


def test_login_student_aliases(client):
    """Проверка входа по алиасам student_k и stud_aai_042."""
    for alias in ["student_k", "stud_aai_042", "stud_05"]:
        resp = client.post("/api/v1/auth/login", json={
            "username": alias,
            "password": "themis2026"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["student_id"] == "stud_aai_042"
        assert data["role"] == "student"


def test_login_teacher_success(client):
    """Успешный вход преподавателя."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "teacher",
        "password": "themis_prof_2026"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["role"] == "teacher"
    assert "Белощицкая" in data["display_name"]
    assert data["student_id"] is None


def test_login_invalid_password(client):
    """Попытка входа с неверным паролем."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "stud_01",
        "password": "wrong_password"
    })
    assert resp.status_code == 401
    assert "Неверное имя пользователя или пароль" in resp.json()["detail"]


def test_login_nonexistent_user(client):
    """Попытка входа несуществующего пользователя."""
    resp = client.post("/api/v1/auth/login", json={
        "username": "unknown_hacker",
        "password": "themis2026"
    })
    assert resp.status_code == 401


def test_auth_me_endpoint(client):
    """Проверка эндпоинта /api/v1/auth/me с токеном и без него."""
    # Без токена -> 401
    resp_unauth = client.get("/api/v1/auth/me")
    assert resp_unauth.status_code == 401

    # Входим
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "stud_01",
        "password": "themis2026"
    })
    token = login_resp.json()["token"]

    # С заголовком Authorization: Bearer <token>
    resp_auth = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp_auth.status_code == 200
    me_data = resp_auth.json()
    assert me_data["authenticated"] is True
    assert me_data["student_id"] == "stud_aai_042"
    assert me_data["role"] == "student"

    # С query-параметром ?token=<token>
    resp_query = client.get(f"/api/v1/auth/me?token={token}")
    assert resp_query.status_code == 200
    assert resp_query.json()["student_id"] == "stud_aai_042"


def test_auth_logout(client):
    """Проверка выхода из системы."""
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "teacher",
        "password": "themis_prof_2026"
    })
    token = login_resp.json()["token"]

    # Выход
    logout_resp = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["success"] is True

    # Проверка, что сессия более не действительна
    check_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert check_resp.status_code == 401


def test_generate_telegram_qr_endpoint(client):
    """Генерация одноразового Deep Link и токена привязки Telegram."""
    resp = client.get("/api/v1/auth/telegram-qr?student_id=stud_aai_042")
    assert resp.status_code == 200
    data = resp.json()

    assert data["token"].startswith("bind_")
    assert len(data["token"]) >= 10
    assert "https://t.me/" in data["deep_link"]
    assert f"start={data['token']}" in data["deep_link"]
    assert data["expires_in"] == 900
    assert "qrserver.com" in data["qr_code_url"]

    # Проверяем запись в SQLite
    binding = get_telegram_binding_token(data["token"])
    assert binding is not None
    assert binding["student_id"] == "stud_aai_042"
    assert binding["status"] == "PENDING"


def test_telegram_bot_one_time_binding_success(client):
    """
    Полный сценарий привязки:
    1. Генерация одноразового токена.
    2. Отправка webhook от Telegram (/start bind_<token>).
    3. Проверка успешного ответа, сжигания токена и обновления student_identities.
    """
    # 1. Генерируем токен
    qr_resp = client.get("/api/v1/auth/telegram-qr?student_id=stud_aai_042")
    token = qr_resp.json()["token"]

    # 2. Имитируем входящее сообщение от Telegram пользователя (@batman99, id: 98765432)
    webhook_payload = {
        "update_id": 1001,
        "message": {
            "message_id": 55,
            "chat": {"id": 98765432, "type": "private"},
            "from": {
                "id": 98765432,
                "first_name": "Брюс",
                "username": "batman99"
            },
            "text": f"/start {token}"
        }
    }

    wb_resp = client.post("/api/v1/tma/webhook", json=webhook_payload)
    assert wb_resp.status_code == 200
    res = wb_resp.json()["result"]
    assert res["ok"] is True
    assert res["action"] == "binding_success"
    assert res["student_id"] == "stud_aai_042"
    assert res["telegram_id"] == 98765432
    assert res["telegram_username"] == "@batman99"

    # 3. Проверяем, что токен сожжен (status = 'USED')
    token_in_db = get_telegram_binding_token(token)
    assert token_in_db["status"] == "USED"

    # 4. Проверяем, что student_identities обновился
    identity = get_student_identity("stud_aai_042")
    assert identity["telegram_id"] == 98765432
    assert identity["telegram_username"] == "@batman99"

    # 5. Проверяем, что /api/v1/auth/me теперь сообщает is_telegram_linked = True
    login_resp = client.post("/api/v1/auth/login", json={
        "username": "stud_01",
        "password": "themis2026"
    })
    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_resp.json()['token']}"}
    )
    assert me_resp.json()["is_telegram_linked"] is True
    assert me_resp.json()["telegram_username"] == "@batman99"


def test_telegram_bot_replay_attack_protection(client):
    """
    Защита от Replay Attack:
    Повторное использование уже использованного токена должно отклоняться.
    """
    # Генерируем токен и используем его в первый раз
    qr_resp = client.get("/api/v1/auth/telegram-qr?student_id=stud_aai_042")
    token = qr_resp.json()["token"]

    webhook_payload = {
        "update_id": 2001,
        "message": {
            "message_id": 60,
            "chat": {"id": 11111, "type": "private"},
            "from": {"id": 11111, "username": "user1"},
            "text": f"/start {token}"
        }
    }
    resp1 = client.post("/api/v1/tma/webhook", json=webhook_payload)
    assert resp1.json()["result"]["action"] == "binding_success"

    # Повторная попытка с тем же токеном (например от другого аккаунта)
    replay_payload = {
        "update_id": 2002,
        "message": {
            "message_id": 61,
            "chat": {"id": 22222, "type": "private"},
            "from": {"id": 22222, "username": "intruder"},
            "text": f"/start {token}"
        }
    }
    resp2 = client.post("/api/v1/tma/webhook", json=replay_payload)
    assert resp2.status_code == 200
    res2 = resp2.json()["result"]
    assert res2["action"] == "binding_rejected"
    assert res2["reason"] == "USED"

    # Проверяем, что студент не был перепривязан на взломщика
    identity = get_student_identity("stud_aai_042")
    assert identity["telegram_id"] == 11111


def test_telegram_bot_expired_token(client):
    """Защита от просроченных токенов привязки."""
    # Создаем заведомо просроченный токен вручную в SQLite
    token = f"bind_expired_{uuid.uuid4().hex[:8]}"
    past_time = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO telegram_binding_tokens (token, student_id, status, expires_at)
        VALUES (?, 'stud_aai_001', 'PENDING', ?)
    """, (token, past_time))
    conn.commit()
    conn.close()

    webhook_payload = {
        "update_id": 3001,
        "message": {
            "message_id": 70,
            "chat": {"id": 33333, "type": "private"},
            "from": {"id": 33333, "username": "late_student"},
            "text": f"/start {token}"
        }
    }
    resp = client.post("/api/v1/tma/webhook", json=webhook_payload)
    assert resp.status_code == 200
    res = resp.json()["result"]
    assert res["action"] == "binding_rejected"
    assert res["reason"] == "EXPIRED"


def test_audit_broadcaster_receives_telegram_linked_event(client):
    """Проверка, что AuditBroadcaster рассылает SSE-событие telegram_linked при привязке."""
    from backend.telegram_bot import telegram_bot
    sub_q = audit_broadcaster.subscribe()
    try:
        # Генерируем токен
        qr_resp = client.get("/api/v1/auth/telegram-qr?student_id=stud_aai_002")
        token = qr_resp.json()["token"]

        # Вызываем вебхук привязки через telegram_bot
        webhook_payload = {
            "update_id": 4001,
            "message": {
                "message_id": 80,
                "chat": {"id": 44444, "type": "private"},
                "from": {"id": 44444, "username": "aigerim_ai"},
                "text": f"/start {token}"
            }
        }
        res = asyncio.run(telegram_bot.handle_update(webhook_payload))
        assert res["ok"] is True
        assert res["action"] == "binding_success"

        # Проверяем доставку события в очередь подписчика
        assert not sub_q.empty()
        event = sub_q.get_nowait()
        assert event["type"] == "telegram_linked"
        assert event["student_id"] == "stud_aai_002"
        assert event["telegram_id"] == 44444
        assert event["telegram_username"] == "@aigerim_ai"
    finally:
        audit_broadcaster.unsubscribe(sub_q)
