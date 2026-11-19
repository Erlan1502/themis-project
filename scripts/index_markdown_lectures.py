"""
index_markdown_lectures.py

Боевой скрипт индексации всех 9 лекций курса "Programming for AI" (PAI, 2026-2027)
из data/lectures_md/ в ChromaDB (HNSW граф + мультиязычные эмбеддинги BAAI/bge-m3)
и реляционную базу SQLite (таблицы syllabus_weeks и lecture_glossary).

Обеспечивает гранулярное смысловое чанкирование (Smart Chunker):
- Разбиение по заголовкам, секциям, блокам кода и логическим абзацам (200-300 слов)
- Сохранение контекста заголовка и кода в каждом чанке
- Полную изоляцию тем через метаданные topic_id
"""

import os
import sys
import re
import json
from typing import List, Dict, Any, Tuple
import yaml

# Добавляем корень проекта в sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.vector_store import vector_store
from backend.rag_service import rag_service
from backend.database import (
    init_db,
    save_syllabus_week,
    save_lecture_glossary,
    save_course,
    get_connection,
)

MD_DIR = os.path.join(r"data", "lectures_md")


def init_syllabus_db():
    """Инициализирует полную схему SQLite базы данных (courses, syllabus_weeks, lecture_glossary, etc.)."""
    init_db()


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


def smart_chunk_markdown(
    body: str,
    topic_id: str,
    week_no: int,
    glossary: List[str],
    max_chars: int = 1100
) -> List[Dict[str, Any]]:
    """
    Интеллектуальный чанкер для лекций и блокнотов Jupyter:
    1. Очищает артефакты и base64.
    2. Разделяет текст по заголовкам всех уровней (#, ##, ###, ####), горизонтальным линиям и нумерованным пунктам.
    3. Длинные блоки делит по параграфам/ячейкам кода (до max_chars), сохраняя контекстный заголовок.
    4. Привязывает концепты темы к каждому чанку.
    """
    # Удаляем base64 и длинные data URIs
    body_clean = re.sub(r'!\[.*?\]\(data:[^)]+\)', '[Иллюстрация к лекции]', body)
    body_clean = re.sub(r'<img\s+src="data:[^"]+"\s*\/?>', '[Иллюстрация к лекции]', body_clean)

    # Регулярка для разделения по заголовкам и разделителям
    raw_sections = re.split(r'\n(?=(?:#{1,4}\s+|---\s*\n|\*\*[0-9]+\.\s+))', body_clean)
    chunks = []
    slide_no = 1
    current_title = f"Неделя {week_no}: Основы темы"

    glossary_lower = [g.lower() for g in glossary] if glossary else []

    for sec in raw_sections:
        sec_clean = sec.strip()
        if not sec_clean or len(sec_clean) < 35:
            continue

        # Извлекаем и нормализуем заголовок секции
        lines = sec_clean.splitlines()
        first_line = lines[0].strip()
        m = re.match(r'^#{1,4}\s+(.+)$', first_line)
        if m:
            clean_t = re.sub(r'[\*\_#]', '', m.group(1)).strip()
            if len(clean_t) > 3:
                current_title = clean_t
        elif first_line.startswith('**') and '**' in first_line[2:]:
            clean_t = first_line.replace('**', '').strip()
            if len(clean_t) > 3:
                current_title = clean_t

        # Если секция слишком длинная (> max_chars), дробим на логические подчасти
        if len(sec_clean) > max_chars:
            sub_parts = re.split(r'\n{2,}', sec_clean)
            buf = []
            buf_len = 0
            sub_idx = 1
            for p in sub_parts:
                p_len = len(p)
                if buf_len + p_len > max_chars and buf:
                    part_text = '\n\n'.join(buf).strip()
                    if len(part_text) >= 35:
                        has_code = any(k in part_text for k in ["```python", "import ", "def ", "class ", "np.", "pd.", "plt.", "torch.", "nn."])
                        matched_concepts = [t for t in glossary_lower if t in part_text.lower()][:5]
                        title_str = f"{current_title} (часть {sub_idx})" if sub_idx > 1 else current_title
                        chunks.append({
                            "slide_number": slide_no,
                            "title": title_str[:120],
                            "text": part_text,
                            "has_code": has_code,
                            "concepts": matched_concepts
                        })
                        slide_no += 1
                        sub_idx += 1
                    buf = [p]
                    buf_len = p_len
                else:
                    buf.append(p)
                    buf_len += p_len
            if buf:
                part_text = '\n\n'.join(buf).strip()
                if len(part_text) >= 35:
                    has_code = any(k in part_text for k in ["```python", "import ", "def ", "class ", "np.", "pd.", "plt.", "torch.", "nn."])
                    matched_concepts = [t for t in glossary_lower if t in part_text.lower()][:5]
                    title_str = f"{current_title} (часть {sub_idx})" if sub_idx > 1 else current_title
                    chunks.append({
                        "slide_number": slide_no,
                        "title": title_str[:120],
                        "text": part_text,
                        "has_code": has_code,
                        "concepts": matched_concepts
                    })
                    slide_no += 1
        else:
            has_code = any(k in sec_clean for k in ["```python", "import ", "def ", "class ", "np.", "pd.", "plt.", "torch.", "nn."])
            matched_concepts = [t for t in glossary_lower if t in sec_clean.lower()][:5]
            chunks.append({
                "slide_number": slide_no,
                "title": current_title[:120],
                "text": sec_clean,
                "has_code": has_code,
                "concepts": matched_concepts
            })
            slide_no += 1

    return chunks


def index_all():
    print("=" * 70)
    print("БОЕВАЯ ИНДЕКСАЦИЯ ЛЕКЦИЙ В CHROMADB (HNSW + BGE-M3) И SQLITE")
    print("=" * 70)

    # 1. Инициализируем таблицы SQLite
    init_syllabus_db()
    course_id = "prog_ai_2026"
    save_course(
        course_id=course_id,
        title="Программирование для искусственного интеллекта (PAI)",
        instructor="Белощицкая Светлана, д.т.н., профессор",
        description="Официальный силлабус дисциплины PAI 2026-2027 Astana IT University"
    )

    md_files = sorted([f for f in os.listdir(MD_DIR) if f.endswith(".md")])
    print(f"Найдено {len(md_files)} лекционных Markdown-файлов в {MD_DIR}.\n")

    total_chunks = 0
    total_code_chunks = 0

    # Канонические демонстрационные реплики для Недели 9
    week_09_demo_turns = [
        {
            "turn": 1,
            "student": "Переобучение происходит, когда веса подстраиваются под специфический шум выборки, создавая избыточную ко-адаптацию нейронов.",
            "system": "Отлично. Ты упомянул ко-адаптацию нейронов. Каким именно математическим механизмом метод Dropout предотвращает эту ко-адаптацию в процессе обратного распространения ошибки?"
        },
        {
            "turn": 2,
            "student": "Dropout случайным образом обнуляет активации нейронов с вероятностью p во время прямого прохода. Это заставляет каждый нейрон обучаться полезным признакам независимо от соседей, имитируя ансамбль подсетей.",
            "system": "Глубокое понимание ансамблевой природы Dropout. А что происходит на экстремальных границах? Например, при слишком высокой вероятности отключения нейронов?"
        },
        {
            "turn": 3,
            "student": "Если Dropout так эффективен, почему бы нам не выключать 80% нейронов для максимальной регуляризации? В какой момент это сломает обучение и вызовет потерю емкости сети (underfitting)?",
            "system": "Блестящий исследовательский вопрос! Отключение 80% нейронов катастрофически снижает эффективную емкость сети (model capacity), вызывая недообучение (underfitting). Баланс между регуляризацией и емкостью — фундаментальный компромисс глубокого обучения."
        }
    ]

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

        # 1. Умное чанкирование
        chunks = smart_chunk_markdown(body, topic_id, week_no, glossary)
        code_chunks = sum(1 for c in chunks if c["has_code"])
        total_code_chunks += code_chunks

        print(f"[{week_no}/9] {title}")
        print(f"      Чанков: {len(chunks)} (из них с кодом: {code_chunks}), Ключевых терминов: {len(glossary)}")

        # 2. Селективная синхронизация с ChromaDB
        col = vector_store.collection
        existing_topic_chunks = col.get(where={"topic_id": topic_id})
        if existing_topic_chunks and existing_topic_chunks.get("ids"):
            # Чанки уже векторизованы в HNSW. Обновляем метаданные с привязкой к course_id
            chunk_ids = existing_topic_chunks["ids"]
            metas = []
            for m in existing_topic_chunks["metadatas"]:
                new_m = dict(m)
                new_m["course_id"] = course_id
                new_m["topic_id"] = topic_id
                metas.append(new_m)
            col.update(ids=chunk_ids, metadatas=metas)
            indexed = len(chunk_ids)
            print(f"      -> Метаданные {indexed} чанков синхронизированы с курсом {course_id}")
        else:
            # Новая тема: выполняем полную векторизацию в HNSW
            indexed = vector_store.add_slides(
                topic_id=topic_id,
                week_number=week_no,
                slides_data=chunks,
                course_id=course_id
            )
            print(f"      -> Векторизовано и сохранено {indexed} чанков в ChromaDB")

        total_chunks += indexed

        # 3. Сохранение метаданных и глоссария в SQLite
        demo_turns = week_09_demo_turns if (week_no == 9 or "week_09" in topic_id) else None
        demo_json = json.dumps(demo_turns, ensure_ascii=False) if demo_turns else None

        save_syllabus_week(
            course_id=course_id,
            topic_id=topic_id,
            week_number=week_no,
            title=title,
            topic_name=topic_name,
            initial_prompt=initial_prompt,
            demo_turns_json=demo_json,
            md_path=fpath,
            chunks_count=indexed
        )

        save_lecture_glossary(
            course_id=course_id,
            topic_id=topic_id,
            terms=glossary
        )

        # 4. Регистрация в RAG-сервисе
        rag_service.register_dynamic_week(
            topic_id=topic_id,
            week_number=week_no,
            title=title,
            topic_name=topic_name,
            initial_prompt=initial_prompt,
            glossary=glossary,
            slides_count=indexed,
            course_id=course_id,
            demo_turns=demo_turns
        )
        print(f"      -> Сохранено в SQLite (глоссарий: {len(glossary)} терминов).\n", flush=True)

    print("=" * 70)
    print(f"ИНДЕКСАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
    print(f"Всего проиндексировано чанков курса {course_id}: {total_chunks}")
    print(f"Из них содержат реальный Python-код: {total_code_chunks}")
    print(f"Векторное хранилище ChromaDB: HNSW Cosine (BGE-M3, 1024-dim)")
    print("=" * 70)
    print(f"Векторное хранилище ChromaDB: HNSW Cosine (BGE-M3, 1024-dim)")
    print("=" * 70)


if __name__ == "__main__":
    index_all()
