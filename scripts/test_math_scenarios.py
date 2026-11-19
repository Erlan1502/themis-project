import sys
sys.path.insert(0, '.')
import math
import numpy as np

# 1. Текущая модель весов при n шагах:
def current_weights(n, gamma=1.35):
    if n == 3:
        w = np.array([0.0556, 0.1215, 0.8229])
        return w / np.sum(w)
    t = np.arange(1, n + 1, dtype=float)
    w = np.exp(gamma * t)
    return w / np.sum(w)

print("=== ТЕКУЩИЕ ВЕСА ===")
for n in [3, 5, 6, 10, 15]:
    w = current_weights(n)
    print(f"n = {n:2d}: w[0]={w[0]:.4f}, w[-1]={w[-1]:.4f}, w[-2]={w[-2]:.4f}, w[last 2 sum]={w[-1]+w[-2]:.4f}")

# 2. Текущий K_density при разном числе токенов:
print("\n=== ТЕКУЩИЙ K_density (alpha=3.5, floor=0.75) ===")
for tokens in [100, 150, 200, 363, 500, 1000, 1500]:
    for nc in [2, 3, 4, 5]:
        raw = (3.5 * nc) / math.sqrt(tokens)
        kd = min(1.0, max(0.75, raw))
        if tokens in [150, 363, 1000]:
            print(f"Tokens={tokens:4d}, concepts={nc}: raw={raw:.3f} -> K_density = {kd:.3f}")
