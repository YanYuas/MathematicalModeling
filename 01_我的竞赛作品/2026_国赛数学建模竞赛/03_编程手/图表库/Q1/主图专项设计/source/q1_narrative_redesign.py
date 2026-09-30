# -*- coding: utf-8 -*-
"""问题一主图：测角 → 求交 → 覆盖圆（计算继承版）。

同一组几何对象画两次：左为全景交会，右为该交会区域的仿射放大。
顶点、直径、最小包围圆全部由 q1_main 实时算出，禁止手写多边形。
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, ConnectionPatch, Polygon, Rectangle

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import q1_main as model  # noqa: E402

OUT = ROOT.parent / "05_连续叙事主图"
OUT.mkdir(exist_ok=True)

INK = "#1A1A1A"
BLUE = "#26466D"
OCHRE = "#C47B2B"
SAGE = "#3D6B52"
SLATE = "#6B7B83"
PAPER = "#FFFFFF"
FILL_W = "#26466D"
FILL_L = "#C47B2B"

TABLE_D = 39.598
TABLE_R = 19.799
TABLE_GAMMA = 1.000
TABLE_JUNGS = 22.863

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial", "DejaVu Sans"],
        "font.size": 9,
        "axes.unicode_minus": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "mathtext.fontset": "stix",
        "savefig.dpi": 600,
    }
)


def compute_geometry():
    target = np.array([300.0, 500.0])
    stations = [np.array([0.0, 0.0]), np.array([600.0, 0.0])]
    bearings = [np.degrees(np.arctan2(*(target - s)[::-1])) for s in stations]
    wedges = model.build_wedges(stations, bearings, eps=1.0)
    vertices = model.candidate_vertices(wedges)
    poly = model.convex_hull(vertices)
    assert poly is not None and len(poly.vertices) >= 3
    d, ends = model.diameter_bruteforce(poly)
    dc, _ = model.diameter_rotating_calipers(poly)
    centre, r = model.mec_bruteforce(poly.vertices)
    _, rw = model.welzl_mec(poly.vertices)
    verts = np.array(poly.vertices, dtype=float)
    ends = np.array(ends, dtype=float)
    assert np.isclose(d, dc, atol=1e-8)
    assert np.isclose(r, rw, atol=1e-8)
    assert d / 2 - 1e-8 <= r <= d / np.sqrt(3) + 1e-8
    assert abs(d - TABLE_D) < 5e-3
    assert abs(r - TABLE_R) < 5e-3
    assert abs(2 * r / d - TABLE_GAMMA) < 5e-3
    for p in verts:
        assert np.linalg.norm(p - centre) <= r + 1e-6
    return {
        "G": target,
        "S": stations,
        "wedges": wedges,
        "L": verts,
        "D": float(d),
        "PQ": ends,
        "C": np.asarray(centre, dtype=float),
        "R": float(r),
        "gamma": float(2 * r / d),
        "jung_hi": float(d / np.sqrt(3)),
    }


def filled_poly(ax, pts, fc, ec, alpha, lw, z=3):
    ax.add_patch(Polygon(pts, closed=True, fc=fc, ec=ec, alpha=alpha, lw=lw, zorder=z))
    loop = np.vstack([pts, pts[0]])
    ax.plot(*loop.T, color=ec, lw=lw, zorder=z + 1)


def panel_label(ax, letter, title):
    ax.text(
        0.0,
        1.08,
        letter,
        transform=ax.transAxes,
        fontsize=11,
        weight="bold",
        color=INK,
        va="bottom",
        ha="left",
    )
    ax.annotate(
        title,
        (0.0, 1.08),
        xycoords="axes fraction",
        xytext=(16, 0),
        textcoords="offset points",
        fontsize=9,
        color=INK,
        va="bottom",
    )


def main():
    geo = compute_geometry()
    g, stations, wedges = geo["G"], geo["S"], geo["wedges"]
    L, d, pq, c, r = geo["L"], geo["D"], geo["PQ"], geo["C"], geo["R"]
    jung_hi, gamma = geo["jung_hi"], geo["gamma"]

    fig, (ax, zoom) = plt.subplots(
        1,
        2,
        figsize=(7.28, 3.35),
        gridspec_kw={"width_ratios": [1.18, 1.0]},
        facecolor=PAPER,
    )
    fig.subplots_adjust(left=0.06, right=0.985, bottom=0.22, top=0.82, wspace=0.16)

    ray_len = 740.0
    for i, w in enumerate(wedges):
        s = w.apex
        p1 = s + ray_len * w.ray_minus.direction
        p2 = s + ray_len * w.ray_plus.direction
        ax.add_patch(
            Polygon(np.array([s, p1, p2]), closed=True, fc=FILL_W, ec="none", alpha=0.10, zorder=1)
        )
        ax.plot([s[0], p1[0]], [s[1], p1[1]], color=BLUE, lw=1.05, zorder=2)
        ax.plot([s[0], p2[0]], [s[1], p2[1]], color=BLUE, lw=1.05, zorder=2)
        ax.plot([s[0], g[0]], [s[1], g[1]], color=BLUE, lw=0.7, ls=(0, (4, 2.5)), alpha=0.85, zorder=2)
        ax.scatter(*s, marker="s", s=28, color=BLUE, zorder=6)
        ax.annotate(
            rf"$S_{i+1}$",
            s,
            xytext=(0, -13),
            textcoords="offset points",
            ha="center",
            va="top",
            color=BLUE,
            fontsize=9,
        )

    filled_poly(ax, L, FILL_L, OCHRE, 0.95, 1.15, z=4)
    ax.scatter(*g, marker="*", s=55, color=OCHRE, zorder=7, linewidths=0.3, edgecolors=INK)
    ax.annotate("G", g, xytext=(8, 4), textcoords="offset points", color=OCHRE, fontsize=9)

    pad = 16.0
    x0, y0 = L.min(axis=0) - pad
    x1, y1 = L.max(axis=0) + pad
    ax.add_patch(
        Rectangle(
            (x0, y0),
            x1 - x0,
            y1 - y0,
            fill=False,
            ec=OCHRE,
            lw=1.0,
            zorder=8,
        )
    )

    ax.set_xlim(-50, 650)
    ax.set_ylim(-70, 640)
    ax.set_aspect("equal")
    ax.set_xticks([0, 300, 600])
    ax.set_yticks([0, 300, 500])
    ax.set_xlabel(r"$x$ (m)", color=INK, fontsize=8)
    ax.set_ylabel(r"$y$ (m)", color=INK, fontsize=8)
    ax.tick_params(labelsize=7, colors=SLATE, length=3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(SLATE)
    ax.spines["bottom"].set_color(SLATE)
    ax.set_facecolor(PAPER)
    panel_label(ax, "a", r"测角并求交  ·  $L=W_1 \cap W_2$,  $\varepsilon=1^{\circ}$")

    Lz = L - g
    pqz = pq - g
    cz = c - g
    filled_poly(zoom, Lz, FILL_L, OCHRE, 0.28, 1.6, z=3)
    zoom.add_patch(Circle(cz, jung_hi, fill=False, ec=SAGE, lw=1.15, ls=":", zorder=4))
    zoom.add_patch(Circle(cz, r, fill=False, ec=BLUE, lw=1.6, zorder=5))
    zoom.plot(*pqz.T, color=OCHRE, lw=2.2, zorder=6)
    zoom.scatter(*Lz.T, s=22, color=SAGE, zorder=7)
    zoom.scatter(*cz, marker="+", s=55, color=INK, zorder=8, linewidths=1.2)

    order = np.argsort(np.arctan2(Lz[:, 1], Lz[:, 0]))
    offsets = [(-20, -8), (8, -12), (8, -2), (6, 8)]
    for k, idx in enumerate(order):
        p = Lz[idx]
        zoom.annotate(
            rf"$V_{k+1}$",
            p,
            xytext=offsets[k % 4],
            textcoords="offset points",
            fontsize=8,
            color=SAGE,
        )
    hi = pqz[int(np.argmax(pqz[:, 1]))]
    lo = pqz[int(np.argmin(pqz[:, 1]))]
    pq_label_at = lo + 0.70 * (hi - lo)
    zoom.annotate(
        r"$PQ$",
        pq_label_at,
        xytext=(-9, 0),
        textcoords="offset points",
        fontsize=8,
        color=OCHRE,
        va="center",
        ha="right",
    )
    zoom.annotate(
        r"$C^\ast$",
        cz,
        xytext=(8, 5),
        textcoords="offset points",
        fontsize=8,
        color=INK,
    )
    zoom.text(
        0.04,
        0.96,
        rf"$\gamma=2R_{{\mathrm{{MEC}}}}/D={gamma:.3f}$",
        transform=zoom.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        color=INK,
    )
    zoom.text(
        cz[0] + jung_hi * 0.62,
        cz[1] + jung_hi * 0.78,
        r"$D/\sqrt{3}$",
        fontsize=7.5,
        color=SAGE,
        ha="left",
        va="bottom",
    )
    zoom.text(
        cz[0] + r * 0.78,
        cz[1] - r * 0.62,
        r"$R_{\mathrm{MEC}}$",
        fontsize=7.5,
        color=BLUE,
        ha="left",
        va="top",
    )

    zoom.set_xlim(x0 - g[0], x1 - g[0])
    zoom.set_ylim(y0 - g[1], y1 - g[1])
    zoom.set_aspect("equal")
    zoom.set_xlabel(r"$x-300$ (m)", color=INK, fontsize=8)
    zoom.set_ylabel(r"$y-500$ (m)", color=INK, fontsize=8)
    zoom.tick_params(labelsize=7, colors=SLATE, length=3)
    zoom.spines["top"].set_visible(False)
    zoom.spines["right"].set_visible(False)
    zoom.spines["left"].set_color(SLATE)
    zoom.spines["bottom"].set_color(SLATE)
    zoom.set_facecolor(PAPER)
    panel_label(zoom, "b", r"同一 $L$ 放大  ·  直径 $\to$ 最小包围圆")

    for src, dst in (((x1, y0), (0.0, 0.0)), ((x1, y1), (0.0, 1.0))):
        fig.add_artist(
            ConnectionPatch(
                xyA=src,
                coordsA=ax.transData,
                xyB=dst,
                coordsB=zoom.transAxes,
                color=SLATE,
                lw=0.7,
                ls=(0, (3, 2)),
                alpha=0.7,
            )
        )

    fig.text(
        0.06,
        0.07,
        (
            rf"$D={d:.3f}$ m    $R_{{\mathrm{{MEC}}}}={r:.3f}$ m    "
            rf"$D/2 \leq R_{{\mathrm{{MEC}}}} \leq D/\sqrt{{3}}$    "
            rf"上界圆 $D/\sqrt{{3}}={jung_hi:.3f}$ m 仅作半径比较"
        ),
        fontsize=7.5,
        color=SLATE,
        ha="left",
        va="center",
    )
    fig.text(
        0.06,
        0.025,
        r"左图角域按真实 $\varepsilon=1^{\circ}$ 绘制；右图多边形、直径端点与圆心均继承左图求交结果，不是重绘对象。",
        fontsize=7.5,
        color=SLATE,
        ha="left",
        va="center",
    )

    stem = OUT / "Q1_连续叙事_测角到覆盖圆"
    for ext in ("png", "svg", "pdf"):
        fig.savefig(
            stem.with_suffix(f".{ext}"),
            dpi=600,
            bbox_inches="tight",
            pad_inches=0.04,
            facecolor=PAPER,
        )
    plt.close(fig)

    print("L vertices:")
    for p in L:
        print(f"  ({p[0]:10.4f}, {p[1]:10.4f})")
    print(f"D={d:.4f}  R_MEC={r:.4f}  gamma={gamma:.4f}  Jung_hi={jung_hi:.4f}")
    print(f"saved {stem}.png/svg/pdf")


if __name__ == "__main__":
    main()

