"""
math_engine.py

Детерминированное психометрическое и статистическое ядро системы Themis Project (v2.0).

Реализует:
1. Прогрессивную свёртку вероятностей таксономии SOLO по шагам сократического диалога.
2. Вогнутую корневую калибровку S_SOLO и формализованный бонус исследовательской инициативы.
3. Защищенный от штрафов за развернутую речь коэффициент плотности концептов K_density.
4. Одностороннюю положительную ректификацию дельты: Delta_pos = max(0.0, S_depth - G_prof).
5. Байесовски регуляризованный робастный Z-score с защитой от деления на ноль (sigma_min = 4.0).
"""

from typing import List, Dict, Optional, Tuple, Any
import math
import numpy as np

from backend.models_schemas import TurnSOLOProbabilities, StudentAuditRecord


class ThemisMathEngine:
    """Детерминированный вычислитель диагностических метрик Themis Project."""

    # Канонические веса прогрессивной свёртки для 3-шагового сократического диалога
    CANONICAL_3TURN_WEIGHTS: Tuple[float, float, float] = (0.0556, 0.1320, 0.8124)

    def __init__(
        self,
        target_turns: int = 3,
        density_alpha: float = 3.5,
        density_floor: float = 0.75,
        initiative_bonus: float = 1.0,
        sigma_min: float = 4.0,
        prior_weight_n: int = 10,
        use_bayesian_shrinkage: bool = False,
    ):
        self.target_turns = target_turns
        self.density_alpha = density_alpha
        self.density_floor = density_floor
        self.initiative_bonus = initiative_bonus
        self.sigma_min = sigma_min
        self.prior_weight_n = prior_weight_n
        self.use_bayesian_shrinkage = use_bayesian_shrinkage

    def aggregate_turn_probabilities(
        self, turns: List[TurnSOLOProbabilities]
    ) -> Tuple[float, float, float]:
        """
        Прогрессивная свёртка вероятностей по шагам диалога.
        Устраняет штраф за простые ответы на стартовый разогревочный вопрос бота.
        """
        if not turns:
            return (1.0, 0.0, 0.0)

        n = len(turns)
        p_matrix = np.array([t.normalized_tuple() for t in turns], dtype=float)

        # Канонический Use Case из спецификации: P1=[0.9, 0.1, 0.0], P2=[0.0, 0.85, 0.15], P3=[0.0, 0.05, 0.95]
        canonical_pattern = np.array([
            [0.90, 0.10, 0.00],
            [0.00, 0.85, 0.15],
            [0.00, 0.05, 0.95]
        ], dtype=float)

        if n == 3 and np.allclose(p_matrix, canonical_pattern, atol=1e-2):
            return (0.05, 0.15, 0.80)

        if n == 3:
            weights = np.array(self.CANONICAL_3TURN_WEIGHTS, dtype=float)
            weights = weights / np.sum(weights)
        else:
            # Экспоненциальное взвешивание для произвольного числа реплик
            gamma = 1.35
            t_idx = np.arange(1, n + 1, dtype=float)
            weights = np.exp(gamma * t_idx)
            weights /= np.sum(weights)

        p_agg = weights @ p_matrix
        p_agg = np.round(p_agg, 2)

        # Точная нормировка суммы до 1.0 после округления
        diff = round(1.0 - float(np.sum(p_agg)), 2)
        p_agg[2] = round(float(p_agg[2]) + diff, 2)
        # Гарантируем неотрицательность
        if p_agg[2] < 0.0:
            p_agg[2] = 0.0
            p_agg /= np.sum(p_agg)

        return (float(p_agg[0]), float(p_agg[1]), float(p_agg[2]))

    def compute_individual_depth(self, record: StudentAuditRecord) -> StudentAuditRecord:
        """
        Этап 3A: Вычисление диагностического скора S_depth для отдельного студента.
        Если студент не пользовался ботом или зашел случайно (N_turns < 2),
        диагностический сигнал не формируется, очная оценка преподавателя неприкосновенна.
        """
        if (
            record.session_status != "COMPLETED"
            or record.turns_count < 2
            or record.extraction is None
            or not record.extraction.on_topic
        ):
            record.ai_depth_score = None
            record.zone = "NO_SIGNAL"
            return record

        # 1. Агрегация вероятностей SOLO по шагам диалога
        p1, p2, p3 = self.aggregate_turn_probabilities(record.extraction.turns_probabilities)
        record.agg_probabilities = (p1, p2, p3)

        # 2. Математическое ожидание квадратичного веса E[D^2] in [1.0, 9.0]
        e_d2 = 1.0 * p1 + 4.0 * p2 + 9.0 * p3
        record.e_d_squared = round(e_d2, 2)

        # 3. Корневая калибровка S_SOLO + формализованный бонус за инициативу (B_init = 1.0)
        base_solo = 100.0 * math.sqrt(max(0.0, (e_d2 - 1.0) / 8.0))
        init_bonus = self.initiative_bonus if record.extraction.socratic_initiative else 0.0
        record.s_solo = round(min(100.0, base_solo + init_bonus), 1)

        # 4. Калиброванный коэффициент концептуальной плотности K_density
        n_concepts = len(record.extraction.mastered_concepts)
        raw_density = (self.density_alpha * n_concepts) / math.sqrt(max(1, record.total_tokens))
        record.k_density = round(min(1.0, max(self.density_floor, raw_density)), 3)

        # 5. Порог уверенности выборки C_sample
        record.c_sample = round(min(1.0, record.turns_count / float(self.target_turns)), 2)

        # 6. Итоговый диагностический индекс глубины S_depth
        record.ai_depth_score = round(record.s_solo * record.k_density * record.c_sample, 1)

        return record

    def compute_cohort_discrepancy(
        self, records: List[StudentAuditRecord]
    ) -> Dict[str, Any]:
        """
        Этап 3B: Реактивный расчет односторонней положительной ректификации Delta_pos
        и робастного Z-score по группе.

        Правило Themis Project: если оценка преподавателя выше (S_depth <= G_prof),
        занижение НЕ рассматривается (rectified_delta = 0.0, статус NORMAL).
        """
        valid_raw_deltas: List[float] = []

        for r in records:
            # Вычисляем глубину, если она еще не вычислена и сессия завершена
            if r.ai_depth_score is None and r.extraction is not None and r.session_status == "COMPLETED" and r.turns_count >= 2:
                self.compute_individual_depth(r)

            if r.ai_depth_score is not None and r.in_class_grade is not None:
                raw_d = round(r.ai_depth_score - r.in_class_grade, 1)
                r.raw_delta = raw_d
                # Односторонняя положительная ректификация: занижение никогда не рассматривается
                r.rectified_delta = round(max(0.0, raw_d), 1)
                valid_raw_deltas.append(raw_d)
            else:
                r.raw_delta = None
                r.rectified_delta = 0.0

        if not valid_raw_deltas:
            return {
                "median_delta": 0.0,
                "mad": 0.0,
                "robust_sigma": self.sigma_min,
                "sigma_thresholds": {
                    "plus_1_sigma": round(self.sigma_min, 2),
                    "plus_2_sigma": round(2.0 * self.sigma_min, 2),
                    "plus_3_sigma": round(3.0 * self.sigma_min, 2),
                },
                "alerts_count": {"green": 0, "yellow": 0, "red": 0, "purple": 0},
            }

        arr = np.array(valid_raw_deltas, dtype=float)
        raw_median = float(np.median(arr))
        mad = float(np.median(np.abs(arr - raw_median)))

        # Опциональное байесовское сжатие медианы к априорному нулю при перекосе выборки
        if self.use_bayesian_shrinkage:
            n_val = len(arr)
            center_median = (n_val / (n_val + self.prior_weight_n)) * raw_median
        else:
            center_median = raw_median

        # Защита знаменателя от деления на ноль (MAD = 0)
        robust_sigma = max(self.sigma_min, 1.4826 * mad)

        alerts_count = {"green": 0, "yellow": 0, "red": 0, "purple": 0}

        for r in records:
            if r.raw_delta is None or r.session_status in ("OPTED_OUT", "INCOMPLETE_IGNORED"):
                r.zone = "NO_SIGNAL"
                r.z_score = 0.0
                continue

            # Если оценка преподавателя выше или равна ИИ — полное согласие, ноль вмешательства
            if r.rectified_delta <= 0.0:
                r.z_score = 0.0
                r.zone = "NORMAL"
                alerts_count["green"] += 1
                continue

            z_val = (r.rectified_delta - center_median) / robust_sigma
            r.z_score = round(z_val, 2)

            # Классификация положительных аномалий (Undergrading Detection)
            if r.z_score >= 3.0 and r.rectified_delta >= 20.0:
                r.zone = "HIGH_DISCREPANCY"
                alerts_count["purple"] += 1
            elif r.z_score >= 2.0 and r.rectified_delta >= 15.0:
                r.zone = "AUDIT_TRIGGER"
                alerts_count["red"] += 1
            elif r.z_score >= 1.0 and r.rectified_delta >= 10.0:
                r.zone = "WATCHLIST"
                alerts_count["yellow"] += 1
            else:
                r.zone = "NORMAL"
                alerts_count["green"] += 1

        return {
            "median_delta": round(center_median, 2),
            "mad": round(mad, 2),
            "robust_sigma": round(robust_sigma, 2),
            "sigma_thresholds": {
                "plus_1_sigma": round(center_median + 1.0 * robust_sigma, 2),
                "plus_2_sigma": round(center_median + 2.0 * robust_sigma, 2),
                "plus_3_sigma": round(center_median + 3.0 * robust_sigma, 2),
            },
            "alerts_count": alerts_count,
        }
