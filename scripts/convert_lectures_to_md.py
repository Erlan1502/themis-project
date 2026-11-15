"""
convert_lectures_to_md.py

Скрипт разбора реальных лекционных материалов курса "Programming for AI" (PAI, 2026-2027)
из папки "Лекции Programming AI" в 9 структурированных Markdown-файлов (.md)
в папку data/lectures_md/.
"""

import os
import json
import re
from typing import List, Dict, Any, Tuple
from pptx import Presentation

BASE_DIR = r"Лекции Programming AI"
OUTPUT_DIR = os.path.join(r"data", "lectures_md")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def clean_markdown_cell(text: str) -> str:
    """Удаляет громоздкие base64-изображения и HTML-шум из markdown ячеек."""
    # Удаляем base64 data URIs
    text = re.sub(r'!\[.*?\]\(data:image\/.*?;base64,.*?\)', '[Иллюстрация к лекции]', text)
    text = re.sub(r'<img\s+src="data:image\/.*?"\s*\/?>', '[Иллюстрация к лекции]', text)
    # Нормализуем множественные пустые строки
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def parse_ipynb(fpath: str) -> str:
    """Извлекает текст и код из Jupyter Notebook."""
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            nb = json.load(f)
    except Exception as e:
        print(f"Ошибка чтения {fpath}: {e}")
        return ""

    parts = []
    cells = nb.get("cells", [])

    for c in cells:
        ctype = c.get("cell_type")
        source = "".join(c.get("source", []))
        if not source.strip():
            continue

        if ctype == "markdown":
            cleaned = clean_markdown_cell(source)
            if cleaned:
                parts.append(cleaned)
        elif ctype == "code":
            code_lines = source.strip()
            # Пропускаем тривиальные вызовы или служебные команды pip/magic
            filtered_lines = []
            for line in code_lines.splitlines():
                if line.startswith("!") or line.startswith("%"):
                    continue
                filtered_lines.append(line)
            clean_code = "\n".join(filtered_lines).strip()
            if clean_code and not clean_code.startswith("#") and len(clean_code) > 10:
                parts.append(f"```python\n{clean_code}\n```")

    return "\n\n".join(parts)


def parse_pptx_slides(fpath: str) -> str:
    """Извлекает структурированный текст и таблицы из презентации PowerPoint."""
    try:
        prs = Presentation(fpath)
    except Exception as e:
        print(f"Ошибка чтения PPTX {fpath}: {e}")
        return ""

    parts = []
    for idx, slide in enumerate(prs.slides, 1):
        title = ""
        if slide.shapes.title and slide.shapes.title.text:
            title = slide.shapes.title.text.strip()

        slide_texts = []
        table_texts = []

        for sh in slide.shapes:
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    t = p.text.strip()
                    if t and t != title:
                        slide_texts.append(t)
            elif sh.has_table:
                rows = []
                for row in sh.table.rows:
                    cells = [c.text.strip() for c in row.cells if c.text.strip()]
                    if cells:
                        rows.append(" | ".join(cells))
                if rows:
                    table_texts.append("\n".join(rows))

        slide_md = []
        slide_title = title or f"Слайд {idx}"
        slide_md.append(f"### {slide_title}")

        if slide_texts:
            slide_md.append("\n".join(f"- {t}" for t in slide_texts))
        if table_texts:
            slide_md.append("\n\nТаблица:\n" + "\n".join(table_texts))

        parts.append("\n".join(slide_md))

    return "\n\n".join(parts)


def extract_glossary_terms(full_text: str) -> List[str]:
    """Извлекает ключевые технические термины для глоссария темы."""
    candidates = set()
    # Английские термины от 3 символов
    en_matches = re.findall(r'\b[A-Za-z][A-Za-z0-9_-]{2,}\b', full_text)
    stop_en = {
        "the", "and", "for", "with", "from", "that", "this", "are", "you", "not",
        "can", "will", "all", "has", "have", "more", "one", "two", "use", "code",
        "example", "file", "data", "true", "false", "none", "print", "line", "test",
        "each", "into", "some", "only", "also", "then", "which", "part", "task"
    }
    for m in en_matches:
        low = m.lower()
        if low not in stop_en and len(low) > 2:
            candidates.add(low)

    # Русские доменные термины
    ru_terms = [
        "регуляризация", "переобучение", "недообучение", "нейросеть", "перцептрон",
        "градиентный спуск", "функция потерь", "оптимизатор", "эмбеддинги",
        "токенизация", "лемматизация", "стемминг", "векторизация", "веса",
        "матрица", "тензор", "массив", "фильтрация", "группировка", "агрегация",
        "сегментация", "классификация", "регрессия", "кластеризация"
    ]
    for rt in ru_terms:
        if rt in full_text.lower():
            candidates.add(rt)

    # Берем наиболее частотные/репрезентативные
    return sorted(list(candidates))[:12]


# Конфигурация маппинга 9 лекций
LECTURE_MAPPINGS = [
    {
        "week_number": 1,
        "topic_id": "week_01_tools_python",
        "folder": "Lecture 1. Programming Tools for Artificial Intelligence-20261113",
        "title": "Неделя 1: Инструменты программирования для ИИ и структуры данных",
        "topic_name": "Основы языка Python, интроспекция, числовые типы, множества (set) и словари (dict)",
        "initial_prompt": (
            "Привет! На первой лекции мы разобрали фундаментальные структуры данных Python. "
            "Почему для быстрого поиска элементов в AI-пайплайнах используют множества (set) и хеш-таблицы словарей (dict), "
            "а не стандартные списки (list), и какова временная сложность поиска в них?"
        ),
        "primary_glossary": ["python", "set", "dict", "hash table", "introspection", "tuple", "time complexity", "o(1)"],
    },
    {
        "week_number": 2,
        "topic_id": "week_02_files_api",
        "folder": "Lecture 2.-20261113",
        "title": "Неделя 2: Работа с файловыми структурами, форматами CSV, JSON, Excel и архивами",
        "topic_name": "Файловые операции pathlib/os, парсинг CSV, сериализация JSON, интеграция Excel и сжатие zipfile",
        "initial_prompt": (
            "Привет! На второй лекции мы изучили работу с файлами и форматами данных. "
            "В чем ключевое отличие потоковой обработки файла через генераторы от считывания всего файла в память, "
            "и почему при работе с внешними REST API критично валидировать JSON-ответы?"
        ),
        "primary_glossary": ["pathlib", "csv", "json", "excel", "openpyxl", "zipfile", "serialization", "streaming"],
    },
    {
        "week_number": 3,
        "topic_id": "week_03_numpy_tensors",
        "folder": "Lecture 3.-20261113",
        "title": "Неделя 3: Библиотека NumPy и тензорные вычисления",
        "topic_name": "Архитектура ndarray, непрерывные блоки памяти C-order, векторизация, broadcasting и обработка изображений",
        "initial_prompt": (
            "Привет! На третьей лекции мы перешли к библиотеке NumPy. "
            "За счет каких низкоуровневых механизмов памяти и архитектуры ndarray векторизованные операции "
            "работают быстрее стандартных циклов for, и как работает механизм broadcasting при выравнивании размерностей?"
        ),
        "primary_glossary": ["numpy", "ndarray", "broadcasting", "vectorization", "dtype", "shape", "strides", "matrix multiplication"],
    },
    {
        "week_number": 4,
        "topic_id": "week_04_pandas_data",
        "folder": "Lecture 4.-20261113",
        "title": "Неделя 4: Анализ табличных данных с библиотекой Pandas",
        "topic_name": "Структуры данных Series и DataFrame, индексация loc/iloc, фильтрация, очистка и инспекция датасетов",
        "initial_prompt": (
            "Привет! На четвертой лекции мы освоили основы Pandas. "
            "В чем заключается принципиальная разница между индексной выборкой loc и позиционной выборкой iloc, "
            "и почему векторная фильтрация через булевы маски предпочтительнее поэлементной итерации?"
        ),
        "primary_glossary": ["pandas", "dataframe", "series", "loc", "iloc", "boolean indexing", "data cleaning", "head"],
    },
    {
        "week_number": 5,
        "topic_id": "week_05_preprocessing_features",
        "folder": "Lecture 5.-20261113",
        "title": "Неделя 5: Агрегация, группировка данных и базовая визуализация в Pandas",
        "topic_name": "Паттерн Split-Apply-Combine, группировка groupby, агрегатные функции, слияние таблиц и визуализация распределений",
        "initial_prompt": (
            "Привет! На пятой неделе мы изучили группировку и агрегацию в Pandas. "
            "Как работает паттерн Split-Apply-Combine в методе groupby, и в каких случаях заполнение пропусков "
            "средним или медианой может сместить общую статистическую оценку выборки?"
        ),
        "primary_glossary": ["groupby", "aggregation", "split-apply-combine", "merge", "join", "missing values", "fillna", "box plot"],
    },
    {
        "week_number": 6,
        "topic_id": "week_06_nlp_text",
        "folder": "Lecture 6-20261113",
        "title": "Неделя 6: Обработка естественного языка (NLP) и анализ текстов",
        "topic_name": "Библиотеки NLTK/Spacy, токенизация, лемматизация, стемминг, TF-IDF, анализ тональности и суммаризация статей",
        "initial_prompt": (
            "Привет! На шестой лекции мы погрузились в обработку естественного языка (NLP). "
            "Чем лемматизация отличается от стемминга при подготовке текста к обучению моделей, "
            "и почему модель мешка слов (Bag-of-Words / TF-IDF) теряет контекст по сравнению с семантическими эмбеддингами?"
        ),
        "primary_glossary": ["nlp", "tokenization", "lemmatization", "stemming", "tf-idf", "nltk", "sentiment analysis", "wordnet"],
    },
    {
        "week_number": 7,
        "topic_id": "week_07_visualization",
        "folder": "Lecture 7-20261113",
        "title": "Неделя 7: Визуализация данных (Matplotlib, Seaborn, Plotly)",
        "topic_name": "Построение статических и интерактивных графиков, статистическая визуализация Seaborn, тепловые карты и 3D-графики",
        "initial_prompt": (
            "Привет! На седьмой лекции мы разобрали инструменты визуализации. "
            "Каковы преимущества статистических графиков Seaborn (например, pairplot или heatmap корреляций) "
            "перед базовым Matplotlib при первичном разведочном анализе данных (EDA)?"
        ),
        "primary_glossary": ["matplotlib", "seaborn", "plotly", "heatmap", "scatter plot", "eda", "histogram", "interactive charts"],
    },
    {
        "week_number": 8,
        "topic_id": "week_08_machine_learning",
        "folder": "Lecture 9-20261113",  # Folder 9 содержит "Introduction to Machine Learning"
        "title": "Неделя 8: Введение в классическое машинное обучение (ML)",
        "topic_name": "Парадигмы Supervised и Unsupervised Learning, разделение выборки train/test split, компромисс Bias-Variance, метрики оценки",
        "initial_prompt": (
            "Привет! На восьмой лекции мы изучили основы классического машинного обучения. "
            "В чем заключается компромисс между смещением (bias) и дисперсией (variance), "
            "и почему высокая точность (accuracy) на обучающей выборке часто сигнализирует о переобучении модели?"
        ),
        "primary_glossary": ["machine learning", "supervised learning", "unsupervised learning", "bias-variance tradeoff", "train test split", "overfitting", "decision tree", "accuracy"],
    },
    {
        "week_number": 9,
        "topic_id": "week_09_deep_learning",
        "folder": "Lecture 8-20261113",  # Folder 8 содержит "Neural Networks" (RU/EN pptx + ipynb)
        "title": "Неделя 9: Глубокое обучение и искусственные нейронные сети",
        "topic_name": "Искусственный нейрон, перцептрон, функции активации (ReLU, Sigmoid), обратное распространение ошибки, Dropout и регуляризация",
        "initial_prompt": (
            "Привет! На лекции мы разобрали глубокие нейронные сети и проблему переобучения. "
            "Каким именно математическим механизмом метод Dropout предотвращает ко-адаптацию нейронов во время обучения, "
            "и что происходит при слишком высокой вероятности отключения весов?"
        ),
        "primary_glossary": ["neural networks", "perceptron", "activation function", "backpropagation", "dropout", "co-adaptation", "underfitting", "regularization"],
    },
]


def convert_all():
    print("Запуск пакетной конвертации лекций в Markdown...")

    for item in LECTURE_MAPPINGS:
        week = item["week_number"]
        topic_id = item["topic_id"]
        folder_name = item["folder"]
        folder_path = os.path.join(BASE_DIR, folder_name)

        print(f"\nОбработка Недели {week}: {item['title']}...")
        if not os.path.exists(folder_path):
            print(f"  ВНИМАНИЕ: Папка {folder_path} не найдена!")
            continue

        files = sorted(os.listdir(folder_path))
        content_sections = []
        source_files = []

        # 1. Сначала обрабатываем ноутбуки .ipynb
        for fname in files:
            if fname.endswith(".ipynb") or fname.endswith(".ipynb_"):
                fpath = os.path.join(folder_path, fname)
                source_files.append(fname)
                print(f"  -> Парсинг ноутбука: {fname}")
                text = parse_ipynb(fpath)
                if text:
                    content_sections.append(f"## Материалы ноутбука: {fname}\n\n{text}")

        # 2. Обрабатываем презентации .pptx (приоритет русскоязычным или основным)
        for fname in files:
            if fname.endswith(".pptx"):
                # Если есть RU версия, отдаем ей приоритет
                if "_EN.pptx" in fname and any("_RU.pptx" in x for x in files):
                    continue
                fpath = os.path.join(folder_path, fname)
                source_files.append(fname)
                print(f"  -> Парсинг слайдов презентации: {fname}")
                slides_text = parse_pptx_slides(fpath)
                if slides_text:
                    content_sections.append(f"## Слайды презентации: {fname}\n\n{slides_text}")

        full_body = "\n\n---\n\n".join(content_sections)

        # Извлекаем расширенный глоссарий из реального текста
        extracted_glossary = extract_glossary_terms(full_body)
        combined_glossary = sorted(list(set(item["primary_glossary"] + extracted_glossary)))

        # Формируем YAML Frontmatter
        frontmatter = f"""---
week_number: {week}
topic_id: "{topic_id}"
title: "{item['title']}"
topic_name: "{item['topic_name']}"
initial_prompt: "{item['initial_prompt']}"
source_files:
{chr(10).join(f'  - "{sf}"' for sf in source_files)}
glossary:
{chr(10).join(f'  - "{g}"' for g in combined_glossary)}
---

# {item['title']}

> **Официальный силлабус дисциплины:** Programming for AI (2026–2027, Astana IT University)
> **Тематический фокус:** {item['topic_name']}

"""
        final_doc = frontmatter + full_body
        out_filename = f"{topic_id}.md"
        out_path = os.path.join(OUTPUT_DIR, out_filename)

        with open(out_path, "w", encoding="utf-8") as out_f:
            out_f.write(final_doc)

        file_size_kb = len(final_doc.encode("utf-8")) / 1024
        print(f"  [OK] Создан файл: {out_path} ({file_size_kb:.1f} КБ, терминов: {len(combined_glossary)})")

    print("\nПакетная конвертация всех 9 лекций успешно завершена!")


if __name__ == "__main__":
    convert_all()

