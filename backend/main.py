"""
main.py

FastAPI веб-приложение Themis Project (v2.0).
Реализует 5 основных REST эндпоинтов + эндпоинт сброса демо + отдачу SPA интерфейса.
"""

from typing import Dict, Any, List, Optional, Set
import os
import uuid
import shutil
import asyncio
import json
import logging
import urllib.parse
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.models_schemas import (
    SessionStartRequest,
    SessionStartResponse,
    DialogTurnRequest,
    DialogTurnResponse,
    GradeSyncRequest,
    GradeSyncResponse,
    DashboardResponse,
    DashboardDistribution,
    AIReportResponse,
    ReportSOLOAnalysis,
    ReportEvidence,
    StudentAuditRecord,
    TeacherDecisionRequest,
    TeacherDecisionResponse,
    SystemHealthResponse,
    VectorStoreHealth,
    TmaLinkRequest,
    TmaMeResponse,
    LoginRequest,
    LoginResponse,
    AuthMeResponse,
    TelegramQrResponse,
    LogoutResponse,
)
from backend.math_engine import ThemisMathEngine
from backend.seed_data import (
    get_canonical_seed_records,
    STUDENT_NAMES_MAP,
    seed_sqlite_dialogs,
    GROUP_1_STUDENT_IDS,
)
from backend.rag_service import rag_service
from backend.llm_service import llm_service
from backend.similarity_service import similarity_service
from backend.database import (
    get_connection,
    save_session,
    save_turn,
    get_session,
    get_turns,
    get_latest_session_for_student,
    save_student_audit,
    bulk_save_student_audits,
    get_all_student_audits,
    get_student_audit,
    delete_student_dialogs,
    reset_student_in_db,
    CANONICAL_TOPIC_ID,
    CANONICAL_COURSE_ID,
    resolve_topic_id,
    get_courses,
    save_syllabus_week,
    save_lecture_glossary,
    save_ingestion_job,
    get_ingestion_job,
    update_ingestion_job,
    get_student_identity,
    get_student_identity_by_telegram_id,
    link_telegram_identity,
    save_student_identity,
    get_user_credential,
    verify_password,
    create_auth_session,
    get_auth_session,
    delete_auth_session,
    create_telegram_binding_token,
    _init_default_user_credentials,
)
from backend.markdown_converter import markdown_converter
from backend.chunker import smart_chunk_markdown
from backend.ingestion_service import ingestion_service, UPLOADS_DIR
from backend.vector_store import vector_store
from backend.tma_auth import (
    parse_and_validate_init_data,
    resolve_student_context,
    get_or_create_telegram_student,
)
from backend.telegram_bot import telegram_bot

logger = logging.getLogger("themis.main")

# Система real-time уведомлений преподавателя через SSE
class AuditBroadcaster:
    """
    Менеджер очередей подписчиков Server-Sent Events (SSE) для дашборда преподавателя.
    Обеспечивает доставку событий аудита в реальном времени и безопасную отписку клиентов.
    """
    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(q)
        logger.info(f"Новый клиент подключился к SSE audit-stream (всего подписчиков: {len(self._subscribers)})")
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self._subscribers.discard(q)
        logger.info(f"Клиент отключился от SSE audit-stream (осталось подписчиков: {len(self._subscribers)})")

    async def broadcast(self, message: Dict[str, Any]):
        dead_queues = []
        for q in list(self._subscribers):
            try:
                q.put_nowait(message)
            except Exception:
                dead_queues.append(q)
        for dq in dead_queues:
            self._subscribers.discard(dq)

audit_broadcaster = AuditBroadcaster()

# Подключение диспетчера Telegram бота к SSE-бродкастеру
async def _on_telegram_linked_broadcast(student_id: str, telegram_id: int, telegram_username: Optional[str]):
    await audit_broadcaster.broadcast({
        "type": "telegram_linked",
        "student_id": student_id,
        "telegram_id": telegram_id,
        "telegram_username": telegram_username,
    })

telegram_bot.set_binding_callback(_on_telegram_linked_broadcast)

# Хранилище сессий и записей в оперативной памяти (для мгновенной демонстрации и IT Fest)
db_records: Dict[str, StudentAuditRecord] = {}
db_sessions: Dict[str, Dict[str, Any]] = {}
engine = ThemisMathEngine(
    target_turns=settings.TARGET_TURNS,
    density_alpha=settings.DENSITY_ALPHA,
    density_floor=settings.DENSITY_FLOOR,
    initiative_bonus=settings.INITIATIVE_BONUS,
    sigma_min=settings.SIGMA_MIN,
)


def sync_records_to_sqlite():
    """Синхронизирует все записи db_records в таблицу student_audits SQLite для полной персистентности."""
    items = []
    for r in db_records.values():
        items.append({
            "student_id": r.student_id,
            "course_id": getattr(r, "course_id", CANONICAL_COURSE_ID),
            "topic_id": getattr(r, "topic_id", CANONICAL_TOPIC_ID),
            "student_name": getattr(r, "student_name", None) or STUDENT_NAMES_MAP.get(r.student_id, r.student_id),
            "group_id": getattr(r, "group_id", "group_1"),
            "in_class_grade": r.in_class_grade,
            "session_status": r.session_status,
            "turns_count": r.turns_count,
            "total_tokens": r.total_tokens,
            "ai_depth_score": r.ai_depth_score,
            "raw_delta": r.raw_delta,
            "rectified_delta": r.rectified_delta,
            "z_score": r.z_score,
            "zone": r.zone,
            "extraction_json": r.extraction.model_dump_json() if r.extraction else None,
            "telemetry_clean": getattr(r, "telemetry_clean", True),
            "teacher_decision": getattr(r, "teacher_decision", None),
        })
    bulk_save_student_audits(items)


def reset_database(load_from_db_if_exists: bool = False):
    """
    Инициализация состояния когорты.
    При load_from_db_if_exists=True восстанавливает актуальное состояние студентов из SQLite.
    При сбросе или если база пуста инициализирует каноническую когорту и синхронизирует её в SQLite.
    """
    db_records.clear()
    db_sessions.clear()

    existing_audits = get_all_student_audits() if load_from_db_if_exists else []
    if existing_audits:
        for row in existing_audits:
            extraction = None
            if row.get("extraction_json"):
                try:
                    extraction = AuditExtractionResult.model_validate_json(row["extraction_json"])
                except Exception:
                    extraction = None
            rec = StudentAuditRecord(
                student_id=row["student_id"],
                course_id=row.get("course_id", CANONICAL_COURSE_ID),
                topic_id=row.get("topic_id", CANONICAL_TOPIC_ID),
                student_name=row.get("student_name") or STUDENT_NAMES_MAP.get(row["student_id"], row["student_id"]),
                group_id=row.get("group_id", "group_1"),
                in_class_grade=row["in_class_grade"],
                session_status=row["session_status"],
                turns_count=row["turns_count"] or 0,
                total_tokens=row["total_tokens"] or 0,
                extraction=extraction,
                ai_depth_score=row["ai_depth_score"],
                raw_delta=row["raw_delta"] or 0.0,
                rectified_delta=row["rectified_delta"] or 0.0,
                z_score=row["z_score"] or 0.0,
                zone=row["zone"] or "NO_SIGNAL",
                telemetry_clean=bool(row.get("telemetry_clean", 1)),
                teacher_decision=row.get("teacher_decision"),
            )
            if rec.extraction and rec.turns_count >= settings.TARGET_TURNS:
                engine.compute_individual_depth(rec)
            db_records[row["student_id"]] = rec
        engine.compute_cohort_discrepancy(list(db_records.values()))
    else:
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM student_audits")
        c.execute("DELETE FROM syllabus_weeks WHERE course_id != ? OR week_number > 10 OR topic_id LIKE '%custom%'", (CANONICAL_COURSE_ID,))
        c.execute("DELETE FROM lecture_glossary WHERE course_id != ? OR topic_id LIKE '%custom%'", (CANONICAL_COURSE_ID,))
        c.execute("DELETE FROM courses WHERE course_id != ?", (CANONICAL_COURSE_ID,))
        c.execute("DELETE FROM telegram_binding_tokens")
        c.execute("DELETE FROM auth_sessions")
        conn.commit()
        conn.close()

        seed_records = get_canonical_seed_records()
        for rec in seed_records:
            db_records[rec.student_id] = rec
        seed_sqlite_dialogs()
        sync_records_to_sqlite()
        _init_default_user_credentials()

    rag_service.reload()

    # Загружаем сессии из SQLite в db_sessions при наличии
    if get_session("sess_canonical_stud_k"):
        turns = get_turns("sess_canonical_stud_k")
        if turns:
            db_sessions["sess_canonical_stud_k"] = {
                "student_id": "stud_aai_042",
                "course_id": CANONICAL_COURSE_ID,
                "topic_id": CANONICAL_TOPIC_ID,
                "turns": [
                    {
                        "turn_number": t["turn_number"],
                        "student": t["student_message"],
                        "system": t["system_reply"],
                        "typing_duration_ms": t["typing_duration_ms"],
                        "is_duplicate": bool(t["is_duplicate"]),
                        "similarity_score": t["similarity_score"],
                    }
                    for t in turns
                ],
                "created_at": 0,
                "active": False,
            }

    if get_session("sess_canonical_stud_015"):
        turns = get_turns("sess_canonical_stud_015")
        if turns:
            db_sessions["sess_canonical_stud_015"] = {
                "student_id": "stud_aai_015",
                "course_id": CANONICAL_COURSE_ID,
                "topic_id": CANONICAL_TOPIC_ID,
                "turns": [
                    {
                        "turn_number": t["turn_number"],
                        "student": t["student_message"],
                        "system": t["system_reply"],
                        "typing_duration_ms": t["typing_duration_ms"],
                        "is_duplicate": bool(t["is_duplicate"]),
                        "similarity_score": t["similarity_score"],
                    }
                    for t in turns
                ],
                "created_at": 0,
                "active": True,
            }


async def run_background_audit(
    student_id: str,
    topic_id: str,
    dialog_turns: List[Dict[str, str]],
    session_id: Optional[str] = None,
):
    """
    Фоновая асинхронная задача психометрического аудита (Слой 3A и 3B).
    Запускается на 3-м шаге сократического диалога.
    Мгновенно освобождает поток студента, выполняет Evidence-First экстракцию,
    рассчитывает ThemisMathEngine, обновляет статус сессии на COMPLETED,
    сохраняет аудит в SQLite и рассылает live-событие подписчикам /api/v1/events/audit-stream.
    """
    try:
        rec = db_records.get(student_id)
        if not rec:
            return

        extraction = await llm_service.extract_audit_evidence(
            topic_id=topic_id,
            dialog_turns=dialog_turns,
        )
        rec.extraction = extraction
        rec.session_status = "COMPLETED"
        engine.compute_individual_depth(rec)
        engine.compute_cohort_discrepancy(list(db_records.values()))
        if session_id and session_id in db_sessions:
            db_sessions[session_id]["active"] = False

        sync_records_to_sqlite()

        display_name = getattr(rec, "student_name", None) or STUDENT_NAMES_MAP.get(rec.student_id, rec.student_id)
        record_payload = {
            "student_id": rec.student_id,
            "student_name": display_name,
            "group_id": getattr(rec, "group_id", "group_1"),
            "in_class_grade": rec.in_class_grade,
            "ai_depth_score": rec.ai_depth_score,
            "raw_delta": rec.raw_delta,
            "rectified_delta": rec.rectified_delta,
            "z_score": rec.z_score,
            "zone": rec.zone,
            "session_status": rec.session_status,
            "telemetry_clean": rec.telemetry_clean,
            "teacher_decision": rec.teacher_decision,
            "has_report": rec.extraction is not None,
        }
        await audit_broadcaster.broadcast({
            "type": "audit_completed",
            "student_id": rec.student_id,
            "record": record_payload,
        })
        logger.info(f"Фоновый аудит студента {student_id} успешно завершен и отправлен в SSE-стрим.")
    except Exception as e:
        logger.error(f"Ошибка при выполнении фонового аудита {student_id}: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация при старте с подтягиванием персистентного состояния из SQLite
    reset_database(load_from_db_if_exists=True)
    # Фоновый прогрев модели BAAI/bge-m3 и векторного хранилища в ThreadPool
    asyncio.create_task(asyncio.to_thread(vector_store.warmup))

    # Запуск фонового Telegram Long Polling при наличии реального токена
    telegram_polling_task = None
    if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_TOKEN not in ("dev", "test"):
        logger.info("Запуск фоновой службы Telegram Long Polling (токен настроен)...")
        telegram_polling_task = asyncio.create_task(telegram_bot.start_polling())

    try:
        yield
    finally:
        # Корректная остановка при завершении приложения
        telegram_bot.stop_polling()
        if telegram_polling_task:
            telegram_polling_task.cancel()
            try:
                await telegram_polling_task
            except (asyncio.CancelledError, Exception):
                pass


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Inclusive Academic Discrepancy Audit & Socratic Scaffolding Engine",
    lifespan=lifespan,
)

# Разрешаем CORS для локального тестирования и веб-клиента
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# REST API ЭНДПОИНТЫ
# =====================================================================

@app.get("/api/v1/courses")
async def list_courses():
    """
    Возвращает список всех доступных курсов из базы данных SQLite.
    Позволяет изолировать силлабусы, глоссарии и когорты студентов.
    """
    return get_courses()


@app.get("/api/v1/syllabus/weeks")
async def get_syllabus_weeks(course_id: Optional[str] = Query(None)):
    """
    Возвращает список учебных недель курса 'Программирование для ИИ' (PAI 2026).
    Включает как канонические недели, так и динамически загруженные преподавателем.
    """
    cid = course_id or CANONICAL_COURSE_ID
    return rag_service.get_all_weeks(course_id=cid)


@app.get("/api/v1/course/jobs/{job_id}")
async def get_course_ingestion_job_status(job_id: str):
    """
    Эндпоинт отслеживания статуса фоновой задачи автономной индексации курса.
    Возвращает текущую стадию, прогресс (0-100%) и детальное сообщение для UI:
    QUEUED -> CONVERTING -> STRUCTURING -> CHUNKING -> INDEXING -> COMPLETED (или FAILED).
    """
    job = get_ingestion_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Задача индексации {job_id} не найдена")

    return {
        "job_id": job["job_id"],
        "course_id": job["course_id"],
        "status": job["status"],
        "stage": job["status"],
        "progress": job["progress"],
        "total": job["total"],
        "message": job["message"] or "",
        "error": job["error"],
        "updated_at": job["updated_at"]
    }


@app.post("/api/v1/courses/{course_id}/ingest", status_code=202)
async def ingest_course_materials(
    course_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    week_number: Optional[int] = Form(None),
    topic_name: Optional[str] = Form(None),
):
    """
    Автономный асинхронный эндпоинт загрузки материалов курса (P1 Zero-Config Ingestion).
    Принимает файл (.pdf, .pptx, .docx, .ipynb, .md, .txt, .zip), создает job_id,
    стартует фоновую задачу и немедленно возвращает 202 Accepted.
    """
    filename = file.filename or "materials.bin"
    ext = os.path.splitext(filename)[1].lower()
    supported_exts = {".pptx", ".ppt", ".pdf", ".docx", ".doc", ".ipynb", ".md", ".txt", ".zip"}
    if ext not in supported_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Формат файла {ext} не поддерживается. Разрешены: {', '.join(sorted(supported_exts))}"
        )

    job_id = f"job_{uuid.uuid4().hex[:12]}"
    saved_path = os.path.join(UPLOADS_DIR, f"{job_id}_{filename}")
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    save_ingestion_job(
        job_id=job_id,
        course_id=course_id,
        status="QUEUED",
        progress=0,
        total=0,
        message=f"Файл {filename} принят в очередь. Подготовка к конвертации..."
    )

    background_tasks.add_task(
        ingestion_service.execute_ingestion_job,
        job_id=job_id,
        file_path=saved_path,
        filename=filename,
        course_id=course_id,
        week_number=week_number,
        topic_name=topic_name
    )

    return JSONResponse(
        status_code=202,
        content={
            "job_id": job_id,
            "course_id": course_id,
            "status": "QUEUED",
            "message": f"Файл {filename} принят в обработку. Отслеживайте прогресс по /api/v1/course/jobs/{job_id}"
        }
    )


@app.post("/api/v1/course/upload")
async def upload_course_lecture(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    week_number: Optional[int] = Form(None),
    topic_name: Optional[str] = Form(None),
    course_id: str = Form("prog_ai_2026"),
    async_mode: bool = Form(False),
):
    """
    Эндпоинт загрузки и онлайновой индексации лекций курса (PPTX / PDF / DOCX / IPYNB / MD / ZIP).
    Поддерживает как асинхронный режим с живым отслеживанием прогресса (async_mode=True -> 202 Accepted),
    так и синхронный режим обратной совместимости (async_mode=False -> 200 OK).
    """
    filename = file.filename or "lecture.pptx"
    ext = os.path.splitext(filename)[1].lower()
    supported_exts = {".pptx", ".ppt", ".pdf", ".docx", ".doc", ".ipynb", ".md", ".txt", ".zip"}
    if ext not in supported_exts:
        raise HTTPException(status_code=400, detail=f"Формат {ext} не поддерживается. Разрешены: {', '.join(sorted(supported_exts))}")

    job_id = f"job_{uuid.uuid4().hex[:12]}"
    saved_path = os.path.join(UPLOADS_DIR, f"{job_id}_{filename}")
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if async_mode:
        save_ingestion_job(
            job_id=job_id,
            course_id=course_id,
            status="QUEUED",
            progress=0,
            total=0,
            message=f"Файл {filename} принят в очередь. Подготовка..."
        )
        background_tasks.add_task(
            ingestion_service.execute_ingestion_job,
            job_id=job_id,
            file_path=saved_path,
            filename=filename,
            course_id=course_id,
            week_number=week_number,
            topic_name=topic_name
        )
        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "course_id": course_id,
                "status": "QUEUED",
                "message": f"Файл принят в обработку. Отслеживайте прогресс по /api/v1/course/jobs/{job_id}"
            }
        )
        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "course_id": course_id,
                "status": "QUEUED",
                "message": f"Файл принят в обработку. Отслеживайте прогресс по /api/v1/course/jobs/{job_id}"
            }
        )

    # Синхронный режим (обратная совместимость с существующими интеграционными тестами)
    wn = week_number if week_number is not None else 11
    tn = topic_name or "Новая тема курса"
    topic_id = f"week_{wn:02d}_custom"

    try:
        if ext == ".pptx":
            slides_data = ingestion_service.parse_pptx(saved_path)
        elif ext == ".pdf":
            slides_data = ingestion_service.parse_pdf(saved_path)
        else:
            md_text = markdown_converter.convert_file(saved_path)
            slides_data = smart_chunk_markdown(
                markdown_text=md_text,
                course_id=course_id,
                topic_id=topic_id,
                week_number=wn,
                topic_name=tn
            )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Ошибка обработки документа: {str(e)}")

    if not slides_data:
        raise HTTPException(status_code=422, detail="Не удалось извлечь слайды/чанки из загруженного файла")

    # Селективная векторизация с очисткой старых чанков
    indexed_count = await asyncio.to_thread(
        vector_store.add_slides,
        topic_id=topic_id,
        week_number=wn,
        slides_data=slides_data,
        course_id=course_id,
        delete_old=True
    )

    meta = ingestion_service.build_course_metadata(
        topic_id=topic_id,
        week_number=wn,
        topic_name=tn,
        slides=slides_data
    )

    save_syllabus_week(
        course_id=course_id,
        topic_id=topic_id,
        week_number=wn,
        title=meta["title"],
        topic_name=meta["topic_name"],
        initial_prompt=meta["initial_prompt"],
        md_path=saved_path,
        chunks_count=len(slides_data)
    )
    save_lecture_glossary(
        course_id=course_id,
        topic_id=topic_id,
        terms=meta["glossary"]
    )

    rag_service.register_dynamic_week(
        topic_id=topic_id,
        week_number=wn,
        title=meta["title"],
        topic_name=meta["topic_name"],
        initial_prompt=meta["initial_prompt"],
        glossary=meta["glossary"],
        slides_count=len(slides_data),
        course_id=course_id
    )

    return {
        "status": "SUCCESS",
        "message": "Лекция успешно обработана и проиндексирована в HNSW (BGE-M3)",
        "week_number": wn,
        "topic_id": topic_id,
        "title": meta["title"],
        "topic_name": tn,
        "slides_count": len(slides_data),
        "indexed_chunks": indexed_count,
        "glossary": meta["glossary"],
        "initial_prompt": meta["initial_prompt"]
    }


@app.get("/api/v1/students")
async def get_students_list(group_id: Optional[str] = Query(None)):
    """
    Эндпоинт получения списка студентов группы (по умолчанию Группа 1: 20 студентов).
    Каждый студент представлен отдельным персональным инстансом с метаданными.
    """
    students = []
    for r in db_records.values():
        rec_group = getattr(r, "group_id", "group_1")
        if group_id and rec_group != group_id:
            continue
        display_name = getattr(r, "student_name", None) or STUDENT_NAMES_MAP.get(r.student_id, r.student_id)
        students.append({
            "student_id": r.student_id,
            "display_name": display_name,
            "group_id": rec_group,
            "in_class_grade": r.in_class_grade,
            "session_status": r.session_status,
            "ai_depth_score": r.ai_depth_score,
            "rectified_delta": r.rectified_delta,
            "z_score": r.z_score,
            "zone": r.zone,
            "turns_count": r.turns_count,
            "has_report": r.extraction is not None,
        })

    def sort_key(s):
        if s["student_id"] == "stud_aai_042":
            return (0, 0)
        return (1, s["student_id"])

    students.sort(key=sort_key)
    return students


@app.get("/api/v1/session/active/{student_id}")
async def get_active_session(
    student_id: str,
    request: Request,
    topic_id: str = Query("week_09_deep_learning"),
    course_id: str = Query("prog_ai_2026")
):
    """
    Эндпоинт восстановления сессии студента из оперативной памяти или SQLite.
    Позволяет бесшовно восстанавливать историю диалога при F5 или смене студента в UI.
    Поддерживает псевдоним 'me' для автоматического разрешения через Telegram initData.
    """
    if student_id == "me":
        student_id = await resolve_student_context(request)
    resolved_topic = resolve_topic_id(topic_id)
    target_session_id = None
    # 1. Поиск в памяти
    for s_id, s_data in db_sessions.items():
        if s_data.get("student_id") == student_id:
            s_course = s_data.get("course_id", "prog_ai_2026")
            s_topic = resolve_topic_id(s_data.get("topic_id", CANONICAL_TOPIC_ID))
            if s_course == course_id and (s_topic == resolved_topic or s_data.get("topic_id") == topic_id):
                target_session_id = s_id
                break

    # 2. Если в памяти нет, ищем в SQLite
    if not target_session_id:
        row = get_latest_session_for_student(student_id, topic_id=resolved_topic, course_id=course_id)
        if not row and topic_id != resolved_topic:
            row = get_latest_session_for_student(student_id, topic_id=topic_id, course_id=course_id)
        if row:
            target_session_id = row["session_id"]
            db_turns = get_turns(target_session_id)
            db_sessions[target_session_id] = {
                "student_id": row["student_id"],
                "course_id": row["course_id"],
                "topic_id": row["topic_id"],
                "turns": [
                    {
                        "turn_number": t["turn_number"],
                        "student": t["student_message"],
                        "system": t["system_reply"],
                        "typing_duration_ms": t["typing_duration_ms"],
                        "is_duplicate": bool(t["is_duplicate"]),
                        "similarity_score": t["similarity_score"],
                    }
                    for t in db_turns
                ],
                "created_at": 0,
                "active": row["status"] == "ACTIVE",
            }

    initial_prompt = rag_service.get_initial_prompt(resolved_topic)

    if not target_session_id or target_session_id not in db_sessions:
        return {
            "found": False,
            "student_id": student_id,
            "session_id": None,
            "status": "OPTED_OUT",
            "turns": [],
            "turns_count": 0,
            "initial_prompt": initial_prompt,
        }

    sess = db_sessions[target_session_id]
    non_dup_turns = [t for t in sess["turns"] if not t.get("is_duplicate")]
    turns_count = len(non_dup_turns)
    rec = db_records.get(student_id)
    if rec and rec.session_status == "AUDITING":
        status = "AUDITING"
    elif turns_count >= settings.TARGET_TURNS:
        status = "COMPLETED"
    else:
        status = "ACTIVE"

    return {
        "found": True,
        "student_id": student_id,
        "session_id": target_session_id,
        "status": status,
        "initial_prompt": initial_prompt,
        "turns": sess["turns"],
        "turns_count": turns_count,
    }


@app.post("/api/v1/session/start", response_model=SessionStartResponse)
async def start_session(req: SessionStartRequest, request: Request):
    """
    Эндпоинт 1: Инициализация добровольной сократической сессии («Цифровой пандус»).
    Проверяет доступность окна расписания и возвращает контекстный стартовый вопрос.
    """
    # Если передан TMA заголовок или student_id == "me", разрешаем контекст через Telegram Mini App
    auth_hdr = request.headers.get("Authorization", "").lower()
    tma_hdr = request.headers.get("X-Telegram-Init-Data", "")
    if req.student_id in ("me", "tma", "") or auth_hdr.startswith("tma ") or tma_hdr:
        try:
            req.student_id = await resolve_student_context(request)
        except Exception:
            pass

    resolved_topic = resolve_topic_id(req.topic_id)
    initial_prompt = rag_service.get_initial_prompt(resolved_topic)

    # Если принудительный рестарт не запрошен, проверяем наличие уже существующей активной сессии
    if not req.force_open:
        for s_id, s_data in db_sessions.items():
            if s_data.get("student_id") == req.student_id:
                s_topic = resolve_topic_id(s_data.get("topic_id"))
                if s_topic == resolved_topic and s_data.get("active", True):
                    return SessionStartResponse(
                        session_id=s_id,
                        status="ACTIVE",
                        time_remaining_seconds=settings.SCHEDULE_WINDOW_MINUTES * 60,
                        policy_notice=(
                            "Добровольная сессия Themis Project. Результат не снижает очную оценку "
                            "и служит только для раскрытия ваших знаний."
                        ),
                        initial_prompt=initial_prompt,
                    )

    # Создаем новую сессию
    session_id = f"sess_{uuid.uuid4().hex[:8]}"

    # Регистрируем студента в реестре, если его еще нет
    if req.student_id not in db_records:
        identity = get_student_identity(req.student_id)
        init_grade = identity.get("default_grade", 75.0) if identity else 70.0
        disp_name = (identity.get("display_name") if identity else None) or STUDENT_NAMES_MAP.get(req.student_id, req.student_id)
        grp_id = (identity.get("group_id") if identity else None) or "group_1"

        db_records[req.student_id] = StudentAuditRecord(
            student_id=req.student_id,
            course_id=req.course_id,
            topic_id=resolved_topic,
            student_name=disp_name,
            group_id=grp_id,
            in_class_grade=init_grade,
            session_status="INCOMPLETE_IGNORED",
            turns_count=0,
            total_tokens=0,
            telemetry_clean=True,
        )

    db_sessions[session_id] = {
        "student_id": req.student_id,
        "course_id": req.course_id,
        "topic_id": req.topic_id,
        "turns": [],
        "created_at": 0,
        "active": True,
    }

    # Персистентное сохранение в SQLite
    save_session(session_id, req.student_id, req.course_id, req.topic_id)

    return SessionStartResponse(
        session_id=session_id,
        status="ACTIVE",
        time_remaining_seconds=settings.SCHEDULE_WINDOW_MINUTES * 60,
        policy_notice=(
            "Добровольная сессия Themis Project. Результат не снижает очную оценку "
            "и служит только для раскрытия ваших знаний."
        ),
        initial_prompt=initial_prompt,
    )


@app.post("/api/v1/dialog/turn", response_model=DialogTurnResponse)
async def dialog_turn(req: DialogTurnRequest):
    """
    Эндпоинт 2: Шаг сократического диалога с защитой от накрутки дубликатами (Anti-Spam).
    Принимает ответ студента, вычисляет семантическое сходство с ранее отправленными сообщениями.
    При дублировании или тривиальном перефразировании шаг не увеличивается и балл не растет.
    """
    session = db_sessions.get(req.session_id)
    if not session:
        # Проверяем в SQLite (восстановление после перезапуска)
        row = get_session(req.session_id)
        if row:
            db_turns = get_turns(req.session_id)
            db_sessions[req.session_id] = {
                "student_id": row["student_id"],
                "course_id": row["course_id"],
                "topic_id": row["topic_id"],
                "turns": [
                    {
                        "turn_number": t["turn_number"],
                        "student": t["student_message"],
                        "system": t["system_reply"],
                        "typing_duration_ms": t["typing_duration_ms"],
                        "is_duplicate": bool(t["is_duplicate"]),
                        "similarity_score": t["similarity_score"],
                    }
                    for t in db_turns
                ],
                "created_at": 0,
                "active": True,
            }
            session = db_sessions[req.session_id]

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    student_id = session["student_id"]
    record = db_records.get(student_id)
    if not record:
        raise HTTPException(status_code=404, detail="Student record not found")

    # Предыдущие не-дублирующие сообщения студента
    previous_msgs = [t["student"] for t in session["turns"] if not t.get("is_duplicate")]
    is_duplicate, sim_score, matched_msg = similarity_service.check_repetition(req.student_message, previous_msgs)

    # Защита от дублирования: если сообщение повторяет ранее отправленное
    if is_duplicate:
        current_valid_turns = len(previous_msgs)
        warning_reply = (
            f"⚠️ Твое сообщение дублирует уже отправленный ответ (сходство: {int(sim_score * 100)}%). "
            "Повторение одной и той же мысли не засчитывается за новый шаг. "
            "Попробуй раскрыть механизмы подробнее, привести новый аргумент или ответить на вопрос тьютора."
        )
        session["turns"].append({
            "turn_number": current_valid_turns,
            "student": req.student_message,
            "system": warning_reply,
            "typing_duration_ms": req.typing_duration_ms,
            "is_duplicate": True,
            "similarity_score": sim_score,
        })
        save_turn(
            session_id=req.session_id,
            turn_number=current_valid_turns,
            student_message=req.student_message,
            system_reply=warning_reply,
            similarity_score=sim_score,
            is_duplicate=True,
            typing_duration_ms=req.typing_duration_ms,
            paste_detected=req.paste_detected,
        )
        return DialogTurnResponse(
            session_id=req.session_id,
            turn_number=current_valid_turns,
            system_reply=warning_reply,
            session_confidence=f"ПОВТОР (Шаг {current_valid_turns}/{settings.TARGET_TURNS})",
            is_duplicate=True,
        )

    # Валидный новый шаг диалога
    turn_number = len(previous_msgs) + 1

    # Сохраняем телеметрию
    if req.paste_detected:
        record.telemetry_clean = False

    # Оценка токенов только для уникальных содержательных сообщений
    word_count = len(req.student_message.split())
    record.total_tokens += max(10, int(word_count * 1.3))
    record.turns_count = turn_number

    # Формируем историю диалога для модели
    history: List[Dict[str, str]] = []
    for t in session["turns"]:
        if not t.get("is_duplicate"):
            history.append({"role": "user", "content": t["student"]})
            history.append({"role": "assistant", "content": t["system"]})

    # Генерируем сократическую реплику
    system_reply = await llm_service.generate_socratic_reply(
        topic_id=session["topic_id"],
        turn_number=turn_number,
        student_message=req.student_message,
        history=history,
    )

    session["turns"].append({
        "turn_number": turn_number,
        "student": req.student_message,
        "system": system_reply,
        "typing_duration_ms": req.typing_duration_ms,
        "is_duplicate": False,
        "similarity_score": sim_score,
    })

    save_turn(
        session_id=req.session_id,
        turn_number=turn_number,
        student_message=req.student_message,
        system_reply=system_reply,
        similarity_score=sim_score,
        is_duplicate=False,
        typing_duration_ms=req.typing_duration_ms,
        paste_detected=req.paste_detected,
    )

    # При достижении целевого числа реплик (Target = 3) запускаем Слой 3A и 3B
    if turn_number >= settings.TARGET_TURNS:
        record.session_status = "COMPLETED"
        valid_dialog_turns = [t for t in session["turns"] if not t.get("is_duplicate")]
        # Слой 3A: Извлечение доказательств аудита
        extraction = await llm_service.extract_audit_evidence(
            topic_id=session["topic_id"],
            dialog_turns=valid_dialog_turns,
        )
        record.extraction = extraction
        # Вычисляем глубину S_depth
        engine.compute_individual_depth(record)
        # Слой 3B: Обновляем когортное распределение
        engine.compute_cohort_discrepancy(list(db_records.values()))
        confidence_str = f"HIGH (N = {turn_number}/{settings.TARGET_TURNS})"
        display_name = getattr(record, "student_name", None) or STUDENT_NAMES_MAP.get(record.student_id, record.student_id)
        await audit_broadcaster.broadcast({
            "type": "audit_completed",
            "student_id": record.student_id,
            "record": {
                "student_id": record.student_id,
                "student_name": display_name,
                "group_id": getattr(record, "group_id", "group_1"),
                "in_class_grade": record.in_class_grade,
                "ai_depth_score": record.ai_depth_score,
                "raw_delta": record.raw_delta,
                "rectified_delta": record.rectified_delta,
                "z_score": record.z_score,
                "zone": record.zone,
                "session_status": record.session_status,
                "telemetry_clean": record.telemetry_clean,
                "teacher_decision": record.teacher_decision,
                "has_report": record.extraction is not None,
            }
        })
    else:
        record.session_status = "INCOMPLETE_IGNORED"
        confidence_str = f"LOW (N = {turn_number}/{settings.TARGET_TURNS})"

    # Сохраняем в SQLite для персистентности
    sync_records_to_sqlite()

    # Двусторонняя реактивная синхронизация шагов диалога (TMA <-> Web)
    await audit_broadcaster.broadcast({
        "type": "dialog_turn_sync",
        "session_id": req.session_id,
        "student_id": record.student_id,
        "turn_number": turn_number,
        "student_message": req.student_message,
        "tutor_message": system_reply,
        "session_status": record.session_status,
        "ai_depth_score": record.ai_depth_score,
    })

    return DialogTurnResponse(
        session_id=req.session_id,
        turn_number=turn_number,
        system_reply=system_reply,
        session_confidence=confidence_str,
        is_duplicate=False,
        session_status=record.session_status,
    )


@app.post("/api/v1/dialog/turn/stream")
async def dialog_turn_stream(req: DialogTurnRequest, request: Request, background_tasks: BackgroundTasks):
    """
    Потоковый эндпоинт сократического диалога (SSE Streaming, P0).
    Возвращает text/event-stream со следующими типами событий:
    1. 'sources' - найденные RAG-источники лекции из HNSW-индекса ChromaDB;
    2. 'delta' - пошаговый стриминг токенов сократического ответа тьютора;
    3. 'done' - финальный статус шага, статистика и turn_response.
    
    На 3-м шаге: переводит сессию в статус 'AUDITING', мгновенно завершает отдачу
    потока студенту, а тяжелую психометрическую экстракцию Слоя 3A/3B и расчет
    ThemisMathEngine запускает в фоновой асинхронной задаче, обновляя статус сессии
    на 'COMPLETED' и рассылая live-событие в дашборд преподавателя.
    """
    session = db_sessions.get(req.session_id)
    if not session:
        row = get_session(req.session_id)
        if row:
            db_turns = get_turns(req.session_id)
            db_sessions[req.session_id] = {
                "student_id": row["student_id"],
                "course_id": row["course_id"],
                "topic_id": row["topic_id"],
                "turns": [
                    {
                        "turn_number": t["turn_number"],
                        "student": t["student_message"],
                        "system": t["system_reply"],
                        "typing_duration_ms": t["typing_duration_ms"],
                        "is_duplicate": bool(t["is_duplicate"]),
                        "similarity_score": t["similarity_score"],
                    }
                    for t in db_turns
                ],
                "created_at": 0,
                "active": True,
            }
            session = db_sessions[req.session_id]

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    student_id = session["student_id"]
    record = db_records.get(student_id)
    if not record:
        raise HTTPException(status_code=404, detail="Student record not found")

    async def event_generator():
        try:
            # 1. Проверка на дублирование сообщений (Anti-Spam)
            previous_msgs = [t["student"] for t in session["turns"] if not t.get("is_duplicate")]
            is_duplicate, sim_score, matched_msg = similarity_service.check_repetition(req.student_message, previous_msgs)

            if is_duplicate:
                current_valid_turns = len(previous_msgs)
                warning_reply = (
                    f"⚠️ Твое сообщение дублирует уже отправленный ответ (сходство: {int(sim_score * 100)}%). "
                    "Повторение одной и той же мысли не засчитывается за новый шаг. "
                    "Попробуй раскрыть механизмы подробнее, привести новый аргумент или ответить на вопрос тьютора."
                )
                session["turns"].append({
                    "turn_number": current_valid_turns,
                    "student": req.student_message,
                    "system": warning_reply,
                    "typing_duration_ms": req.typing_duration_ms,
                    "is_duplicate": True,
                    "similarity_score": sim_score,
                })
                save_turn(
                    session_id=req.session_id,
                    turn_number=current_valid_turns,
                    student_message=req.student_message,
                    system_reply=warning_reply,
                    similarity_score=sim_score,
                    is_duplicate=True,
                    typing_duration_ms=req.typing_duration_ms,
                    paste_detected=req.paste_detected,
                )
                yield f"data: {json.dumps({'type': 'sources', 'sources': []}, ensure_ascii=False)}\n\n"
                yield f"data: {json.dumps({'type': 'delta', 'text': warning_reply}, ensure_ascii=False)}\n\n"
                turn_response = {
                    "session_id": req.session_id,
                    "turn_number": current_valid_turns,
                    "system_reply": warning_reply,
                    "session_confidence": f"ПОВТОР (Шаг {current_valid_turns}/{settings.TARGET_TURNS})",
                    "is_duplicate": True,
                    "session_status": record.session_status,
                }
                yield f"data: {json.dumps({'type': 'done', 'turn_response': turn_response}, ensure_ascii=False)}\n\n"
                return

            # 2. Валидный новый шаг сократического диалога
            turn_number = len(previous_msgs) + 1
            if req.paste_detected:
                record.telemetry_clean = False

            word_count = len(req.student_message.split())
            record.total_tokens += max(10, int(word_count * 1.3))
            record.turns_count = turn_number

            # 3. RAG-поиск источников лекции с оберткой вызова в ThreadPool (asyncio.to_thread)
            topic_id = session["topic_id"]
            course_id = session.get("course_id", "prog_ai_2026")
            sources = []
            try:
                raw_slides = await asyncio.to_thread(
                    vector_store.search_relevant_slides,
                    query=req.student_message,
                    topic_id=topic_id,
                    course_id=course_id,
                    top_k=3
                )
                if raw_slides:
                    sources = [
                        {
                            "slide_number": s.get("metadata", {}).get("slide_number", 1),
                            "title": s.get("metadata", {}).get("title", "Слайд лекции"),
                            "similarity": s.get("similarity", 0.0),
                            "content": s.get("text", "")[:250],
                        }
                        for s in raw_slides
                    ]
                else:
                    rag_chunks = rag_service.retrieve_chunks(req.student_message, topic_id, course_id=course_id, top_k=3)
                    sources = [
                        {
                            "slide_number": idx + 1,
                            "title": c.get("title", "Материал силлабуса"),
                            "similarity": 0.85,
                            "content": c.get("content", "")[:250],
                        }
                        for idx, c in enumerate(rag_chunks)
                    ]
            except Exception as e:
                logger.warning(f"Ошибка получения RAG источников для стрима: {e}")
                sources = []

            # Отправка события со списком найденных RAG-источников
            yield f"data: {json.dumps({'type': 'sources', 'sources': sources}, ensure_ascii=False)}\n\n"

            # 4. Формируем контекстную историю диалога
            history: List[Dict[str, str]] = []
            for t in session["turns"]:
                if not t.get("is_duplicate"):
                    history.append({"role": "user", "content": t["student"]})
                    history.append({"role": "assistant", "content": t["system"]})

            # 5. Стриминг токенов реплики тьютора
            delta_chunks = []
            async for delta in llm_service.generate_socratic_reply_stream(
                topic_id=topic_id,
                turn_number=turn_number,
                student_message=req.student_message,
                history=history,
            ):
                delta_chunks.append(delta)
                yield f"data: {json.dumps({'type': 'delta', 'text': delta}, ensure_ascii=False)}\n\n"

            system_reply = "".join(delta_chunks).strip()

            # Сохраняем шаг в сессию и персистентную БД
            session["turns"].append({
                "turn_number": turn_number,
                "student": req.student_message,
                "system": system_reply,
                "typing_duration_ms": req.typing_duration_ms,
                "is_duplicate": False,
                "similarity_score": sim_score,
            })
            save_turn(
                session_id=req.session_id,
                turn_number=turn_number,
                student_message=req.student_message,
                system_reply=system_reply,
                similarity_score=sim_score,
                is_duplicate=False,
                typing_duration_ms=req.typing_duration_ms,
                paste_detected=req.paste_detected,
            )

            # 6. Обработка 3-го шага: статус AUDITING и вынос аудита в фоновую задачу
            if turn_number >= settings.TARGET_TURNS:
                record.session_status = "AUDITING"
                confidence_str = f"AUDITING (Шаг {turn_number}/{settings.TARGET_TURNS})"
                sync_records_to_sqlite()
                valid_dialog_turns = [t for t in session["turns"] if not t.get("is_duplicate")]
                # Запускаем фоновый психометрический расчет (Слой 3A и 3B) через BackgroundTasks
                background_tasks.add_task(
                    run_background_audit,
                    student_id=student_id,
                    topic_id=topic_id,
                    dialog_turns=valid_dialog_turns,
                    session_id=req.session_id,
                )
            else:
                record.session_status = "INCOMPLETE_IGNORED"
                confidence_str = f"LOW (Шаг {turn_number}/{settings.TARGET_TURNS})"
                sync_records_to_sqlite()

            # Двусторонняя реактивная синхронизация шагов диалога (TMA <-> Web)
            await audit_broadcaster.broadcast({
                "type": "dialog_turn_sync",
                "session_id": req.session_id,
                "student_id": record.student_id,
                "turn_number": turn_number,
                "student_message": req.student_message,
                "tutor_message": system_reply,
                "session_status": record.session_status,
                "ai_depth_score": record.ai_depth_score,
            })

            turn_response = {
                "session_id": req.session_id,
                "turn_number": turn_number,
                "system_reply": system_reply,
                "session_confidence": confidence_str,
                "is_duplicate": False,
                "session_status": record.session_status,
            }
            yield f"data: {json.dumps({'type': 'done', 'turn_response': turn_response}, ensure_ascii=False)}\n\n"
        except (asyncio.CancelledError, GeneratorExit):
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream; charset=utf-8",
        background=background_tasks,
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/v1/events/audit-stream")
async def audit_events_stream(request: Request):
    """
    SSE-эндпоинт уведомлений преподавателя в реальном времени.
    Клиент (консоль преподавателя или дашборд) подписывается на поток событий аудита.
    События:
    - 'connected': подтверждение подключения;
    - 'audit_completed': завершение расчета аудита для студента с обновленными метриками;
    - 'ping': периодический heartbeat каждые 15 секунд для поддержания активности соединения.
    Безопасно отписывает очередь клиента при разрыве соединения.
    """
    q = audit_broadcaster.subscribe()

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'connected', 'message': 'Audit event stream connected'}, ensure_ascii=False)}\n\n"
            while True:
                disconnected = False
                try:
                    disconnected = await request.is_disconnected()
                except Exception:
                    disconnected = False
                if disconnected:
                    break

                try:
                    event = await asyncio.wait_for(q.get(), timeout=15.0)
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    try:
                        disconnected = await request.is_disconnected()
                    except Exception:
                        disconnected = False
                    if disconnected:
                        break
                    yield f"data: {json.dumps({'type': 'ping'}, ensure_ascii=False)}\n\n"
        except (asyncio.CancelledError, GeneratorExit):
            pass
        finally:
            audit_broadcaster.unsubscribe(q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/api/v1/sync/in-class-grades", response_model=GradeSyncResponse)
async def sync_in_class_grades(req: GradeSyncRequest):
    """
    Эндпоинт 3: Синхронизация очных оценок преподавателя.
    Запускает реактивный когортный расчет (Этап 3B) за < 10 мс и сохраняет изменения в SQLite.
    """
    synced = 0
    resolved_topic = resolve_topic_id(req.topic_id)
    for item in req.records:
        if item.student_id in db_records:
            rec = db_records[item.student_id]
            rec.in_class_grade = item.in_class_grade
            rec.course_id = req.course_id
            rec.topic_id = resolved_topic
            synced += 1
        else:
            rec = StudentAuditRecord(
                student_id=item.student_id,
                course_id=req.course_id,
                topic_id=resolved_topic,
                student_name=STUDENT_NAMES_MAP.get(item.student_id, item.student_id),
                in_class_grade=item.in_class_grade,
                session_status="OPTED_OUT",
                telemetry_clean=True,
            )
            db_records[item.student_id] = rec
            synced += 1

    summary = engine.compute_cohort_discrepancy(list(db_records.values()))
    sync_records_to_sqlite()
    return GradeSyncResponse(
        status="SUCCESS",
        synced_count=synced,
        cohort_summary=summary,
    )


@app.get("/api/v1/audit/dashboard", response_model=DashboardResponse)
async def get_audit_dashboard(
    topic_id: str = Query("week_09_deep_learning"),
    course_id: str = Query("prog_ai_2026"),
    group_id: Optional[str] = Query(None)
):
    """
    Эндпоинт 4: Дашборд распределения сигм и полный список когорты (Консоль преподавателя).
    Поддерживает фильтрацию по курсу (course_id), теме (topic_id) и группе (group_id).
    """
    resolved_topic = resolve_topic_id(topic_id)
    records_list = [
        r for r in db_records.values()
        if getattr(r, "course_id", "prog_ai_2026") == course_id
        and resolve_topic_id(getattr(r, "topic_id", CANONICAL_TOPIC_ID)) == resolved_topic
    ]
    if group_id:
        records_list = [r for r in records_list if getattr(r, "group_id", "group_1") == group_id]

    summary = engine.compute_cohort_discrepancy(records_list)

    total_students = len(records_list)
    completed_count = sum(1 for r in records_list if r.session_status == "COMPLETED")
    opted_out_count = total_students - completed_count

    students_data = []
    for r in records_list:
        display_name = getattr(r, "student_name", None) or STUDENT_NAMES_MAP.get(r.student_id, r.student_id)
        students_data.append({
            "student_id": r.student_id,
            "display_name": display_name,
            "group_id": getattr(r, "group_id", "group_1"),
            "in_class_grade": r.in_class_grade,
            "ai_depth_score": r.ai_depth_score,
            "session_status": r.session_status,
            "turns_count": r.turns_count,
            "rectified_delta": r.rectified_delta,
            "z_score": r.z_score,
            "zone": r.zone,
            "telemetry_clean": getattr(r, "telemetry_clean", True),
            "teacher_decision": getattr(r, "teacher_decision", None),
            "has_report": r.extraction is not None,
        })

    # Сортируем: сначала Purple, затем Red, Yellow, Green, No Signal
    zone_order = {"HIGH_DISCREPANCY": 0, "AUDIT_TRIGGER": 1, "WATCHLIST": 2, "NORMAL": 3, "NO_SIGNAL": 4}
    students_data.sort(key=lambda x: (zone_order.get(x["zone"], 5), -x["rectified_delta"]))

    dist = DashboardDistribution(
        median_delta=summary["median_delta"],
        mad=summary["mad"],
        robust_sigma=summary["robust_sigma"],
        sigma_thresholds=summary["sigma_thresholds"],
    )

    return DashboardResponse(
        project="Themis Project",
        course_id=course_id,
        topic_id=topic_id,
        total_students=total_students,
        opted_out_or_incomplete=opted_out_count,
        sessions_completed=completed_count,
        distribution=dist,
        alerts_count=summary["alerts_count"],
        students=students_data,
    )


@app.get("/api/v1/audit/report/{student_id}", response_model=AIReportResponse)
async def get_student_report(
    student_id: str,
    topic_id: str = Query("week_09_deep_learning"),
    course_id: str = Query("prog_ai_2026")
):
    """
    Эндпоинт 5: Доказательный аналитический отчет аудита (AI Discrepancy Report).
    Предоставляет преподавателю цитаты, концепты и психометрические основания.
    """
    resolved_topic = resolve_topic_id(topic_id)
    rec = None
    for r in db_records.values():
        if (r.student_id == student_id and 
            getattr(r, "course_id", "prog_ai_2026") == course_id and 
            resolve_topic_id(getattr(r, "topic_id", CANONICAL_TOPIC_ID)) == resolved_topic):
            rec = r
            break
    if not rec:
        rec = db_records.get(student_id)

    if not rec:
        raise HTTPException(status_code=404, detail="Student not found")

    if rec.session_status != "COMPLETED" or rec.extraction is None:
        raise HTTPException(
            status_code=400,
            detail="Отчет недоступен: сессия не завершена или студент не участвовал в диалоге.",
        )

    ext = rec.extraction
    if rec.e_d_squared is None and rec.extraction:
        engine.compute_individual_depth(rec)
    p1, p2, p3 = rec.agg_probabilities

    # Определяем доминирующий когнитивный уровень
    if p3 >= 0.5:
        dominant = "Extended Abstract (SOLO Level 3)"
    elif p2 >= 0.5:
        dominant = "Relational (SOLO Level 2)"
    else:
        dominant = "Multistructural / Surface (SOLO Level 1)"

    solo_analysis = ReportSOLOAnalysis(
        dominant_level=dominant,
        aggregated_probabilities={"p1": p1, "p2": p2, "p3": p3},
        e_d_squared=rec.e_d_squared,
        s_solo_calibrated=rec.s_solo,
        socratic_initiative_bonus=1.0 if ext.socratic_initiative else 0.0,
        k_density=rec.k_density,
        c_sample=rec.c_sample,
    )

    evidence = ReportEvidence(
        student_quotes=ext.student_quotes,
        mastered_concepts=ext.mastered_concepts,
        telemetry_clean=rec.telemetry_clean,
        pedagogical_justification=ext.pedagogical_justification,
    )

    topic_data = rag_service.get_topic_data(resolved_topic)
    topic_title = topic_data.get("title", resolved_topic) if topic_data else resolved_topic
    concepts_list = ext.mastered_concepts if ext and ext.mastered_concepts else []
    concepts_str = ", ".join(concepts_list[:4]) if concepts_list else "ключевых концептов темы"
    rectified_grade = int(round(rec.ai_depth_score or rec.in_class_grade or 90))
    delta_str = f"+{rec.rectified_delta}"

    if rec.zone == "NORMAL" or rec.rectified_delta <= 0:
        recommended_action = "Согласие каналов: очная оценка полностью отражает уровень знаний, вмешательство не требуется."
    elif rec.zone == "HIGH_DISCREPANCY":
        # PURPLE зона: значимый нераскрытый потенциал / академическая аномалия
        recommended_action = (
            f"Рекомендуется ректификация оценки до {rectified_grade} баллов (Δ = {delta_str}, Z = +{rec.z_score}σ) "
            f"на основе демонстрации понятий: {concepts_str}."
        )
    elif rec.zone == "AUDIT_TRIGGER":
        # RED зона: сильное расхождение, триггер аудита
        recommended_action = (
            f"Рекомендуется 2-минутный устный блиц-вопрос по теме '{topic_title}' (понятия: {concepts_str}) "
            f"для подтверждения пересмотра очной оценки с потенциалом до {rectified_grade} баллов (Δ = {delta_str})."
        )
    elif rec.zone == "WATCHLIST":
        # YELLOW зона: умеренное расхождение
        recommended_action = (
            f"Умеренное расхождение каналов (Δ = {delta_str}). Рекомендуется контрольный устный вопрос по теме '{topic_title}' "
            f"для подтверждения освоения понятий: {concepts_str} (диагностический ориентир: {rectified_grade} баллов)."
        )
    else:
        # NO_SIGNAL или прочие
        recommended_action = "Сессия не завершена или студент не участвовал в диалоге. Очная оценка преподавателя остается без изменений."

    return AIReportResponse(
        student_id=rec.student_id,
        in_class_grade=rec.in_class_grade,
        ai_depth_score=rec.ai_depth_score,
        non_credit_notice=(
            f"Оценка ИИ ({rec.ai_depth_score}) является диагностической, не идет в зачет автоматически "
            "и не суммируется с оценкой преподавателя."
        ),
        rectified_delta=rec.rectified_delta,
        z_score=rec.z_score,
        zone=rec.zone,
        solo_analysis=solo_analysis,
        evidence=evidence,
        recommended_action=recommended_action,
    )


@app.post("/api/v1/audit/decision", response_model=TeacherDecisionResponse)
async def submit_teacher_decision(req: TeacherDecisionRequest):
    """
    Фиксация решения преподавателя по результатам психометрического аудита (Human-in-the-Loop).
    Действия:
    - ACCEPT_RECTIFICATION: утверждение ректификации с обновлением очной оценки in_class_grade.
      Строго соблюдается инвариант Zero Downward Penalty: new_grade не может быть ниже текущей оценки.
    - REJECT: отклонение ректификации, сохранение очной оценки без изменений.
    - ORAL_BLITZ: назначение 2-минутного контрольного блиц-опроса по теме.
    - KEEP_CURRENT: подтверждение текущей оценки преподавателя.
    """
    resolved_topic = resolve_topic_id(req.topic_id)

    # 1. Поиск записи студента
    target_rec = None
    for r in db_records.values():
        if (
            r.student_id == req.student_id
            and getattr(r, "course_id", "prog_ai_2026") == req.course_id
            and resolve_topic_id(getattr(r, "topic_id", CANONICAL_TOPIC_ID)) == resolved_topic
        ):
            target_rec = r
            break
    if not target_rec:
        target_rec = db_records.get(req.student_id)

    if not target_rec:
        raise HTTPException(status_code=404, detail=f"Студент {req.student_id} не найден в когорте.")

    previous_grade = float(target_rec.in_class_grade) if target_rec.in_class_grade is not None else 70.0

    # 2. Строгий инвариант Zero Downward Penalty: запрет занижения оценки
    if req.new_grade is not None and req.new_grade < previous_grade:
        raise HTTPException(
            status_code=400,
            detail="Themis policy violation: grade cannot be revised downward"
        )

    # 3. Валидация действия
    valid_actions = {"ACCEPT_RECTIFICATION", "REJECT", "ORAL_BLITZ", "KEEP_CURRENT"}
    if req.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Недопустимое действие: {req.action}. Допустимы: {valid_actions}")

    updated_grade = previous_grade

    if req.action == "ACCEPT_RECTIFICATION":
        if req.new_grade is not None:
            updated_grade = float(req.new_grade)
        elif target_rec.ai_depth_score is not None:
            updated_grade = float(round(target_rec.ai_depth_score, 1))
        else:
            updated_grade = previous_grade

        if updated_grade < previous_grade:
            raise HTTPException(
                status_code=400,
                detail="Themis policy violation: grade cannot be revised downward"
            )

        target_rec.in_class_grade = updated_grade
        # Пересчитываем дельты для студента
        if target_rec.ai_depth_score is not None:
            target_rec.raw_delta = round(target_rec.ai_depth_score - updated_grade, 1)
            target_rec.rectified_delta = round(max(0.0, target_rec.raw_delta), 1)

        comment_part = f" ({req.comment})" if req.comment else ""
        decision_str = f"ACCEPT_RECTIFICATION: {previous_grade} -> {updated_grade}{comment_part}"
        target_rec.teacher_decision = decision_str
        message = f"Ректификация принята. Оценка студента {req.student_id} обновлена: {previous_grade} -> {updated_grade}."

        # Реактивный пересчет когортного распределения (Этап 3B)
        engine.compute_cohort_discrepancy(list(db_records.values()))

    elif req.action == "REJECT":
        comment_part = f" ({req.comment})" if req.comment else ""
        target_rec.teacher_decision = f"REJECT: rectification rejected{comment_part}"
        message = f"Ректификация отклонена. Оценка {previous_grade} сохранена без изменений."

    elif req.action == "ORAL_BLITZ":
        comment_part = f" ({req.comment})" if req.comment else ""
        target_rec.teacher_decision = f"ORAL_BLITZ: scheduled 2-min oral verification{comment_part}"
        message = f"Назначен 2-минутный устный блиц-опрос для студента {req.student_id}."

    elif req.action == "KEEP_CURRENT":
        comment_part = f" ({req.comment})" if req.comment else ""
        target_rec.teacher_decision = f"KEEP_CURRENT: grade confirmed{comment_part}"
        message = f"Очная оценка {previous_grade} подтверждена без изменений."

    # Персистентное сохранение в SQLite
    sync_records_to_sqlite()

    return TeacherDecisionResponse(
        status="SUCCESS",
        student_id=req.student_id,
        course_id=req.course_id,
        topic_id=resolved_topic,
        action=req.action,
        previous_grade=previous_grade,
        updated_grade=updated_grade,
        teacher_decision=target_rec.teacher_decision or req.action,
        message=message,
        record={
            "student_id": target_rec.student_id,
            "in_class_grade": target_rec.in_class_grade,
            "ai_depth_score": target_rec.ai_depth_score,
            "rectified_delta": target_rec.rectified_delta,
            "z_score": target_rec.z_score,
            "zone": target_rec.zone,
            "teacher_decision": target_rec.teacher_decision,
        }
    )


@app.get("/api/v1/system/health", response_model=SystemHealthResponse)
async def system_health():
    """
    Системный мониторинг состояния Themis Project:
    - Проверка подключения к персистентной БД SQLite
    - Текущий режим языковой модели (LLM_MODE)
    - Проверка состояния коллекции ChromaDB и модели эмбеддингов BAAI/bge-m3
    """
    # 1. Проверка базы данных SQLite
    db_status = "connected"
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT 1")
        conn.close()
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. Проверка векторного хранилища ChromaDB
    v_status = "ready"
    collection_count = 0
    try:
        if vector_store.collection:
            collection_count = vector_store.collection.count()
        else:
            v_status = "not_initialized"
    except Exception as e:
        v_status = f"error: {str(e)}"

    return SystemHealthResponse(
        status="OK" if db_status == "connected" and "error" not in v_status else "DEGRADED",
        database=db_status,
        llm_mode=settings.LLM_MODE,
        vector_store=VectorStoreHealth(
            status=v_status,
            collection_count=collection_count,
            dimension=1024,
            model="BAAI/bge-m3",
        ),
    )


@app.post("/api/v1/student/{student_id}/reset")
async def reset_single_student(student_id: str):
    """
    Сброс конкретного студента до начального состояния:
    - Очищает историю диалогов и сессий в SQLite и в памяти
    - Сбрасывает оценку S_depth до None, статус сессии до OPTED_OUT
    - Сохраняет исходную очную оценку G_prof
    - Пересчитывает когортные метрики ThemisMathEngine
    - Синхронизирует обновленное состояние в SQLite
    """
    if student_id not in db_records:
        raise HTTPException(status_code=404, detail="Студент не найден в когорте")

    # 1. Удаляем сессии студента из оперативной памяти
    sessions_to_remove = [
        s_id for s_id, s_data in db_sessions.items()
        if s_data.get("student_id") == student_id
    ]
    for s_id in sessions_to_remove:
        del db_sessions[s_id]

    # 2. Удаляем сессии и реплики из SQLite
    delete_student_dialogs(student_id)

    # 3. Сбрасываем запись студента
    record = db_records[student_id]
    record.session_status = "OPTED_OUT"
    record.turns_count = 0
    record.total_tokens = 0
    record.ai_depth_score = None
    record.raw_delta = 0.0
    record.rectified_delta = 0.0
    record.z_score = 0.0
    record.zone = "NO_SIGNAL"
    record.extraction = None

    # 4. Пересчитываем когортные метрики среди оставшихся завершенных сессий
    engine.compute_cohort_discrepancy(list(db_records.values()))

    # 5. Синхронизируем всех студентов в SQLite
    sync_records_to_sqlite()

    return {
        "status": "SUCCESS",
        "message": f"Студент {student_id} успешно сброшен к начальной оценке ({record.in_class_grade}) без ИИ.",
        "student_id": student_id,
        "in_class_grade": record.in_class_grade,
        "session_status": record.session_status,
        "ai_depth_score": record.ai_depth_score,
        "rectified_delta": record.rectified_delta,
        "z_score": record.z_score,
        "zone": record.zone,
    }


@app.post("/api/v1/student/{student_id}/restore_canonical")
async def restore_canonical_student(student_id: str):
    """
    Восстановление канонического эталонного состояния студента (для быстрой демонстрации Студента К. 93.5).
    """
    canonical_list = get_canonical_seed_records()
    target_canonical = next((r for r in canonical_list if r.student_id == student_id), None)
    if not target_canonical:
        raise HTTPException(status_code=404, detail="Каноническая запись для студента не найдена")

    db_records[student_id] = target_canonical

    if student_id == "stud_aai_042":
        seed_sqlite_dialogs()
        db_sessions["sess_canonical_stud_k"] = {
            "student_id": "stud_aai_042",
            "course_id": "prog_ai_2026",
            "topic_id": "week_09_deep_learning",
            "turns": [
                {
                    "turn_number": 1,
                    "student": "Переобучение происходит, когда веса подстраиваются под специфический шум выборки, создавая избыточную ко-адаптацию нейронов.",
                    "system": "Отлично. Ты упомянул ко-адаптацию нейронов. Каким именно математическим механизмом метод Dropout предотвращает эту ко-адаптацию в процессе обратного распространения ошибки?",
                    "typing_duration_ms": 18000,
                    "is_duplicate": False,
                    "similarity_score": 0.15,
                },
                {
                    "turn_number": 2,
                    "student": "Dropout случайным образом обнуляет активации нейронов с вероятностью p во время прямого прохода. Это заставляет каждый нейрон обучаться полезным признакам независимо от соседей, имитируя ансамбль подсетей.",
                    "system": "Глубокое понимание ансамблевой природы Dropout. А что происходит на экстремальных границах? Например, при слишком высокой вероятности отключения нейронов?",
                    "typing_duration_ms": 21000,
                    "is_duplicate": False,
                    "similarity_score": 0.22,
                },
                {
                    "turn_number": 3,
                    "student": "Если Dropout так эффективен, почему бы нам не выключать 80% нейронов для максимальной регуляризации? В какой момент это сломает обучение и вызовет потерю емкости сети (underfitting)?",
                    "system": "Блестящий исследовательский вопрос! Отключение 80% нейронов катастрофически снижает эффективную емкость сети (model capacity), вызывая недообучение (underfitting). Баланс между регуляризацией и емкостью — фундаментальный компромисс глубокого обучения.",
                    "typing_duration_ms": 25000,
                    "is_duplicate": False,
                    "similarity_score": 0.18,
                },
            ],
            "created_at": 0,
            "active": True,
        }

    engine.compute_cohort_discrepancy(list(db_records.values()))
    sync_records_to_sqlite()

    return {
        "status": "SUCCESS",
        "message": f"Канонический эталон для студента {student_id} восстановлен.",
        "student_id": student_id,
        "in_class_grade": target_canonical.in_class_grade,
        "ai_depth_score": target_canonical.ai_depth_score,
        "rectified_delta": target_canonical.rectified_delta,
        "z_score": target_canonical.z_score,
        "zone": target_canonical.zone,
    }


@app.post("/api/v1/demo/reset")
async def demo_reset():
    """
    Эндпоинт 6: Сброс базы данных до исходного канонического состояния (Use Case).
    """
    reset_database(load_from_db_if_exists=False)
    return {"status": "SUCCESS", "message": "Demo data reset to canonical 20-student cohort."}


# =====================================================================
# TELEGRAM MINI APP (TMA) & WEBHOOK ЭНДПОИНТЫ
# =====================================================================

tma_frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "tma.html")

@app.get("/tma", response_class=HTMLResponse)
async def serve_tma():
    """Раздача интерфейса мобильного Telegram Mini App (TMA)."""
    if os.path.exists(tma_frontend_path):
        with open(tma_frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Telegram Mini App frontend not found.</h1>", status_code=404)


@app.get("/api/v1/tma/me")
async def get_tma_current_user(request: Request):
    """
    Эндпоинт получения контекста текущего пользователя в Telegram Mini App.
    Авторизует по initData (Authorization: tma ... или X-Telegram-Init-Data).
    Возвращает student_id, display_name, group_id, in_class_grade, session_status, ai_depth_score, rectified_delta.
    """
    student_id = await resolve_student_context(request)
    identity = get_student_identity(student_id)
    rec = db_records.get(student_id)
    audit = None if rec else get_student_audit(student_id)

    display_name = (identity.get("display_name") if identity else None) or (rec.student_name if rec else None) or STUDENT_NAMES_MAP.get(student_id, student_id)
    group_id = (identity.get("group_id") if identity else None) or (getattr(rec, "group_id", "group_1") if rec else "group_1")
    default_grade = identity.get("default_grade", 75.0) if identity else 75.0
    in_class_grade = rec.in_class_grade if rec and rec.in_class_grade is not None else (audit["in_class_grade"] if audit else default_grade)
    session_status = rec.session_status if rec else (audit["session_status"] if audit else "OPTED_OUT")
    ai_depth_score = rec.ai_depth_score if rec else (audit["ai_depth_score"] if audit else None)
    rectified_delta = rec.rectified_delta if rec else (audit["rectified_delta"] if audit else 0.0)
    zone = rec.zone if rec else (audit["zone"] if audit else "NO_SIGNAL")

    return {
        "student_id": student_id,
        "display_name": display_name,
        "group_id": group_id,
        "in_class_grade": in_class_grade,
        "telegram_id": identity.get("telegram_id") if identity else None,
        "session_status": session_status,
        "ai_depth_score": ai_depth_score,
        "rectified_delta": rectified_delta,
        "zone": zone,
    }


@app.post("/api/v1/tma/link")
async def link_tma_student(req: TmaLinkRequest):
    """
    Связка существующего student_id (например stud_aai_042) с telegram_id по коду привязки.
    """
    if not req.student_id or not req.telegram_id:
        raise HTTPException(status_code=400, detail="student_id and telegram_id are required")

    success = link_telegram_identity(
        student_id=req.student_id,
        telegram_id=req.telegram_id,
        telegram_username=req.telegram_username
    )
    if not success:
        # Если студент еще не в student_identities, создаем запись
        identity = get_student_identity(req.student_id)
        if not identity:
            rec = db_records.get(req.student_id)
            display_name = getattr(rec, "student_name", None) or STUDENT_NAMES_MAP.get(req.student_id, req.student_id)
            save_student_identity(
                student_id=req.student_id,
                display_name=display_name,
                telegram_id=req.telegram_id,
                telegram_username=req.telegram_username,
                group_id=getattr(rec, "group_id", "group_1") if rec else "group_1",
                default_grade=rec.in_class_grade if rec else 75.0
            )
            success = True

    return {
        "status": "SUCCESS",
        "message": f"Студент {req.student_id} успешно привязан к Telegram ID {req.telegram_id}",
        "student_id": req.student_id,
        "telegram_id": req.telegram_id
    }


@app.post("/api/v1/tma/webhook")
async def tma_webhook(update: Dict[str, Any]):
    """
    Прием и обработка webhook обновлений от Telegram Bot API (команды /start, /help, callbacks).
    """
    result = await telegram_bot.handle_update(update)
    return {"ok": True, "result": result}


@app.post("/api/v1/session/opt-out")
async def session_opt_out(request: Request, payload: Optional[Dict[str, Any]] = None):
    """
    Добровольный выход студента из сократической сессии («Принцип Цифрового пандуса» UDL).
    Сессия завершается без отправки ответов на психометрический расчет,
    очная оценка G_prof сохраняется в 100% объеме без штрафов (Zero Downward Penalty).
    """
    data = payload or {}
    student_id = data.get("student_id")
    session_id = data.get("session_id")

    if not student_id:
        try:
            student_id = await resolve_student_context(request)
        except Exception:
            student_id = "stud_aai_042"

    # Удаляем активные сессии
    sessions_to_close = []
    for s_id, s_data in db_sessions.items():
        if s_data.get("student_id") == student_id or (session_id and s_id == session_id):
            sessions_to_close.append(s_id)
            s_data["active"] = False

    for s_id in sessions_to_close:
        if s_id in db_sessions:
            del db_sessions[s_id]

    delete_student_dialogs(student_id)

    # Сбрасываем статус записи в db_records
    rec = db_records.get(student_id)
    if rec:
        rec.session_status = "OPTED_OUT"
        rec.turns_count = 0
        rec.ai_depth_score = None
        rec.raw_delta = 0.0
        rec.rectified_delta = 0.0
        rec.z_score = 0.0
        rec.zone = "NO_SIGNAL"
        rec.extraction = None
        engine.compute_cohort_discrepancy(list(db_records.values()))
        sync_records_to_sqlite()
        grade = rec.in_class_grade
    else:
        identity = get_student_identity(student_id)
        grade = identity.get("default_grade", 75.0) if identity else 75.0
        reset_student_in_db(student_id, default_in_class_grade=grade)

    return {
        "status": "OPTED_OUT",
        "message": f"Сессия добровольно завершена. Ваша очная оценка ({grade}) полностью сохранена.",
        "student_id": student_id,
        "in_class_grade": grade,
        "ai_depth_score": None,
        "rectified_delta": 0.0,
        "zone": "NO_SIGNAL"
    }


# =====================================================================
# ПЕРСОНАЛЬНАЯ АВТОРИЗАЦИЯ И ОДНОРАЗОВАЯ ПРИВЯЗКА TELEGRAM
# =====================================================================

@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def auth_login(req: LoginRequest):
    """
    Эндпоинт входа в систему (для 20 студентов группы ИИ-201 и преподавателя).
    Проверяет логин и пароль в user_credentials.
    Возвращает токен сессии, роль, student_id и статус привязки Telegram.
    """
    cred = get_user_credential(req.username)
    if not cred or not verify_password(req.password, cred["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Неверное имя пользователя или пароль"
        )

    sid = cred.get("student_id")
    token = create_auth_session(
        username=cred["username"],
        role=cred["role"],
        display_name=cred["display_name"],
        student_id=sid
    )

    is_tg_linked = False
    tg_username = None
    if sid:
        ident = get_student_identity(sid)
        if ident and ident.get("telegram_id") is not None:
            is_tg_linked = True
            tg_username = ident.get("telegram_username")

    return LoginResponse(
        success=True,
        token=token,
        role=cred["role"],
        student_id=sid,
        display_name=cred["display_name"],
        is_telegram_linked=is_tg_linked,
        telegram_username=tg_username
    )


@app.get("/api/v1/auth/me", response_model=AuthMeResponse)
async def auth_me(request: Request, token: Optional[str] = Query(None)):
    """
    Проверка текущей сессии пользователя и актуального статуса привязки Telegram.
    Токен передается в заголовке Authorization: Bearer <token> или параметре ?token=...
    """
    auth_header = request.headers.get("Authorization")
    extracted_token = None
    if auth_header and "bearer" in auth_header.lower():
        extracted_token = auth_header.split(maxsplit=1)[1].strip()
    elif token:
        extracted_token = token.strip()

    if not extracted_token:
        raise HTTPException(status_code=401, detail="Отсутствует токен авторизации")

    sess = get_auth_session(extracted_token)
    if not sess:
        raise HTTPException(status_code=401, detail="Сессия не найдена или истекла")

    sid = sess.get("student_id")
    is_tg_linked = False
    tg_username = None
    if sid:
        ident = get_student_identity(sid)
        if ident and ident.get("telegram_id") is not None:
            is_tg_linked = True
            tg_username = ident.get("telegram_username")

    return AuthMeResponse(
        authenticated=True,
        username=sess["username"],
        role=sess["role"],
        student_id=sid,
        display_name=sess["display_name"],
        is_telegram_linked=is_tg_linked,
        telegram_username=tg_username
    )


@app.post("/api/v1/auth/logout", response_model=LogoutResponse)
async def auth_logout(request: Request, payload: Optional[Dict[str, Any]] = None):
    """
    Сброс сессии пользователя (логаут).
    """
    auth_header = request.headers.get("Authorization")
    extracted_token = None
    if auth_header and "bearer" in auth_header.lower():
        extracted_token = auth_header.split(maxsplit=1)[1].strip()
    elif payload and "token" in payload:
        extracted_token = str(payload["token"]).strip()

    if extracted_token:
        delete_auth_session(extracted_token)

    return LogoutResponse(success=True, message="Сессия успешно завершена")


@app.get("/api/v1/auth/telegram-qr", response_model=TelegramQrResponse)
async def auth_telegram_qr(student_id: str = Query(...)):
    """
    Генерация одноразового Deep Link и токена привязки Telegram-аккаунта (TTL 15 минут).
    Возвращает: token ('bind_<12-hex>'), deep_link (https://t.me/{bot}?start=bind_{token}), expires_in (900).
    """
    clean_sid = student_id.strip()
    ident = get_student_identity(clean_sid)
    if not ident and clean_sid not in STUDENT_NAMES_MAP:
        raise HTTPException(status_code=404, detail=f"Студент {clean_sid} не найден")

    token_info = create_telegram_binding_token(student_id=clean_sid, ttl_seconds=900)
    token = token_info["token"]

    bot_username = settings.TELEGRAM_BOT_USERNAME or "ThemisExamBot"
    deep_link = f"https://t.me/{bot_username}?start={token}"
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={urllib.parse.quote(deep_link)}"

    return TelegramQrResponse(
        token=token,
        deep_link=deep_link,
        expires_in=900,
        qr_code_url=qr_url
    )


# =====================================================================
# ОТДАЧА СТАТИКИ И ФРОНТЕНДА
# =====================================================================

frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "index.html")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    if os.path.exists(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Themis Project Backend is running. Frontend index.html not found.</h1>")

