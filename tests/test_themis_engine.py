"""
test_themis_engine.py

Pytest suite для детерминированного психометрического ядра ThemisMathEngine v2.0.
Проверяет все математические инварианты, точность канонических значений и устойчивость к краевым случаям.
"""

import pytest
import numpy as np
from backend.models_schemas import TurnSOLOProbabilities, AuditExtractionResult, StudentAuditRecord
from backend.math_engine import ThemisMathEngine


@pytest.fixture
def engine():
    return ThemisMathEngine()


def test_canonical_weights(engine):
    """Проверка канонических весов 3-шаговой сократической сессии."""
    assert engine.CANONICAL_3TURN_WEIGHTS == (0.0556, 0.1320, 0.8124)
    assert abs(sum(engine.CANONICAL_3TURN_WEIGHTS) - 1.0) < 1e-4


def test_student_k_turn_aggregation(engine):
    """Проверка свёртки реплик Студента К. в канонический вектор [0.05, 0.15, 0.80]."""
    turns = [
        TurnSOLOProbabilities(turn_number=1, p1=0.90, p2=0.10, p3=0.00),
        TurnSOLOProbabilities(turn_number=2, p1=0.00, p2=0.85, p3=0.15),
        TurnSOLOProbabilities(turn_number=3, p1=0.00, p2=0.05, p3=0.95),
    ]
    p_agg = engine.aggregate_turn_probabilities(turns)
    assert p_agg == (0.05, 0.15, 0.80)


def test_student_k_depth_score(engine):
    """
    Проверка расчёта индекса глубины познания S_depth для Студента К.
    Инвариант: E[D^2] = 7.85, S_SOLO = 93.5, K_density = 1.0, S_depth = 93.5.
    """
    extraction = AuditExtractionResult(
        on_topic=True,
        student_quotes=[
            "Если Dropout так эффективен, почему бы нам не выключать 80% нейронов для максимальной регуляризации? "
            "В какой момент это сломает обучение и вызовет потерю емкости сети (underfitting)?"
        ],
        mastered_concepts=["co-adaptation", "model capacity", "dropout rate trade-off", "underfitting"],
        socratic_initiative=True,
        pedagogical_justification="Студент связал регуляризацию с потерей емкости сети.",
        turns_probabilities=[
            TurnSOLOProbabilities(turn_number=1, p1=0.90, p2=0.10, p3=0.00),
            TurnSOLOProbabilities(turn_number=2, p1=0.00, p2=0.85, p3=0.15),
            TurnSOLOProbabilities(turn_number=3, p1=0.00, p2=0.05, p3=0.95),
        ]
    )
    record = StudentAuditRecord(
        student_id="stud_aai_042",
        in_class_grade=70.0,
        session_status="COMPLETED",
        turns_count=3,
        total_tokens=180,
        extraction=extraction
    )

    res = engine.compute_individual_depth(record)
    assert res.agg_probabilities == (0.05, 0.15, 0.80)
    assert res.e_d_squared == 7.85
    assert res.s_solo == 93.5
    assert res.k_density == 1.0
    assert res.c_sample == 1.0
    assert res.ai_depth_score == 93.5


def test_session_validity_gate(engine):
    """
    Проверка шлюза валидности:
    - 0 реплик (OPTED_OUT) -> ai_depth_score = None, zone = NO_SIGNAL
    - 1 реплика (INCOMPLETE_IGNORED) -> ai_depth_score = None, zone = NO_SIGNAL
    - on_topic = False -> ai_depth_score = None, zone = NO_SIGNAL
    """
    # 0 реплик
    r0 = StudentAuditRecord(student_id="stud_opt_out", in_class_grade=85.0, session_status="OPTED_OUT", turns_count=0)
    engine.compute_individual_depth(r0)
    assert r0.ai_depth_score is None
    assert r0.zone == "NO_SIGNAL"

    # 1 реплика
    r1 = StudentAuditRecord(student_id="stud_incomplete", in_class_grade=88.0, session_status="INCOMPLETE_IGNORED", turns_count=1)
    engine.compute_individual_depth(r1)
    assert r1.ai_depth_score is None
    assert r1.zone == "NO_SIGNAL"

    # Оффтопик
    ext_off = AuditExtractionResult(
        on_topic=False,
        student_quotes=[],
        mastered_concepts=[],
        pedagogical_justification="Спам или оффтопик",
        turns_probabilities=[TurnSOLOProbabilities(turn_number=1, p1=1.0, p2=0.0, p3=0.0)]
    )
    r_off = StudentAuditRecord(student_id="stud_spam", in_class_grade=75.0, session_status="COMPLETED", turns_count=3, extraction=ext_off)
    engine.compute_individual_depth(r_off)
    assert r_off.ai_depth_score is None
    assert r_off.zone == "NO_SIGNAL"


def test_positive_only_rectification(engine):
    """
    Проверка односторонней положительной ректификации:
    Если G_prof >= S_depth (преподаватель оценил выше), delta_pos = 0.0, статус NORMAL.
    Занижение оценки преподавателя никогда не допускается.
    """
    records = [
        StudentAuditRecord(
            student_id="stud_high_prof",
            in_class_grade=95.0,
            session_status="COMPLETED",
            turns_count=3,
            total_tokens=150,
            ai_depth_score=60.0
        ),
        StudentAuditRecord(
            student_id="stud_equal",
            in_class_grade=80.0,
            session_status="COMPLETED",
            turns_count=3,
            total_tokens=150,
            ai_depth_score=80.0
        )
    ]
    summary = engine.compute_cohort_discrepancy(records)
    for r in records:
        assert r.rectified_delta == 0.0
        assert r.z_score == 0.0
        assert r.zone == "NORMAL"


def test_zero_division_protection(engine):
    """Проверка защиты от деления на ноль при MAD = 0."""
    records = [
        StudentAuditRecord(student_id=f"stud_{i}", in_class_grade=80.0, session_status="COMPLETED", turns_count=3, ai_depth_score=80.0)
        for i in range(5)
    ]
    summary = engine.compute_cohort_discrepancy(records)
    assert summary["mad"] == 0.0
    assert summary["robust_sigma"] == engine.sigma_min  # 4.0


def test_canonical_cohort_distribution(engine):
    """
    Проверка полной канонической когорты из Use Case (12 завершенных сессий).
    Инварианты:
    - median_delta = 2.5
    - mad = 3.8
    - robust_sigma = 5.63
    - thresholds: +1s = 8.13, +2s = 13.77, +3s = 19.40
    - alerts: green=9, yellow=2, red=0, purple=1
    - Студент К. (stud_aai_042): rectified_delta = 23.5, z_score = 3.73, zone = HIGH_DISCREPANCY
    """
    # 12 студентов с точными дельтами
    # raw: [-3.2, -1.5, -1.3, 0.4, 1.1, 2.0, 3.0, 4.2, 6.3, 11.0, 13.2, 23.5]
    raw_deltas = [-3.2, -1.5, -1.3, 0.4, 1.1, 2.0, 3.0, 4.2, 6.3, 11.0, 13.2, 23.5]
    records = []
    base_prof = 70.0

    for i, d in enumerate(raw_deltas):
        sid = "stud_aai_042" if i == 11 else f"stud_{i+1:03d}"
        prof = 70.0 if i == 11 else (base_prof + (i * 2))
        depth = prof + d
        rec = StudentAuditRecord(
            student_id=sid,
            in_class_grade=prof,
            session_status="COMPLETED",
            turns_count=3,
            ai_depth_score=round(depth, 1)
        )
        records.append(rec)

    summary = engine.compute_cohort_discrepancy(records)

    assert summary["median_delta"] == 2.5
    assert summary["mad"] == 3.8
    assert summary["robust_sigma"] == 5.63
    assert summary["sigma_thresholds"]["plus_1_sigma"] == 8.13
    assert summary["sigma_thresholds"]["plus_2_sigma"] == 13.77
    assert summary["sigma_thresholds"]["plus_3_sigma"] == 19.40

    assert summary["alerts_count"]["green"] == 9
    assert summary["alerts_count"]["yellow"] == 2
    assert summary["alerts_count"]["red"] == 0
    assert summary["alerts_count"]["purple"] == 1

    stud_k = next(r for r in records if r.student_id == "stud_aai_042")
    assert stud_k.rectified_delta == 23.5
    assert stud_k.z_score == 3.73
    assert stud_k.zone == "HIGH_DISCREPANCY"

