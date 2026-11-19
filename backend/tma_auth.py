"""
tma_auth.py

Криптографическая авторизация Telegram Mini App (TMA),
валидация initData по спецификации Telegram Bot API,
связка telegram_id <-> student_id (Zero-Friction гостевой вход)
и внедрение зависимости FastAPI resolve_student_context.
"""

import hmac
import hashlib
import json
import time
import urllib.parse
import logging
from typing import Dict, Any, Optional, Tuple
from fastapi import Request, HTTPException

from backend.config import settings
from backend.database import (
    get_student_identity,
    get_student_identity_by_telegram_id,
    save_student_identity,
    save_student_audit,
    CANONICAL_COURSE_ID,
    CANONICAL_TOPIC_ID,
)

logger = logging.getLogger("themis.tma_auth")

DEFAULT_INIT_DATA_TTL = 86400  # 24 часа


def parse_and_validate_init_data(
    init_data_raw: str,
    bot_token: Optional[str] = None,
    max_age_seconds: int = DEFAULT_INIT_DATA_TTL,
    allow_dev_mode: bool = True
) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Криптографическая валидация строки Telegram.WebApp.initData по официальному алгоритму Telegram:
    1. Извлекается параметр `hash`.
    2. Все остальные query-параметры сортируются по алфавиту в формате `key=value\n`.
    3. Вычисляется `secret_key = HMAC-SHA256(b"WebAppData", bot_token)`.
    4. Вычисляется `HMAC-SHA256(secret_key, data_check_string)`.
    5. Сверяется с `hash` через безопасное сравнение `hmac.compare_digest`.
    6. Проверяется свежесть `auth_date` (TTL <= max_age_seconds).
    
    Поддерживает Dev/Demo режим (если bot_token='dev'/'test' или не задан).
    
    Возвращает: (is_valid, parsed_data_dict, error_message)
    """
    if not init_data_raw or not isinstance(init_data_raw, str):
        return False, None, "initData is empty or not a string"

    token = bot_token or settings.TELEGRAM_BOT_TOKEN
    is_dev_token = token in ("", "dev", "test")

    try:
        # Разбор query-строки (parse_qsl декодирует URL-encoded символы)
        pairs = urllib.parse.parse_qsl(init_data_raw, keep_blank_values=True)
        if not pairs:
            return False, None, "Failed to parse query string"
        
        parsed_dict: Dict[str, str] = dict(pairs)
    except Exception as e:
        return False, None, f"Query parsing exception: {str(e)}"

    provided_hash = parsed_dict.get("hash")
    if not provided_hash:
        return False, None, "Missing 'hash' parameter in initData"

    # Извлечение JSON структуры user
    user_data = None
    if "user" in parsed_dict:
        try:
            user_data = json.loads(parsed_dict["user"])
        except Exception as e:
            return False, None, f"Failed to parse 'user' JSON: {str(e)}"

    # Проверка свежести auth_date
    auth_date_str = parsed_dict.get("auth_date")
    if auth_date_str:
        try:
            auth_date = int(auth_date_str)
            current_time = int(time.time())
            if current_time - auth_date > max_age_seconds:
                if not (allow_dev_mode and is_dev_token):
                    return False, None, f"initData expired (age {current_time - auth_date}s > {max_age_seconds}s)"
                else:
                    logger.warning("TMA Auth: auth_date expired but allowed in DEV mode")
        except ValueError:
            return False, None, "Invalid auth_date integer"
    else:
        if not (allow_dev_mode and is_dev_token):
            return False, None, "Missing auth_date parameter"

    # Формирование data_check_string: ключи сортируются по алфавиту (кроме hash)
    sorted_pairs = []
    for k, v in sorted(parsed_dict.items()):
        if k != "hash":
            sorted_pairs.append(f"{k}={v}")
    data_check_string = "\n".join(sorted_pairs)

    # В Dev-режиме с тестовым токеном разрешаем упрощенную валидацию
    if allow_dev_mode and is_dev_token:
        # Проверяем, если хеш совпадает с тестовым расчетом — отлично,
        # если нет — логируем предупреждение и пропускаем (для удобства мок-тестов)
        secret_key = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
        calc_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc_hash, provided_hash):
            logger.warning("TMA Auth: signature mismatch in DEV mode; allowing for demo/test purposes")
        
        result_payload = {**parsed_dict, "user": user_data}
        return True, result_payload, None

    # Боевая криптографическая проверка
    secret_key = hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, provided_hash):
        return False, None, "Cryptographic HMAC-SHA256 signature mismatch"

    result_payload = {**parsed_dict, "user": user_data}
    return True, result_payload, None


def create_test_init_data(
    user: Dict[str, Any],
    bot_token: str = "dev",
    auth_date: Optional[int] = None,
    query_id: Optional[str] = "AAHd78x1AAAAAN3v_Vw",
    **extra_params
) -> str:
    """
    Генерирует криптографически корректную строку initData для автотестов и интеграции.
    """
    if auth_date is None:
        auth_date = int(time.time())

    params: Dict[str, str] = {
        "auth_date": str(auth_date),
        "user": json.dumps(user, separators=(",", ":"), ensure_ascii=False),
    }
    if query_id:
        params["query_id"] = query_id
    for k, v in extra_params.items():
        params[k] = str(v)

    # data_check_string
    sorted_pairs = [f"{k}={v}" for k, v in sorted(params.items())]
    data_check_string = "\n".join(sorted_pairs)

    # HMAC-SHA256
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    sig = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    params["hash"] = sig

    return urllib.parse.urlencode(params)


def get_or_create_telegram_student(
    telegram_user: Dict[str, Any],
    course_id: str = CANONICAL_COURSE_ID,
    default_grade: float = 75.0
) -> str:
    """
    Бесшовный вход («Zero-Friction» для жюри и студентов в TMA):
    1. Ищет профиль в student_identities по telegram_id.
    2. Если найден — возвращает связанный student_id.
    3. Если не найден — регистрирует stud_tg_<telegram_id>, сохраняет ФИО из профиля
       Telegram и создает начальную запись в student_audits (с безопасным статусом OPTED_OUT
       и базовой оценкой G_prof = default_grade), чтобы студент сразу появился на дашборде.
    """
    raw_tg_id = telegram_user.get("id")
    if not raw_tg_id:
        raise ValueError("telegram_user dict must contain 'id'")
    telegram_id = int(raw_tg_id)

    # 1. Поиск по telegram_id в БД
    existing = get_student_identity_by_telegram_id(telegram_id)
    if existing:
        student_id = existing["student_id"]
        # Гарантируем наличие записи в student_audits даже после сброса базы
        try:
            from backend.database import get_student_audit
            existing_audit = get_student_audit(student_id)
            if not existing_audit:
                grade = existing.get("default_grade", default_grade)
                disp_name = existing.get("display_name", student_id)
                save_student_audit(
                    student_id=student_id,
                    student_name=disp_name,
                    group_id=existing.get("group_id", "group_1"),
                    in_class_grade=grade,
                    session_status="OPTED_OUT",
                    turns_count=0,
                    total_tokens=0,
                    ai_depth_score=None,
                    raw_delta=0.0,
                    rectified_delta=0.0,
                    z_score=0.0,
                    zone="NO_SIGNAL",
                    course_id=course_id,
                    topic_id=CANONICAL_TOPIC_ID,
                    telemetry_clean=True,
                )
        except Exception as e:
            logger.debug(f"Audit check on existing TMA student deferred: {e}")

        # Синхронизация с in-memory db_records
        try:
            from backend.main import db_records
            from backend.models_schemas import StudentAuditRecord
            if student_id not in db_records:
                rec_grade = existing.get("default_grade", default_grade)
                db_records[student_id] = StudentAuditRecord(
                    student_id=student_id,
                    course_id=course_id,
                    topic_id=CANONICAL_TOPIC_ID,
                    student_name=existing.get("display_name", student_id),
                    group_id=existing.get("group_id", "group_1"),
                    in_class_grade=rec_grade,
                    session_status="OPTED_OUT",
                    turns_count=0,
                    total_tokens=0,
                    ai_depth_score=None,
                    raw_delta=0.0,
                    rectified_delta=0.0,
                    z_score=0.0,
                    zone="NO_SIGNAL",
                    telemetry_clean=True,
                )
        except Exception:
            pass

        return student_id

    # 2. Создание нового профиля
    student_id = f"stud_tg_{telegram_id}"
    first_name = (telegram_user.get("first_name") or "").strip()
    last_name = (telegram_user.get("last_name") or "").strip()
    username = telegram_user.get("username")

    display_name = f"{first_name} {last_name}".strip()
    if not display_name:
        display_name = f"@{username}" if username else f"Студент TMA #{telegram_id % 10000}"

    # Сохраняем в student_identities
    save_student_identity(
        student_id=student_id,
        display_name=display_name,
        telegram_id=telegram_id,
        telegram_username=username,
        group_id="group_1",
        default_grade=default_grade,
    )

    # Создаем базовую очную запись в student_audits
    save_student_audit(
        student_id=student_id,
        student_name=display_name,
        group_id="group_1",
        in_class_grade=default_grade,
        session_status="OPTED_OUT",
        turns_count=0,
        total_tokens=0,
        ai_depth_score=None,
        raw_delta=0.0,
        rectified_delta=0.0,
        z_score=0.0,
        zone="NO_SIGNAL",
        course_id=course_id,
        topic_id=CANONICAL_TOPIC_ID,
        telemetry_clean=True,
    )

    # Синхронизация с in-memory db_records (если приложение запущено)
    try:
        from backend.main import db_records, engine
        from backend.models_schemas import StudentAuditRecord
        if student_id not in db_records:
            rec = StudentAuditRecord(
                student_id=student_id,
                course_id=course_id,
                topic_id=CANONICAL_TOPIC_ID,
                student_name=display_name,
                group_id="group_1",
                in_class_grade=default_grade,
                session_status="OPTED_OUT",
                turns_count=0,
                total_tokens=0,
                ai_depth_score=None,
                raw_delta=0.0,
                rectified_delta=0.0,
                z_score=0.0,
                zone="NO_SIGNAL",
                telemetry_clean=True,
            )
            db_records[student_id] = rec
            engine.compute_cohort_discrepancy(list(db_records.values()))
    except Exception as e:
        logger.debug(f"In-memory sync skipped/deferred: {e}")

    logger.info(f"Создан новый студент из Telegram Mini App: {student_id} ({display_name})")
    return student_id


async def resolve_student_context(request: Request) -> str:
    """
    Зависимость FastAPI для идентификации студента:
    1. Проверяет заголовок Authorization: tma <initData> или X-Telegram-Init-Data.
    2. При наличии валидирует криптографическую подпись Telegram и возвращает student_id.
    3. При отсутствии делает безопасный fallback на query/path/body student_id
       (для Web-интерфейса и тестового режима).
    """
    # 1. Извлечение TMA initData из заголовков или query
    auth_header = request.headers.get("Authorization", "")
    tma_header = request.headers.get("X-Telegram-Init-Data", "")
    query_init_data = request.query_params.get("init_data", "")

    raw_init_data = ""
    if auth_header:
        parts = auth_header.split(maxsplit=1)
        if len(parts) == 2 and parts[0].lower() in ("tma", "bearer"):
            # Проверяем, похож ли токен на query-параметры Telegram (содержит hash=)
            if "hash=" in parts[1]:
                raw_init_data = parts[1]
    
    if not raw_init_data and tma_header:
        raw_init_data = tma_header

    if not raw_init_data and query_init_data:
        raw_init_data = query_init_data

    # 2. Если передан initData — проводим криптографическую авторизацию
    if raw_init_data:
        is_valid, parsed_data, err = parse_and_validate_init_data(raw_init_data)
        if not is_valid:
            logger.warning(f"TMA Auth failed: {err}")
            raise HTTPException(status_code=401, detail=f"Invalid Telegram initData: {err}")

        user = parsed_data.get("user") if parsed_data else None
        if not user or not isinstance(user, dict) or "id" not in user:
            raise HTTPException(status_code=400, detail="Telegram initData missing valid user profile")

        student_id = get_or_create_telegram_student(user)
        return student_id

    # 3. Fallback: для Web SPA консоли и тестов проверяем query, path параметры
    if "student_id" in request.query_params:
        return request.query_params["student_id"]

    if "student_id" in request.path_params:
        return request.path_params["student_id"]

    # Дефолтный студент для Web-режима
    return "stud_aai_042"
