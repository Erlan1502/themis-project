"""
test_markdown_converter_and_ingestion.py

Тесты для Шага 5 (Автономный пайплайн загрузки курсов Zero-Config .md Ingestion):
- Конвертер документов: .pdf, .pptx, .docx, .ipynb, .md, .zip в структурированный Markdown.
- Семантический чанкер (Smart Markdown Chunker):
  - Иерархическое деление по заголовкам
  - Атомарная защита от разрезания блоков кода, таблиц и формул LaTeX
  - Инжекция контекстных breadcrumbs
  - Связка с глоссарием
- Авто-структурирование курса и лекции (метаданные, глоссарий, initial_prompt, demo_turns).
- Фоновая индексация и REST API:
  - POST /api/v1/courses/{course_id}/ingest (202 Accepted + job_id)
  - GET /api/v1/course/jobs/{job_id} (статусы, прогресс 0-100%, stage, error)
  - POST /api/v1/course/upload (обратная совместимость: sync 200 OK / async 202)
  - Селективный upsert в ChromaDB HNSW с удалением чанков только своей темы.
"""

import os
import io
import json
import time
import zipfile
import tempfile
import pytest
import docx
from pptx import Presentation
from starlette.testclient import TestClient

from backend.main import app, reset_database
from backend.markdown_converter import markdown_converter, clean_markdown_text
from backend.chunker import smart_chunk_markdown, SemanticMarkdownChunker
from backend.ingestion_service import ingestion_service
from backend.vector_store import vector_store
from backend.database import get_ingestion_job, get_syllabus_week, get_lecture_glossary


@pytest.fixture(autouse=True)
def setup_db():
    reset_database()
    yield


@pytest.fixture
def client():
    return TestClient(app)


def test_markdown_cleaner():
    """Тест очистки текста: удаление base64, склейка переносов, пробелы в заголовках."""
    raw = (
        "#Заголовок без пробела\n\n"
        "Слово с пере-\nносом строки.\n\n"
        "![изображение](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=)\n\n"
        "\n\n\nМного пустых строк."
    )
    cleaned = clean_markdown_text(raw)
    assert "# Заголовок без пробела" in cleaned
    assert "переносом строки" in cleaned
    assert "data:image" not in cleaned
    assert "[Иллюстрация к лекции]" in cleaned
    assert "\n\n\n" not in cleaned


def test_convert_docx():
    """Тест конвертации Word (.docx) в чистый Markdown с заголовками, списками и таблицами."""
    doc = docx.Document()
    doc.add_heading("Сверточные нейронные сети (CNN)", level=1)
    doc.add_paragraph("Сверточные слои используют пространственные фильтры для карт признаков.")
    doc.add_heading("Архитектура свертки", level=2)
    doc.add_paragraph("Ядро свертки (kernel)", style="List Bullet")
    doc.add_paragraph("Шаг свертки (stride)", style="List Bullet")

    table = doc.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Слой"
    table.rows[0].cells[1].text = "Размерность"
    table.rows[1].cells[0].text = "Conv2D"
    table.rows[1].cells[1].text = "32x32x64"

    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        tmp_path = f.name
    doc.save(tmp_path)

    try:
        md = markdown_converter.convert_docx(tmp_path)
        assert "# Сверточные нейронные сети (CNN)" in md
        assert "## Архитектура свертки" in md
        assert "- Ядро свертки (kernel)" in md
        assert "| Слой | Размерность |" in md
        assert "| Conv2D | 32x32x64 |" in md
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_convert_pptx():
    """Тест конвертации презентации PowerPoint (.pptx) в Markdown."""
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Глубокое обучение и регуляризация"
    body = slide.shapes.placeholders[1]
    body.text = "Метод Dropout обнуляет случайные нейроны.\nWeight decay добавляет L2 штраф к весам."

    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
        tmp_path = f.name
    prs.save(tmp_path)

    try:
        md = markdown_converter.convert_pptx(tmp_path)
        assert "## Глубокое обучение и регуляризация" in md
        assert "Dropout" in md
        assert "Weight decay" in md
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_convert_ipynb():
    """Тест конвертации Jupyter Notebook (.ipynb) в чистый Markdown."""
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# Работа с тензорами PyTorch\n",
                    "Введение в тензорные операции.\n",
                    "![img](data:image/jpeg;base64,1234567890)"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "source": [
                    "%matplotlib inline\n",
                    "!pip install torch\n",
                    "import torch\n",
                    "x = torch.ones((2, 2))\n",
                    "print(x)"
                ]
            }
        ],
        "metadata": {},
        "nbformat": 4,
        "nbformat_minor": 2
    }

    with tempfile.NamedTemporaryFile(suffix=".ipynb", delete=False, mode="w", encoding="utf-8") as f:
        tmp_path = f.name
        json.dump(nb, f)

    try:
        md = markdown_converter.convert_ipynb(tmp_path)
        assert "# Работа с тензорами PyTorch" in md
        assert "data:image" not in md
        # Магические команды IPython должны быть отфильтрованы
        assert "%matplotlib" not in md
        assert "!pip install" not in md
        # Код должен быть обернут в блок python
        assert "```python" in md
        assert "import torch" in md
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_convert_pdf():
    """Тест конвертации PDF в Markdown."""
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 400 400] /Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>> >> endobj\n"
        b"4 0 obj <</Length 65>> stream\n"
        b"BT /F1 12 Tf 20 300 Td (Gradient Boosting and CatBoost Ensemble) Tj ET\n"
        b"endstream endobj\n"
        b"5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        b"xref\n0 6\n0000000000 65535 f \ntrailer <</Size 6 /Root 1 0 R>>\nstartxref\n360\n%%EOF\n"
    )

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        tmp_path = f.name
        f.write(pdf_content)

    try:
        md = markdown_converter.convert_pdf(tmp_path)
        assert "Gradient Boosting and CatBoost Ensemble" in md
        assert "## " in md
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_convert_zip_archive():
    """Тест пакетной конвертации ZIP-архива курсовых документов."""
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
        zip_path = f.name

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("lecture_01.md", "# Введение в Python\n\nОсновы синтаксиса и типы данных.")
        zf.writestr("notes.txt", "Важные концепты: переменные, циклы, функции.")

    try:
        results = markdown_converter.convert_zip(zip_path, course_id="prog_ai_2026")
        assert len(results) == 2
        fnames = [r["file_name"] for r in results]
        assert "lecture_01.md" in fnames
        assert "notes.txt" in fnames
        assert "Введение в Python" in results[0]["markdown"]
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)


def test_smart_chunker_atomic_protection_and_breadcrumbs():
    """
    Тест Smart Markdown Chunker:
    - Защита от разрезания блоков кода, таблиц и выключных формул LaTeX
    - Инжекция контекстных хлебных крошек в начало каждого чанка
    - Связка с глоссарием темы
    """
    code_block = "```python\nimport torch.nn as nn\nclass MLP(nn.Module):\n    def __init__(self):\n        super().__init__()\n```"
    table_block = "| Параметр | Значение |\n| --- | --- |\n| learning_rate | 0.001 |\n| batch_size | 32 |"
    math_block = "$$\nL(\\theta) = -\\frac{1}{N}\\sum_{i=1}^N y_i \\log(\\hat{y}_i)\n$$"

    md = (
        "# Регуляризация нейросетей\n\n"
        "Введение в методы регуляризации и борьбу с переобучением моделей.\n\n"
        f"## Архитектура модели\n\n{code_block}\n\n"
        f"## Таблица гиперпараметров\n\n{table_block}\n\n"
        f"## Функция потерь\n\n{math_block}\n"
    )

    glossary = ["регуляризация", "переобучение", "learning_rate", "batch_size"]
    chunks = smart_chunk_markdown(
        markdown_text=md,
        course_id="prog_ai_2026",
        topic_id="week_09_deep_learning",
        week_number=9,
        course_title="Programming for AI",
        topic_name="Регуляризация",
        glossary=glossary,
        max_chunk_size=500
    )

    assert len(chunks) >= 3

    # Проверяем инжекцию хлебных крошек
    for c in chunks:
        assert "[Курс: Programming for AI | Тема: Регуляризация | Раздел:" in c["text"]
        assert c["chunk_id"].startswith("prog_ai_2026_week_09_deep_learning_chunk_")

    # Проверяем, что неделимые блоки не разорваны
    has_code_chunk = next(c for c in chunks if c["has_code"])
    assert "class MLP(nn.Module):" in has_code_chunk["raw_text"]
    assert "```python" in has_code_chunk["raw_text"]

    has_table_chunk = next(c for c in chunks if c["has_table"])
    assert "| learning_rate | 0.001 |" in has_table_chunk["raw_text"]
    assert "| --- | --- |" in has_table_chunk["raw_text"]

    has_math_chunk = next(c for c in chunks if c["has_math"])
    assert "L(\\theta)" in has_math_chunk["raw_text"]


def test_auto_structure_topic():
    """Тест авто-структурирования темы лекции (определение названия, initial_prompt, demo_turns)."""
    raw_md = (
        "# Трансформеры и механизм внимания (Self-Attention)\n\n"
        "Механизм self-attention позволяет сопоставлять разные позиции последовательности.\n"
        "Ключевые матрицы: Query, Key, Value. Мульти-головое внимание (Multi-Head Attention).\n"
        "Регуляризация через dropout и слой LayerNorm."
    )

    structured = ingestion_service.auto_structure_topic(
        markdown_text=raw_md,
        filename="lecture_12_transformers.md",
        course_id="prog_ai_2026"
    )

    assert "Трансформеры" in structured["topic_name"]
    assert structured["week_number"] == 12
    assert "week_12" in structured["topic_id"]
    assert len(structured["glossary"]) >= 5
    assert len(structured["demo_turns"]) == 3
    assert "Привет! На занятии мы разобрали тему" in structured["initial_prompt"]


def test_api_course_ingest_async_and_jobs(client):
    """
    Интеграционный тест REST API:
    - POST /api/v1/courses/{course_id}/ingest возвращает 202 Accepted и job_id
    - GET /api/v1/course/jobs/{job_id} отслеживает стадии индексации
    - По завершении статус становится COMPLETED и неделя доступна в силлабусе
    """
    md_content = (
        "# Градиентный бустинг и деревья решений (CatBoost)\n\n"
        "Градиентный бустинг строит ансамбль решающих деревьев последовательно.\n"
        "Каждое дерево аппроксимирует антиградиент функции потерь.\n\n"
        "## Регуляризация\n\n"
        "Для предотвращения переобучения используются L2 регуляризация и early stopping.\n"
    )

    # 1. Отправляем запрос на асинхронную индексацию
    file_bytes = io.BytesIO(md_content.encode("utf-8"))
    resp = client.post(
        "/api/v1/courses/prog_ai_2026/ingest",
        files={"file": ("lecture_catboost.md", file_bytes, "text/markdown")},
        data={"week_number": 14, "topic_name": "Градиентный бустинг CatBoost"}
    )

    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "QUEUED"
    job_id = data["job_id"]

    # 2. Проверяем получение статуса через GET /api/v1/course/jobs/{job_id}
    job_resp = client.get(f"/api/v1/course/jobs/{job_id}")
    assert job_resp.status_code == 200
    job_data = job_resp.json()
    assert job_data["job_id"] == job_id
    assert job_data["course_id"] == "prog_ai_2026"
    assert "status" in job_data
    assert "progress" in job_data
    assert "stage" in job_data

    # 3. Ждем завершения фоновой задачи (до 10 секунд)
    completed = False
    for _ in range(50):
        time.sleep(0.1)
        j = get_ingestion_job(job_id)
        if j and j["status"] == "COMPLETED":
            completed = True
            break
        elif j and j["status"] == "FAILED":
            pytest.fail(f"Фоновая индексация завершилась с ошибкой: {j.get('error')}")

    assert completed is True
    final_job = get_ingestion_job(job_id)
    assert final_job["progress"] == 100
    assert "успешно завершена" in final_job["message"].lower()

    # 4. Проверяем, что новая неделя появилась в силлабусе курса
    weeks_resp = client.get("/api/v1/syllabus/weeks")
    assert weeks_resp.status_code == 200
    weeks = weeks_resp.json()
    week_14 = next((w for w in weeks if w.get("week_number") == 14), None)
    assert week_14 is not None
    assert "CatBoost" in week_14["topic_name"] or "CatBoost" in week_14["title"]


def test_api_course_upload_async_and_sync_compatibility(client):
    """
    Тест эндпоинта /api/v1/course/upload:
    - При async_mode=False (по умолчанию) работает синхронно и возвращает 200 OK
    - При async_mode=True работает асинхронно и возвращает 202 Accepted
    """
    md_content = "# Введение в нейронные сети\n\nПерцептрон и функция активации Sigmoid.\n"
    
    # 1. Синхронный вызов (обратная совместимость)
    resp_sync = client.post(
        "/api/v1/course/upload",
        files={"file": ("lecture_sync.md", io.BytesIO(md_content.encode("utf-8")), "text/markdown")},
        data={"week_number": 15, "topic_name": "Введение в нейросети"}
    )
    assert resp_sync.status_code == 200
    sync_data = resp_sync.json()
    assert sync_data["status"] == "SUCCESS"
    assert sync_data["week_number"] == 15

    # 2. Асинхронный вызов
    resp_async = client.post(
        "/api/v1/course/upload",
        files={"file": ("lecture_async.md", io.BytesIO(md_content.encode("utf-8")), "text/markdown")},
        data={"week_number": 16, "topic_name": "Сверточные сети", "async_mode": "true"}
    )
    assert resp_async.status_code == 202
    async_data = resp_async.json()
    assert "job_id" in async_data
    assert async_data["status"] == "QUEUED"


def test_selective_chroma_delete_on_reindex():
    """Тест селективного удаления чанков: при переиндексации удаляются чанки только своей темы."""
    course_id = "test_course_selective"
    topic_1 = "week_01_intro"
    topic_2 = "week_02_advanced"

    chunks_1 = [
        {"chunk_id": f"{course_id}_{topic_1}_c1", "title": "T1", "text": "Текст первой темы лекции"}
    ]
    chunks_2 = [
        {"chunk_id": f"{course_id}_{topic_2}_c1", "title": "T2", "text": "Текст второй темы лекции"}
    ]

    # Добавляем обе темы
    vector_store.add_slides(topic_id=topic_1, week_number=1, slides_data=chunks_1, course_id=course_id)
    vector_store.add_slides(topic_id=topic_2, week_number=2, slides_data=chunks_2, course_id=course_id)

    # Проверяем, что чанки присутствуют
    assert vector_store.get_topic_slides_count(topic_id=topic_1, course_id=course_id) == 1
    assert vector_store.get_topic_slides_count(topic_id=topic_2, course_id=course_id) == 1

    # Удаляем селективно только topic_1
    vector_store.delete_topic_chunks(topic_id=topic_1, course_id=course_id)

    # Проверяем: topic_1 удален, а topic_2 остался нетронутым!
    assert vector_store.get_topic_slides_count(topic_id=topic_1, course_id=course_id) == 0
    assert vector_store.get_topic_slides_count(topic_id=topic_2, course_id=course_id) == 1
