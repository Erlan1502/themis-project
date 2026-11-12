# =====================================================================
# THEMIS PROJECT - DOCKERFILE
# Inclusive Academic Discrepancy Audit & Socratic Scaffolding Engine
# =====================================================================

FROM python:3.11-slim

# Системные зависимости для C++ сборки HNSW, SQLite и работы с документами
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости и устанавливаем их
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем исходный код проекта
COPY backend /app/backend
COPY frontend /app/frontend
COPY data /app/data
COPY tests /app/tests

# Создаем директории для персистентных данных
RUN mkdir -p /app/data/uploads /app/data/chroma_db

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000

CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

