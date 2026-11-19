"""
database.py

Постоянное реляционное хранилище Themis Project на базе SQLite.
Обеспечивает сохранение истории сократических сессий, пошаговых реплик,
детекции повторов (similarity), результатов психометрического аудита,
а также мульти-курсовую изоляцию (courses, syllabus_weeks, lecture_glossary,
student_identities, ingestion_jobs).
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "themis_data.db")

CANONICAL_COURSE_ID = "prog_ai_2026"
CANONICAL_TOPIC_ID = "week_09_deep_learning"
TOPIC_ALIASES = {
    "topic_05_regularization": "week_09_deep_learning",
}


def resolve_topic_id(topic_id: Optional[str]) -> str:
    """Унифицирует идентификатор темы, приводя алиасы к каноническому ID."""
    if not topic_id:
        return CANONICAL_TOPIC_ID
    return TOPIC_ALIASES.get(topic_id, topic_id)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate_db(conn: sqlite3.Connection):
    """Плавная миграция существующих таблиц SQLite к новой мульти-курсовой схеме."""
    cursor = conn.cursor()

    # 1. Миграция syllabus_weeks: добавление course_id и составного ключа (course_id, topic_id)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='syllabus_weeks'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(syllabus_weeks)")
        cols = [c["name"] for c in cursor.fetchall()]
        if "course_id" not in cols:
            cursor.execute("ALTER TABLE syllabus_weeks RENAME TO _mig_sw_old")
            cursor.execute("""
                CREATE TABLE syllabus_weeks (
                    course_id TEXT NOT NULL,
                    topic_id TEXT NOT NULL,
                    week_number INTEGER,
                    title TEXT NOT NULL,
                    topic_name TEXT,
                    initial_prompt TEXT,
                    demo_turns_json TEXT,
                    md_path TEXT,
                    chunks_count INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (course_id, topic_id)
                )
            """)
            cursor.execute("""
                INSERT OR REPLACE INTO syllabus_weeks (
                    course_id, topic_id, week_number, title, topic_name, initial_prompt, demo_turns_json, md_path, chunks_count, updated_at
                )
                SELECT 
                    'prog_ai_2026', topic_id, week_number, title, topic_name, initial_prompt, NULL, md_path, chunks_count, updated_at
                FROM _mig_sw_old
            """)
            cursor.execute("DROP TABLE _mig_sw_old")
            conn.commit()

    # 2. Миграция lecture_glossary: добавление course_id и составного ключа (course_id, topic_id, term)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='lecture_glossary'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(lecture_glossary)")
        cols = [c["name"] for c in cursor.fetchall()]
        if "course_id" not in cols:
            cursor.execute("ALTER TABLE lecture_glossary RENAME TO _mig_lg_old")
            cursor.execute("""
                CREATE TABLE lecture_glossary (
                    course_id TEXT NOT NULL,
                    topic_id TEXT NOT NULL,
                    term TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (course_id, topic_id, term)
                )
            """)
            cursor.execute("""
                INSERT OR IGNORE INTO lecture_glossary (course_id, topic_id, term)
                SELECT 'prog_ai_2026', topic_id, term FROM _mig_lg_old
            """)
            cursor.execute("DROP TABLE _mig_lg_old")
            conn.commit()

    # 3. Миграция student_audits: составной ключ (student_id, course_id, topic_id) + telemetry_clean, teacher_decision
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='student_audits'")
    if cursor.fetchone():
        cursor.execute("PRAGMA table_info(student_audits)")
        col_infos = cursor.fetchall()
        cols = [c["name"] for c in col_infos]
        pk_cols = [c["name"] for c in col_infos if c["pk"] > 0]
        if "course_id" not in cols or "telemetry_clean" not in cols or len(pk_cols) < 3:
            cursor.execute("ALTER TABLE student_audits RENAME TO _mig_sa_old")
            cursor.execute("""
                CREATE TABLE student_audits (
                    student_id TEXT NOT NULL,
                    course_id TEXT NOT NULL DEFAULT 'prog_ai_2026',
                    topic_id TEXT NOT NULL DEFAULT 'week_09_deep_learning',
                    student_name TEXT,
                    group_id TEXT DEFAULT 'group_1',
                    in_class_grade REAL,
                    session_status TEXT,
                    turns_count INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0,
                    ai_depth_score REAL,
                    raw_delta REAL,
                    rectified_delta REAL,
                    z_score REAL,
                    zone TEXT,
                    extraction_json TEXT,
                    telemetry_clean BOOLEAN DEFAULT 1,
                    teacher_decision TEXT DEFAULT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (student_id, course_id, topic_id)
                )
            """)
            # Проверяем какие колонки были в старой таблице
            old_has_tel = "telemetry_clean" in cols
            old_has_dec = "teacher_decision" in cols
            tel_expr = "telemetry_clean" if old_has_tel else "1"
            dec_expr = "teacher_decision" if old_has_dec else "NULL"

            cursor.execute(f"""
                INSERT OR REPLACE INTO student_audits (
                    student_id, course_id, topic_id, student_name, group_id, in_class_grade, session_status,
                    turns_count, total_tokens, ai_depth_score, raw_delta, rectified_delta,
                    z_score, zone, extraction_json, telemetry_clean, teacher_decision, updated_at
                )
                SELECT 
                    student_id, 'prog_ai_2026', 'week_09_deep_learning', student_name, group_id, in_class_grade, session_status,
                    turns_count, total_tokens, ai_depth_score, raw_delta, rectified_delta,
                    z_score, zone, extraction_json, {tel_expr}, {dec_expr}, updated_at
                FROM _mig_sa_old
            """)
            cursor.execute("DROP TABLE _mig_sa_old")
            conn.commit()


def init_db():
    """Инициализация схемы таблиц SQLite с поддержкой курсов, силлабуса и сессий."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Таблица курсов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            course_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            instructor TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Таблица силлабуса недель
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS syllabus_weeks (
            course_id TEXT NOT NULL,
            topic_id TEXT NOT NULL,
            week_number INTEGER,
            title TEXT NOT NULL,
            topic_name TEXT,
            initial_prompt TEXT,
            demo_turns_json TEXT,
            md_path TEXT,
            chunks_count INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (course_id, topic_id)
        )
    """)

    # 3. Таблица глоссария тем
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lecture_glossary (
            course_id TEXT NOT NULL,
            topic_id TEXT NOT NULL,
            term TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (course_id, topic_id, term)
        )
    """)

    # 4. Таблица цифровых личностей студентов (TMA / Telegram связка)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_identities (
            student_id TEXT PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            telegram_username TEXT,
            display_name TEXT,
            group_id TEXT DEFAULT 'group_1',
            default_grade REAL DEFAULT 75.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 5. Таблица фоновых задач индексации курсов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingestion_jobs (
            job_id TEXT PRIMARY KEY,
            course_id TEXT NOT NULL,
            status TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            message TEXT,
            error TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 6. Таблица сессий
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            topic_id TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 7. Таблица диалоговых реплик
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dialog_turns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            turn_number INTEGER NOT NULL,
            student_message TEXT NOT NULL,
            system_reply TEXT NOT NULL,
            similarity_score REAL DEFAULT 0.0,
            is_duplicate INTEGER DEFAULT 0,
            typing_duration_ms INTEGER DEFAULT 0,
            paste_detected INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        )
    """)

    # 8. Таблица аудита студентов и ректификации с составным ключом
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_audits (
            student_id TEXT NOT NULL,
            course_id TEXT NOT NULL DEFAULT 'prog_ai_2026',
            topic_id TEXT NOT NULL DEFAULT 'week_09_deep_learning',
            student_name TEXT,
            group_id TEXT DEFAULT 'group_1',
            in_class_grade REAL,
            session_status TEXT,
            turns_count INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            ai_depth_score REAL,
            raw_delta REAL,
            rectified_delta REAL,
            z_score REAL,
            zone TEXT,
            extraction_json TEXT,
            telemetry_clean BOOLEAN DEFAULT 1,
            teacher_decision TEXT DEFAULT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (student_id, course_id, topic_id)
        )
    """)

    conn.commit()

    # Запускаем миграцию на случай существования старой схемы
    _migrate_db(conn)

    # Очистка временных таблиц миграции при наличии
    try:
        cursor.execute("DROP TABLE IF EXISTS _mig_sw_old")
        cursor.execute("DROP TABLE IF EXISTS _mig_lg_old")
        cursor.execute("DROP TABLE IF EXISTS _mig_sa_old")
        conn.commit()
    except Exception:
        pass

    # Гарантируем наличие основного курса PAI в таблице courses
    cursor.execute("""
        INSERT OR IGNORE INTO courses (course_id, title, instructor, description)
        VALUES (
            'prog_ai_2026',
            'Программирование для искусственного интеллекта (PAI)',
            'Белощицкая Светлана, д.т.н., профессор',
            'Официальный силлабус дисциплины PAI 2026-2027 Astana IT University'
        )
    """)

    # Гарантируем наличие ключевых канонических понятий темы deep learning в lecture_glossary
    cursor.execute("""
        INSERT OR IGNORE INTO lecture_glossary (course_id, topic_id, term)
        VALUES 
        ('prog_ai_2026', 'week_09_deep_learning', 'model capacity'),
        ('prog_ai_2026', 'week_09_deep_learning', 'dropout rate trade-off')
    """)

    conn.commit()
    conn.close()

    # Инициализация дефолтных студентов в student_identities
    _init_default_student_identities()


def _init_default_student_identities():
    """Предзаполнение таблицы student_identities для 20 студентов канонической Группы 1."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM student_identities")
        row = cursor.fetchone()
        if row and row["cnt"] == 0:
            student_names = {
                "stud_aai_042": "Студент К. (Анонимный аудит)",
                "stud_aai_001": "Алексей Смирнов",
                "stud_aai_002": "Айгерим Тулегенова",
                "stud_aai_003": "Даниил Морозов",
                "stud_aai_004": "Екатерина Волкова",
                "stud_aai_005": "Жандос Касымов",
                "stud_aai_006": "Иван Новиков",
                "stud_aai_007": "Мария Федорова",
                "stud_aai_008": "Нурлан Сапаров",
                "stud_aai_009": "Ольга Васильева",
                "stud_aai_010": "Павел Ковалев",
                "stud_aai_011": "Руслан Ахметов",
                "stud_aai_015": "София Михайлова",
                "stud_aai_019": "Тимур Исаев",
                "stud_aai_020": "Александр Попов",
                "stud_aai_021": "Виктория Лебедева",
                "stud_aai_022": "Дмитрий Козлов",
                "stud_aai_023": "Елена Соколова",
                "stud_aai_024": "Игорь Павлов",
                "stud_aai_025": "Ксения Макарова",
            }
            default_grades = {
                "stud_aai_042": 70.0, "stud_aai_001": 72.0, "stud_aai_002": 74.0, "stud_aai_003": 75.0,
                "stud_aai_004": 78.0, "stud_aai_005": 80.0, "stud_aai_006": 82.0, "stud_aai_007": 85.0,
                "stud_aai_008": 87.0, "stud_aai_009": 88.0, "stud_aai_010": 68.0, "stud_aai_011": 71.0,
                "stud_aai_015": 73.0, "stud_aai_019": 76.0, "stud_aai_020": 86.0, "stud_aai_021": 89.0,
                "stud_aai_022": 90.0, "stud_aai_023": 91.0, "stud_aai_024": 92.0, "stud_aai_025": 94.0,
            }
            for s_id, name in student_names.items():
                cursor.execute("""
                    INSERT OR IGNORE INTO student_identities
                    (student_id, display_name, group_id, default_grade)
                    VALUES (?, ?, 'group_1', ?)
                """, (s_id, name, default_grades.get(s_id, 75.0)))
            conn.commit()
        conn.close()
    except Exception:
        pass


# =====================================================================
# КУРСЫ И СИЛЛАБУС (COURSES, SYLLABUS_WEEKS, LECTURE_GLOSSARY)
# =====================================================================

def get_courses() -> List[Dict[str, Any]]:
    """Получить список всех курсов."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses ORDER BY created_at ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_course(course_id: str) -> Optional[Dict[str, Any]]:
    """Получить курс по ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses WHERE course_id = ?", (course_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_course(course_id: str, title: str, instructor: str = "", description: str = ""):
    """Сохранить или обновить курс."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO courses (course_id, title, instructor, description)
        VALUES (?, ?, ?, ?)
    """, (course_id, title, instructor, description))
    conn.commit()
    conn.close()


def save_syllabus_week(
    course_id: str,
    topic_id: str,
    week_number: int,
    title: str,
    topic_name: str,
    initial_prompt: str,
    demo_turns_json: Optional[str] = None,
    md_path: str = "",
    chunks_count: int = 0
):
    """Сохранить или обновить запись недели силлабуса."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO syllabus_weeks 
        (course_id, topic_id, week_number, title, topic_name, initial_prompt, demo_turns_json, md_path, chunks_count, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (course_id, topic_id, week_number, title, topic_name, initial_prompt, demo_turns_json, md_path, chunks_count))
    conn.commit()
    conn.close()


def get_syllabus_weeks(course_id: str = "prog_ai_2026") -> List[Dict[str, Any]]:
    """Получить все недели силлабуса для курса."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM syllabus_weeks 
        WHERE course_id = ?
        ORDER BY week_number ASC
    """, (course_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_syllabus_week(course_id: str, topic_id: str) -> Optional[Dict[str, Any]]:
    """Получить конкретную неделю силлабуса по курсу и теме."""
    conn = get_connection()
    cursor = conn.cursor()
    resolved = resolve_topic_id(topic_id)
    cursor.execute("""
        SELECT * FROM syllabus_weeks 
        WHERE course_id = ? AND (topic_id = ? OR topic_id = ?)
    """, (course_id, resolved, topic_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_lecture_glossary(course_id: str, topic_id: str, terms: List[str]):
    """Сохранить термины глоссария для темы."""
    conn = get_connection()
    cursor = conn.cursor()
    resolved = resolve_topic_id(topic_id)
    for t in terms:
        clean_t = str(t).strip().lower()
        if clean_t:
            cursor.execute("""
                INSERT OR IGNORE INTO lecture_glossary (course_id, topic_id, term)
                VALUES (?, ?, ?)
            """, (course_id, resolved, clean_t))
    conn.commit()
    conn.close()


def get_lecture_glossary(course_id: str, topic_id: str) -> List[str]:
    """Получить список терминов глоссария темы."""
    conn = get_connection()
    cursor = conn.cursor()
    resolved = resolve_topic_id(topic_id)
    cursor.execute("""
        SELECT term FROM lecture_glossary 
        WHERE course_id = ? AND (topic_id = ? OR topic_id = ?)
        ORDER BY term ASC
    """, (course_id, resolved, topic_id))
    rows = cursor.fetchall()
    conn.close()
    return [r["term"] for r in rows]


# =====================================================================
# СТУДЕНТЫ И ИНЖЕСТ (STUDENT_IDENTITIES, INGESTION_JOBS)
# =====================================================================

def get_student_identity(student_id: str) -> Optional[Dict[str, Any]]:
    """Получить профиль студента."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student_identities WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_student_identity(
    student_id: str,
    display_name: str,
    telegram_id: Optional[int] = None,
    telegram_username: Optional[str] = None,
    group_id: str = "group_1",
    default_grade: float = 75.0
):
    """Создать или обновить профиль студента."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO student_identities 
        (student_id, telegram_id, telegram_username, display_name, group_id, default_grade)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (student_id, telegram_id, telegram_username, display_name, group_id, default_grade))
    conn.commit()
    conn.close()


def save_ingestion_job(
    job_id: str,
    course_id: str,
    status: str,
    progress: int = 0,
    total: int = 0,
    message: str = "",
    error: Optional[str] = None
):
    """Создать запись задачи индексации."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO ingestion_jobs 
        (job_id, course_id, status, progress, total, message, error, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (job_id, course_id, status, progress, total, message, error))
    conn.commit()
    conn.close()


def get_ingestion_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Получить статус задачи индексации."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ingestion_jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_ingestion_job(
    job_id: str,
    status: Optional[str] = None,
    progress: Optional[int] = None,
    total: Optional[int] = None,
    message: Optional[str] = None,
    error: Optional[str] = None
):
    """Обновить статус и прогресс задачи индексации в SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    fields = []
    params = []
    if status is not None:
        fields.append("status = ?")
        params.append(status)
    if progress is not None:
        fields.append("progress = ?")
        params.append(progress)
    if total is not None:
        fields.append("total = ?")
        params.append(total)
    if message is not None:
        fields.append("message = ?")
        params.append(message)
    if error is not None:
        fields.append("error = ?")
        params.append(error)
    fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(job_id)
    if fields:
        cursor.execute(f"UPDATE ingestion_jobs SET {', '.join(fields)} WHERE job_id = ?", tuple(params))
        conn.commit()
    conn.close()


# =====================================================================
# СЕССИИ И РЕПЛИКИ (SESSIONS, DIALOG_TURNS)
# =====================================================================

def save_session(
    session_id: str,
    student_id: str,
    course_id: str = "prog_ai_2026",
    topic_id: str = "week_09_deep_learning",
    status: str = "ACTIVE"
):
    conn = get_connection()
    cursor = conn.cursor()
    resolved_topic = resolve_topic_id(topic_id)
    cursor.execute("""
        INSERT OR REPLACE INTO sessions (session_id, student_id, course_id, topic_id, status)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, student_id, course_id, resolved_topic, status))
    conn.commit()
    conn.close()


def save_turn(
    session_id: str,
    turn_number: int,
    student_message: str,
    system_reply: str,
    similarity_score: float = 0.0,
    is_duplicate: bool = False,
    typing_duration_ms: int = 0,
    paste_detected: bool = False
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO dialog_turns 
        (session_id, turn_number, student_message, system_reply, similarity_score, is_duplicate, typing_duration_ms, paste_detected)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        turn_number,
        student_message,
        system_reply,
        similarity_score,
        1 if is_duplicate else 0,
        typing_duration_ms,
        1 if paste_detected else 0
    ))
    conn.commit()
    conn.close()


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Получить запись сессии по session_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def get_turns(session_id: str) -> List[Dict[str, Any]]:
    """Получить все реплики сессии, включая дубликаты."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM dialog_turns 
        WHERE session_id = ? 
        ORDER BY id ASC
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_student_messages(session_id: str) -> List[str]:
    """Возвращает все предыдущие уникальные сообщения студента в этой сессии для проверки схожести."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT student_message FROM dialog_turns 
        WHERE session_id = ? AND is_duplicate = 0
        ORDER BY id ASC
    """, (session_id,))
    rows = cursor.fetchall()
    conn.close()
    return [r["student_message"] for r in rows]


def get_all_student_messages_for_topic(
    student_id: str,
    topic_id: str,
    course_id: Optional[str] = None
) -> List[str]:
    """Возвращает сообщения студента по данной теме за все сессии для сквозного сравнения."""
    conn = get_connection()
    cursor = conn.cursor()
    resolved_topic = resolve_topic_id(topic_id)
    if course_id:
        cursor.execute("""
            SELECT dt.student_message FROM dialog_turns dt
            JOIN sessions s ON dt.session_id = s.session_id
            WHERE s.student_id = ? AND s.course_id = ? AND (s.topic_id = ? OR s.topic_id = ?) AND dt.is_duplicate = 0
            ORDER BY dt.id ASC
        """, (student_id, course_id, resolved_topic, topic_id))
    else:
        cursor.execute("""
            SELECT dt.student_message FROM dialog_turns dt
            JOIN sessions s ON dt.session_id = s.session_id
            WHERE s.student_id = ? AND (s.topic_id = ? OR s.topic_id = ?) AND dt.is_duplicate = 0
            ORDER BY dt.id ASC
        """, (student_id, resolved_topic, topic_id))
    rows = cursor.fetchall()
    conn.close()
    return [r["student_message"] for r in rows]


def get_latest_session_for_student(
    student_id: str,
    topic_id: Optional[str] = None,
    course_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Возвращает последнюю сохраненную сессию для студента с поддержкой фильтрации по курсу и теме."""
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM sessions WHERE student_id = ?"
    params = [student_id]
    if course_id:
        query += " AND course_id = ?"
        params.append(course_id)
    if topic_id:
        resolved = resolve_topic_id(topic_id)
        query += " AND (topic_id = ? OR topic_id = ?)"
        params.extend([resolved, topic_id])
    query += " ORDER BY created_at DESC LIMIT 1"
    cursor.execute(query, tuple(params))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def get_student_turns(
    student_id: str,
    topic_id: Optional[str] = None,
    course_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Возвращает реплики диалога студента из последней сессии."""
    session = get_latest_session_for_student(student_id, topic_id, course_id)
    if not session:
        return []
    return get_turns(session["session_id"])


# =====================================================================
# АУДИТ СТУДЕНТОВ (STUDENT_AUDITS)
# =====================================================================

def save_student_audit(
    student_id: str,
    student_name: str,
    group_id: str,
    in_class_grade: float,
    session_status: str,
    turns_count: int = 0,
    total_tokens: int = 0,
    ai_depth_score: Optional[float] = None,
    raw_delta: float = 0.0,
    rectified_delta: float = 0.0,
    z_score: float = 0.0,
    zone: str = "NO_SIGNAL",
    extraction_json: Optional[str] = None,
    course_id: str = "prog_ai_2026",
    topic_id: str = "week_09_deep_learning",
    telemetry_clean: bool = True,
    teacher_decision: Optional[str] = None,
):
    """Сохранение или обновление записи аудита студента в SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    resolved_topic = resolve_topic_id(topic_id)
    cursor.execute("""
        INSERT OR REPLACE INTO student_audits (
            student_id, course_id, topic_id, student_name, group_id, in_class_grade, session_status,
            turns_count, total_tokens, ai_depth_score, raw_delta, rectified_delta,
            z_score, zone, extraction_json, telemetry_clean, teacher_decision, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        student_id, course_id, resolved_topic, student_name, group_id, in_class_grade, session_status,
        turns_count, total_tokens, ai_depth_score, raw_delta, rectified_delta,
        z_score, zone, extraction_json, 1 if telemetry_clean else 0, teacher_decision
    ))
    conn.commit()
    conn.close()


def bulk_save_student_audits(records: List[Dict[str, Any]]):
    """Массовое сохранение записей студентов в SQLite с поддержкой course_id и topic_id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT OR REPLACE INTO student_audits (
            student_id, course_id, topic_id, student_name, group_id, in_class_grade, session_status,
            turns_count, total_tokens, ai_depth_score, raw_delta, rectified_delta,
            z_score, zone, extraction_json, telemetry_clean, teacher_decision, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, [
        (
            r["student_id"],
            r.get("course_id", "prog_ai_2026"),
            resolve_topic_id(r.get("topic_id", "week_09_deep_learning")),
            r.get("student_name", r["student_id"]),
            r.get("group_id", "group_1"),
            r["in_class_grade"],
            r["session_status"],
            r.get("turns_count", 0),
            r.get("total_tokens", 0),
            r.get("ai_depth_score"),
            r.get("raw_delta", 0.0),
            r.get("rectified_delta", 0.0),
            r.get("z_score", 0.0),
            r.get("zone", "NO_SIGNAL"),
            r.get("extraction_json"),
            1 if r.get("telemetry_clean", True) else 0,
            r.get("teacher_decision"),
        )
        for r in records
    ])
    conn.commit()
    conn.close()


def get_all_student_audits(
    course_id: Optional[str] = None,
    topic_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Получение записей аудита студентов из SQLite (с опциональной фильтрацией по курсу и теме)."""
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM student_audits WHERE 1=1"
    params = []
    if course_id:
        query += " AND course_id = ?"
        params.append(course_id)
    if topic_id:
        resolved = resolve_topic_id(topic_id)
        query += " AND (topic_id = ? OR topic_id = ?)"
        params.extend([resolved, topic_id])
    query += " ORDER BY student_id ASC"
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student_audit(
    student_id: str,
    course_id: Optional[str] = None,
    topic_id: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Получение записи аудита конкретного студента из SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM student_audits WHERE student_id = ?"
    params = [student_id]
    if course_id:
        query += " AND course_id = ?"
        params.append(course_id)
    if topic_id:
        resolved = resolve_topic_id(topic_id)
        query += " AND (topic_id = ? OR topic_id = ?)"
        params.extend([resolved, topic_id])
    query += " ORDER BY updated_at DESC LIMIT 1"
    cursor.execute(query, tuple(params))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return dict(row)


def delete_student_dialogs(
    student_id: str,
    course_id: Optional[str] = None,
    topic_id: Optional[str] = None
):
    """Полное удаление диалоговых сессий и реплик студента из SQLite (для чистого сброса сессии)."""
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT session_id FROM sessions WHERE student_id = ?"
    params = [student_id]
    if course_id:
        query += " AND course_id = ?"
        params.append(course_id)
    if topic_id:
        resolved = resolve_topic_id(topic_id)
        query += " AND (topic_id = ? OR topic_id = ?)"
        params.extend([resolved, topic_id])
    cursor.execute(query, tuple(params))
    sess_ids = [r["session_id"] for r in cursor.fetchall()]
    if sess_ids:
        placeholders = ",".join("?" for _ in sess_ids)
        cursor.execute(f"DELETE FROM dialog_turns WHERE session_id IN ({placeholders})", sess_ids)
        cursor.execute(f"DELETE FROM sessions WHERE session_id IN ({placeholders})", sess_ids)
    conn.commit()
    conn.close()


def reset_student_in_db(
    student_id: str,
    default_in_class_grade: float = 70.0,
    student_name: Optional[str] = None,
    group_id: str = "group_1",
    course_id: str = "prog_ai_2026",
    topic_id: str = "week_09_deep_learning"
):
    """
    Сброс студента в SQLite к начальному состоянию без ИИ:
    - Удаляет сессии и реплики из dialog_turns и sessions
    - Сбрасывает оценку в student_audits до очной (G_prof), ai_depth_score=None, rectified_delta=0, z_score=0, zone='NO_SIGNAL', session_status='OPTED_OUT'
    """
    resolved_topic = resolve_topic_id(topic_id)
    delete_student_dialogs(student_id, course_id=course_id, topic_id=resolved_topic)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO student_audits (
            student_id, course_id, topic_id, student_name, group_id, in_class_grade, session_status,
            turns_count, total_tokens, ai_depth_score, raw_delta, rectified_delta,
            z_score, zone, extraction_json, telemetry_clean, teacher_decision, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, 'OPTED_OUT', 0, 0, NULL, 0.0, 0.0, 0.0, 'NO_SIGNAL', NULL, 1, NULL, CURRENT_TIMESTAMP)
    """, (
        student_id,
        course_id,
        resolved_topic,
        student_name or student_id,
        group_id,
        default_in_class_grade,
    ))
    conn.commit()
    conn.close()


# Инициализируем БД при импорте модуля
init_db()
