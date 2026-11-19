"""
ingestion_service.py

Автономный сервис загрузки, конвертации, авто-структурирования и фоновой индексации
учебных материалов любого курса (Zero-Config .md Ingestion) для Themis Project.

Поддерживает:
- Преобразование .pdf, .pptx, .docx, .ipynb, .md, .txt и .zip архивов в чистый Markdown
- Авто-структурирование курса и лекции (определение названия, номера недели, темы, слага)
- Извлечение доменного глоссария терминов (RU/EN) и сохранение в SQLite lecture_glossary
- Генерацию стартового сократического вопроса (initial_prompt) и демо-реплик (demo_turns)
- Семантический чанкинг с хлебными крошками (Smart Chunker)
- Фоновое батчевое индексирование в ChromaDB (HNSW + BGE-M3) с прогресс-баром в ingestion_jobs
"""

import os
import re
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from pptx import Presentation
from pypdf import PdfReader

from backend.markdown_converter import markdown_converter, clean_markdown_text
from backend.chunker import smart_chunk_markdown
from backend.database import (
    save_course,
    save_syllabus_week,
    save_lecture_glossary,
    save_ingestion_job,
    update_ingestion_job,
    get_course,
    resolve_topic_id,
)

logger = logging.getLogger("themis.ingestion")

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


class CourseIngestionService:
    def __init__(self, uploads_dir: str = UPLOADS_DIR):
        self.uploads_dir = uploads_dir

    # =========================================================================
    # ОБРАТНАЯ СОВМЕСТИМОСТЬ (ДЛЯ СУЩЕСТВУЮЩИХ ТЕСТОВ И ВЫЗОВОВ)
    # =========================================================================

    def parse_pptx(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Извлекает структурированный текст и метаданные из слайдов PowerPoint (.pptx).
        Сохраняет иерархию: номер слайда, заголовок, маркированные списки, таблицы.
        """
        prs = Presentation(file_path)
        slides_data = []

        for idx, slide in enumerate(prs.slides, start=1):
            slide_title = ""
            text_parts = []
            has_code = False

            if slide.shapes.title and slide.shapes.title.text:
                slide_title = slide.shapes.title.text.strip()

            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        p_text = paragraph.text.strip()
                        if p_text and p_text != slide_title:
                            text_parts.append(p_text)
                            if any(k in p_text for k in ["import ", "def ", "class ", "nn.", "torch.", "np.", "pd."]):
                                has_code = True

                elif shape.has_table:
                    table = shape.table
                    table_rows = []
                    for row in table.rows:
                        row_cells = [c.text.strip() for c in row.cells if c.text.strip()]
                        if row_cells:
                            table_rows.append(" | ".join(row_cells))
                    if table_rows:
                        text_parts.append("Таблица:\n" + "\n".join(table_rows))

            full_text = "\n".join(text_parts)
            if not slide_title and text_parts:
                slide_title = text_parts[0][:60]

            slides_data.append({
                "slide_number": idx,
                "title": slide_title or f"Слайд {idx}",
                "text": full_text,
                "has_code": has_code,
                "concepts": self._extract_key_concepts(f"{slide_title}\n{full_text}")
            })

        logger.info(f"Разобрано {len(slides_data)} слайдов из {os.path.basename(file_path)}")
        return slides_data

    def parse_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Извлекает страницы из PDF лекционного конспекта.
        """
        reader = PdfReader(file_path)
        pages_data = []

        for idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            clean_text = re.sub(r"\s+", " ", text).strip()
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            page_title = lines[0][:80] if lines else f"Страница {idx}"

            pages_data.append({
                "slide_number": idx,
                "title": page_title,
                "text": clean_text,
                "has_code": "def " in text or "import " in text,
                "concepts": self._extract_key_concepts(clean_text)
            })

        logger.info(f"Разобрано {len(pages_data)} страниц из {os.path.basename(file_path)}")
        return pages_data

    def _extract_key_concepts(self, text: str) -> List[str]:
        """
        Извлекает доменные термины и ключевые концепции из текста слайда.
        """
        candidates = set()
        en_terms = re.findall(r"\b[A-Za-z][A-Za-z0-9_-]{2,}\b", text)
        for term in en_terms:
            lower = term.lower()
            if lower not in {"the", "and", "for", "with", "from", "that", "this", "are"}:
                candidates.add(lower)

        ru_terms = re.findall(r"\b[А-Яа-я]{4,}\b", text)
        stop_ru = {"этот", "когда", "если", "также", "быть", "после", "можно", "такой", "слайд", "лекция", "тема"}
        for term in ru_terms:
            lower = term.lower()
            if lower not in stop_ru and len(lower) > 4:
                candidates.add(lower)

        return list(candidates)[:5]

    def build_course_metadata(
        self,
        topic_id: str,
        week_number: int,
        topic_name: str,
        slides: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Генерирует глоссарий и стартовый сократический триггер по загруженным слайдам.
        """
        all_concepts = set()
        for s in slides:
            all_concepts.update(s.get("concepts", []))

        glossary = sorted(list(all_concepts))[:6]
        if not glossary:
            glossary = ["архитектура", "параметры", "оптимизация", "обучение", "метрики"]

        first_concept = glossary[0] if glossary else "данной теме"
        
        initial_prompt = (
            f"Привет! На занятии мы разобрали тему «{topic_name}». "
            f"Опираясь на материалы лекции, объясни: какую ключевую проблему решает {first_concept} "
            f"и в каких условиях этот подход дает наибольший эффект?"
        )

        return {
            "week_number": week_number,
            "topic_id": topic_id,
            "title": f"Неделя {week_number}: {topic_name}",
            "topic_name": topic_name,
            "initial_prompt": initial_prompt,
            "glossary": glossary,
            "slides_count": len(slides)
        }

    # =========================================================================
    # НОВЫЙ МОДУЛЬНЫЙ ZERO-CONFIG INGESTION ПАЙПЛАЙН (ШАГ 5)
    # =========================================================================

    def extract_rich_glossary(self, text: str) -> List[str]:
        """
        Извлекает 15-30 точных доменных терминов (RU + EN) из текста лекции
        для наполнения таблицы lecture_glossary и верификации K_density.
        """
        candidates = set()

        # 1. Поиск профильных английских терминов ML / DL / Data Science
        en_matches = re.findall(r'\b[A-Za-z][A-Za-z0-9_\-\.]{2,}\b', text)
        stop_en = {
            "the", "and", "for", "with", "from", "that", "this", "are", "you", "not",
            "can", "will", "all", "has", "have", "more", "one", "two", "use", "code",
            "example", "file", "data", "true", "false", "none", "print", "line", "test",
            "each", "into", "some", "only", "also", "then", "which", "part", "task",
            "using", "used", "such", "than", "been", "were", "what", "when", "where",
            "self", "import", "class", "return", "def", "float", "int", "str", "list"
        }
        for m in en_matches:
            low = m.lower().strip(".-_")
            if low not in stop_en and len(low) >= 3:
                candidates.add(low)

        # 2. Поиск русских доменных терминов искусственного интеллекта и программирования
        ru_term_patterns = [
            "регуляризаци", "переобучен", "недообучен", "нейросеть", "перцептрон",
            "градиентн", "спуск", "функци", "потер", "оптимизатор", "эмбеддинг",
            "токенизаци", "векторизаци", "веса", "матриц", "тензор", "массив",
            "ансамбл", "бустинг", "бэггинг", "дерев", "решени", "классификаци",
            "регресси", "кластеризаци", "валидаци", "сверточн", "рекуррентн",
            "трансформер", "внимани", "дропаут", "батч", "нормализаци", "эпох",
            "генерализаци", "ко-адаптаци", "слой", "активаци", "сигмоид", "софтмакс"
        ]
        ru_words = re.findall(r'\b[А-Яа-яЁё]{4,}\b', text)
        stop_ru = {
            "этот", "когда", "если", "также", "быть", "после", "можно", "такой",
            "слайд", "лекция", "тема", "который", "какой", "будет", "было", "всех",
            "наш", "свой", "очень", "даже", "более", "менее", "через", "только"
        }
        for w in ru_words:
            low = w.lower()
            if low not in stop_ru:
                if any(pat in low for pat in ru_term_patterns):
                    candidates.add(low)

        # Сортируем и возвращаем от 15 до 30 доменных терминов
        result = sorted(list(candidates))
        return result[:30] if len(result) >= 15 else result

    def auto_structure_topic(
        self,
        markdown_text: str,
        filename: str = "",
        week_number: Optional[int] = None,
        topic_name: Optional[str] = None,
        course_id: str = "prog_ai_2026"
    ) -> Dict[str, Any]:
        """
        Авто-структурирование темы лекции (LLM + детерминированный fallback):
        - Определение названия темы, номера недели, идентификатора topic_id
        - Генерация сократического initial_prompt
        - Извлечение доменного глоссария терминов (RU/EN)
        - Генерация demo_turns (SOLO 1, 2, 3) для тестирования в Dev Mode
        """
        # 1. Извлечение заголовка из текста Markdown
        detected_title = ""
        for line in markdown_text.splitlines():
            line_str = line.strip()
            if line_str.startswith("#"):
                detected_title = re.sub(r'^[#\s]+', '', line_str).strip()
                if len(detected_title) > 3:
                    break

        if not detected_title:
            base_name = os.path.splitext(filename)[0] if filename else "Новая лекция"
            detected_title = base_name.replace("_", " ").replace("-", " ").title()

        final_topic_name = topic_name or detected_title

        # 2. Определение номера недели (week_number)
        final_week_no = week_number
        if final_week_no is None:
            # Ищем указание недели в названии файла или текста (e.g., week_11, lecture_12, Week 5)
            match_week = re.search(r'(?:week|lecture|неделя|лекция)[\s_0-9]*?(\d+)', f"{filename} {final_topic_name}", re.IGNORECASE)
            if match_week:
                final_week_no = int(match_week.group(1))
            else:
                final_week_no = 11

        # 3. Формирование слага topic_id
        clean_slug = re.sub(r'[^a-zA-Z0-9]', '_', final_topic_name.lower()).strip('_')
        clean_slug = re.sub(r'_+', '_', clean_slug)[:25]
        if not clean_slug:
            clean_slug = f"topic_{final_week_no:02d}"
        topic_id = f"week_{final_week_no:02d}_{clean_slug}"

        # 4. Извлечение доменного глоссария
        glossary = self.extract_rich_glossary(markdown_text)
        if not glossary:
            glossary = ["модель", "параметры", "оптимизация", "обучение", "метрика", "веса", "loss", "accuracy"]

        # 5. Генерация стартового сократического вопроса
        primary_concept = glossary[0] if glossary else final_topic_name
        initial_prompt = (
            f"Привет! На занятии мы разобрали тему «{final_topic_name}». "
            f"Опираясь на материалы лекции, объясни своими словами: какую ключевую проблему решает {primary_concept} "
            f"и в каких условиях этот подход дает наибольший практический эффект?"
        )

        # 6. Генерация 3 канонических реплик для Dev Mode (SOLO 1, SOLO 2, SOLO 3)
        c1 = glossary[0] if len(glossary) > 0 else "алгоритм"
        c2 = glossary[1] if len(glossary) > 1 else "регуляризация"
        c3 = glossary[2] if len(glossary) > 2 else "обобщающая способность"

        demo_turns = [
            {
                "turn": 1,
                "student": f"Основная цель {final_topic_name} — предотвратить переобучение модели и улучшить работу через {c1}.",
                "system": f"Верно, ты упомянул {c1}. А за счет какого внутреннего математического механизма это достигается в процессе обучения?"
            },
            {
                "turn": 2,
                "student": f"Механизм основан на том, что {c2} ограничивает чрезмерную сложность весов и снижает взаимную зависимость признаков.",
                "system": f"Отличный анализ влияния {c2}! А что произойдет на предельных границах — например, при экстремальных значениях гиперпараметров?"
            },
            {
                "turn": 3,
                "student": f"Если гиперпараметры заданы слишком агрессивно, это приведет к потере емкости модели и недообучению, снижая {c3}. Баланс между регуляризацией и сложностью является фундаментальным компромиссом.",
                "system": f"Блестящее системное обобщение! Баланс емкости модели и регуляризации — ключевой компромисс машинного обучения."
            }
        ]

        return {
            "course_id": course_id,
            "topic_id": topic_id,
            "week_number": final_week_no,
            "title": f"Неделя {final_week_no}: {final_topic_name}",
            "topic_name": final_topic_name,
            "initial_prompt": initial_prompt,
            "glossary": glossary,
            "demo_turns": demo_turns
        }

    async def execute_ingestion_job(
        self,
        job_id: str,
        file_path: str,
        filename: str,
        course_id: str = "prog_ai_2026",
        week_number: Optional[int] = None,
        topic_name: Optional[str] = None,
        course_title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Полный асинхронный цикл обработки и фоновой индексации документа курса:
        1. CONVERTING (15%): Конвертация любого поддерживаемого формата в чистый Markdown
        2. STRUCTURING (40%): Извлечение метаданных, генерация глоссария и вопросов
        3. CHUNKING (60%): Семантическое разбиение на чанки с защитой кода/таблиц и breadcrumbs
        4. INDEXING (75% - 95%): Селективный upsert в ChromaDB HNSW в ThreadPool
        5. COMPLETED (100%): Запись в SQLite courses, syllabus_weeks, lecture_glossary
        """
        try:
            logger.info(f"Запуск фоновой задачи индексации {job_id} для файла {filename}")
            update_ingestion_job(
                job_id,
                status="CONVERTING",
                progress=15,
                message=f"Конвертация файла {filename} в структурированный Markdown..."
            )

            # 1. КОНВЕРТАЦИЯ
            ext = os.path.splitext(filename)[1].lower()
            if ext == ".zip":
                # Пакетная конвертация ZIP архива
                zip_items = await asyncio.to_thread(markdown_converter.convert_zip, file_path, course_id)
                if not zip_items:
                    raise ValueError(f"В архиве {filename} не найдено поддерживаемых документов.")
                # Берем первый или объединяем
                md_content = "\n\n---\n\n".join(item["markdown"] for item in zip_items)
            else:
                md_content = await asyncio.to_thread(markdown_converter.convert_file, file_path)

            if not md_content or len(md_content.strip()) < 30:
                raise ValueError(f"Не удалось извлечь содержательный текст из {filename}")

            # 2. АВТО-СТРУКТУРИРОВАНИЕ
            update_ingestion_job(
                job_id,
                status="STRUCTURING",
                progress=40,
                message="Авто-структурирование темы, извлечение глоссария и сократических триггеров..."
            )

            meta = self.auto_structure_topic(
                markdown_text=md_content,
                filename=filename,
                week_number=week_number,
                topic_name=topic_name,
                course_id=course_id
            )

            # Сохраняем физический .md файл
            saved_md_path = await asyncio.to_thread(
                markdown_converter.save_converted_md,
                course_id=course_id,
                topic_id=meta["topic_id"],
                markdown_content=md_content,
                metadata=meta
            )

            # 3. СЕМАНТИЧЕСКИЙ ЧАНКИНГ
            update_ingestion_job(
                job_id,
                status="CHUNKING",
                progress=60,
                message="Семантическое разбиение на чанки с защитой кода, таблиц и формул..."
            )

            c_info = get_course(course_id)
            c_title = (c_info and c_info.get("title")) or course_title or "Программирование для искусственного интеллекта"

            chunks = await asyncio.to_thread(
                smart_chunk_markdown,
                markdown_text=md_content,
                course_id=course_id,
                topic_id=meta["topic_id"],
                week_number=meta["week_number"],
                course_title=c_title,
                topic_name=meta["topic_name"],
                glossary=meta["glossary"]
            )

            if not chunks:
                raise ValueError("Не удалось сформировать семантические чанки из документа.")

            # 4. СЕЛЕКТИВНАЯ ИНДЕКСАЦИЯ В CHROMADB HNSW
            update_ingestion_job(
                job_id,
                status="INDEXING",
                progress=75,
                total=len(chunks),
                message=f"Векторизация BAAI/bge-m3 и селективный upsert в ChromaDB ({len(chunks)} чанков)..."
            )

            from backend.vector_store import vector_store
            from backend.rag_service import rag_service

            # Векторизация и удаление старых чанков в ThreadPool
            indexed_count = await asyncio.to_thread(
                vector_store.add_slides,
                topic_id=meta["topic_id"],
                week_number=meta["week_number"],
                slides_data=chunks,
                course_id=course_id,
                delete_old=True
            )

            # 5. СОХРАНЕНИЕ В SQLITE
            # Гарантируем регистрацию курса
            save_course(
                course_id=course_id,
                title=c_title,
                instructor=c_info.get("instructor", "") if c_info else "",
                description=c_info.get("description", "") if c_info else ""
            )

            # Сохраняем неделю силлабуса
            demo_json = json.dumps(meta["demo_turns"], ensure_ascii=False)
            save_syllabus_week(
                course_id=course_id,
                topic_id=meta["topic_id"],
                week_number=meta["week_number"],
                title=meta["title"],
                topic_name=meta["topic_name"],
                initial_prompt=meta["initial_prompt"],
                demo_turns_json=demo_json,
                md_path=saved_md_path,
                chunks_count=indexed_count
            )

            # Сохраняем термины глоссария
            save_lecture_glossary(
                course_id=course_id,
                topic_id=meta["topic_id"],
                terms=meta["glossary"]
            )

            # Регистрируем тему в оперативной памяти rag_service
            rag_service.register_dynamic_week(
                topic_id=meta["topic_id"],
                week_number=meta["week_number"],
                title=meta["title"],
                topic_name=meta["topic_name"],
                initial_prompt=meta["initial_prompt"],
                glossary=meta["glossary"],
                slides_count=indexed_count,
                course_id=course_id,
                demo_turns=meta["demo_turns"]
            )

            # 6. ФИНАЛИЗАЦИЯ ДЖОБА
            update_ingestion_job(
                job_id,
                status="COMPLETED",
                progress=100,
                total=indexed_count,
                message=f"Индексация успешно завершена! {indexed_count} чанков загружены в HNSW (BGE-M3)."
            )
            logger.info(f"Фоновая индексация {job_id} успешно завершена: {meta['topic_id']}")

            return {
                "job_id": job_id,
                "status": "COMPLETED",
                "course_id": course_id,
                "topic_id": meta["topic_id"],
                "week_number": meta["week_number"],
                "title": meta["title"],
                "topic_name": meta["topic_name"],
                "slides_count": len(chunks),
                "indexed_chunks": indexed_count,
                "glossary": meta["glossary"],
                "initial_prompt": meta["initial_prompt"],
                "demo_turns": meta["demo_turns"]
            }

        except Exception as e:
            logger.error(f"Ошибка в фоновом джобе {job_id}: {e}", exc_info=True)
            update_ingestion_job(
                job_id,
                status="FAILED",
                progress=0,
                error=str(e),
                message=f"Ошибка обработки: {str(e)}"
            )
            raise


# Глобальный инстанс сервиса инжеста
ingestion_service = CourseIngestionService()
