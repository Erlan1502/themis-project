"""
test_ingestion_and_rag.py

Тесты для сервиса загрузки курсов «на лету» (Zero-Config Ingestion),
векторного хранилища ChromaDB с графом HNSW и RAG-заземления сократического тьютора.
"""

import os
import tempfile
import pytest
from pptx import Presentation
from pptx.util import Inches, Pt
from fastapi.testclient import TestClient

from backend.main import app
from backend.ingestion_service import ingestion_service
from backend.vector_store import vector_store
from backend.rag_service import rag_service

client = TestClient(app)


@pytest.fixture
def sample_pptx():
    """Создает временный презентационный файл .pptx с двумя слайдами по машинному обучению."""
    prs = Presentation()
    
    # Слайд 1: Введение в градиентный бустинг
    slide_layout = prs.slide_layouts[1]
    slide1 = prs.slides.add_slide(slide_layout)
    slide1.shapes.title.text = "Градиентный бустинг и ансамблирование"
    content1 = slide1.shapes.placeholders[1]
    content1.text = (
        "Градиентный бустинг последовательно строит деревья решений. "
        "Каждое новое дерево обучается на антиградиент функции потерь (псевдо-остатки). "
        "Ключевые параметры: learning rate, max depth, subsample."
    )

    # Слайд 2: Регуляризация в CatBoost и XGBoost
    slide2 = prs.slides.add_slide(slide_layout)
    slide2.shapes.title.text = "Борьба с переобучением в градиентном бустинге"
    content2 = slide2.shapes.placeholders[1]
    content2.text = (
        "Для предотвращения переобучения используются L2 регуляризация весов листьев и shrinkage. "
        "Ранняя остановка (early stopping) прекращает обучение при росте валидационной ошибки."
    )

    temp_file = tempfile.NamedTemporaryFile(suffix=".pptx", delete=False)
    temp_path = temp_file.name
    temp_file.close()
    prs.save(temp_path)

    yield temp_path

    # Очистка
    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_pptx_parsing(sample_pptx):
    slides = ingestion_service.parse_pptx(sample_pptx)
    assert len(slides) == 2
    assert "бустинг" in slides[0]["title"].lower()
    assert "псевдо-остатки" in slides[0]["text"]
    assert "early stopping" in slides[1]["text"].lower()


def test_vector_store_hnsw_indexing_and_search(sample_pptx):
    slides = ingestion_service.parse_pptx(sample_pptx)
    topic_id = "test_week_boosting"
    
    # 1. Индексация в HNSW
    count = vector_store.add_slides(topic_id=topic_id, week_number=11, slides_data=slides)
    assert count == 2

    # 2. Семантический поиск по концепту
    query = "Как ранняя остановка защищает модель от переобучения?"
    results = vector_store.search_relevant_slides(query=query, topic_id=topic_id, top_k=1)
    
    assert len(results) == 1
    assert "early stopping" in results[0]["text"].lower() or "переобучением" in results[0]["text"].lower()


def test_upload_course_api_endpoint(sample_pptx):
    with open(sample_pptx, "rb") as f:
        response = client.post(
            "/api/v1/course/upload",
            files={"file": ("lecture_boosting.pptx", f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
            data={"week_number": 11, "topic_name": "Градиентный бустинг и ансамбли (CatBoost)"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["week_number"] == 11
    assert data["slides_count"] == 2
    assert len(data["glossary"]) > 0

    # Проверяем, что неделя появилась в силлабусе курса
    weeks_resp = client.get("/api/v1/syllabus/weeks")
    assert weeks_resp.status_code == 200
    weeks = weeks_resp.json()
    week_11 = next((w for w in weeks if w["week_number"] == 11), None)
    assert week_11 is not None
    assert "CatBoost" in week_11["topic_name"]

