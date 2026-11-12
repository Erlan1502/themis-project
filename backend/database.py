"""
database.py

Постоянное реляционное хранилище Themis Project на базе SQLite.
Обеспечивает сохранение истории сократических сессий, пошаговых реплик,
детекции повторов (similarity) и результатов психометрического аудита.
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional

DB_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "themis_data.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Инициализация схемы таблиц SQLite."""
    conn = get_connection()
    cursor = conn.cursor()

    # Таблица сессий
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

    # Таблица диалоговых реплик с фиксацией схожести и флага повтора
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

    # Таблица аудита студентов и ректификации
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_audits (
            student_id TEXT PRIMARY KEY,
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
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_session(session_id: str, student_id: str, course_id: str, topic_id: str, status: str = "ACTIVE"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO sessions (session_id, student_id, course_id, topic_id, status)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, student_id, course_id, topic_id, status))
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


def get_all_student_messages_for_topic(student_id: str, topic_id: str) -> List[str]:
    """Возвращает сообщения студента по данной теме за все сессии для сквозного сравнения."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT dt.student_message FROM dialog_turns dt
        JOIN sessions s ON dt.session_id = s.session_id
        WHERE s.student_id = ? AND s.topic_id = ? AND dt.is_duplicate = 0
    """, (student_id, topic_id))
    rows = cursor.fetchall()
    conn.close()
    return [r["student_message"] for r in rows]


# Инициализируем БД при импорте модуля
init_db()

