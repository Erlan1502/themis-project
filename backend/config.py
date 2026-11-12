"""
config.py

Конфигурация Themis Project (v2.0) на базе Pydantic Settings.
Поддерживает чтение из переменных окружения и .env файла.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Themis Project"
    VERSION: str = "2.0.0"

    # Режим работы LLM: "gemini" | "mock" | "local_qwen" | "cloud"
    LLM_MODE: str = "gemini"

    # Google Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Настройки окна доступа к сократическому боту (45 минут по регламенту)
    SCHEDULE_FORCE_OPEN: bool = True
    SCHEDULE_WINDOW_MINUTES: int = 45

    # Настройки для подключения к реальным Qwen3.5 инстансам (vLLM / llama-server / OpenAI API)
    QWEN_BASE_URL: str = "http://localhost:8000/v1"
    QWEN_API_KEY: str = "empty"
    QWEN_DIALOG_MODEL: str = "Qwen/Qwen3.5-4B"
    QWEN_AUDIT_MODEL: str = "Qwen/Qwen3.5-27B"

    # Параметры ThemisMathEngine
    TARGET_TURNS: int = 3
    DENSITY_ALPHA: float = 3.5
    DENSITY_FLOOR: float = 0.75
    INITIATIVE_BONUS: float = 1.0
    SIGMA_MIN: float = 4.0
    PRIOR_WEIGHT_N: int = 10
    USE_BAYESIAN_SHRINKAGE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

