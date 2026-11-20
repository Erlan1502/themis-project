Ниже представлен полный финальный архитектурный, математический и UX-аудит **Themis Project (v2.0)** по результатам построчной сверки `@PROJECT_STATE.md` и `@PLAN.md` с фактическим исходным кодом в `backend/` и `frontend/`.

> **Режим работы:** Сейчас активен **Plan Mode**, поэтому исходный код не модифицировался, а файл `c:\Users\erlan\Desktop\Themis\themis-project\UPDATED_PLAN.md` еще не записан на диск. Ознакомьтесь с полным отчетом и проектом `@UPDATED_PLAN.md` ниже — после вашего подтверждения переключите режим (**toggle to Act mode**), и я сохраню этот документ в корень репозитория.

---

# АНАЛИТИЧЕСКИЙ РАЗБОР ПО НАПРАВЛЕНИЯМ АУДИТА (1–3)

## Направление 1. Сквозной аудит `backend/` (стыки модулей и скрытые баги)

### 1.1. Рассинхрон состояния в памяти (`db_records`, `RAGService._map`) и SQLite при работе Web SPA, TMA и SSE
В SQLite (`backend/database.py:135, 281`) таблица `student_audits` переведена на составной первичный ключ `(student_id, course_id, topic_id)`, однако **оперативное ядро в `backend/main.py` осталось плоским**:

1. **Коллизия ключа `db_records` (`backend/main.py:150, 198–227, 804, 884, 1080`):**
   - `db_records: Dict[str, StudentAuditRecord] = {}` индексируется **только по `student_id`**, а не по `(student_id, course_id, topic_id)`.
   - При старте/шаге сессии на новой неделе или новом курсе (`main.py:804, 884, 1080`) `db_records.get(student_id)` возвращает запись студента от **Недели 9** (`topic_id="week_09_deep_learning"`) и перезаписывает в ней `turns_count`, `extraction` и `ai_depth_score`, не меняя `topic_id`. В итоге `GET /api/v1/audit/dashboard?topic_id=week_01_tools_python` (`main.py:1372–1376`) возвращает **0 студентов**, а аудит Недели 9 оказывается затерт данными Недели 1.
   - При перезапуске сервера (`reset_database(load_from_db_if_exists=True)`, `main.py:226`) цикл `db_records[row["student_id"]] = rec` оставляет в памяти только последнюю строку из SQLite для каждого `student_id`.
   - Во всех точках пересчета, кроме `get_audit_dashboard` (`main.py:227, 301, 986, 1352, 1608, 1729, 1796, 1956`, `tma_auth.py:301`), вызывается `engine.compute_cohort_discrepancy(list(db_records.values()))`, смешивая дельты **всех курсов и недель** в одну выборку.
   - Эндпоинт `GET /api/v1/students` (`main.py:628`) принимает только `group_id` и игнорирует `course_id` и `topic_id`, хотя `frontend/index.html:1492` передает их в query-строке.
2. **Падение QR-привязки с `sqlite3.IntegrityError` после гостевого входа в TMA (`backend/database.py:208, 828–848` + `backend/tma_auth.py:240–276`):**
   - В `student_identities` колонка `telegram_id` имеет ограничение `UNIQUE` (`database.py:208`).
   - Если студент или член жюри сначала открыл бота/Mini App напрямую (сработал Zero-Friction гостевой вход `get_or_create_telegram_student`, создавший профиль `stud_tg_<id>` с этим `telegram_id`), а затем отсканировал персональный QR-код привязки студента (`bind_<hex>`), вызов `link_telegram_identity` (`telegram_bot.py:294` -> `database.py:836`) выполняет `UPDATE student_identities SET telegram_id = ? WHERE student_id = 'stud_aai_042'` и **падает с `IntegrityError: UNIQUE constraint failed: student_identities.telegram_id`**, оставляя в `db_records` и БД осиротевшего клона `stud_tg_<id>`.
3. **Рассинхрон начальных оценок `G_prof` между `database.py` и `seed_data.py`:**
   - В `backend/database.py:395–401` (`_init_default_student_identities`) зашиты оценки `stud_aai_001: 72.0, stud_aai_002: 74.0, ..., stud_aai_015: 73.0`, тогда как в `backend/seed_data.py:146–229` у тех же студентов оценки `85.0, 82.0, ..., 88.0`. При fallback к `student_identities` (`main.py:806, 1849, 1961`) всплывают чужие оценки.
4. **Пробелы в SSE-синхронизации (`/api/v1/events/audit-stream`):**
   - В `run_background_audit` (`main.py:276–333`), если внутри фоновой задачи случается исключение, `except Exception` логирует ошибку, но оставляет `rec.session_status = "AUDITING"` в памяти и SQLite навечно — спиннер у студента никогда не снимается.
   - Событие `dialog_turn_sync` (`main.py:1016, 1237`) не содержит `course_id`, `topic_id` и `sources`.
   - Эндпоинты `POST /api/v1/audit/decision`, `POST /api/v1/student/{id}/reset`, `POST /api/v1/student/{id}/restore_canonical`, `POST /api/v1/demo/reset` и `POST /api/v1/session/opt-out` **не публикуют событий в `audit_broadcaster`**, поэтому открытый на проекторе дашборд преподавателя и мобильный TMA не обновляются реактивно при отказе от сессии, сбросе или утверждении нового балла.
   - В таблице `sessions` (`database.py:955`) колонка `status` всегда остается `'ACTIVE'` и нигде не обновляется до `'COMPLETED'` / `'OPTED_OUT'`.
5. **Коллизия тем разных курсов в `RAGService` (`backend/rag_service.py:375–380, 422–440, 479`):**
   - `self._map` хранит темы по ключу `topic_id` без `course_id`, а `load_from_db()` запрашивает `SELECT term FROM lecture_glossary WHERE topic_id = ?` без `AND course_id = ?`.

### 1.2. Аудит `backend/vector_store.py` (строки 48–82, 178): риск `InvalidDimensionException`
- Существующая коллекция `themis_lecture_slides` в `data/chroma_db` создана с размерностью **1024** (`BAAI/bge-m3`).
- При сбое инициализации `SentenceTransformer("BAAI/bge-m3")` (в том числе при обрыве связи с `huggingface.co`, так как **не делается повторная попытка с `local_files_only=True`** для чтения уже скачанных весов из локального кэша!) строка `60` загружает `cointegrated/rubert-tiny2` (**312-dim**), а строки `73–78` при полном отказе возвращают MD5-вектор длины **384** (`vec = [0.0] * 384`).
- Любой `upsert` в `add_slides` (`vector_store.py:178`, без `try/except`) на 1024-мерной коллекции немедленно падает с `chromadb.errors.InvalidDimensionException`, роняя загрузку лекции на демо со статусом `FAILED`, а `search_relevant_slides` тихо деградирует в пустой ответ. Кроме того, `/api/v1/system/health` (`main.py:1683–1688`) всегда рапортует `status="ready", dimension=1024, model="BAAI/bge-m3"`, скрывая деградацию.

### 1.3. Устойчивость `llm_service.py` и `ingestion_service.py` на живом демо
1. **Зависание до 90 секунд в `backend/llm_service.py` (`строки 43, 61, 166–181`):**
   - Клиент `AsyncOpenAI` создается с `timeout=30.0` и дефолтным `max_retries=2`. При «черной дыре» Wi-Fi на площадке или `429/503` от внешнего API один шаг диалога зависнет до **90 секунд** прежде чем сработает fallback на `_mock_socratic_reply_stream`.
   - Отсутствует **Circuit Breaker**: если сеть упала на Шаге 1, система прождет таймаут на Шаге 1, затем снова на Шаге 2, снова на Шаге 3 и еще раз на `extract_audit_evidence`.
   - **Баг «склейки» при обрыве стрима (`строки 173–181`):** если реальная LLM успела выдать половину ответа в `generate_socratic_reply_stream`, а затем соединение оборвалось, блок `except` дописывает в тот же бабл **полный mock-ответ с начала**, создавая сломанный текст.
   - **Утечка сценария Студента К. на чужие темы (`строка 329`):** в `_mock_audit_extraction` условие `if "80%" in full_text or "underfitting" in full_text.lower() or "емкост" in full_text.lower():` не проверяет `topic_id`! Более того, `ingestion_service.py:311` сам генерирует демо-реплику Шага 3 со словами *«потере емкости модели»*, что в оффлайн/fallback режиме подставляет цитаты про **Dropout** в карточку любого загруженного курса!
2. **Уязвимости `backend/ingestion_service.py` и `backend/markdown_converter.py`:**
   - В `main.py:440, 498` и `markdown_converter.py:300–303` разрешены старые бинарные форматы `.ppt` и `.doc`, которые не поддерживаются `python-pptx` / `python-docx` и гарантированно падают с `BadZipFile / PackageNotFoundError`.
   - В `ingestion_service.py:274–278` генерация `clean_slug = re.sub(r'[^a-zA-Z0-9]', '_', ...)` удаляет всю кириллицу: две русскоязычные лекции на одной неделе («Трансформеры» и «Ансамбли») получают одинаковый `topic_id = week_11_topic_11` и затирают друг друга.
   - В `markdown_converter.py:322–366` `convert_zip` не ограничивает размер распаковки, не проверяет Zip-Slip (`..` в путях архива) и не удаляет временную папку `tempfile.mkdtemp`. Нет лимита размера загружаемого файла в `main.py:449`.

---

## Направление 2. Стресс-аудит математического ядра (`math_engine.py`, `seed_data.py`, `similarity_service.py`)

### 2.1. Пограничный случай: `G_prof > S_depth` у большинства студентов (`Median_Delta < 0`)
Разберем строго математически поведение `ThemisMathEngine.compute_cohort_discrepancy` (`backend/math_engine.py:212–267`) и графика `renderGaussianChart` (`frontend/index.html:2205–2288`), когда очные оценки большинства группы выше оценок ИИ (например, `raw_median = -12.0`, `robust_sigma = 4.0`):

1. **Искажение $Z^+$:** В строке `241` вычисляется `z_val = (r.rectified_delta - center_median) / robust_sigma`. Поскольку `rectified_delta` усечена снизу нулем ($\Delta^+ \ge 0$), а `center_median = -12.0 < 0`, вычитание отрицательной медианы добавляет ко всем студентам с любой минимальной положительной дельтой фиктивный сдвиг $+3.0\sigma$! Студент со случайным шумом $\Delta^+ = +0.5$ балла ($G_{\text{prof}}=80.0, S_{\text{depth}}=80.5$) получает **`z_score = +3.12σ`**, а студент с $\Delta^+ = +10.0$ получает `+5.50σ` при статусе `WATCHLIST` (противоречие с легендой `+1σ..+2σ`).
2. **Разрушение порогов и графика преподавателя:**
   - Пороги `sigma_thresholds` (`строки 263–265`) становятся **отрицательными или нулевыми**: `plus_1_sigma = -8.0`, `plus_2_sigma = -4.0`, `plus_3_sigma = 0.0` (а при `median = -18.0` даже `+3σ = -6.0`!).
   - На графике (`frontend/index.html:2222, 2241, 2368`) ось X начинается с `min: -4`, а все точки студентов откладываются по `x = rectified_delta >= 0`. В результате купол Гаусса уезжает за левый край холста, линии `+1σ` и `+2σ` исчезают, все студенты с $\Delta^+ = 0$ оказываются правее линии `+3σ`, а в плашках легенды под графиком выводятся абсурдные отрицательные пороги для неотрицательной величины $\Delta^+$.
3. **КРИТИЧЕСКАЯ СКРЫТАЯ МИНА (`seed_data.py:160–186` + `main.py:224–225`):**
   Этот пограничный случай **уже взрывается прямо сейчас при обычном перезапуске сервера!**
   - В `seed_data.py:160–186` у 11 фоновых студентов (`stud_aai_001`..`stud_aai_011`) целевой `ai_depth_score` (`75.4..84.2`) задан вручную, но внутри `extraction` у всех 11 зашит одинаковый шаблон `turns_probabilities=[(0.7,0.3,0.0), (0.2,0.6,0.2), (0.1,0.4,0.5)]` и `mastered_concepts=["dropout", "regularization", "co-adaptation"]` (где `"regularization"` отсутствует в глоссарии Недели 9, снижая `k_density` до `0.75`).
   - При первом старте (`compute_cohort_discrepancy`) пересчет пропускается (`if r.ai_depth_score is None`), но **при рестарте сервера** `main.py:224–225` принудительно вызывает `engine.compute_individual_depth(rec)` для всех завершенных записей из SQLite!
   - В результате у всех 11 студентов `ai_depth_score` мгновенно сбрасывается в **`57.4`**, Павел Ковалев и Руслан Ахметов исчезают из желтой зоны `WATCHLIST`, а **`median_delta` падает с `+2.5` до `-18.6`**, уводя все три порога (`+1σ, +2σ, +3σ`) в отрицательную область!
   - Обратная сторона той же мины до рестарта: в `models_schemas.py:72` поле `e_d_squared: float = 1.0` (не `None`), поэтому проверка `if rec.e_d_squared is None:` в `main.py:1460` не срабатывает, и клик по любому из 11 фоновых студентов на дашборде открывает карточку с нулями: **`p1: 0%, p2: 0%, p3: 0%, E[D²] = 1.00, K_density = 0.0`**.

### 2.2. Прочие математические стыки (`math_engine.py` и `similarity_service.py`)
- **Точное решение для одностороннего центра $Z^+$:** Для расчета положительных аномалий на полуоси $\Delta^+ \ge 0$ зафиксировать эффективный центр $\mu_{\text{eff}} = \max(0.0, \text{center\_median})$, сохранив вычисление $\text{MAD}$ и $\sigma_{\text{rob}} = \max(\sigma_{\min}, 1.4826 \cdot \text{MAD})$ по полному двустороннему вектору `valid_raw_deltas`. При `raw_median >= 0` (включая каноническую когорту $\text{Median}=2.5, \text{MAD}=3.8, \sigma_{\text{rob}}=5.63$) формула дает **100% идентичные числа**, а при `raw_median < 0` фиксирует нулевую гипотезу в $\mu_{\text{eff}} = 0.0$, сохраняя пороги $+1\sigma, +2\sigma, +3\sigma$ строго положительными ($\ge 4.0, 8.0, 12.0$).
- **Баг валидации галлюцинаций глоссария (`math_engine.py:139–144`):** условие `if validated: record.extraction.mastered_concepts = validated` при пустом списке `validated == []` (когда все концепты от LLM оказались вне глоссария) **не перезаписывает** список и оставляет галлюцинации в расчете `K_density`! Нужно присваивать `validated` безусловно и передавать текст реплик/цитат в `student_text`.
- **Несоответствие константы весов (`math_engine.py:25 vs 62`):** атрибут класса `CANONICAL_3TURN_WEIGHTS = (0.0556, 0.1320, 0.8124)` расходится с реально используемыми на строке `62` весами `(0.0556, 0.1215, 0.8229)`. Также в `main.py:152–158` в `ThemisMathEngine` не прокинуты `prior_weight_n` и `use_bayesian_shrinkage` из `settings`.

---

## Направление 3. UX-аудит `frontend/` глазами пользователя и жюри хакатона (`index.html` и `tma.html`)

### 3.1. Критические дефекты визуальной чистоты и сценария на сцене
1. **Белый текст на белом фоне в Доказательной карточке (`frontend/index.html:2529, 2595–2664` — P0 UX):**
   - После перевода `index.html` на светлую корпоративную тему (`bg-[#f8fafc]`, карточка `bg-white` на стр. `2529`) внутри JS-шаблона `renderEvidenceCard` для завершенных сессий остались старые dark-mode стили: заголовок `<h3 class="text-sm font-bold text-white">ДОКАЗАТЕЛЬНАЯ КАРТОЧКА АУДИТА</h3>` (**невидим на белом фоне!**), подписи `text-slate-300` / `text-slate-400` почти не читаются на проекторе, а черные блоки `bg-slate-900` конфликтуют со светлой версткой соседнего графика и состояния `OPTED_OUT`.
   - Аналогичные остатки темной темы портят читаемость бейджа `TG` в шапке (`строки 3199, 3202`: `text-amber-300` на белом), карточки привязки Telegram (`строки 3279–3342`: `bg-emerald-950/40 text-slate-300`) и статусов диалога при стриминге/SSE (`строки 1120–1175, 1383–1396, 1791, 1934–1953`).
2. **Застывшая статика при смене курса/недели (`frontend/index.html:142, 460–524, 1796–1801`):**
   - Крупный заголовок `#header-course-name` и `#header-week-topic` (`строка 142`) никогда не обновляется из JS: спикер выбирает Неделю 1 или загружает новую лекцию со сцены, а сверху по-прежнему написано *«Неделя 9: Глубокое обучение и регуляризация нейросетей»*.
   - В Dev-режиме блок `#card-solo-taxonomy` и `#syllabus-citations-list` (`строки 460–524`) на 100% статичен (*«Level 4»*, *«Слайд 14... Cos: 0.89»*, *«24.2 сек»*) даже на Шаге 0/3 и на других неделях, при этом использует 4-уровневую шкалу (`L1..L4`) вместо 3-уровневой модели ядра (`SOLO 1..3`).
   - Кнопки быстрого ввода `fillStudentMessage` (`строки 1796–1801`) не читают `week.demo_turns` загруженной лекции и подставляют текст про Dropout на любой новой теме.
3. **Наглядность `AI Discrepancy Report` для главного вопроса преподавателя (*«Почему ИИ оценил глубину студента выше меня?»*):**
   - В карточке уже отлично поданы три опоры Evidence-First: прямая цитата студента, верифицированные концепты глоссария и вероятности SOLO (`p1/p2/p3`).
   - **Чего не хватает для мгновенного считывания за 5 секунд на сцене:** (а) исправления светлой типографики; (б) компактной **формулы-расшифровки балла** ($S_{\text{SOLO}} \times K_{\text{density}} \times C_{\text{sample}} = S_{\text{depth}}$, например `93.5 × 1.00 × 1.00 = 93.5`), чтобы жюри видело, что `93.5` — не галлюцинация LLM, а строгий детерминированный расчет; (в) индикатора чистоты телеметрии (`Ручной набор • Без вставок` vs `⚠️ Обнаружен Copy-Paste`) и кнопки раскрытия полного 3-шагового транскрипта диалога.
4. **Связка QR-привязки Telegram и синхронизации TMA ↔ Desktop (`index.html` + `tma.html` + `telegram_bot.py`):**
   - В `tma.html` модалка успешного завершения `#modal-completed` (`строки 442, 847`) привязана **только к истечению 45-минутного таймера** (даже при 0 ответов!), а когда член жюри реально завершает 3 шага на смартфоне, финальный экран с подтверждением передачи в консоль преподавателя не появляется (нет даже кнопки «Завершить и посмотреть итог»).
   - На строке `638` в `tma.html` вызывается безусловный `startTimer(45 * 60)`, затирающий реальный остаток времени сессии со строки `627`; тема и глоссарий в `tma.html` захардкожены под Dropout (`строки 145, 314–324`), а найденные RAG-слайды (`sourcesMeta`, `строка 768`) принимаются по SSE, но не рендерятся под ответом тьютора.
   - QR-код в шапке (`openTmaQrModal`, `index.html:2971–2972`) хардкодит `ThemisExamBot`, формирует `pai_${currentWeek}` (который `telegram_bot.py:178` понимает только для `week_09`), а оба QR-генератора зависят от внешнего сайта `api.qrserver.com`. Кнопка `Открыть Mini App в браузере` (`index.html:3006`) не передает `student_id` и `course_id`.

---

# ПРОЕКТ ФАЙЛА `@UPDATED_PLAN.md` (Готов к записи после вашего подтверждения)

```markdown
# UPDATED_PLAN.md — Финальный архитектурный, математический и UX-аудит Themis Project (v2.0)

**Дата аудита:** 20.11.2026  
**Статус базового плана (`@PLAN.md`):** 7 / 7 этапов закрыты, 88 / 88 автотестов проходят.  
**Неприкосновенные конституционные инварианты (подтверждены и сохраняются во всех патчах):**
1. **Добровольность «Цифрового пандуса» (UDL Optional Affordance):** статусы `OPTED_OUT` и незавершенные входы (`< 2` валидных реплик, `INCOMPLETE_IGNORED`) не формируют $S_{\text{depth}}$, не меняют $G_{\text{prof}}$ и исключены из расчета медианы/MAD потока.
2. **Некредитный диагностический статус $S_{\text{depth}}$:** индекс глубины носит строго информационный характер, никогда не суммируется с $G_{\text{prof}}$ и не изменяет ведомость без явного действия преподавателя (`Human-in-the-Loop`).
3. **Односторонняя положительная ректификация и Zero Downward Penalty:** $\Delta^+ = \max(0, S_{\text{depth}} - G_{\text{prof}})$, $\text{new\_grade} \ge G_{\text{prof}}$ на уровне математического ядра, REST API и обоих интерфейсов.

---

## 1. Вердикт приемки

### 1.1. Общая оценка готовности архитектуры
Архитектура **Themis Project v2.0** находится на уровне **крепкого пред-демонстрационного MVP (готовность к сцене ~82%)**, но содержит **ряд скрытых стыковых дефектов (5 блокеров уровня P0 и 9 рисков уровня P1)**, которые не ловятся текущими 88 unit/integration-тестами, однако с высокой вероятностью проявятся во время живого выступления на хакатоне (при перезапуске сервера, нестабильном Wi-Fi площадки, переключении между неделями/курсами или открытии карточки аудита на проекторе).

### 1.2. Качество закрытия `@PLAN.md` и сверка с паспортом `@PROJECT_STATE.md`
Базовые цели 7 шагов `@PLAN.md` (SSE-стриминг реплик, анти-спам реплик, конвертер документов, Smart Chunker, криптография TMA `HMAC-SHA256`, запрет занижения балла `400 Bad Request`) реализованы качественно. Вместе с тем выявлены **фактические расхождения между декларациями `@PROJECT_STATE.md` и реальным кодом**:

| Заявление в `@PROJECT_STATE.md` | Фактическое состояние в коде `backend/` и `frontend/` |
|---|---|
| Полная мульти-курсовая и мульти-темная изоляция по ключу `(student_id, course_id, topic_id)` (разд. 2, 4.1) | Изоляция реализована в схеме SQLite, но **нарушена в памяти `backend/main.py:150`**: словарь `db_records` индексируется только по `student_id`, из-за чего диалог на новой неделе перезаписывает запись Недели 9, а пересчет когорты смешивает разные курсы/темы. |
| Единый редизайн `index.html` и `tma.html` в светлую корпоративную тему `#f8fafc` и 100% удаление статики (разд. 2, 6.1) | `tma.html` остался в темной теме (`#090d16`), а в `index.html` внутри светлой карточки `AI Discrepancy Report` (`стр. 2599`) остался заголовок `text-white` на `bg-white` (невидимый текст!) и блок статических заглушек `#card-solo-taxonomy` / `#header-week-topic` (`стр. 142, 460–524`). |
| Детерминированная консистентность метрик когорты ($\text{Median}=2.5, \text{MAD}=3.8, \sigma_{\text{rob}}=5.63$) после перезапуска (разд. 2, 5) | На холодном сидировании метрики совпадают, но **после первого же рестарта сервера** `main.py:224–225` пересчитывает шаблонные `extraction` 11 фоновых студентов из `seed_data.py`, обрушивая их `S_depth` с `75..84` до `57.4` и уводя медиану потока в `-18.6`. |
| При сбое сети / LLM в UI всплывает баннер с кнопкой «Повторить попытку» без очистки поля ввода (разд. 6.2, стр. 319) | Фактически `sendStudentMessage` (`index.html:1817`) и `handleSendTurn` (`tma.html:709`) очищают `input.value = ''` **до** завершения запроса, а кнопки повтора нет. |

---

## 2. Реестр дефектов и рисков демо

| Критичность | Файл и строки | Суть проблемы | Точное решение |
|---|---|---|---|
| **P0** | `backend/seed_data.py` *(145–186)*,<br>`backend/main.py` *(224–225, 1460–1461)* | **Обрушение когорты при рестарте и нули в карточке аудита:** у 11 фоновых студентов (`stud_aai_001`..`011`) `ai_depth_score` задан вручную (`75.4..84.2`), но шаблон `extraction` при вызове `compute_individual_depth` на рестарте сервера дает `57.4` у всех 11, уничтожая зону `WATCHLIST` и уводя `median_delta` в `-18.6`. До рестарта клик по этим студентам отдает `p1=p2=p3=0%, E[D²]=1.00, K_density=0.0`, т.к. `rec.e_d_squared` равен `1.0` (не `None`). | В `seed_data.py` откалибровать `turns_probabilities`, валидные термины глоссария Недели 9 (`4` концепта -> `K_density = 1.0`) и `total_tokens` для `stud_aai_001`..`011`, вызывая `compute_individual_depth(rec)` сразу при генерации сида, чтобы расчет давал точные целевые `ai_depth_score` и на старте, и после рестарта. В `main.py:1460` проверять `if rec.agg_probabilities == (0.0, 0.0, 0.0) and rec.extraction:`. |
| **P0** | `backend/main.py` *(150, 198–228, 290, 628–660, 804–821, 884, 986, 1080, 1352, 1608, 1702–1730)* | **Коллизия `db_records[student_id]` между курсами и неделями:** in-memory реестр не учитывает `course_id` и `topic_id`. Прохождение диалога на любой неделе, кроме 9-й, мутирует запись Недели 9, оставляя дашборд выбранной недели пустым, а `compute_cohort_discrepancy` вызывается по всем курсам/темам разом. | Перевести ключ `db_records` на кортеж `(student_id, course_id, resolved_topic)` с хелперами `get_or_create_record(sid, cid, tid)` и `recompute_topic_cohort(cid, tid)`. При первом обращении к новой паре `(course_id, topic_id)` лениво инициализировать очную ведомость группы (`OPTED_OUT`, `G_prof` из канонического профиля студента). Добавить фильтрацию `course_id, topic_id` в `GET /api/v1/students` и `/student/{id}/reset`. |
| **P0** | `backend/vector_store.py` *(48–82, 176–184)*,<br>`backend/main.py` *(1669–1688)* | **Риск падения ChromaDB с `InvalidDimensionException`:** при недоступности `huggingface.co` `_get_model()` не пробует `local_files_only=True` и переключается на `rubert-tiny2` (312-dim) либо MD5-вектор (384-dim), что при `upsert` в 1024-мерную коллекцию `themis_lecture_slides` роняет индексацию лекции необработанным исключением. | 1) В `_get_model()` при ошибке сети сначала вызывать `SentenceTransformer(self.model_name, local_files_only=True)`.<br>2) Полностью удалить fallback на 312-мерный `rubert-tiny2`.<br>3) Перевести оффлайн хэш-вектор в строгую размерность `1024` с L2-нормализацией, выставлять флаг `is_fallback_mode = True`, запрещать перезапись боевой коллекции хэшами в `add_slides` (обрабатывать через `try/except`) и честно отражать статус в `/api/v1/system/health`. |
| **P0** | `backend/math_engine.py` *(212–267)*,<br>`backend/main.py` *(152–158)*,<br>`frontend/index.html` *(2205–2288)* | **Искажение $Z^+$ и отрицательные пороги $+1\sigma..+3\sigma$ при $G_{\text{prof}} > S_{\text{depth}}$ у большинства группы:** при `raw_median < 0` вычитание отрицательной медианы из $\Delta^+ \ge 0$ завышает $Z^+$ для шумовых дельт (`+0.5` балла -> `+3.12σ`), а пороги `sigma_thresholds` уходят в `< 0`, уводя купол и линии сигм за левый край графика `Δ⁺`. | Зафиксировать односторонний референсный центр $\mu_{\text{eff}} = \max(0.0, \text{center\_median})$ для расчета `z_val` и `sigma_thresholds` (сохраняя расчет `mad` и `robust_sigma` по полному двустороннему массиву `valid_raw_deltas` и возвращая `raw_median_delta` справочно). При `center_median >= 0` математика на 100% совпадает с текущими эталонами (`2.5 / 3.8 / 5.63`). Передать `prior_weight_n` и `use_bayesian_shrinkage` из `settings` в `main.py:152`. |
| **P0** | `frontend/index.html` *(2529, 2595–2664, 1120–1175, 1383–1396, 1934–1953, 3199–3202, 3279–3342)* | **Невидимый заголовок и конфликт темной/светлой темы:** внутри белой панели `bg-white` (`стр. 2529`) заголовок `ДОКАЗАТЕЛЬНАЯ КАРТОЧКА АУДИТА` отрендерен классом `text-white`, подписи — `text-slate-300`, а статусные бейджи чата, шапки `TG` и карточки привязки используют бледные dark-mode цвета поверх белого фона. | Привести HTML-шаблоны в `renderEvidenceCard`, `renderTelegramBindingCard`, `updateAuthUI`, `sendStudentMessage`, `onWeekChanged` и `initAuditStream` к единой высококонтрастной светлой палитре (`text-slate-900`, `bg-slate-50`, `border-slate-200`, насыщенные акценты `text-violet-800`, `text-emerald-800`, `text-amber-800`). |
| **P1** | `backend/llm_service.py` *(43, 61, 102, 151, 166–182, 201, 276–333 в `main.py`, 329)* | **Фриз до 90с на демо при сбое внешнего API + склейка стрима + утечка Dropout-мока:** `timeout=30.0` × `max_retries=2` дает до 90с ожидания на одном шаге; нет Circuit Breaker; обрыв посреди стрима дописывает поверх полуфразы весь mock-ответ; `_mock_audit_extraction` (`стр. 329`) реагирует на слово «емкость» на любой неделе/курсе; падение `run_background_audit` оставляет вечный статус `AUDITING`. | Задать `max_retries=0`, таймауты `10.0s` (диалог) / `15.0s` (аудит) и Circuit Breaker на 60с после сбоя сети для мгновенного бесшовного перехода в детерминированный fallback. В стриминге вызывать mock только если `yielded_chars == 0`. Ограничить ветку Студента К. (`стр. 329`) проверкой `topic_id in ("week_09_deep_learning", "topic_05_regularization")`. В `run_background_audit` добавить `except`-восстановление через `_mock_audit_extraction` + отправку SSE, чтобы сессия никогда не зависала в `AUDITING`. |
| **P1** | `backend/database.py` *(208, 395–401, 828–848, 955)*,<br>`backend/tma_auth.py` *(240–276)* | **`IntegrityError` при QR-привязке после гостевого TMA и рассинхрон оценок сида:** если с телефона уже заходили в TMA до сканирования QR, `telegram_id` занят записью `stud_tg_<id>`, и `link_telegram_identity` падает на `UNIQUE(telegram_id)`. Оценки в `_init_default_student_identities` не совпадают с `seed_data.py`. | В `link_telegram_identity` внутри транзакции освобождать/сливать временный профиль `stud_tg_<telegram_id>` (и удалять его дубль из `student_audits` / `db_records`) перед привязкой `telegram_id` к целевому `student_id`. Синхронизировать словарь `default_grades` в `database.py:395` с каноническими оценками `seed_data.py`. Добавить `update_session_status(session_id, status)`. |
| **P1** | `backend/ingestion_service.py` *(274–278, 311)*,<br>`backend/markdown_converter.py` *(300–303, 322–366)*,<br>`backend/main.py` *(440, 449, 498, 525–542)* | **Хрупкость инжеста на битых/русскоязычных файлах:** кириллические темы без латиницы получают одинаковый `week_11_topic_11`; заявлены неподдерживаемые бинарные `.ppt`/`.doc`; в `convert_zip` нет очистки `temp_dir`, защиты от Zip-Slip и лимита размера; дублируется `return` в `main.py:534`. | Добавить транслитерацию RU->EN (или короткий хэш-суффикс) при генерации `clean_slug` в `auto_structure_topic`; убрать `.ppt`/`.doc` из `supported_exts` с понятной подсказкой сохранить в `.pptx`/`.docx`/`.pdf`; ограничить размер загрузки (напр. 25 МБ), проверять пути внутри ZIP и удалять `temp_dir` в `finally`; убрать дубль `return` и слово-триггер «емкости» из шаблона `demo_turns`. |
| **P1** | `backend/math_engine.py` *(25, 139–144)*,<br>`backend/rag_service.py` *(375–380, 422–440, 479)* | **Пропуск галлюцинаций концептов при пустом пересечении и коллизия глоссариев:** `if validated:` в `math_engine.py:143` не очищает `mastered_concepts`, когда ни один термин не совпал с глоссарием (`validated == []`); `rag_service` хранит и читает глоссарий без учета `course_id`. | Заменить `if validated:` на безусловное присваивание `record.extraction.mastered_concepts = validated` с передачей `student_text=" ".join(record.extraction.student_quotes)`. В `rag_service` добавить композитный индекс `(course_id, topic_id)` с обратной совместимостью по `topic_id`, а в `SELECT term FROM lecture_glossary` добавить фильтр `course_id = ?`. |
| **P1** | `backend/telegram_bot.py` *(176–180, 381–419)*,<br>`backend/main.py` *(1538, 1693, 1748, 1812, 1916)* | **Сбои Telegram deep-link и неполный SSE-бродкаст:** `build_tma_url` снимает `pai_` только для `week_09`; текстовый fallback бота шлет `web_app` с `http://localhost`, вызывая `400 Bad Request` в Telegram API; нет `answerCallbackQuery`; действия преподавателя, сброс и `opt-out` не пушат SSE. | В `build_tma_url` нормализовать любой `pai_<topic_id>` -> `<topic_id>`; в fallback-ответе использовать безопасный `self.build_inline_keyboard()`; добавить `answer_callback_query`; добавить публикацию SSE-события `cohort_updated` в `/audit/decision`, `/reset`, `/restore_canonical`, `/demo/reset` и `/session/opt-out`. |
| **P1** | `frontend/index.html` *(142, 460–524, 1796–1801, 2971–3009)*,<br>`frontend/tma.html` *(145, 432–443, 627–638, 767–785)* | **Фронтенд-рассинхрон на демо:** шапка курса/недели и карточка SOLO/RAG в `index.html` статичны; `fillStudentMessage` не берет `week.demo_turns` новых лекций; в `tma.html` нет экрана завершения после 3-го шага, таймер принудительно сбрасывается в `45:00`, тема/глоссарий и `sourcesMeta` не обновляются динамически; QR зависит от `api.qrserver.com`. | Обновлять `#header-course-name`, `#header-week-topic`, `#card-solo-taxonomy` и `fillStudentMessage` (`week.demo_turns`) динамически; в `tma.html` подгружать тему/глоссарий из `/api/v1/syllabus/weeks`, рендерить RAG-источники, исправить таймер и показывать ненавязчивый баннер/кнопку итогов после 3-го шага; прокидывать `bot_username` из API и добавить локальный fallback генерации/отображения ссылки при оффлайне, а в `openTmaInNewTab` передавать `student_id` и `course_id`. |

---

## 3. Точечные UX-улучшения для демо (высокий импакт без переписывания верстки)

1. **Прозрачная формула доверия в `AI Discrepancy Report` (`frontend/index.html`):**
   Добавить под тройкой метрик (`G_prof | S_depth | Δ+`) одну компактную моноширинную строку детерминированной декомпозиции:
   `S_depth = S_SOLO (92.5 + 1.0 иниц.) × K_density (1.00) × C_sample (1.00) = 93.5` + бейдж верификации телеметрии (`✓ Естественный ввод • 0 вставок` или `⚠️ Вставка из буфера`), а также сворачиваемый аккордеон **«Показать полный диалог (3 шага)»** прямо внутри карточки. Это за 3 секунды снимает главный вопрос жюри и преподавателя: *«Откуда взялось число 93.5 и можно ли ему доверять?»*.
2. **Единая высококонтрастная светлая тема для проектора (`frontend/index.html`):**
   Убрать остаточные черные блоки и невидимый `text-white` в карточке аудита, статусах диалога и плашке Telegram, заменив их на чистые карточки `bg-slate-50` с четкими цветовыми акцентами зон (`Violet / Rose / Amber / Emerald`). На большом экране или проекторе хакатона контраст вырастет кратно.
3. **Живой финал 3-го шага в мобильном `TMA` (`frontend/tma.html`):**
   При достижении `turn_number >= 3` и приходе SSE `audit_completed` показывать над полем ввода компактную карточку-плашку *«✓ Минимум (3/3 шага) выполнен! Диагностический индекс рассчитан и передан преподавателю. Вы можете углубить мысль или завершить сессию»* с кнопкой открытия итогового экрана `#modal-completed` (где уже отображается гарантированная защита $G_{\text{prof}}$). Сейчас после 3-го ответа на телефоне визуально ничего не происходит.
4. **Бесшовный сценический поток «Загрузил новую лекцию -> Прошел 3 шага в 1 клик» (`frontend/index.html`):**
   При завершении инжеста новой лекции в модалке загрузки автоматически переключать селектор `#select-syllabus-week` на только что созданную неделю, обновлять главный заголовок страницы и подхватывать сгенерированные бэкендом `week.demo_turns` в кнопки `⚡ Быстрый ввод (SOLO 1 / 2 / 3)`. Спикер сможет загрузить любой PDF/PPTX из зала и тут же за 15 секунд показать полный цикл сократического диалога именно по этому файлу.
5. **Мгновенный статус двигателя ИИ и неразрушающий повтор при сбое сети (`frontend/index.html` & `tma.html`):**
   Добавить в шапку аккуратный индикатор режима (`/api/v1/system/health`: `Gemini Live` / `Offline Deterministic`), а при сетевой ошибке стриминга **не стирать** текст студента из поля ввода (восстанавливать черновик и показывать кнопку `↻ Повторить отправку`).

---

## 4. Чек-лист реализации (`- [ ]`)

Ниже приведен пошаговый план атомарных патчей для модели-исполнителя с критериями приемки через `pytest`:

- [x] **Шаг 1. Стабилизация векторного хранилища и защита размерности 1024-dim (P0)**
  - **Целевые файлы:** `backend/vector_store.py`, `backend/main.py` (`/api/v1/system/health`), `backend/models_schemas.py`.
  - **Изменения:** добавить оффлайн-попытку `SentenceTransformer(self.model_name, local_files_only=True)` в `BgeM3EmbeddingFunction._get_model()`; удалить 312-мерный fallback `cointegrated/rubert-tiny2`; привести резервный детерминированный хэш-эмбеддер к размерности `1024` с L2-нормализацией и флагом `is_degraded`; защитить `add_slides` блоком `try/except` без порчи боевой HNSW-коллекции; прокинуть реальный статус и размерность в `/api/v1/system/health`.
  - **Проверка (`pytest`):** существующие тесты + новый unit-тест симуляции недоступности `SentenceTransformer`, проверяющий отсутствие `InvalidDimensionException` при `query` и `add_slides` на 1024-мерной коллекции.

- [x] **Шаг 2. Стресс-устойчивость математического ядра и эталонных данных `seed_data` (P0)**
  - **Целевые файлы:** `backend/math_engine.py`, `backend/seed_data.py`, `backend/main.py`.
  - **Изменения:**
    1. В `ThemisMathEngine.compute_cohort_discrepancy` ввести $\mu_{\text{eff}} = \max(0.0, \text{center\_median})$ для расчета `z_score` и `sigma_thresholds` (`+1σ, +2σ, +3σ`), сохранив `mad` и `robust_sigma` по двустороннему `valid_raw_deltas`.
    2. В `ThemisMathEngine.compute_individual_depth` исправить баг `if validated:` (присваивать `validated` даже при `[]`, передавая текст цитат в `student_text`) и синхронизировать константу `CANONICAL_3TURN_WEIGHTS = (0.0556, 0.1215, 0.8229)`.
    3. Прокинуть `prior_weight_n` и `use_bayesian_shrinkage` из `settings` при создании `engine` в `backend/main.py`.
    4. В `backend/seed_data.py` откалибровать `extraction` для `stud_aai_001`..`stud_aai_011` на реальных терминах глоссария Недели 9 так, чтобы `compute_individual_depth` детерминированно возвращал эталонные `ai_depth_score`, `E[D²]`, `K_density` и вероятности SOLO как до, так и после перезапуска сервера.
  - **Проверка (`pytest`):** все тесты `tests/test_themis_engine.py` и `tests/test_end_to_end_validation.py` (`Median=2.5, MAD=3.8, σ_rob=5.63`) + новые стресс-тесты: (а) когорта с большинством `G_prof > S_depth` (`raw_median < 0` -> пороги `+1σ..+3σ > 0`, шумовая дельта `+0.5` остается в `NORMAL`); (б) инвариантность метрик когорты после `reset_database(load_from_db_if_exists=True)`; (в) обнуление галлюцинированных концептов вне глоссария.

- [x] **Шаг 3. Мульти-курсовая/мульти-темная изоляция `db_records`, починка TMA-привязки и SSE-синхронизации (P0/P1)**
  - **Целевые файлы:** `backend/main.py`, `backend/database.py`, `backend/rag_service.py`, `backend/tma_auth.py`, `backend/telegram_bot.py`.
  - **Изменения:**
    1. Перевести `db_records` в `backend/main.py` на ключ `(student_id, course_id, resolved_topic)`, изолировать вызовы `compute_cohort_discrepancy` строго рамками одной пары `(course_id, resolved_topic)` и поддержать `course_id, topic_id` в `GET /api/v1/students` и `/student/{id}/reset`.
    2. Синхронизировать `default_grades` в `database.py:_init_default_student_identities` с `seed_data.py` и обновлять `sessions.status` при завершении/отказе.
    3. В `database.py:link_telegram_identity` устранить `IntegrityError` на `UNIQUE(telegram_id)` при слиянии ранее созданного гостевого профиля `stud_tg_<id>` с реальным студентом ведомости.
    4. В `rag_service.py` изолировать глоссарий и карту тем по `(course_id, topic_id)`.
    5. В `telegram_bot.py` исправить парсинг `pai_<topic_id>` для всех недель, защитить fallback-клавиатуру от не-HTTPS `PUBLIC_URL` и добавить `answerCallbackQuery`.
    6. Добавить `course_id`, `topic_id`, `sources` в SSE `dialog_turn_sync` и рассылку `cohort_updated` при `/audit/decision`, `/reset`, `/restore_canonical`, `/demo/reset`, `/session/opt-out`.
  - **Проверка (`pytest`):** тесты `tests/test_tma_and_telegram_bot.py` + новые тесты: (а) гостевой вход в TMA с последующей привязкой того же `telegram_id` по QR-токену без `IntegrityError`; (б) прохождение одним студентом двух разных недель без затирания аудита Недели 9.

- [x] **Шаг 4. Отказоустойчивость `llm_service.py` и `ingestion_service.py` на живой сцене (P1)**
  - **Целевые файлы:** `backend/config.py`, `backend/llm_service.py`, `backend/ingestion_service.py`, `backend/markdown_converter.py`, `backend/main.py`.
  - **Изменения:**
    1. В `llm_service.py` установить `max_retries=0`, таймауты `10s / 15s`, реализовать 60-секундный Circuit Breaker для мгновенного fallback в mock при обрыве интернета, предотвратить склейку полуфразы стрима с mock-ответом, передавать актуальное название курса в системный промпт и ограничить триггер цитаты Студента К. (`_mock_audit_extraction`) только темой Недели 9.
    2. В `main.py:run_background_audit` гарантировать выход из статуса `AUDITING` через fallback-экстракцию даже при исключении.
    3. В `ingestion_service.py` и `markdown_converter.py` добавить транслитерацию кириллицы для `topic_id`, лимит размера файла (25 МБ), защиту от Zip-Slip, очистку `temp_dir` в `finally`, убрать неподдерживаемые `.ppt`/`.doc` и дубль `return` в `main.py`.
  - **Проверка (`pytest`):** тесты `tests/test_markdown_converter_and_ingestion.py` и `tests/test_stream_and_performance.py` + новые тесты на таймаут LLM (Circuit Breaker < 1с на повторном вызове), две русскоязычные лекции на одной неделе (разные `topic_id`) и корректную отбраковку битого файла со статусом `FAILED`.

- [x] **Шаг 5. Финальная полировка UX `frontend/index.html` и `frontend/tma.html` (P0/P1)**
  - **Целевые файлы:** `frontend/index.html`, `frontend/tma.html`, `backend/main.py` (при необходимости отдачи `bot_username` и транскрипта в отчете).
  - **Изменения:**
    1. Исправить все неконтрастные dark-mode классы (`text-white` на `bg-white` в `AI Discrepancy Report`, бейджи чата, `TG` и карточку привязки) в `frontend/index.html`.
    2. Добавить в `AI Discrepancy Report` строку формулы расчета $S_{\text{depth}}$, индикатор чистоты телеметрии и раскрытие реплик диалога.
    3. Оживить динамическое обновление `#header-course-name`, `#header-week-topic`, карточек SOLO/RAG (3 уровня SOLO), автовыбор загруженной лекции и подстановку `week.demo_turns` в `fillStudentMessage`; сохранять текст в поле ввода при сбое сети.
    4. В `frontend/tma.html` подключить динамическую загрузку названия темы и глоссария из API, отрисовку RAG-источников под ответом тьютора, корректный таймер сессии и плашку/экран успешного завершения после 3-го шага; передавать `student_id` и `course_id` при открытии TMA из браузера и фильтрации `dialog_turn_sync`.
  - **Проверка (`pytest` + E2E):** прогон полного набора `pytest` (целевой результат: 100% pass всех существующих 88 тестов + новых регрессионных тестов аудита, соблюдение всех 3 конституционных инвариантов Themis Project).
```

---

### Следующий шаг
Если вы согласны с выводами аудита и структурой документа, подтвердите отчет и **переключитесь в Act mode** (**toggle to Act mode**), чтобы я записал этот план в файл `c:\Users\erlan\Desktop\Themis\themis-project\UPDATED_PLAN.md` (без изменения исходного кода проекта).