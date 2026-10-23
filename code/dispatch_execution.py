import numpy as np
from scipy.optimize import linprog


def execute_fixed_plan(P, load, pv, price, s0, start=0, end=None,
                       target_soc=None, dt=1 / 6, eta=0.9,
                       pmax=5000 / 6, smin=1200.0, smax=10800.0):
    """Optimize the realized dispatch while keeping the purchase plan fixed."""
    if end is None:
        end = len(P)
    m = end - start
    if m <= 0:
        return tuple(np.zeros(0) for _ in range(5))

    # blocks: charge, discharge, emergency purchase, spill, SOC
    n = 5 * m
    c = np.zeros(n)
    c[:2 * m] = 1e-7
    c[2 * m:3 * m] = 5 * np.asarray(price[start:end])
    c[3 * m:4 * m] = 1e-9

    rows = 2 * m + (target_soc is not None)
    Aeq = np.zeros((rows, n))
    beq = np.zeros(rows)
    for k, t in enumerate(range(start, end)):
        # C-D-E+R = P+G-L (all energy variables are kWh per 10 min)
        Aeq[2 * k, k] = 1
        Aeq[2 * k, m + k] = -1
        Aeq[2 * k, 2 * m + k] = -1
        Aeq[2 * k, 3 * m + k] = 1
        beq[2 * k] = P[t] + pv[t] * dt - load[t] * dt

        Aeq[2 * k + 1, 4 * m + k] = 1
        Aeq[2 * k + 1, k] = -eta
        Aeq[2 * k + 1, m + k] = 1 / eta
        if k:
            Aeq[2 * k + 1, 4 * m + k - 1] = -1
        else:
            beq[2 * k + 1] = s0

    if target_soc is not None:
        Aeq[-1, 5 * m - 1] = 1
        beq[-1] = target_soc

    bounds = ([(0, pmax)] * (2 * m) + [(0, None)] * (2 * m)
              + [(smin, smax)] * m)
    res = linprog(c, A_eq=Aeq, b_eq=beq, bounds=bounds, method='highs')
    if not res.success:
        raise RuntimeError(res.message)
    x = res.x
    x[np.abs(x) < 1e-8] = 0.0
    return (x[:m], x[m:2 * m], x[2 * m:3 * m],
            x[3 * m:4 * m], x[4 * m:5 * m])
