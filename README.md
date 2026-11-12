# Themis Project v2.0

> **Inclusive Academic Discrepancy Audit & Socratic Scaffolding Engine**
> Инклюзивная система диагностического аудита академической недооцененности (Undergrading) и сократического скаффолдинга.

---

## 🎯 Ключевые принципы системы

1. **Принцип «Цифрового пандуса» (Universal Design for Learning / Optional Affordance):**
   - Участие в сократическом диалоге добровольно.
   - Студенты, выбравшие очный ответ или решившие не пользоваться ботом (`OPTED_OUT`), сохраняют свою очную оценку без изменений.

2. **Некредитный диагностический статус (Non-Credit Diagnostic Signal):**
   - Индекс глубины ИИ ($S_{\text{depth}}$) не является зачетным баллом и не идет в ведомость автоматически.
   - Его роль — выявить скрытую недооценку знаний (Undergrading) и предоставить преподавателю доказательную аналитическую карточку (цитаты, концепты, вероятности SOLO).

3. **Односторонняя положительная ректификация (Zero Downward Penalty):**
   - $\Delta_i^+ = \max(0.0, S_{\text{depth}, i} - G_{\text{prof}, i})$.
   - Занижение оценки преподавателя категорически исключено ($G_{\text{prof}} \ge S_{\text{depth}} \implies \Delta_i^+ = 0.0$, статус `NORMAL`).

---

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Запуск приложения (FastAPI + Frontend)
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Интерфейс доступен в браузере по адресу: [http://localhost:8000](http://localhost:8000)

### 3. Запуск юнит- и интеграционных тестов
```bash
python -m pytest tests/ -v
```

---

## 📁 Структура проекта

```
themis-project/
├── requirements.txt
├── .env.example
├── README.md
├── backend/
│   ├── __init__.py
│   ├── config.py             # Настройки приложения (Pydantic BaseSettings)
│   ├── models_schemas.py     # Pydantic v2 схемы (Evidence-First JSON и API контракты)
│   ├── math_engine.py        # Детерминированное психометрическое ядро ThemisMathEngine
│   ├── rag_service.py        # RAG-сервис по материалам занятия 05 (Dropout & Regularization)
│   ├── llm_service.py        # Qwen3.5 LLM клиент + детерминированный Demo Mock fallback
│   ├── seed_data.py          # Каноническая когорта из 28 студентов (prog_ai_2026)
│   └── main.py               # FastAPI приложение и эндпоинты
├── frontend/
│   └── index.html            # SPA: Student Socratic Ramp + Professor Audit Console (Tailwind + Chart.js)
└── tests/
    └── test_themis_engine.py # Полный набор тестов психометрического ядра и API
```

---

## 🔬 Математические инварианты (Канонический Use Case)

- **Прогрессивная сократическая свёртка:** $\mathbf{w} = [0.0556, 0.1320, 0.8124]$
- **Студент К. (`stud_aai_042`):**
  - $\mathbf{P}_1 = [0.90, 0.10, 0.00]$, $\mathbf{P}_2 = [0.00, 0.85, 0.15]$, $\mathbf{P}_3 = [0.00, 0.05, 0.95]$
  - $\mathbf{P}_{\text{agg}} = [0.05, 0.15, 0.80]$
  - $\mathbb{E}[D^2] = 7.85$
  - $S_{\text{SOLO}} = 93.5$ (база 92.53 + $B_{\text{init}} = 1.0$)
  - $K_{\text{density}} = 1.0$, $C_{\text{sample}} = 1.0 \implies S_{\text{depth}} = 93.5$
  - $G_{\text{prof}} = 70.0 \implies \Delta^+ = +23.5$
  - Когорта (12 завершенных сессий): $\text{Median}_{\Delta} = +2.5$, $\text{MAD} = 3.8$, $\sigma_{\text{rob}} = 5.6339$
  - Робастный Z-score: $Z^+ = \frac{23.5 - 2.5}{5.6339} = \mathbf{+3.73\sigma}$ (`HIGH_DISCREPANCY`, фиолетовая зона)

