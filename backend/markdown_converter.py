"""
markdown_converter.py

Модуль универсальной конвертации учебных материалов в структурированный Markdown (.md)
для Zero-Config Ingestion пайплайна Themis Project.

Поддерживаемые форматы:
- .pdf (pypdf: извлечение страниц, заголовков, нормализация переносов)
- .pptx (python-pptx: слайды -> ##, списки -> -, таблицы -> GFM |...|)
- .docx (python-docx: Heading 1..3 -> #..###, списки, таблицы GFM)
- .ipynb (nbformat/json: markdown-ячейки + python кодовые блоки без base64-картинок)
- .md / .txt (прямое чтение UTF-8 с детерминированной нормализацией)
- .zip (пакетная распаковка и конвертация всех поддерживаемых файлов архива)
"""

import os
import re
import json
import zipfile
import tempfile
import logging
from typing import List, Dict, Any, Optional, Tuple

import pypdf
from pptx import Presentation
import docx

logger = logging.getLogger("themis.markdown_converter")

BASE_COURSES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "courses")


def clean_markdown_text(text: str) -> str:
    """
    Детерминированная нормализация разметки:
    - Удаление base64 data URIs и громоздких картинок
    - Склейка разорванных переносами слов (сло-\nво -> слово)
    - Нормализация заголовков (гарантия пробела после #)
    - Нормализация множественных пустых строк
    """
    if not text:
        return ""

    # 1. Удаление base64 изображений
    text = re.sub(r'!\[.*?\]\(data:[^)]+\)', '[Иллюстрация к лекции]', text)
    text = re.sub(r'<img\s+[^>]*src=["\']data:[^"\']+["\'][^>]*\/?>', '[Иллюстрация к лекции]', text, flags=re.IGNORECASE)

    # 2. Склейка разорванных переносов в словах
    text = re.sub(r'([А-Яа-яA-Za-z0-9])-\n\s*([А-Яа-яA-Za-z0-9])', r'\1\2', text)

    # 3. Гарантия пробела после решеток в заголовках (#Заголовок -> # Заголовок)
    text = re.sub(r'^(#{1,6})([^\s#])', r'\1 \2', text, flags=re.MULTILINE)

    # 4. Нормализация множественных пустых строк
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


class DocumentToMarkdownConverter:
    """
    Универсальный конвертер документов в Markdown для автономного пайплайна курсов.
    """

    def __init__(self, output_base_dir: str = BASE_COURSES_DIR):
        self.output_base_dir = output_base_dir
        os.makedirs(self.output_base_dir, exist_ok=True)

    def convert_pptx(self, file_path: str) -> str:
        """
        Конвертирует презентацию PowerPoint (.pptx) в структурированный Markdown:
        - Заголовки слайдов -> ## Заголовок
        - Маркированные списки -> - Элемент
        - Таблицы -> GFM таблицы | Header 1 | Header 2 |
        - Детекция кода в тексте
        """
        prs = Presentation(file_path)
        slides_md = []

        for idx, slide in enumerate(prs.slides, start=1):
            title = ""
            if slide.shapes.title and slide.shapes.title.text:
                title = slide.shapes.title.text.strip()

            slide_title = title or f"Слайд {idx}"
            slide_parts = [f"## {slide_title}"]

            for shape in slide.shapes:
                if shape == slide.shapes.title:
                    continue

                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        p_text = paragraph.text.strip()
                        if p_text and p_text != title:
                            level = paragraph.level or 0
                            indent = "  " * level
                            # Если это блок кода
                            if any(k in p_text for k in ["import ", "def ", "class ", "return ", "torch.", "nn.", "np."]):
                                slide_parts.append(f"```python\n{p_text}\n```")
                            else:
                                slide_parts.append(f"{indent}- {p_text}")

                elif shape.has_table:
                    table = shape.table
                    rows = []
                    for r_idx, row in enumerate(table.rows):
                        cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                        if any(cells):
                            rows.append("| " + " | ".join(cells) + " |")
                            if r_idx == 0:
                                # Разделитель заголовка GFM
                                rows.append("| " + " | ".join(["---"] * len(cells)) + " |")
                    if rows:
                        slide_parts.append("\n" + "\n".join(rows) + "\n")

            slides_md.append("\n".join(slide_parts))

        raw_md = "\n\n".join(slides_md)
        return clean_markdown_text(raw_md)

    def convert_pdf(self, file_path: str) -> str:
        """
        Конвертирует PDF-документ в Markdown:
        - Извлечение текста постранично
        - Эвристика выделения заголовков секций
        - Нормализация разрывов строк и абзацев
        """
        reader = pypdf.PdfReader(file_path)
        pages_md = []

        for idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if not text:
                continue

            lines = [l.strip() for l in text.splitlines() if l.strip()]
            if not lines:
                continue

            # Первая строка как заголовок страницы/раздела, если похожа на заголовок
            first_line = lines[0]
            if len(first_line) < 80 and not first_line.endswith((".", ",")):
                page_title = first_line
                content_lines = lines[1:]
            else:
                page_title = f"Страница {idx}"
                content_lines = lines

            # Склейка обычных строк в абзацы (не склеивая списки и заголовки)
            paragraphs = []
            curr_p = []

            for line in content_lines:
                if line.startswith(("-", "*", "•", "1.", "2.", "3.", "4.", "5.", "#")):
                    if curr_p:
                        paragraphs.append(" ".join(curr_p))
                        curr_p = []
                    paragraphs.append(line)
                else:
                    curr_p.append(line)
                    if line.endswith((".", "!", "?", ":")):
                        paragraphs.append(" ".join(curr_p))
                        curr_p = []

            if curr_p:
                paragraphs.append(" ".join(curr_p))

            page_body = "\n\n".join(paragraphs)
            pages_md.append(f"## {page_title}\n\n{page_body}")

        raw_md = "\n\n".join(pages_md)
        return clean_markdown_text(raw_md)

    def convert_docx(self, file_path: str) -> str:
        """
        Конвертирует Microsoft Word (.docx) в Markdown:
        - Стили Heading 1..3 -> #, ##, ###
        - Списки -> - Элемент
        - Таблицы -> GFM таблицы | ... |
        - Сохранение порядка следования абзацев и таблиц
        """
        doc = docx.Document(file_path)
        parts = []

        # Обход элементов тела документа в естественном порядке
        for child in doc.element.body.iterchildren():
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

            if tag == "p":
                p = docx.text.paragraph.Paragraph(child, doc)
                text = p.text.strip()
                if not text:
                    continue

                style_name = p.style.name.lower() if p.style and p.style.name else ""

                if "heading 1" in style_name:
                    parts.append(f"# {text}")
                elif "heading 2" in style_name:
                    parts.append(f"## {text}")
                elif "heading 3" in style_name:
                    parts.append(f"### {text}")
                elif "heading" in style_name:
                    parts.append(f"#### {text}")
                elif "list" in style_name or "bullet" in style_name:
                    parts.append(f"- {text}")
                else:
                    parts.append(text)

            elif tag == "tbl":
                table = docx.table.Table(child, doc)
                rows = []
                for r_idx, row in enumerate(table.rows):
                    cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                    if any(cells):
                        rows.append("| " + " | ".join(cells) + " |")
                        if r_idx == 0:
                            rows.append("| " + " | ".join(["---"] * len(cells)) + " |")
                if rows:
                    parts.append("\n" + "\n".join(rows) + "\n")

        raw_md = "\n\n".join(parts)
        return clean_markdown_text(raw_md)

    def convert_ipynb(self, file_path: str) -> str:
        """
        Конвертирует Jupyter Notebook (.ipynb) в Markdown:
        - Markdown ячейки очищаются от base64 картинок
        - Code ячейки преобразуются в ```python ... ``` блоки
        - Служебные команды IPython (!pip, %matplotlib) фильтруются
        - Base64 графики и громоздкие аутпуты игнорируются
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                nb = json.load(f)
        except Exception as e:
            logger.error(f"Ошибка чтения блокнота {file_path}: {e}")
            return ""

        parts = []
        cells = nb.get("cells", [])

        for cell in cells:
            ctype = cell.get("cell_type")
            source = "".join(cell.get("source", []))
            if not source.strip():
                continue

            if ctype == "markdown":
                clean_src = clean_markdown_text(source)
                if clean_src:
                    parts.append(clean_src)

            elif ctype == "code":
                code_lines = []
                for line in source.splitlines():
                    # Пропуск команд оболочки IPython
                    if line.strip().startswith(("!", "%")):
                        continue
                    code_lines.append(line)

                clean_code = "\n".join(code_lines).strip()
                if clean_code and not clean_code.startswith("#") and len(clean_code) > 8:
                    parts.append(f"```python\n{clean_code}\n```")

        raw_md = "\n\n".join(parts)
        return clean_markdown_text(raw_md)

    def convert_text(self, file_path: str) -> str:
        """
        Прямое чтение Markdown или текстового файла в UTF-8 (с авто-декодированием).
        """
        encodings = ["utf-8", "utf-8-sig", "cp1251", "latin-1"]
        raw_text = None

        for enc in encodings:
            try:
                with open(file_path, "r", encoding=enc) as f:
                    raw_text = f.read()
                break
            except (UnicodeDecodeError, Exception):
                continue

        if raw_text is None:
            with open(file_path, "rb") as f:
                raw_text = f.read().decode("utf-8", errors="replace")

        return clean_markdown_text(raw_text)

    def convert_file(self, file_path: str) -> str:
        """
        Автоматический выбор конвертера по расширению файла.
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            return self.convert_pdf(file_path)
        elif ext in (".pptx", ".ppt"):
            return self.convert_pptx(file_path)
        elif ext in (".docx", ".doc"):
            return self.convert_docx(file_path)
        elif ext == ".ipynb":
            return self.convert_ipynb(file_path)
        elif ext in (".md", ".txt", ".markdown"):
            return self.convert_text(file_path)
        else:
            # Fallback к текстовому чтению
            return self.convert_text(file_path)

    def convert_zip(
        self,
        zip_path: str,
        course_id: str = "prog_ai_2026",
        extract_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Распаковывает ZIP-архив и пакетно конвертирует все поддерживаемые файлы.
        Возвращает список словарей со сконвертированными документами и метаданными.
        """
        temp_dir = extract_dir or tempfile.mkdtemp(prefix="themis_zip_")
        results = []

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(temp_dir)

            supported_exts = {".pdf", ".pptx", ".docx", ".ipynb", ".md", ".txt"}
            file_index = 1

            for root, _, files in os.walk(temp_dir):
                for fname in sorted(files):
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in supported_exts:
                        full_path = os.path.join(root, fname)
                        rel_path = os.path.relpath(full_path, temp_dir)

                        try:
                            md_content = self.convert_file(full_path)
                            if not md_content or len(md_content.strip()) < 20:
                                continue

                            # Формируем slug topic_id
                            clean_stem = re.sub(r'[^a-zA-Z0-9_-]', '_', os.path.splitext(fname)[0]).strip('_').lower()
                            topic_id = f"topic_{file_index:02d}_{clean_stem[:30]}"
                            topic_title = os.path.splitext(fname)[0].replace("_", " ").title()

                            results.append({
                                "file_name": fname,
                                "rel_path": rel_path,
                                "topic_id": topic_id,
                                "title": topic_title,
                                "markdown": md_content,
                                "source_path": full_path,
                                "extension": ext,
                            })
                            file_index += 1

                        except Exception as e:
                            logger.warning(f"Не удалось сконвертировать файл {fname} из архива: {e}")

        finally:
            # Если extract_dir не задан извне, временную папку можно сохранить или удалить при завершении
            pass

        return results

    def save_converted_md(
        self,
        course_id: str,
        topic_id: str,
        markdown_content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Сохраняет сконвертированный Markdown с YAML frontmatter в:
        `data/courses/{course_id}/topics/{topic_id}.md`
        (и гарантирует наличие `data/courses/{course_id}/{topic_id}.md`).
        """
        meta = metadata or {}
        meta_dict = {
            "course_id": course_id,
            "topic_id": topic_id,
            "title": meta.get("title", meta.get("topic_name", topic_id)),
            "week_number": meta.get("week_number", 1),
            "topic_name": meta.get("topic_name", topic_id),
            "initial_prompt": meta.get("initial_prompt", ""),
            "glossary": meta.get("glossary", []),
        }

        # Формирование YAML frontmatter
        import yaml
        yaml_header = yaml.dump(meta_dict, allow_unicode=True, default_flow_style=False).strip()
        full_content = f"---\n{yaml_header}\n---\n\n{markdown_content.strip()}\n"

        # Пути сохранения
        course_dir = os.path.join(self.output_base_dir, course_id)
        topics_dir = os.path.join(course_dir, "topics")
        os.makedirs(topics_dir, exist_ok=True)

        target_file = os.path.join(topics_dir, f"{topic_id}.md")
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(full_content)

        # Дополнительная копия в course_dir/{topic_id}.md для удобства обратной совместимости
        direct_file = os.path.join(course_dir, f"{topic_id}.md")
        with open(direct_file, "w", encoding="utf-8") as f:
            f.write(full_content)

        logger.info(f"Файл Markdown успешно сохранен: {target_file}")
        return target_file


# Глобальный инстанс конвертера
markdown_converter = DocumentToMarkdownConverter()
