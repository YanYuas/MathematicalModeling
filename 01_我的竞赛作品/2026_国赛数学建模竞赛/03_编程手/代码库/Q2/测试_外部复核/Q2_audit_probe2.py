# -*- coding: utf-8 -*-
"""Probe 2: (i) alpha=0 2-D feasible AREA at target 40 deg; (ii) PNG dpi/size."""
import struct, glob, os
import numpy as np

EPS = np.deg2rad(1.0); R_WORST = 1000.0
D_LO, D_HI = 5.0, 1500.0

def guaranteed(a, b, alphas):
    A = np.asarray(a, float).reshape(-1, 1, 1); B = np.asarray(b, float).reshape(1, -1, 1)
    AL = np.asarray(alphas, float).reshape(1, 1, -1)
    S = A * A + B * B
    sin_min = np.ones(S.shape[:2] + (alphas.size,)); d2max = np.zeros_like(sin_min)
    for r in (D_LO, D_HI):
        d2 = np.sqrt(np.maximum(S + r * r - 2.0 * r * (A * np.cos(AL) + B * np.sin(AL)), 0.0))
        num = np.abs(A * np.sin(AL) - B * np.cos(AL))
        s = np.where(d2 > 1e-9, num / np.maximum(d2, 1e-12), 0.0)
        sin_min = np.minimum(sin_min, s); d2max = np.maximum(d2max, d2)
    return np.degrees(np.arcsin(np.clip(sin_min, 0, 1))).min(axis=2), d2max.max(axis=2)

ag = np.arange(700.0, 821.0, 1.0); bg = np.arange(590.0, 711.0, 1.0)
al0 = np.array([0.0]); al1 = np.linspace(-EPS, EPS, 801)
P0 = np.empty((ag.size, bg.size)); D0 = np.empty_like(P0)
P1 = np.empty_like(P0); D1 = np.empty_like(P0)
for i, a in enumerate(ag):
    p, d = guaranteed(np.array([a]), bg, al0); P0[i], D0[i] = p[0], d[0]
    p, d = guaranteed(np.array([a]), bg, al1); P1[i], D1[i] = p[0], d[0]

print("=" * 78)
print("E. 2-D feasible AREA on grid a in [700,820], b in [590,710], target 40 deg")
for lbl, P, D in (("alpha = 0     ", P0, D0), ("alpha in [-1,1]", P1, D1)):
    ok = (P >= 40.0) & (D <= R_WORST)
    if ok.any():
        ai, bi = np.where(ok)
        print("   %s area = %6d m^2 ; a in [%.0f, %.0f] ; b in [%.0f, %.0f]"
              % (lbl, int(ok.sum()), ag[ai].min(), ag[ai].max(), bg[bi].min(), bg[bi].max()))
    else:
        print("   %s area =      0 m^2 (EMPTY)" % lbl)
print("   note: the quoted '37.03 m band' is the b-slice at a=d_hat=752.5 only.")

print()
print("=" * 78)
print("F. PNG metadata (pixels + pHYs dpi)")
def png_info(path):
    with open(path, "rb") as f:
        data = f.read()
    w = h = None; dpi = None
    i = 8
    while i + 8 <= len(data):
        ln = struct.unpack(">I", data[i:i+4])[0]; typ = data[i+4:i+8]
        if typ == b"IHDR":
            w, h = struct.unpack(">II", data[i+8:i+16])
        if typ == b"pHYs":
            px, py, unit = struct.unpack(">IIB", data[i+8:i+17])
            if unit == 1:
                dpi = (round(px * 0.0254, 1), round(py * 0.0254, 1))
        if typ == b"IEND":
            break
        i += 12 + ln
    return w, h, dpi, len(data)

for pat in ["E:/CUMCM2026/交付准备区/Q2_待交付_v2/图/*.png",
            "E:/CUMCM2026/WorkArea_数学国赛/Q2_问题二/Alpha修正版/图/*.png"]:
    print("   --- %s" % pat)
    for p in sorted(glob.glob(pat)):
        w, h, dpi, size = png_info(p)
        print("   %-34s %5dx%-5d dpi=%-14s %6.0f KB" % (os.path.basename(p), w, h, str(dpi), size / 1024.0))
