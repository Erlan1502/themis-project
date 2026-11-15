"""
index_markdown_lectures.py

Индексирует все 9 сконвертированных лекций из data/lectures_md/ в ChromaDB (HNSW + BGE-M3)
и обновляет базу SQLite (таблицы syllabus_weeks и lecture_glossary).
"""

import os
import sys
import re
from typing import List, Dict, Any, Tuple
import yaml

# Добавляем корень проекта в sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.vector_store import vector_store
from backend.rag_service import rag_service
from backend.database import get_connection

MD_DIR = os.path.join(r"data", "lectures_md")


def init_syllabus_db():
    """Создает таблицы в SQLite для хранения метаданных лекций и глоссария."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS syllabus_weeks (
            week_number INTEGER PRIMARY KEY,
            topic_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            topic_name TEXT NOT NULL,
            initial_prompt TEXT NOT NULL,
            md_path TEXT NOT NULL,
            chunks_count INTEGER DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lecture_glossary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id TEXT NOT NULL,
            term TEXT NOT NULL,
            UNIQUE(topic_id, term),
            FOREIGN KEY (topic_id) REFERENCES syllabus_weeks(topic_id)
        )
    """)
    conn.commit()
    conn.close()


def parse_frontmatter_and_body(content: str) -> Tuple[Dict[str, Any], str]:
    """Разделяет YAML frontmatter и markdown-тело."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body_text = parts[2]
            try:
                meta = yaml.safe_load(fm_text)
                return meta or {}, body_text.strip()
            except Exception:
                pass
    return {}, content.strip()


def chunk_markdown(body: str, topic_id: str, week_no: int) -> List[Dict[str, Any]]:
    """Разбивает тело Markdown на смысловые чанки по секциям ## или ###."""
    sections = re.split(r'\n(?=#{2,3}\s+)', body)
    chunks = []
    slide_no = 1

    for sec in sections:
        sec_clean = sec.strip()
        if not sec_clean or len(sec_clean) < 30:
            continue

        # Извлекаем заголовок секции
        lines = sec_clean.splitlines()
        first_line = lines[0]
        title_match = re.match(r'#{2,3}\s+(.+)', first_line)
        title = title_match.group(1).strip() if title_match else f"Секция {slide_no}"

        # Проверяем наличие кода
        has_code = "```python" in sec_clean or "import " in sec_clean

        chunks.append({
            "slide_number": slide_no,
            "title": title[:100],
            "text": sec_clean,
            "has_code": has_code,
            "concepts": []
        })
        slide_no += 1

    return chunks


def index_all():
    print("Инициализация таблиц силлабуса в SQLite...")
    init_syllabus_db()

    conn = get_connection()
    cursor = conn.cursor()

    md_files = sorted([f for f in os.listdir(MD_DIR) if f.endswith(".md")])
    print(f"Найдено {len(md_files)} Markdown-лекций в {MD_DIR}.")

    total_chunks = 0
    for fname in md_files:
        fpath = os.path.join(MD_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            raw_text = f.read()

        meta, body = parse_frontmatter_and_body(raw_text)
        week_no = meta.get("week_number", 1)
        topic_id = meta.get("topic_id", fname.replace(".md", ""))
        title = meta.get("title", f"Неделя {week_no}")
        topic_name = meta.get("topic_name", title)
        initial_prompt = meta.get("initial_prompt", "Привет! О чем мы говорили на лекции?")
        glossary = meta.get("glossary", [])

        # 1. Чанкирование Markdown
        chunks = chunk_markdown(body, topic_id, week_no)
        print(f"\n[Неделя {week_no}] {title}")
        print(f"  Чанков: {len(chunks)}, Терминов: {len(glossary)}")

        # 2. Индексация в HNSW граф ChromaDB
        indexed = vector_store.add_slides(
            topic_id=topic_id,
            week_number=week_no,
            slides_data=chunks
        )
        total_chunks += indexed

        # 3. Сохранение в SQLite
        cursor.execute("""
            INSERT OR REPLACE INTO syllabus_weeks
            (week_number, topic_id, title, topic_name, initial_prompt, md_path, chunks_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (week_no, topic_id, title, topic_name, initial_prompt, fpath, len(chunks)))

        for term in glossary:
            cursor.execute("""
                INSERT OR IGNORE INTO lecture_glossary (topic_id, term)
                VALUES (?, ?)
            """, (topic_id, str(term).lower()))

        # 4. Регистрация в rag_service
        rag_service.register_dynamic_week(
            topic_id=topic_id,
            week_number=week_no,
            title=title,
            topic_name=topic_name,
            initial_prompt=initial_prompt,
            glossary=glossary,
            slides_count=len(chunks)
        )

    conn.commit()
    conn.close()
    print(f"\nВсего успешно проиндексировано {total_chunks} чанков в ChromaDB и SQLite!")


if __name__ == "__main__":
    from typing import Tuple
    index_all()
