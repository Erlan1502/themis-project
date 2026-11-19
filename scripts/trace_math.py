import sys
sys.path.insert(0, '.')
import math
import numpy as np
from backend.models_schemas import TurnSOLOProbabilities, StudentAuditRecord, AuditExtractionResult
from backend.math_engine import ThemisMathEngine

engine = ThemisMathEngine()

# Data from user's actual extraction
turns_probs = [
    TurnSOLOProbabilities(turn_number=1, p1=0.7, p2=0.3, p3=0.0),
    TurnSOLOProbabilities(turn_number=2, p1=0.15, p2=0.7, p3=0.15),
    TurnSOLOProbabilities(turn_number=3, p1=0.05, p2=0.65, p3=0.3),
    TurnSOLOProbabilities(turn_number=4, p1=0.0, p2=0.25, p3=0.75),
    TurnSOLOProbabilities(turn_number=5, p1=0.0, p2=0.1, p3=0.9),
    TurnSOLOProbabilities(turn_number=6, p1=0.0, p2=0.05, p3=0.95),
]

p1, p2, p3 = engine.aggregate_turn_probabilities(turns_probs)
print(f"1. Aggregated probabilities: p1={p1}, p2={p2}, p3={p3}")

e_d2 = 1.0 * p1 + 4.0 * p2 + 9.0 * p3
print(f"2. E[D^2] = {e_d2:.4f}")

base_solo = 100.0 * math.sqrt(max(0.0, (e_d2 - 1.0) / 8.0))
init_bonus = 1.0 # socratic_initiative was True!
s_solo = min(100.0, base_solo + init_bonus)
print(f"3. base_solo = {base_solo:.2f}, init_bonus = {init_bonus}, s_solo = {s_solo:.2f}")

# 4. K_density
# mastered_concepts: ["dropout", "underfitting", "batch"] -> len = 3
# total_tokens = 363
# density_alpha = 3.5
# density_floor = 0.75
n_concepts = 3
total_tokens = 363
raw_density = (3.5 * n_concepts) / math.sqrt(total_tokens)
k_density = min(1.0, max(0.75, raw_density))
print(f"4. n_concepts = {n_concepts}, total_tokens = {total_tokens}")
print(f"   raw_density = (3.5 * {n_concepts}) / sqrt({total_tokens}) = {10.5:.2f} / {math.sqrt(total_tokens):.2f} = {raw_density:.4f}")
print(f"   k_density = {k_density:.4f} (HIT THE FLOOR OF 0.75!)")

# 5. C_sample
c_sample = min(1.0, 6 / 3.0)
print(f"5. c_sample = {c_sample}")

# 6. Final score
ai_depth = s_solo * k_density * c_sample
print(f"6. ai_depth_score = s_solo ({s_solo:.2f}) * k_density ({k_density:.2f}) * c_sample ({c_sample:.2f}) = {ai_depth:.2f} -> {round(ai_depth, 1)}")
