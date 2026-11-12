"""
ingestion_service.py

Сервис парсинга и динамической обработки материалов курса (PPTX / PDF).
Позволяет преподавателю загружать презентации лекций «на лету» без перезапуска системы,
разбивает слайды на семантические чанки, извлекает глоссарий и генерирует
стартовые сократические вопросы для RAG-контура.
"""

import os
import re
import logging
from typing import List, Dict, Any, Tuple
from pptx import Presentation
from pypdf import PdfReader

logger = logging.getLogger("themis.ingestion")

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


class CourseIngestionService:
    def __init__(self, uploads_dir: str = UPLOADS_DIR):
        self.uploads_dir = uploads_dir

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

            # Извлечение заголовка слайда
            if slide.shapes.title and slide.shapes.title.text:
                slide_title = slide.shapes.title.text.strip()

            # Обход всех фигур и таблиц на слайде
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        p_text = paragraph.text.strip()
                        if p_text and p_text != slide_title:
                            text_parts.append(p_text)
                            # Эвристика детекции кода
                            if any(k in p_text for k in ["import ", "def ", "class ", "nn.", "torch.", "np.", "pd."]):
                                has_code = True

                elif shape.has_table:
                    # Извлечение содержимого таблиц
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
                # Берем первую строку как заголовок, если явно не задан
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
        # Поиск английских терминов и устойчивых русских терминов
        candidates = set()
        en_terms = re.findall(r"\b[A-Za-z][A-Za-z0-9_-]{2,}\b", text)
        for term in en_terms:
            lower = term.lower()
            if lower not in {"the", "and", "for", "with", "from", "that", "this", "are"}:
                candidates.add(lower)

        # Выделение русских технических терминов
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

        # Выбираем наиболее значимые концепты (до 6)
        glossary = sorted(list(all_concepts))[:6]
        if not glossary:
            glossary = ["архитектура", "параметры", "оптимизация", "обучение", "метрики"]

        # Формируем стартовый сократический вопрос по первому слайду
        first_slide_text = slides[0]["text"] if slides else ""
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


ingestion_service = CourseIngestionService()

