"""
models_schemas.py

Pydantic v2 схемы для системы Themis Project (v2.0):
1. Evidence-First extraction schemas (Qwen3.5 LLM auditor output).
2. API request and response data models.
3. Internal audit structures.
"""

from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from pydantic import BaseModel, Field, field_validator


# =====================================================================
# 1. EVIDENCE-FIRST PROTOCOL SCHEMAS (LLM AUDIT EXTRACTION)
# =====================================================================

class TurnSOLOProbabilities(BaseModel):
    """Распределение вероятностей по уровням таксономии SOLO для одного шага диалога."""
    turn_number: int = Field(..., ge=1, description="Номер реплики студента в диалоге")
    p1: float = Field(..., ge=0.0, le=1.0, description="Surface / Multistructural (определения, факты)")
    p2: float = Field(..., ge=0.0, le=1.0, description="Relational (механизмы, причинно-следственные связи)")
    p3: float = Field(..., ge=0.0, le=1.0, description="Extended Abstract (компромиссы, синтез, границы)")

    def normalized_tuple(self) -> Tuple[float, float, float]:
        """Возвращает нормализованную тройку вероятностей (сумма = 1.0)."""
        total = self.p1 + self.p2 + self.p3
        if total <= 1e-9:
            return (1.0, 0.0, 0.0)
        return (self.p1 / total, self.p2 / total, self.p3 / total)


class AuditExtractionResult(BaseModel):
    """
    Строгая схема ответа LLM-экстрактора (Qwen3.5-27B / 9B).
    Порядок полей критичен (Evidence-First): модель сначала извлекает цитаты и концепты,
    и только в конце вычисляет вероятности SOLO.
    """
    on_topic: bool = Field(..., description="True, если ответы студента относятся к теме занятия")
    student_quotes: List[str] = Field(..., description="Прямые цитаты студента, доказывающие глубину понимания")
    mastered_concepts: List[str] = Field(..., description="Освоенные доменные концепты из глоссария занятия")
    socratic_initiative: bool = Field(
        default=False,
        description="True, если студент самостоятельно сформулировал исследовательский вопрос 3-го уровня"
    )
    pedagogical_justification: str = Field(..., description="Краткое аналитическое обоснование для преподавателя")
    turns_probabilities: List[TurnSOLOProbabilities] = Field(
        ..., description="Оценка вероятностей SOLO по каждому шагу диалога"
    )


# =====================================================================
# 2. СТРУКТУРЫ ДАННЫХ АУДИТА СТУДЕНТА (ВНУТРЕННЕЕ СОСТОЯНИЕ)
# =====================================================================

@dataclass
class StudentAuditRecord:
    student_id: str
    in_class_grade: Optional[float] = None  # Очная оценка преподавателя G_prof (неприкосновенна)
    session_status: str = "OPTED_OUT"      # OPTED_OUT | INCOMPLETE_IGNORED | COMPLETED
    turns_count: int = 0
    total_tokens: int = 0
    extraction: Optional[AuditExtractionResult] = None

    # Вычисляемые диагностические метрики (не зачетные, не суммируются с G_prof)
    agg_probabilities: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    e_d_squared: float = 1.0
    s_solo: float = 0.0
    k_density: float = 0.0
    c_sample: float = 0.0
    ai_depth_score: Optional[float] = None  # Диагностический индекс глубины S_depth
    raw_delta: Optional[float] = None       # Сырая разница S_depth - G_prof
    rectified_delta: float = 0.0            # Положительная ректификация max(0.0, S_depth - G_prof)
    z_score: float = 0.0                    # Односторонний робастный Z-score
    zone: str = "NO_SIGNAL"                 # NO_SIGNAL | NORMAL | WATCHLIST | AUDIT_TRIGGER | HIGH_DISCREPANCY
    telemetry_clean: bool = True            # Флаг чистоты ввода (без аномального copy-paste)


# =====================================================================
# 3. REST API МОДЕЛИ ЗАПРОСОВ И ОТВЕТОВ
# =====================================================================

class SessionStartRequest(BaseModel):
    student_id: str = Field(..., description="Идентификатор студента, напр. stud_aai_042")
    course_id: str = Field(..., description="Идентификатор курса, напр. prog_ai_2026")
    topic_id: str = Field(..., description="Идентификатор темы, напр. topic_05_regularization")
    force_open: Optional[bool] = Field(default=False, description="Принудительное открытие окна для демонстрации")


class SessionStartResponse(BaseModel):
    session_id: str
    status: str
    time_remaining_seconds: int
    policy_notice: str
    initial_prompt: str


class DialogTurnRequest(BaseModel):
    session_id: str
    student_message: str
    paste_detected: bool = Field(default=False, description="Флаг детекции вставки из буфера")
    typing_duration_ms: int = Field(default=0, description="Время набора сообщения в миллисекундах")


class DialogTurnResponse(BaseModel):
    session_id: str
    turn_number: int
    system_reply: str
    session_confidence: str


class GradeSyncItem(BaseModel):
    student_id: str
    in_class_grade: float = Field(..., ge=0.0, le=100.0)


class GradeSyncRequest(BaseModel):
    course_id: str
    topic_id: str
    records: List[GradeSyncItem]


class GradeSyncResponse(BaseModel):
    status: str
    synced_count: int
    cohort_summary: Dict[str, Any]


class DashboardDistribution(BaseModel):
    median_delta: float
    mad: float
    robust_sigma: float
    sigma_thresholds: Dict[str, float]


class DashboardResponse(BaseModel):
    project: str = "Themis Project"
    topic_id: str
    total_students: int
    opted_out_or_incomplete: int
    sessions_completed: int
    distribution: DashboardDistribution
    alerts_count: Dict[str, int]
    students: Optional[List[Dict[str, Any]]] = None


class ReportSOLOAnalysis(BaseModel):
    dominant_level: str
    aggregated_probabilities: Dict[str, float]
    e_d_squared: float
    s_solo_calibrated: float
    socratic_initiative_bonus: float
    k_density: float
    c_sample: float


class ReportEvidence(BaseModel):
    student_quotes: List[str]
    mastered_concepts: List[str]
    telemetry_clean: bool
    pedagogical_justification: str


class AIReportResponse(BaseModel):
    student_id: str
    in_class_grade: Optional[float]
    ai_depth_score: Optional[float]
    non_credit_notice: str
    rectified_delta: float
    z_score: float
    zone: str
    solo_analysis: ReportSOLOAnalysis
    evidence: ReportEvidence
    recommended_action: str

