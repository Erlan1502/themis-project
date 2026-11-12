"""
rag_service.py

Локальный RAG-сервис (Retrieval-Augmented Generation) для системы Themis Project.
Интегрирует официальный силлабус дисциплины:
"Программирование для ИИ" (PAI, 2026-2027, Astana IT University)
Преподаватель: Белощицкая Светлана, доктор технических наук, профессор.

Содержит полную структуру 10 учебных недель с темами, чанками и глоссарием.
"""

from typing import List, Dict, Any, Optional
import math
import re


SYLLABUS_WEEKS: List[Dict[str, Any]] = [
    {
        "week_number": 1,
        "topic_id": "week_01_tools_python",
        "title": "Неделя 1: Инструменты программирования для ИИ",
        "topic_name": "Инструменты программирования для ИИ: Python, Colab, Git и среды разработки",
        "initial_prompt": (
            "Привет! На первой неделе мы знакомимся с инструментами разработчика ИИ. "
            "Как ты думаешь: почему в реальных проектах машинного обучения принято разбивать код на модули и классы, "
            "а не хранить весь пайплайн в одном длинном блокноте Jupyter Notebook?"
        ),
        "glossary": ["python", "jupyter notebook", "google colab", "git", "github", "oop", "classes", "pep8"],
        "chunks": [
            {
                "id": "w1_c1",
                "title": "Среды разработки и версионирование в AI",
                "content": (
                    "Инструменты программирования для ИИ включают Python, Jupyter Notebook, Google Colab, PyCharm, VS Code. "
                    "Использование Git и GitHub необходимо для контроля версий и командной разработки. "
                    "Платформы GPU/TPU (Google Colab, Kaggle, AWS, Azure) ускоряют обучение ресурсоемких моделей."
                ),
            },
            {
                "id": "w1_c2",
                "title": "Модульность и основы ООП в Python",
                "content": (
                    "Основы языка: переменные, типы данных, условия, циклы, функции, модули и пакеты. "
                    "Структуры данных: списки, словари, множества, кортежи. "
                    "Принципы объектно-ориентированного программирования (ООП): классы, объекты, наследование и инкапсуляция "
                    "позволяют создавать переиспользуемые компоненты для моделей машинного обучения."
                ),
            },
        ],
    },
    {
        "week_number": 2,
        "topic_id": "week_02_files_api",
        "title": "Неделя 2: Работа с файлами и REST API",
        "topic_name": "Работа с файлами, внешними данными и REST API: pathlib, CSV, JSON, Requests",
        "initial_prompt": (
            "Привет! На этой неделе мы разбираем работу с файлами и внешними API. "
            "В чем заключается главная опасность считывания 10-гигабайтного CSV-файла через стандартный f.read() "
            "и как потоковая обработка или модуль pathlib с генераторами решают эту проблему?"
        ),
        "glossary": ["pathlib", "csv", "json", "rest api", "requests", "exception handling", "streaming", "json parsing"],
        "chunks": [
            {
                "id": "w2_c1",
                "title": "Файловые операции и форматы CSV/JSON",
                "content": (
                    "Работа с файловой системой средствами os и pathlib. Создание, чтение, запись, копирование и перемещение файлов. "
                    "Форматы хранения данных: TXT, CSV, JSON. Построчная обработка больших массивов данных для экономии ОЗУ."
                ),
            },
            {
                "id": "w2_c2",
                "title": "Интеграция с REST API и обработка ошибок",
                "content": (
                    "Получение внешних данных с использованием библиотеки Requests. Основы взаимодействия с REST API "
                    "и парсинг структурированных JSON-ответов. Обработка сетевых ошибок, HTTP-статусов и исключений (try/except)."
                ),
            },
        ],
    },
    {
        "week_number": 3,
        "topic_id": "week_03_numpy_tensors",
        "title": "Неделя 3: Библиотека NumPy и тензорные вычисления",
        "topic_name": "Библиотека NumPy и основы тензорных вычислений для задач искусственного интеллекта",
        "initial_prompt": (
            "Привет! На третьей неделе мы переходим к тензорным вычислениям. "
            "За счет каких низкоуровневых механизмов памяти векторизованные операции в NumPy и механизм broadcasting "
            "работают значительно быстрее стандартных циклов for в Python?"
        ),
        "glossary": ["numpy", "ndarray", "broadcasting", "vectorization", "tensors", "matrix multiplication", "strides", "gpu acceleration"],
        "chunks": [
            {
                "id": "w3_c1",
                "title": "Архитектура массивов ndarray и векторизация",
                "content": (
                    "Назначение библиотеки NumPy. Создание массивов ndarray, типы данных (dtype), размерность и форма (shape). "
                    "Индексация, срезы и изменение формы массивов. Векторизованные операции над непрерывными блоками памяти C-order."
                ),
            },
            {
                "id": "w3_c2",
                "title": "Broadcasting, матричные операции и тензоры",
                "content": (
                    "Основные математические и статистические операции. Матричное умножение и линейная алгебра. "
                    "Механизм транслирования размерностей (broadcasting). Понятие тензора. Сравнение NumPy arrays с PyTorch/TensorFlow tensors "
                    "и базовый перенос вычислений на GPU."
                ),
            },
        ],
    },
    {
        "week_number": 4,
        "topic_id": "week_04_pandas_data",
        "title": "Неделя 4: Анализ данных в Pandas",
        "topic_name": "Библиотека Pandas: загрузка, первичный анализ, группировка и очистка наборов данных",
        "initial_prompt": (
            "Привет! На лекции по Pandas мы изучали обработку табличных данных. "
            "В какой ситуации объединение таблиц через merge() с параметром how='inner' может привести "
            "к скрытому искажению и потере репрезентативности выборки для обучения модели?"
        ),
        "glossary": ["pandas", "dataframe", "series", "groupby", "merge", "join", "missing values", "eda", "concat"],
        "chunks": [
            {
                "id": "w4_c1",
                "title": "Структуры данных Series и DataFrame",
                "content": (
                    "Применение Pandas в AI-проектах. Структуры Series и DataFrame. Загрузка из CSV, Excel, JSON. "
                    "Первичный разведочный анализ данных (EDA): методы head(), info(), describe(). Фильтрация и сортировка."
                ),
            },
            {
                "id": "w4_c2",
                "title": "Агрегация, пропуски и слияние данных",
                "content": (
                    "Работа с пропущенными (NaN) и дублирующимися значениями. Группировка и агрегирование данных с помощью groupby(). "
                    "Объединение таблиц: merge, join, concat. Подготовка структурированных таблиц для последующей обработки в Scikit-learn."
                ),
            },
        ],
    },
    {
        "week_number": 5,
        "topic_id": "week_05_preprocessing_features",
        "title": "Неделя 5: Предобработка данных в Scikit-learn",
        "topic_name": "Предварительная обработка данных и конструирование признаков: Pandas и Scikit-learn",
        "initial_prompt": (
            "Привет! На пятой неделе мы разбираем подготовку признаков. "
            "Почему расчет среднего и дисперсии для StandardScaler ДО разбиения выборки на train и test "
            "приводит к утечке данных (data leakage) и иллюзии высокого качества модели?"
        ),
        "glossary": ["data leakage", "standardscaler", "minmaxscaler", "labelencoder", "onehotencoder", "pipeline", "train_test_split", "feature engineering"],
        "chunks": [
            {
                "id": "w5_c1",
                "title": "Масштабирование и кодирование признаков",
                "content": (
                    "Основные этапы подготовки данных для моделей ИИ. Поиск и обработка аномальных значений. "
                    "Масштабирование числовых признаков: StandardScaler, MinMaxScaler. "
                    "Кодирование категориальных признаков: LabelEncoder, OneHotEncoder."
                ),
            },
            {
                "id": "w5_c2",
                "title": "Предотвращение утечки данных и Scikit-learn Pipeline",
                "content": (
                    "Разделение данных на обучающую и тестовую выборки с помощью train_test_split. Несбалансированные выборки. "
                    "Конструирование признаков (feature engineering). Использование Scikit-learn Pipeline для объединения шагов "
                    "трансформации и предотвращения утечки данных (data leakage)."
                ),
            },
        ],
    },
    {
        "week_number": 6,
        "topic_id": "week_06_nlp_text",
        "title": "Неделя 6: Обработка текстов и основы NLP",
        "topic_name": "Библиотеки для обработки текстовых данных и введение в NLP: NLTK, spaCy, Scikit-learn",
        "initial_prompt": (
            "Привет! На лекции по NLP мы сравнили частотные и плотные представления текста. "
            "Почему разреженная матрица TF-IDF теряет синтаксический контекст и семантическую близость слов-синонимов, "
            "и каким образом векторные эмбеддинги решают этот недостаток?"
        ),
        "glossary": ["nlp", "tokenization", "lemmatization", "stemming", "bag of words", "tf-idf", "embeddings", "spacy", "nltk"],
        "chunks": [
            {
                "id": "w6_c1",
                "title": "Токенизация, очистка и морфологический анализ",
                "content": (
                    "Представление текстовых данных в Python. Возможности библиотек NLTK и spaCy. "
                    "Очистка текста, удаление стоп-слов, токенизация, стемминг и лемматизация. "
                    "Построение текстового пайплайна для задач классификации."
                ),
            },
            {
                "id": "w6_c2",
                "title": "Векторизация текстов: TF-IDF и Word Embeddings",
                "content": (
                    "Представление текста с помощью Bag of Words и TF-IDF средствами Scikit-learn. "
                    "Введение в векторные представления слов и текстов (word embeddings). "
                    "Плотные семантические пространства и семантическое сходство."
                ),
            },
        ],
    },
    {
        "week_number": 7,
        "topic_id": "week_07_visualization",
        "title": "Неделя 7: Визуализация данных и результатов моделей",
        "topic_name": "Библиотеки визуализации данных и результатов моделей: Matplotlib, Seaborn, TensorBoard",
        "initial_prompt": (
            "Привет! На этой неделе мы изучаем визуальный анализ моделей. "
            "Представь, что в задаче бинарной классификации классы сильно несбалансированы (99 к 1). "
            "Почему график ROC-AUC может выглядеть оптимистично (0.95), тогда как Precision-Recall Curve вскроет серьезные ошибки?"
        ),
        "glossary": ["matplotlib", "seaborn", "confusion matrix", "roc curve", "pr curve", "tensorboard", "heatmap", "correlation"],
        "chunks": [
            {
                "id": "w7_c1",
                "title": "Статистическая визуализация Matplotlib и Seaborn",
                "content": (
                    "Построение линейных графиков, гистограмм, диаграмм рассеяния (scatter plots), boxplot. "
                    "Библиотека Seaborn для статистического анализа. Визуальный анализ распределений и корреляционных матриц (heatmaps)."
                ),
            },
            {
                "id": "w7_c2",
                "title": "Кривые обучения, метрики и TensorBoard",
                "content": (
                    "Визуализация результатов классификации: матрицы ошибок (confusion matrix), ROC-кривые, Precision-Recall кривые. "
                    "Отображение метрик и результатов экспериментов. Мониторинг процесса обучения в TensorBoard."
                ),
            },
        ],
    },
    {
        "week_number": 8,
        "topic_id": "week_08_machine_learning",
        "title": "Неделя 8: Машинное обучение в Scikit-learn",
        "topic_name": "Библиотека Scikit-learn: построение, обучение и валидация моделей классификации и регрессии",
        "initial_prompt": (
            "Привет! На восьмой неделе мы строим классические модели ML. "
            "Объясни: как компромисс смещения и дисперсии (bias-variance tradeoff) проявляется при увеличении глубины дерева решений, "
            "и почему ансамблевые методы (например, Random Forest) способны уменьшать дисперсию без роста смещения?"
        ),
        "glossary": ["scikit-learn", "classification", "regression", "cross-validation", "bias-variance tradeoff", "f1-score", "gridsearchcv"],
        "chunks": [
            {
                "id": "w8_c1",
                "title": "Архитектура Scikit-learn и базовые модели",
                "content": (
                    "Единый интерфейс работы с моделями: fit(), predict(), transform(). "
                    "Реализация базовых алгоритмов классификации: Logistic Regression, Decision Trees, KNN, Random Forest. "
                    "Кластеризация: K-Means. Метрики качества: accuracy, precision, recall, F1-score, ROC-AUC, MAE, MSE, R2."
                ),
            },
            {
                "id": "w8_c2",
                "title": "Кросс-валидация и оптимизация гиперпараметров",
                "content": (
                    "Разделение на train/test и K-Fold кросс-валидация. Настройка гиперпараметров с помощью GridSearchCV и RandomizedSearchCV. "
                    "Сохранение и загрузка обученных моделей (joblib/pickle)."
                ),
            },
        ],
    },
    {
        "week_number": 9,
        "topic_id": "week_09_deep_learning",
        "title": "Неделя 9: Глубокое обучение и динамика Dropout",
        "topic_name": "Введение в глубокое обучение: PyTorch, функции активации, MLP и динамика Dropout",
        "initial_prompt": (
            "Привет! На лекции мы разобрали проблему переобучения в глубоких сетях. "
            "Подумай: почему обычное увеличение объема данных не всегда спасает от ко-адаптации признаков?"
        ),
        "glossary": [
            "pytorch", "tensors", "mlp", "activation functions", "relu", "backpropagation", 
            "dropout", "co-adaptation", "model capacity", "underfitting", "overfitting", "inverted dropout"
        ],
        "chunks": [
            {
                "id": "w9_c1",
                "title": "Основы глубоких сетей и градиентный спуск",
                "content": (
                    "Понятия нейронных сетей: нейрон, слой, функции активации (ReLU, Sigmoid, Tanh), loss function, optimizer (SGD, Adam). "
                    "Создание тензоров, многослойный перцептрон (MLP). Forward pass, расчет потерь, backpropagation, обучение эпохами и batch size."
                ),
            },
            {
                "id": "w9_c2",
                "title": "Ко-адаптация весов и механизм регуляризации Dropout",
                "content": (
                    "В глубоких сетях возникает ко-адаптация (co-adaptation) весов. "
                    "Алгоритм Dropout (Srivastava et al., 2014) случайно отключает нейроны с вероятностью p во время обучения. "
                    "Inverted Dropout масштабирует веса на 1/(1-p). Экстремальный Dropout (p >= 0.8) вызывает потерю емкости сети (underfitting)."
                ),
            },
        ],
    },
    {
        "week_number": 10,
        "topic_id": "week_10_capstone_project",
        "title": "Неделя 10: Интеграция мини-проекта ИИ",
        "topic_name": "Разработка мини-проекта в области искусственного интеллекта: интеграция данных, библиотек и моделей",
        "initial_prompt": (
            "Привет! Десятая неделя посвящена интеграции прикладного ИИ-проекта. "
            "С какими главными вызовами ты столкнешься при переносе обученной модели из исследовательского блокнота "
            "в продакшен-сервис с REST API и обеспечением масштабируемости инференса?"
        ),
        "glossary": ["end-to-end pipeline", "model deployment", "rest api", "github", "inference optimization", "monitoring", "eda"],
        "chunks": [
            {
                "id": "w10_c1",
                "title": "Сквозной пайплайн проекта ИИ",
                "content": (
                    "Выбор прикладной задачи и датасета. Загрузка и EDA (Pandas, NumPy, Seaborn). "
                    "Очистка и пайплайн предобработки. Обучение и валидация моделей (Scikit-learn / PyTorch). "
                    "Сравнение подходов и конфигураций моделей."
                ),
            },
            {
                "id": "w10_c2",
                "title": "Архитектура поставки и демонстрация результатов",
                "content": (
                    "Организация программного проекта и размещение исходного кода в GitHub. "
                    "Упаковка модели в REST API (FastAPI) и подготовка краткого отчета и презентации для итоговой защиты проекта."
                ),
            },
        ],
    },
]

# Быстрый индекс тем по topic_id
WEEKS_BY_ID: Dict[str, Dict[str, Any]] = {w["topic_id"]: w for w in SYLLABUS_WEEKS}

# Алиас для канонической темы из спецификации (topic_05_regularization указывает на Неделю 9)
WEEKS_BY_ID["topic_05_regularization"] = WEEKS_BY_ID["week_09_deep_learning"]


class RAGService:
    """Сервис поиска и извлечения контекста силлабуса PAI 2026 для сократического бота."""

    def __init__(self):
        self._weeks = SYLLABUS_WEEKS
        self._map = WEEKS_BY_ID

    def get_all_weeks(self) -> List[Dict[str, Any]]:
        """Возвращает список всех 10 недель для селектора на фронтенде."""
        return [
            {
                "week_number": w["week_number"],
                "topic_id": w["topic_id"],
                "title": w["title"],
                "topic_name": w["topic_name"],
                "initial_prompt": w["initial_prompt"],
                "glossary": w["glossary"],
            }
            for w in self._weeks
        ]

    def get_topic_data(self, topic_id: str) -> Optional[Dict[str, Any]]:
        return self._map.get(topic_id) or self._map.get("week_09_deep_learning")

    def get_initial_prompt(self, topic_id: str) -> str:
        data = self.get_topic_data(topic_id)
        if data:
            return data["initial_prompt"]
        return "Привет! Расскажи своими словами ключевые концепты сегодняшней темы лекции."

    def get_glossary(self, topic_id: str) -> List[str]:
        data = self.get_topic_data(topic_id)
        if data:
            return data["glossary"]
        return []

    def register_dynamic_week(
        self,
        topic_id: str,
        week_number: int,
        title: str,
        topic_name: str,
        initial_prompt: str,
        glossary: List[str],
        slides_count: int = 0
    ) -> Dict[str, Any]:
        """Динамическая регистрация загруженной лекции в силлабус курса."""
        week_data = {
            "week_number": week_number,
            "topic_id": topic_id,
            "title": title,
            "topic_name": topic_name,
            "initial_prompt": initial_prompt,
            "glossary": glossary,
            "chunks": [],
            "slides_count": slides_count
        }
        existing_idx = next((i for i, w in enumerate(self._weeks) if w["topic_id"] == topic_id or w["week_number"] == week_number), None)
        if existing_idx is not None:
            self._weeks[existing_idx] = week_data
        else:
            self._weeks.append(week_data)
            self._weeks.sort(key=lambda x: x["week_number"])

        self._map[topic_id] = week_data
        return week_data

    def retrieve_chunks(self, query: str, topic_id: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Поиск релевантных фрагментов для контекстного заземления:
        Сначала опрашивает HNSW векторную базу ChromaDB по слайдам лекции.
        При отсутствии загруженных слайдов использует текстовые чанки силлабуса.
        """
        try:
            from backend.vector_store import vector_store
            vector_results = vector_store.search_relevant_slides(query=query, topic_id=topic_id, top_k=top_k)
            if vector_results:
                return [
                    {
                        "id": f"slide_{r['metadata'].get('slide_number', 1)}",
                        "title": r['metadata'].get('title', 'Слайд лекции'),
                        "content": r['text']
                    }
                    for r in vector_results
                ]
        except Exception:
            pass

        topic = self.get_topic_data(topic_id)
        if not topic:
            return []

        chunks = topic.get("chunks", [])
        if not chunks:
            return []

        query_words = set(re.findall(r"\w+", query.lower()))
        scored_chunks = []
        for chunk in chunks:
            text = (chunk["title"] + " " + chunk["content"]).lower()
            chunk_words = set(re.findall(r"\w+", text))
            intersection = query_words.intersection(chunk_words)
            score = len(intersection) / math.sqrt(max(1, len(chunk_words)))
            scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored_chunks[:top_k]]


# Синглтон сервиса
rag_service = RAGService()
