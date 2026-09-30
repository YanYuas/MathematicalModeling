# -*- coding: utf-8 -*-
"""Q2 external-audit numerical probe.
Question: are the two headline claims ("37 m -> 0.1 m degeneracy" and
"-2.01 deg cost") stated on the SAME footing (same target, same search space)?
ASCII-only output (Windows console codepage safe).
"""
import numpy as np

EPS = np.deg2rad(1.0)
R_WORST = 1000.0
D_LO, D_HI = 5.0, 1500.0
D_HAT = (D_LO + D_HI) / 2.0
DELTA_D = (D_HI - D_LO) / 2.0


def guaranteed(a, b, alphas):
    """(Na,Nb) arrays -> worst-case intersection angle (deg) and max d2 over
    alpha in alphas and r in {5,1500}."""
    A = np.asarray(a, float).reshape(-1, 1, 1)
    B = np.asarray(b, float).reshape(1, -1, 1)
    AL = np.asarray(alphas, float).reshape(1, 1, -1)
    S = A * A + B * B
    sin_min = np.ones(S.shape[:2] + (alphas.size,))
    d2max = np.zeros_like(sin_min)
    for r in (D_LO, D_HI):
        d2 = np.sqrt(np.maximum(S + r * r - 2.0 * r * (A * np.cos(AL) + B * np.sin(AL)), 0.0))
        num = np.abs(A * np.sin(AL) - B * np.cos(AL))
        s = np.where(d2 > 1e-9, num / np.maximum(d2, 1e-12), 0.0)
        sin_min = np.minimum(sin_min, s)
        d2max = np.maximum(d2max, d2)
    return np.degrees(np.arcsin(np.clip(sin_min, 0, 1))).min(axis=2), d2max.max(axis=2)


print("=" * 78)
print("A. alpha = 0 : 2-D maximum over (a,b)")
al0 = np.array([0.0])
bb1 = np.arange(590.0, 711.0, 1.0)
best0 = (-1.0, None, None)
for a in np.arange(700.0, 821.0, 1.0):
    p, d = guaranteed(np.array([a]), bb1, al0)
    p, d = p[0], d[0]
    ok = d <= R_WORST
    if ok.any():
        i = int(np.argmax(np.where(ok, p, -1.0)))
        if p[i] > best0[0]:
            best0 = (float(p[i]), float(a), float(bb1[i]))
print("   max guaranteed angle = %.4f deg at (a,b)=(%.1f, %.1f)" % best0)
print("   closed form arccos(747.5/1000) = %.4f deg (a=d_hat=752.5)" % np.degrees(np.arccos(DELTA_D / R_WORST)))

print()
print("=" * 78)
print("B. alpha in [-1,1] : 2-D maximum over (a,b)  (reproduce 39.616)")
al = np.linspace(-EPS, EPS, 801)
best = (-1.0, None, None)
for a in np.arange(700.0, 821.0, 2.0):
    p, d = guaranteed(np.array([a]), bb1, al)
    p, d = p[0], d[0]
    ok = d <= R_WORST
    if ok.any():
        i = int(np.argmax(np.where(ok, p, -1.0)))
        if p[i] > best[0]:
            best = (float(p[i]), float(a), float(bb1[i]))
print("   coarse  = %.4f deg at (%.1f, %.1f)" % best)
for step, half in ((0.25, 3.0), (0.05, 1.0)):
    sub = np.arange(best[2] - half, best[2] + half + 1e-9, step)
    for a in np.arange(best[1] - half, best[1] + half + 1e-9, step):
        p, d = guaranteed(np.array([a]), sub, al)
        p, d = p[0], d[0]
        ok = d <= R_WORST
        if ok.any():
            i = int(np.argmax(np.where(ok, p, -1.0)))
            if p[i] > best[0]:
                best = (float(p[i]), float(a), float(sub[i]))
    print("   step=%.2f -> %.6f deg at (%.2f, %.2f)" % (step, best[0], best[1], best[2]))
PHI_STAR = best[0]
PHI0 = float(np.degrees(np.arccos(DELTA_D / R_WORST)))
print("   cost = %.4f - %.4f = %.4f deg" % (PHI0, PHI_STAR, PHI0 - PHI_STAR))

print()
print("=" * 78)
print("C. feasible-set measure vs target angle (alpha in [-1,1], 1 m grid)")
ag = np.arange(700.0, 821.0, 1.0)
bg = np.arange(590.0, 711.0, 1.0)
P = np.empty((ag.size, bg.size))
Dm = np.empty_like(P)
for i, a in enumerate(ag):
    p, d = guaranteed(np.array([a]), bg, al)
    P[i], Dm[i] = p[0], d[0]
print("   %-12s %-12s %-10s %-8s %s" % ("phi_target", "area(m^2)", "cells", "best_a", "b-width at that a"))
for t in [40.0, 39.9, 39.8, 39.7, 39.65, round(PHI_STAR, 4), 39.5, 39.0, 38.0]:
    ok = (P >= t) & (Dm <= R_WORST)
    n = int(ok.sum())
    widths = []
    for i in range(ag.size):
        idx = np.where(ok[i])[0]
        widths.append(bg[idx].max() - bg[idx].min() if idx.size else 0.0)
    j = int(np.argmax(widths))
    print("   %-12.4f %-12.0f %-10d %-8.0f %.1f" % (t, float(n), n, ag[j], widths[j]))

print()
print("=" * 78)
print("D. same-footing comparison: b-interval at FIXED a, 0.05 m grid")
bs = np.arange(590.0, 711.0, 0.05)
for a in [752.5, 764.0]:
    for t in [40.0, 39.616]:
        for label, alv in (("alpha=0   ", al0), ("alpha=+-1 ", al)):
            p, d = guaranteed(np.array([a]), bs, alv)
            p, d = p[0], d[0]
            ok = (p >= t) & (d <= R_WORST)
            idx = np.where(ok)[0]
            if idx.size:
                print("   a=%7.1f target=%.3f %s -> b in [%.2f, %.2f]  width=%.3f m"
                      % (a, t, label, bs[idx].min(), bs[idx].max(), bs[idx].max() - bs[idx].min()))
            else:
                print("   a=%7.1f target=%.3f %s -> EMPTY (infeasible)" % (a, t, label))
