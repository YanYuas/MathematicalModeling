# -*- coding: utf-8 -*-
"""Q1 v3 统一美化出图入口。

所有成图均由 Python/matplotlib 生成。脚本保留既有真实扫描数据和几何算法，
统一执行白底、无图内总标题、可编辑 SVG/PDF 和 600 dpi PNG 预览的版式规范。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Arc, Wedge
import numpy as np


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "source"
sys.path.insert(0, str(SOURCE))

import q1_figures_legacy_clean as legacy  # noqa: E402
import q1_figures_beautified_v2 as fixed  # noqa: E402


PALETTE = {
    "ink": "#1A1A1A",
    "slate": "#6B7B83",
    "paper": "#FFFFFF",
    "field": "#B8CFE0",
    "geometry": "#26466D",
    "ochre": "#C47B2B",
    "rust": "#8C3A2A",
    "sage": "#3D6B52",
    "gold": "#D4A843",
}
LINE_WIDTH = {"main": 2.2, "theory": 1.4, "aux": 0.7}
OUTPUTS = {
    "geometry": HERE / "02_几何示意",
    "parameter": HERE / "03_参数扫描",
    "statistics": HERE / "04_统计分布",
}

mpl.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "Arial", "DejaVu Sans", "sans-serif"],
        "font.size": 9,
        "axes.linewidth": 0.8,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "legend.frameon": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "mathtext.fontset": "stix",
        "savefig.dpi": 600,
    }
)


def category_for(name: str) -> str:
    if name.startswith(("fig5_1_6", "fig5_1_8", "fig5_1_11", "fig5_1_12", "fig5_1_13")):
        return "parameter"
    if name.startswith("fig5_1_7"):
        return "statistics"
    return "geometry"


def save_figure(fig: Figure, name: str, *_: object, **__: object) -> None:
    """Save each result in a print-ready and two editable/reviewable formats."""
    out_dir = OUTPUTS[category_for(name)]
    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / name
    for extension, options in (
        (".png", {"dpi": 600}),
        (".svg", {}),
        (".pdf", {}),
    ):
        fig.savefig(
            base.with_suffix(extension),
            bbox_inches="tight",
            pad_inches=0.04,
            facecolor=PALETTE["paper"],
            **options,
        )
    plt.close(fig)


def style_axis(ax: Axes, xlabel: str | None = None, ylabel: str | None = None,
               title: str | None = None, equal: bool = False) -> None:
    """Use external captions: ``title`` is accepted only for legacy compatibility."""
    ax.set_facecolor(PALETTE["paper"])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(PALETTE["slate"])
    ax.spines["bottom"].set_color(PALETTE["slate"])
    ax.tick_params(colors=PALETTE["slate"], width=0.8)
    if xlabel:
        ax.set_xlabel(xlabel, color=PALETTE["ink"])
    if ylabel:
        ax.set_ylabel(ylabel, color=PALETTE["ink"])
    if equal:
        ax.set_aspect("equal")


def prepare(module: object) -> None:
    module.PALETTE.update(PALETTE)
    module.LW.update(LINE_WIDTH)
    module.DPI = 600
    module.FIG_DIR_GEO = str(OUTPUTS["geometry"])
    module.FIG_DIR_PARAM = str(OUTPUTS["parameter"])
    module.FIG_DIR_STAT = str(OUTPUTS["statistics"])
    module.FIG_DIR_FLOW = str(OUTPUTS["geometry"])
    module.save_fig = save_figure
    module.style_ax = style_axis


@contextmanager
def paper_layout():
    """Temporarily remove legacy figure titles and constrain old oversized canvases."""
    original_suptitle = Figure.suptitle
    original_title = Axes.set_title
    original_figure = plt.figure
    original_subplots = plt.subplots

    def compact(size: object) -> object:
        if not isinstance(size, tuple) or len(size) != 2 or size[0] <= 8:
            return size
        scale = 8.0 / size[0]
        return (8.0, round(size[1] * scale, 2))

    def figure(*args: object, **kwargs: object) -> Figure:
        if "figsize" in kwargs:
            kwargs["figsize"] = compact(kwargs["figsize"])
        return original_figure(*args, **kwargs)

    def subplots(*args: object, **kwargs: object):
        if "figsize" in kwargs:
            kwargs["figsize"] = compact(kwargs["figsize"])
        return original_subplots(*args, **kwargs)

    Figure.suptitle = lambda self, *args, **kwargs: None
    Axes.set_title = lambda self, *args, **kwargs: None
    plt.figure = figure
    plt.subplots = subplots
    try:
        yield
    finally:
        Figure.suptitle = original_suptitle
        Axes.set_title = original_title
        plt.figure = original_figure
        plt.subplots = original_subplots


def fig5_1_1_single_station_wedge() -> None:
    """Paper Figure 5.1-1: the single-station uncertainty mechanism."""
    fig, ax = plt.subplots(figsize=(7.2, 5.0), facecolor=PALETTE["paper"])
    station = np.array([0.0, 0.0])
    theta, eps, radius = 53.0, 1.0, 260.0
    wedge = Wedge(station, radius, theta - eps, theta + eps, facecolor=PALETTE["field"],
                  alpha=0.75, edgecolor=PALETTE["geometry"], linewidth=1.0)
    ax.add_patch(wedge)
    for angle, linestyle, width in (
        (theta - eps, "--", LINE_WIDTH["theory"]),
        (theta, "-", LINE_WIDTH["main"]),
        (theta + eps, "--", LINE_WIDTH["theory"]),
    ):
        direction = np.array([np.cos(np.deg2rad(angle)), np.sin(np.deg2rad(angle))])
        endpoint = station + radius * direction
        ax.plot([0, endpoint[0]], [0, endpoint[1]], color=PALETTE["geometry"],
                linestyle=linestyle, linewidth=width)
    ax.plot(0, 0, marker="s", markersize=9, color=PALETTE["geometry"],
            markeredgecolor="white", markeredgewidth=1.2, zorder=5)
    ax.text(-4, -20, r"检测站 $S_1$", ha="center", color=PALETTE["geometry"], weight="bold")
    arc = Arc(station, 104, 104, theta1=theta - eps, theta2=theta + eps,
              color=PALETTE["ochre"], linewidth=1.8)
    ax.add_patch(arc)
    mid = np.array([75 * np.cos(np.deg2rad(theta)), 75 * np.sin(np.deg2rad(theta))])
    ax.text(mid[0] + 20, mid[1] - 7, r"$2\varepsilon=2^\circ$", color=PALETTE["ochre"],
            weight="bold", bbox={"boxstyle": "round,pad=0.22", "fc": "white", "ec": PALETTE["ochre"]})
    ax.text(185, 218, r"上界 $\theta+\varepsilon$", color=PALETTE["geometry"], fontsize=8)
    ax.text(194, 105, r"下界 $\theta-\varepsilon$", color=PALETTE["geometry"], fontsize=8)
    ax.annotate("单站测向仅约束方向，\n无法确定距离。", xy=(155, 200), xytext=(160, 82),
                color=PALETTE["slate"], ha="center",
                arrowprops={"arrowstyle": "->", "color": PALETTE["slate"], "lw": 1.0})
    style_axis(ax, r"$x$ (m)", r"$y$ (m)", equal=True)
    ax.set_xlim(-55, 300)
    ax.set_ylim(-50, 285)
    ax.grid(True, alpha=0.18)
    save_figure(fig, "fig5_1_1_single_station_wedge")


def fig5_1_3_jung_counterexample() -> None:
    """Paper Figure 5.1-3: a readable Thales counterexample without risky glyphs."""
    from matplotlib.patches import Circle, Polygon

    fig, ax = plt.subplots(figsize=(7.2, 5.5), facecolor=PALETTE["paper"])
    side = 100.0
    vertices = np.array([[0, 0], [side, 0], [side / 2, side * np.sqrt(3) / 2]])
    centre_d = np.array([side / 2, 0.0])
    centre_mec = np.array([side / 2, side / (2 * np.sqrt(3))])
    r_d, r_mec = side / 2, side / np.sqrt(3)
    ax.add_patch(Polygon(vertices, closed=True, fill=False, edgecolor=PALETTE["ink"], linewidth=LINE_WIDTH["main"]))
    ax.add_patch(Circle(centre_d, r_d, fill=False, edgecolor=PALETTE["rust"], linestyle="--",
                        linewidth=LINE_WIDTH["theory"], label=r"直径圆：$R=D/2$"))
    ax.add_patch(Circle(centre_mec, r_mec, fill=False, edgecolor=PALETTE["sage"],
                        linewidth=LINE_WIDTH["main"], label=r"最小包围圆：$R=D/\sqrt{3}$"))
    ax.plot([0, side], [0, 0], color=PALETTE["ochre"], linewidth=3.0)
    for point, label, offset in zip(vertices, ["A", "B", "C"], [(-9, -10), (9, -10), (0, 8)]):
        ax.plot(*point, "o", color=PALETTE["ink"], markersize=6)
        ax.text(point[0] + offset[0], point[1] + offset[1], label, weight="bold", fontsize=11)
    ax.text(50, 6, r"$D=100\ \mathrm{m}$", ha="center", color=PALETTE["ochre"], weight="bold",
            bbox={"boxstyle": "round,pad=0.18", "fc": "white", "ec": PALETTE["ochre"]})
    ax.text(50, 68, r"$\angle ACB=60^\circ<90^\circ$", ha="center", color=PALETTE["rust"], weight="bold",
            bbox={"boxstyle": "round,pad=0.28", "fc": "white", "ec": PALETTE["rust"]})
    ax.annotate("顶点 C 位于直径圆外", xy=vertices[2], xytext=(82, 102), ha="center", color=PALETTE["rust"],
                arrowprops={"arrowstyle": "->", "color": PALETTE["rust"], "lw": 1.0})
    ax.text(50, -23, r"因此以直径 $D$ 为直径的圆不能覆盖该等边三角形。", ha="center", color=PALETTE["ink"])
    style_axis(ax, r"$x$ (m)", r"$y$ (m)", equal=True)
    ax.set_xlim(-18, 118)
    ax.set_ylim(-32, 120)
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.18)
    save_figure(fig, "fig5_1_3_jung_counterexample")


def fig5_1_10_geometry_construction() -> None:
    """Paper Figure 5.1-2: global bearings paired with a legible local zoom."""
    from matplotlib.patches import Circle, Polygon

    fig, (ax_global, ax_zoom) = plt.subplots(1, 2, figsize=(7.8, 3.8), facecolor=PALETTE["paper"],
                                              gridspec_kw={"width_ratios": [1, 1.05], "wspace": 0.35})
    s1, s2, source = np.array([0.0, 0.0]), np.array([600.0, 0.0]), np.array([300.0, 500.0])
    eps = 1.0
    angles = [np.rad2deg(np.arctan2(source[1] - s[1], source[0] - s[0])) for s in (s1, s2)]
    for station, angle in zip((s1, s2), angles):
        for bearing, style, alpha in ((angle - eps, "--", 0.50), (angle, "-", 0.78), (angle + eps, "--", 0.50)):
            endpoint = station + 700 * np.array([np.cos(np.deg2rad(bearing)), np.sin(np.deg2rad(bearing))])
            ax_global.plot([station[0], endpoint[0]], [station[1], endpoint[1]], color=PALETTE["geometry"],
                           linestyle=style, linewidth=1.15 if style == "--" else 1.8, alpha=alpha)
        ax_global.add_patch(Wedge(station, 700, angle - eps, angle + eps, facecolor=PALETTE["field"], alpha=0.22))
    ax_global.scatter([0, 600], [0, 0], marker="s", s=45, color=PALETTE["geometry"], zorder=4)
    ax_global.scatter(*source, marker="*", s=130, color=PALETTE["gold"], edgecolor=PALETTE["ink"], zorder=5)
    ax_global.text(0, -55, r"$S_1$", ha="center", color=PALETTE["geometry"], weight="bold")
    ax_global.text(600, -55, r"$S_2$", ha="center", color=PALETTE["geometry"], weight="bold")
    ax_global.text(316, 520, r"$G$", color=PALETTE["gold"], weight="bold")
    ax_global.annotate("基线 600 m", xy=(0, -28), xytext=(600, -28), ha="center", va="center",
                       arrowprops={"arrowstyle": "<->", "color": PALETTE["slate"], "lw": 0.9}, color=PALETTE["slate"], fontsize=8)
    style_axis(ax_global, r"$x$ (m)", r"$y$ (m)", equal=True)
    ax_global.set_xlim(-80, 680)
    ax_global.set_ylim(-90, 660)
    ax_global.set_xticks([0, 300, 600])
    ax_global.set_yticks([0, 250, 500])
    ax_global.grid(True, alpha=0.15)

    vertices = np.array([[311.866, 499.793], [300.000, 480.777], [288.134, 499.793], [300.000, 520.375]])
    polygon = np.vstack([vertices, vertices[0]])
    centre = np.array([300.0, (480.777 + 520.375) / 2])
    ax_zoom.add_patch(Polygon(vertices, closed=True, facecolor=PALETTE["field"], alpha=0.78,
                              edgecolor=PALETTE["geometry"], linewidth=LINE_WIDTH["main"]))
    ax_zoom.add_patch(Circle(centre, 19.799, fill=False, edgecolor=PALETTE["sage"], linestyle="--", linewidth=1.8))
    ax_zoom.plot([300, 300], [480.777, 520.375], color=PALETTE["ochre"], linewidth=2.8)
    offsets = [(2.2, -1.2), (2.3, -1.8), (-8.5, -1.2), (-8.5, 1.0)]
    for index, (point, offset) in enumerate(zip(vertices, offsets), start=1):
        ax_zoom.scatter(*point, color=PALETTE["ochre"], s=25, zorder=5)
        ax_zoom.text(point[0] + offset[0], point[1] + offset[1], rf"$V_{index}$", fontsize=8, color=PALETTE["ink"])
    ax_zoom.scatter(*source, marker="*", s=105, color=PALETTE["gold"], edgecolor=PALETTE["ink"], zorder=6)
    ax_zoom.text(302.2, 501.8, r"$G$", color=PALETTE["gold"], weight="bold")
    ax_zoom.text(0.03, 0.97, "$D=39.598$ m\n$R_{MEC}=19.799$ m\n$\\gamma=1.000$", transform=ax_zoom.transAxes,
                 va="top", color=PALETTE["ink"], fontsize=8,
                 bbox={"boxstyle": "round,pad=0.28", "fc": "white", "ec": PALETTE["sage"]})
    style_axis(ax_zoom, r"$x$ (m)", r"$y$ (m)", equal=True)
    ax_zoom.set_xlim(275, 325)
    ax_zoom.set_ylim(473, 528)
    ax_zoom.grid(True, alpha=0.15)
    save_figure(fig, "fig5_1_10_geometry_construction")


def fig5_1_4_jung_sandwich() -> None:
    """Paper Figure 5.1-4: the empirical lower equality and Jung upper bound."""
    from matplotlib.patches import Circle, Polygon

    fig, (ax_geo, ax_scale) = plt.subplots(1, 2, figsize=(7.8, 3.7), facecolor=PALETTE["paper"],
                                            gridspec_kw={"width_ratios": [1.05, 1.25], "wspace": 0.38})
    d, r_mec, r_upper = 39.598, 19.799, 39.598 / np.sqrt(3)
    points = np.array([[0, -d / 2], [d * 0.30, 0], [0, d / 2], [-d * 0.30, 0]])
    ax_geo.add_patch(Polygon(points, closed=True, facecolor=PALETTE["field"], alpha=0.65,
                             edgecolor=PALETTE["geometry"], linewidth=LINE_WIDTH["main"]))
    ax_geo.add_patch(Circle((0, 0), r_upper, fill=False, color=PALETTE["slate"], linestyle=":",
                            linewidth=LINE_WIDTH["theory"], label=r"Jung 上界 $D/\sqrt{3}$"))
    ax_geo.add_patch(Circle((0, 0), r_mec, fill=False, color=PALETTE["sage"], linestyle="-",
                            linewidth=LINE_WIDTH["main"], label=r"$R_{MEC}=D/2$"))
    ax_geo.plot([0, 0], [-d / 2, d / 2], color=PALETTE["ochre"], linewidth=2.8)
    ax_geo.scatter(points[:, 0], points[:, 1], s=20, color=PALETTE["geometry"], zorder=3)
    ax_geo.text(2.5, 0, r"$D=39.598$ m", color=PALETTE["ochre"], va="center", fontsize=8)
    style_axis(ax_geo, equal=True)
    ax_geo.set_xlim(-28, 28)
    ax_geo.set_ylim(-28, 28)
    ax_geo.set_xticks([])
    ax_geo.set_yticks([])
    ax_geo.legend(loc="lower center", bbox_to_anchor=(0.5, -0.24), ncol=1, fontsize=7.5)

    ax_scale.axhspan(d / 2, r_upper, color=PALETTE["ochre"], alpha=0.11)
    ax_scale.vlines(0, 0, r_upper, color=PALETTE["slate"], linewidth=1.0)
    ax_scale.hlines([d / 2, r_mec], -0.12, 0.12, color=PALETTE["sage"], linewidth=3.0)
    ax_scale.hlines(r_upper, -0.12, 0.12, color=PALETTE["slate"], linewidth=2.0, linestyles=":")
    ax_scale.text(0.17, r_mec, r"$D/2=R_{MEC}=19.799$ m", va="center", color=PALETTE["sage"], weight="bold")
    ax_scale.text(0.17, r_upper, r"$D/\sqrt{3}=22.862$ m", va="center", color=PALETTE["slate"], weight="bold")
    ax_scale.text(0.0, 8, "$\\gamma=1.000$\n下界取等", ha="center", color=PALETTE["sage"], weight="bold",
                  bbox={"boxstyle": "round,pad=0.35", "fc": "white", "ec": PALETTE["sage"]})
    style_axis(ax_scale, ylabel="覆盖半径 (m)")
    ax_scale.set_xlim(-0.32, 1.15)
    ax_scale.set_ylim(0, 26)
    ax_scale.set_xticks([])
    ax_scale.grid(axis="y", alpha=0.18)
    save_figure(fig, "fig5_1_4_jung_sandwich")


def fig5_1_2_wedge_evolution() -> None:
    """Show how two station wedges contract to a small feasible region."""
    fig, axes = plt.subplots(1, 3, figsize=(8.2, 2.9), facecolor=PALETTE["paper"])
    s1, s2, g = np.array([0., 0.]), np.array([600., 0.]), np.array([300., 500.])
    for ax, eps, label in zip(axes, (8., 3., 1.), ("较宽角域", "收窄", "最终定位")):
        for s in (s1, s2):
            a = np.degrees(np.arctan2(g[1]-s[1], g[0]-s[0]))
            ax.add_patch(Wedge(s, 780, a-eps, a+eps, facecolor=PALETTE["field"], alpha=.30,
                               edgecolor=PALETTE["geometry"], linewidth=.8))
            for aa in (a-eps, a+eps):
                q = s + 780*np.array([np.cos(np.radians(aa)), np.sin(np.radians(aa))])
                ax.plot([s[0],q[0]],[s[1],q[1]],"--",color=PALETTE["geometry"],lw=.8,alpha=.7)
        ax.scatter([0,600],[0,0],marker="s",s=24,color=PALETTE["geometry"])
        ax.scatter(*g,marker="*",s=75,color=PALETTE["gold"],edgecolor=PALETTE["ink"],zorder=4)
        ax.text(.5,.96,label,transform=ax.transAxes,ha="center",va="top",weight="bold",color=PALETTE["ink"])
        ax.text(.5,.05,rf"$\varepsilon={eps:g}^\circ$",transform=ax.transAxes,ha="center",color=PALETTE["slate"])
        style_axis(ax, r"$x$ (m)", r"$y$ (m)", equal=True); ax.set_xlim(-120,720); ax.set_ylim(-100,700); ax.grid(alpha=.12)
    fig.tight_layout(w_pad=1.0); save_figure(fig,"fig5_1_2_wedge_evolution")


def fig5_1_7_gamma_distribution() -> None:
    """Report the near-degenerate Monte-Carlo gamma distribution without a misleading histogram."""
    data = json.loads((SOURCE / "q1_scan_results.json").read_text(encoding="utf-8"))["gamma_mc"]
    labels, means, spreads = [], [], []
    for key in ("n2","n3","n4","n5"):
        vals = np.asarray(data[key]["gammas"], dtype=float); labels.append(key.replace("n","n="))
        means.append(float(np.mean(vals))); spreads.append(float(np.max(np.abs(vals-1))))
    fig, ax = plt.subplots(figsize=(6.4,3.5), facecolor=PALETTE["paper"])
    ax.axhspan(.999999,1.000001,color=PALETTE["sage"],alpha=.14,label="γ≈1 的数值容差带")
    ax.plot(labels,means,"o-",color=PALETTE["sage"],lw=2.2,ms=7)
    for x, y in zip(range(len(labels)), means):
        ax.text(x, y + 2e-7, f"{y:.6f}", ha="center", fontsize=8)
    style_axis(ax,"测站数 n",r"平均覆盖比 $\gamma$")
    ax.set_ylim(.999998,1.000002); ax.grid(axis="y",alpha=.18); ax.legend(loc="upper right")
    ax.text(.02,.06,"样本均值均等于 1（浮点误差量级）",transform=ax.transAxes,color=PALETTE["slate"],fontsize=8)
    save_figure(fig,"fig5_1_7_gamma_distribution")


def fig5_1_11_sensitivity_triplet() -> None:
    d=json.loads((SOURCE/"q1_scan_results.json").read_text(encoding="utf-8"))
    fig,axs=plt.subplots(1,3,figsize=(8.1,3.0),facecolor=PALETTE["paper"])
    specs=[("scan_phi","phi","D",r"夹角 $\phi$ (°)","D (m)"),("scan_eps","eps","D",r"误差 $\varepsilon$ (°)","D (m)"),("scan_n","n","D","测站数 n","D (m)")]
    for ax,(key,xk,yk,xlab,ylab) in zip(axs,specs):
        rows=d[key]; x=[r[xk] for r in rows]; y=[r[yk] for r in rows]
        ax.plot(x,y,"o-",color=PALETTE["geometry"],lw=1.8,ms=4); style_axis(ax,xlab,ylab); ax.grid(alpha=.16)
    fig.tight_layout(w_pad=1.1); save_figure(fig,"fig5_1_11_sensitivity_triplet")


def fig5_1_12_param_space_partition() -> None:
    d=json.loads((SOURCE/"q1_scan_results.json").read_text(encoding="utf-8"))["scan_grid"]
    ph=sorted({r["phi"] for r in d}); ep=sorted({r["eps"] for r in d}); z=np.full((len(ep),len(ph)),np.nan)
    for r in d: z[ep.index(r["eps"]),ph.index(r["phi"])] = r["D"]
    fig,ax=plt.subplots(figsize=(6.4,4.0),facecolor=PALETTE["paper"])
    im=ax.imshow(z,origin="lower",aspect="auto",cmap="YlOrBr",extent=[min(ph)-7.5,max(ph)+7.5,min(ep)-.125,max(ep)+.125])
    ax.set_xticks(ph); ax.set_yticks(ep); style_axis(ax,r"夹角 $\phi$ (°)",r"误差 $\varepsilon$ (°)"); c=fig.colorbar(im,ax=ax,pad=.02); c.set_label("D (m)"); ax.grid(alpha=.15)
    save_figure(fig,"fig5_1_12_param_space_partition")


def fig5_1_9_algorithm_flowchart() -> None:
    """A compact four-stage algorithm map for the manuscript."""
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    fig, ax = plt.subplots(figsize=(10.2, 3.6), facecolor=PALETTE["paper"])
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis("off")
    stages = [
        (0.35, "01 角域建模", "输入站址、示向度\n误差 ±ε", PALETTE["field"]),
        (2.85, "02 候选顶点", "边界射线两两求交\n跨站组合", "#DCE8F0"),
        (5.35, "03 凸包与覆盖", "顶点过滤 → 凸包 L\n直径 D / R_MEC", "#F3E2C9"),
        (7.85, "04 结论检验", "Jung 界与双实现复核\n输出 γ 与定位区域", "#D7E8DC"),
    ]
    for i,(x,title,body,fill) in enumerate(stages):
        box=FancyBboxPatch((x,.95),1.8,2.05,boxstyle="round,pad=.06,rounding_size=.12",fc=fill,ec=PALETTE["geometry"],lw=1.4)
        ax.add_patch(box); ax.text(x+.9,2.58,title,ha="center",va="center",fontsize=10,weight="bold",color=PALETTE["ink"])
        ax.text(x+.9,1.78,body,ha="center",va="center",fontsize=8.5,color=PALETTE["ink"],linespacing=1.6)
        if i < len(stages)-1:
            ax.add_patch(FancyArrowPatch((x+1.86,1.98),(x+2.36,1.98),arrowstyle="-|>",mutation_scale=14,lw=1.5,color=PALETTE["ochre"]))
    ax.text(.35,3.45,"问题一｜从角域到可核验覆盖结论",fontsize=14,weight="bold",color=PALETTE["ink"])
    ax.text(.35,.35,"三条不变量：角域闭合 · 顶点可行 · Jung 界通过",fontsize=8.5,color=PALETTE["slate"])
    save_figure(fig, "fig5_1_9_algorithm_flowchart")


def fig5_1_13_phi_D_theory() -> None:
    d=json.loads((SOURCE/"q1_scan_results.json").read_text(encoding="utf-8"))["scan_phi"]
    x=np.array([r["phi"] for r in d]); y=np.array([r["D"] for r in d]);
    fig,ax=plt.subplots(figsize=(6.4,3.8),facecolor=PALETTE["paper"])
    ax.plot(x,y,"o",color=PALETTE["geometry"],label="扫描结果")
    xx=np.linspace(x.min(),x.max(),300); ax.plot(xx, y[0]*np.sin(np.radians(20))/np.sin(np.radians(xx)),color=PALETTE["ochre"],lw=1.8,label=r"理论趋势 $D\propto1/\sin\phi$")
    style_axis(ax,r"夹角 $\phi$ (°)","定位直径 D (m)"); ax.grid(alpha=.16); ax.legend(loc="upper right"); save_figure(fig,"fig5_1_13_phi_D_theory")


import core_redesign as redesigned

fig5_1_1_single_station_wedge = lambda: redesigned.figure1(save_figure)
fig5_1_10_geometry_construction = lambda: redesigned.figure2(save_figure)
fig5_1_3_jung_counterexample = lambda: redesigned.figure3(save_figure)
fig5_1_4_jung_sandwich = lambda: redesigned.figure4(save_figure)
fig5_1_9_algorithm_flowchart = lambda: redesigned.flowchart(save_figure)

FIGURES: list[tuple[str, Callable[[], None]]] = [
    ("5.1-1", fig5_1_1_single_station_wedge),
    ("5.1-2", fig5_1_2_wedge_evolution),
    ("5.1-3", fig5_1_3_jung_counterexample),
    ("5.1-4", fig5_1_4_jung_sandwich),
    ("5.1-5", lambda: redesigned.figure5(save_figure)),
    ("5.1-6", legacy.fig_5_1_6_param_scan),
    ("5.1-7", fig5_1_7_gamma_distribution),
    ("5.1-8", fixed.fig_5_1_8_n_and_grid),
    ("5.1-9", fig5_1_9_algorithm_flowchart),
    ("5.1-10", fig5_1_10_geometry_construction),
    ("5.1-11", fig5_1_11_sensitivity_triplet),
    ("5.1-12", fig5_1_12_param_space_partition),
    ("5.1-13", fig5_1_13_phi_D_theory),
]

PAPER_FIGURES = [
    FIGURES[0],
    ("5.1-2", fig5_1_10_geometry_construction),
    FIGURES[2],
    FIGURES[3],
    FIGURES[4],
    ("5.1-9", fig5_1_9_algorithm_flowchart),
]


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Invalid PNG: {path}")
    return (int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big"))


def write_manifest() -> None:
    assets = []
    for category, directory in OUTPUTS.items():
        for png in sorted(directory.glob("*.png")):
            svg, pdf = png.with_suffix(".svg"), png.with_suffix(".pdf")
            assets.append({
                "file": str(png.relative_to(HERE)).replace("\\", "/"),
                "category": category,
                "pixels": png_dimensions(png),
                "bytes": png.stat().st_size,
                "svg": svg.exists() and svg.stat().st_size > 0,
                "pdf": pdf.exists() and pdf.stat().st_size > 0,
            })
    scan = SOURCE / "q1_scan_results.json"
    manifest = {
        "version": "v3.0",
        "backend": "Python/matplotlib",
        "exports": ["PNG 600 dpi", "SVG editable text", "PDF editable text"],
        "source_data": "source/q1_scan_results.json",
        "source_data_sha256": hashlib.sha256(scan.read_bytes()).hexdigest(),
        "assets": assets,
    }
    (HERE / "图表清单_v3.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the unified Q1 v3 figure set.")
    parser.add_argument("--paper-only", action="store_true", help="Produce five core paper figures and the algorithm flowchart.")
    args = parser.parse_args()
    prepare(legacy)
    prepare(fixed)
    targets = PAPER_FIGURES if args.paper_only else FIGURES
    with paper_layout():
        for number, make in targets:
            print(f"[generate] Figure {number}")
            make()
    write_manifest()
    (HERE / '核心图数值核验.json').write_text(json.dumps(redesigned.RESULTS,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"[complete] {len(targets)} figures written to {HERE}")


if __name__ == "__main__":
    main()
