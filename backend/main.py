"""
main.py

FastAPI веб-приложение Themis Project (v2.0).
Реализует 5 основных REST эндпоинтов + эндпоинт сброса демо + отдачу SPA интерфейса.
"""

from typing import Dict, Any, List, Optional
import os
import uuid
import shutil
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
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
)
from backend.ingestion_service import ingestion_service, UPLOADS_DIR
from backend.vector_store import vector_store

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
        })
    bulk_save_student_audits(items)


def reset_database(load_from_db_if_exists: bool = False):
    """
    Инициализация состояния когорты (20 студентов Группы 1).
    При load_from_db_if_exists=True восстанавливает актуальное состояние студентов из SQLite.
    При сбросе инициализирует каноническую когорту и синхронизирует её в SQLite.
    """
    db_records.clear()
    db_sessions.clear()

    existing_audits = get_all_student_audits() if load_from_db_if_exists else []
    if existing_audits and len(existing_audits) == 20:
        for row in existing_audits:
            extraction = None
            if row.get("extraction_json"):
                try:
                    extraction = AuditExtractionResult.model_validate_json(row["extraction_json"])
                except Exception:
                    extraction = None
            rec = StudentAuditRecord(
                student_id=row["student_id"],
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
                telemetry_clean=True,
            )
            db_records[row["student_id"]] = rec
        engine.compute_cohort_discrepancy(list(db_records.values()))
    else:
        conn = get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM student_audits")
        conn.commit()
        conn.close()

        seed_records = get_canonical_seed_records()
        for rec in seed_records:
            db_records[rec.student_id] = rec
        seed_sqlite_dialogs()
        sync_records_to_sqlite()

    # Загружаем сессии из SQLite в db_sessions при наличии
    if get_session("sess_canonical_stud_k"):
        turns = get_turns("sess_canonical_stud_k")
        if turns:
            db_sessions["sess_canonical_stud_k"] = {
                "student_id": "stud_aai_042",
                "course_id": "prog_ai_2026",
                "topic_id": "topic_05_regularization",
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

    if get_session("sess_canonical_stud_015"):
        turns = get_turns("sess_canonical_stud_015")
        if turns:
            db_sessions["sess_canonical_stud_015"] = {
                "student_id": "stud_aai_015",
                "course_id": "prog_ai_2026",
                "topic_id": "topic_05_regularization",
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Инициализация при старте с подтягиванием персистентного состояния из SQLite
    reset_database(load_from_db_if_exists=True)
    yield
    # Очистка при завершении


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

@app.get("/api/v1/syllabus/weeks")
async def get_syllabus_weeks():
    """
    Возвращает список учебных недель курса 'Программирование для ИИ' (PAI 2026).
    Включает как канонические недели, так и динамически загруженные преподавателем.
    """
    return rag_service.get_all_weeks()


@app.post("/api/v1/course/upload")
async def upload_course_lecture(
    file: UploadFile = File(...),
    week_number: int = Form(...),
    topic_name: str = Form(...),
):
    """
    Эндпоинт загрузки и онлайновой индексации лекций курса (PPTX / PDF).
    Демонстрирует Zero-Config Ingestion на IT Fest:
    1. Сохраняет файл в data/uploads/
    2. Разбирает слайды на семантические чанки
    3. Индексирует в ChromaDB (HNSW граф) с помощью модели эмбеддингов BGE-M3
    4. Автоматически извлекает глоссарий и генерирует стартовый сократический триггер
    5. Регистрирует новую неделю в силлабусе курса без перезапуска сервера
    """
    filename = file.filename or "lecture.pptx"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".pptx", ".pdf"]:
        raise HTTPException(status_code=400, detail="Поддерживаются только презентации .pptx и документы .pdf")

    saved_path = os.path.join(UPLOADS_DIR, f"week_{week_number}_{filename}")
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        if ext == ".pptx":
            slides_data = ingestion_service.parse_pptx(saved_path)
        else:
            slides_data = ingestion_service.parse_pdf(saved_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Ошибка парсинга презентации: {str(e)}")

    if not slides_data:
        raise HTTPException(status_code=422, detail="Не удалось извлечь слайды из загруженного файла")

    topic_id = f"week_{week_number:02d}_custom"

    # Векторизация и индексация в HNSW граф ChromaDB
    indexed_count = vector_store.add_slides(
        topic_id=topic_id,
        week_number=week_number,
        slides_data=slides_data
    )

    # Генерация метаданных и глоссария
    meta = ingestion_service.build_course_metadata(
        topic_id=topic_id,
        week_number=week_number,
        topic_name=topic_name,
        slides=slides_data
    )

    # Динамическая регистрация в силлабусе
    rag_service.register_dynamic_week(
        topic_id=topic_id,
        week_number=week_number,
        title=meta["title"],
        topic_name=meta["topic_name"],
        initial_prompt=meta["initial_prompt"],
        glossary=meta["glossary"],
        slides_count=len(slides_data)
    )

    return {
        "status": "SUCCESS",
        "message": "Лекция успешно обработана и проиндексирована в HNSW (BGE-M3)",
        "week_number": week_number,
        "topic_id": topic_id,
        "title": meta["title"],
        "topic_name": topic_name,
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
async def get_active_session(student_id: str, topic_id: str = Query("topic_05_regularization")):
    """
    Эндпоинт восстановления сессии студента из оперативной памяти или SQLite.
    Позволяет бесшовно восстанавливать историю диалога при F5 или смене студента в UI.
    """
    target_session_id = None
    # 1. Поиск в памяти
    for s_id, s_data in db_sessions.items():
        if s_data.get("student_id") == student_id and s_data.get("topic_id") == topic_id:
            target_session_id = s_id
            break

    # 2. Если в памяти нет, ищем в SQLite
    if not target_session_id:
        row = get_latest_session_for_student(student_id, topic_id)
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

    initial_prompt = rag_service.get_initial_prompt(topic_id)

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
    status = "COMPLETED" if turns_count >= settings.TARGET_TURNS else "ACTIVE"

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
async def start_session(req: SessionStartRequest):
    """
    Эндпоинт 1: Инициализация добровольной сократической сессии («Цифровой пандус»).
    Проверяет доступность окна расписания и возвращает контекстный стартовый вопрос.
    """
    # Если принудительный рестарт не запрошен, проверяем наличие уже существующей активной сессии
    if not req.force_open:
        for s_id, s_data in db_sessions.items():
            if s_data.get("student_id") == req.student_id and s_data.get("topic_id") == req.topic_id and s_data.get("active", True):
                initial_prompt = rag_service.get_initial_prompt(req.topic_id)
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
        db_records[req.student_id] = StudentAuditRecord(
            student_id=req.student_id,
            in_class_grade=70.0,
            session_status="INCOMPLETE_IGNORED",
            turns_count=0,
            total_tokens=0,
        )

    initial_prompt = rag_service.get_initial_prompt(req.topic_id)

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
    else:
        record.session_status = "INCOMPLETE_IGNORED"
        confidence_str = f"LOW (N = {turn_number}/{settings.TARGET_TURNS})"

    # Сохраняем в SQLite для персистентности
    sync_records_to_sqlite()

    return DialogTurnResponse(
        session_id=req.session_id,
        turn_number=turn_number,
        system_reply=system_reply,
        session_confidence=confidence_str,
        is_duplicate=False,
    )


@app.post("/api/v1/sync/in-class-grades", response_model=GradeSyncResponse)
async def sync_in_class_grades(req: GradeSyncRequest):
    """
    Эндпоинт 3: Синхронизация очных оценок преподавателя.
    Запускает реактивный когортный расчет (Этап 3B) за < 10 мс.
    """
    synced = 0
    for item in req.records:
        if item.student_id in db_records:
            db_records[item.student_id].in_class_grade = item.in_class_grade
            synced += 1
        else:
            rec = StudentAuditRecord(
                student_id=item.student_id,
                in_class_grade=item.in_class_grade,
                session_status="OPTED_OUT",
            )
            db_records[item.student_id] = rec
            synced += 1

    summary = engine.compute_cohort_discrepancy(list(db_records.values()))
    return GradeSyncResponse(
        status="SUCCESS",
        synced_count=synced,
        cohort_summary=summary,
    )


@app.get("/api/v1/audit/dashboard", response_model=DashboardResponse)
async def get_audit_dashboard(
    topic_id: str = Query("topic_05_regularization"),
    group_id: Optional[str] = Query(None)
):
    """
    Эндпоинт 4: Дашборд распределения сигм и полный список когорты (Консоль преподавателя).
    Поддерживает фильтрацию по группе (group_id='group_1' — 20 студентов).
    Если group_id не указан — выдает полную когорту потока (28 студентов).
    """
    if group_id:
        records_list = [r for r in db_records.values() if getattr(r, "group_id", "group_1") == group_id]
    else:
        records_list = list(db_records.values())

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
            "telemetry_clean": r.telemetry_clean,
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
        topic_id=topic_id,
        total_students=total_students,
        opted_out_or_incomplete=opted_out_count,
        sessions_completed=completed_count,
        distribution=dist,
        alerts_count=summary["alerts_count"],
        students=students_data,
    )


@app.get("/api/v1/audit/report/{student_id}", response_model=AIReportResponse)
async def get_student_report(student_id: str, topic_id: str = Query("topic_05_regularization")):
    """
    Эндпоинт 5: Доказательный аналитический отчет аудита (AI Discrepancy Report).
    Предоставляет преподавателю цитаты, концепты и психометрические основания.
    """
    rec = db_records.get(student_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Student not found")

    if rec.session_status != "COMPLETED" or rec.extraction is None:
        raise HTTPException(
            status_code=400,
            detail="Отчет недоступен: сессия не завершена или студент не участвовал в диалоге.",
        )

    ext = rec.extraction
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

    recommended_action = (
        "Рекомендуется задать 1 контрольный устный блиц-вопрос по емкости модели на следующем "
        f"занятии для подтверждения пересмотра очной оценки (ориентир потенциала: {int(rec.ai_depth_score or 90)})."
    )

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
            "topic_id": "topic_05_regularization",
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
# ОТДАЧА СТАТИКИ И ФРОНТЕНДА
# =====================================================================

frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "index.html")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    if os.path.exists(frontend_path):
        with open(frontend_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Themis Project Backend is running. Frontend index.html not found.</h1>")

