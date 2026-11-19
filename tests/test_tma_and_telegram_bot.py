"""
test_tma_and_telegram_bot.py

Тесты для Шага 6:
- Криптографическая валидация Telegram.WebApp.initData по алгоритму HMAC-SHA256.
- Проверка защиты от модификации данных, устаревания auth_date и Dev/Demo fallback.
- Создание цифровой личности («Zero-Friction» гостевой вход для жюри/студентов stud_tg_<id>).
- Связка существующего student_id с telegram_id (POST /api/v1/tma/link).
- Разрешение контекста студента через FastAPI dependency (resolve_student_context).
- Раздача мобильного интерфейса GET /tma (tma.html).
- Эндпоинты TMA: GET /api/v1/tma/me, POST /api/v1/session/opt-out.
- Webhook Telegram Bot API: /start с deep linking, /help, callbacks.
"""

import pytest
import time
import json
import urllib.parse
from starlette.testclient import TestClient

from backend.main import app, reset_database, db_records
from backend.config import settings
from backend.tma_auth import (
    parse_and_validate_init_data,
    create_test_init_data,
    get_or_create_telegram_student,
)
from backend.database import (
    get_connection,
    get_student_identity,
    get_student_identity_by_telegram_id,
    get_student_audit,
)
from backend.telegram_bot import telegram_bot


@pytest.fixture(autouse=True)
def setup_db():
    reset_database()
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM student_identities WHERE telegram_id IS NOT NULL")
    conn.commit()
    conn.close()
    yield


@pytest.fixture
def client():
    return TestClient(app)


# =====================================================================
# 1. ТЕСТЫ КРИПТОГРАФИЧЕСКОЙ ВАЛИДАЦИИ initData
# =====================================================================

def test_tma_crypto_valid_signature():
    """Тест успешной криптографической валидации initData с валидным HMAC-SHA256."""
    bot_token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz_TEST"
    user_data = {
        "id": 88442211,
        "first_name": "Айдар",
        "last_name": "Мусин",
        "username": "aidar_m",
        "language_code": "ru"
    }
    
    init_data = create_test_init_data(user=user_data, bot_token=bot_token)
    
    # Валидация с тем же токеном
    is_valid, parsed, err = parse_and_validate_init_data(
        init_data,
        bot_token=bot_token,
        allow_dev_mode=False
    )
    
    assert is_valid is True
    assert err is None
    assert parsed is not None
    assert parsed["user"]["id"] == 88442211
    assert parsed["user"]["first_name"] == "Айдар"
    assert parsed["user"]["username"] == "aidar_m"


def test_tma_crypto_tampered_data_fails():
    """Тест: любая модификация данных в initData нарушает подпись и отклоняется."""
    bot_token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz_TEST"
    user_data = {"id": 11223344, "first_name": "Хакер"}
    
    init_data = create_test_init_data(user=user_data, bot_token=bot_token)
    
    # Злоумышленник пытается подменить id пользователя в строке query
    tampered_init_data = init_data.replace("11223344", "99999999")
    
    is_valid, parsed, err = parse_and_validate_init_data(
        tampered_init_data,
        bot_token=bot_token,
        allow_dev_mode=False
    )
    
    assert is_valid is False
    assert parsed is None
    assert "signature mismatch" in err.lower() or "mismatch" in err.lower()


def test_tma_crypto_expired_auth_date():
    """Тест: устаревшая строка initData (старше TTL 86400 сек) отклоняется."""
    bot_token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz_TEST"
    user_data = {"id": 55667788, "first_name": "Студент"}
    
    # auth_date 2 дня назад
    expired_date = int(time.time()) - (2 * 86400)
    init_data = create_test_init_data(user=user_data, bot_token=bot_token, auth_date=expired_date)
    
    is_valid, parsed, err = parse_and_validate_init_data(
        init_data,
        bot_token=bot_token,
        max_age_seconds=86400,
        allow_dev_mode=False
    )
    
    assert is_valid is False
    assert "expired" in err.lower()


def test_tma_dev_mode_fallback():
    """Тест: в режиме DEV (bot_token='dev') разрешается работа для локального тестирования."""
    user_data = {"id": 77711122, "first_name": "Жюри Демо"}
    init_data = create_test_init_data(user=user_data, bot_token="dev")
    
    is_valid, parsed, err = parse_and_validate_init_data(
        init_data,
        bot_token="dev",
        allow_dev_mode=True
    )
    
    assert is_valid is True
    assert parsed["user"]["first_name"] == "Жюри Демо"


# =====================================================================
# 2. ТЕСТЫ СОЗДАНИЯ ЦИФРОВОЙ ЛИЧНОСТИ И СВЯЗКИ ID
# =====================================================================

def test_get_or_create_telegram_student_guest():
    """Тест Zero-Friction регистрации нового студента/члена жюри из Telegram."""
    tg_user = {
        "id": 99887766,
        "first_name": "Ерлан",
        "last_name": "Аудитор",
        "username": "erlan_jury"
    }
    
    student_id = get_or_create_telegram_student(tg_user, default_grade=78.0)
    assert student_id == "stud_tg_99887766"
    
    # Проверяем запись в student_identities
    identity = get_student_identity_by_telegram_id(99887766)
    assert identity is not None
    assert identity["student_id"] == "stud_tg_99887766"
    assert identity["display_name"] == "Ерлан Аудитор"
    assert identity["telegram_username"] == "erlan_jury"
    assert identity["default_grade"] == 78.0
    
    # Проверяем начальную запись в student_audits
    audit = get_student_audit(student_id)
    assert audit is not None
    assert audit["in_class_grade"] == 78.0
    assert audit["session_status"] == "OPTED_OUT"
    assert audit["zone"] == "NO_SIGNAL"
    
    # Повторный вызов не создает дубликат, а возвращает тот же student_id
    re_id = get_or_create_telegram_student(tg_user)
    assert re_id == student_id


def test_tma_link_existing_student(client):
    """Тест связки существующего студента ведомости (stud_aai_042) с telegram_id."""
    payload = {
        "student_id": "stud_aai_042",
        "telegram_id": 33445566,
        "telegram_username": "student_k_tg"
    }
    
    resp = client.post("/api/v1/tma/link", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    assert data["student_id"] == "stud_aai_042"
    assert data["telegram_id"] == 33445566
    
    # Проверяем, что теперь get_student_identity_by_telegram_id находит stud_aai_042
    linked = get_student_identity_by_telegram_id(33445566)
    assert linked is not None
    assert linked["student_id"] == "stud_aai_042"


# =====================================================================
# 3. ТЕСТЫ ЭНДПОИНТОВ TMA (GET /tma, GET /api/v1/tma/me, OPT-OUT)
# =====================================================================

def test_serve_tma_html(client):
    """Тест раздачи статического интерфейса мобильного приложения GET /tma."""
    resp = client.get("/tma")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]
    html = resp.text
    assert "telegram-web-app.js" in html
    assert "Themis Project" in html
    assert "chat-messages" in html
    assert "visualViewport" in html or "100dvh" in html


def test_tma_me_endpoint_with_auth_header(client):
    """Тест получения профиля через GET /api/v1/tma/me с заголовком Authorization: tma <initData>."""
    tg_user = {
        "id": 44332211,
        "first_name": "Дана",
        "last_name": "Серикова",
        "username": "dana_s"
    }
    init_data = create_test_init_data(user=tg_user, bot_token=settings.TELEGRAM_BOT_TOKEN)
    
    resp = client.get("/api/v1/tma/me", headers={"Authorization": f"tma {init_data}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["student_id"] == "stud_tg_44332211"
    assert data["display_name"] == "Дана Серикова"
    assert data["in_class_grade"] == 75.0
    assert data["session_status"] == "OPTED_OUT"


def test_tma_session_start_and_opt_out(client):
    """
    Тест полного цикла добровольности UDL:
    - Старт сессии через TMA авторизацию;
    - Добровольный выход без штрафа (POST /api/v1/session/opt-out);
    - Гарантия сохранения очной оценки (Zero Downward Penalty).
    """
    tg_user = {"id": 12300077, "first_name": "Тест", "last_name": "Пандус"}
    init_data = create_test_init_data(user=tg_user, bot_token=settings.TELEGRAM_BOT_TOKEN)
    headers = {"Authorization": f"tma {init_data}"}
    
    # 1. Старт сессии
    start_resp = client.post("/api/v1/session/start", json={
        "student_id": "me",
        "course_id": "prog_ai_2026",
        "topic_id": "week_09_deep_learning",
        "force_open": True
    }, headers=headers)
    
    assert start_resp.status_code == 200
    s_data = start_resp.json()
    session_id = s_data["session_id"]
    assert "session_id" in s_data
    
    # 2. Проверяем active/me
    active_resp = client.get("/api/v1/session/active/me?topic_id=week_09_deep_learning", headers=headers)
    assert active_resp.status_code == 200
    act_data = active_resp.json()
    assert act_data["student_id"] == "stud_tg_12300077"
    assert act_data["session_id"] == session_id
    
    # 3. Добровольный выход (Opt-Out)
    opt_resp = client.post("/api/v1/session/opt-out", json={
        "session_id": session_id,
        "student_id": "stud_tg_12300077"
    }, headers=headers)
    
    assert opt_resp.status_code == 200
    opt_data = opt_resp.json()
    assert opt_data["status"] == "OPTED_OUT"
    assert opt_data["in_class_grade"] == 75.0
    assert opt_data["rectified_delta"] == 0.0
    assert "полностью сохранена" in opt_data["message"]


# =====================================================================
# 4. ТЕСТЫ WEBHOOK TELEGRAM BOT API
# =====================================================================

def test_telegram_bot_webhook_start_command(client):
    """Тест обработки команды /start в webhook Telegram бота."""
    update = {
        "update_id": 1001,
        "message": {
            "message_id": 42,
            "from": {
                "id": 991122,
                "first_name": "Болат",
                "username": "bolat_t"
            },
            "chat": {
                "id": 991122,
                "type": "private"
            },
            "text": "/start"
        }
    }
    
    resp = client.post("/api/v1/tma/webhook", json=update)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["result"]["action"] == "start_handled"


def test_telegram_bot_webhook_start_deep_linking(client):
    """Тест deep linking: /start pai_week_09 формирует URL с конкретной темой."""
    update = {
        "update_id": 1002,
        "message": {
            "message_id": 43,
            "from": {
                "id": 991133,
                "first_name": "Студент",
                "username": "student_deep"
            },
            "chat": {
                "id": 991133,
                "type": "private"
            },
            "text": "/start pai_week_09"
        }
    }
    
    resp = client.post("/api/v1/tma/webhook", json=update)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["result"]["action"] == "start_handled"
    assert data["result"]["start_param"] == "pai_week_09"
    
    # Проверяем генерацию URL клавиатуры
    tma_url = telegram_bot.build_tma_url("pai_week_09")
    assert "/tma" in tma_url
    assert "week_09_deep_learning" in tma_url


def test_telegram_bot_webhook_help_and_callback(client):
    """Тест команд /help и callback query в webhook Telegram бота."""
    # 1. /help
    resp_help = client.post("/api/v1/tma/webhook", json={
        "update_id": 1003,
        "message": {
            "message_id": 44,
            "chat": {"id": 991144},
            "text": "/help"
        }
    })
    assert resp_help.status_code == 200
    assert resp_help.json()["result"]["action"] == "help_handled"

    # 2. Callback info_udl
    resp_cb = client.post("/api/v1/tma/webhook", json={
        "update_id": 1004,
        "callback_query": {
            "id": "cq_123",
            "data": "info_udl",
            "message": {
                "chat": {"id": 991144}
            }
        }
    })
    assert resp_cb.status_code == 200
    assert resp_cb.json()["result"]["action"] == "callback_handled"
