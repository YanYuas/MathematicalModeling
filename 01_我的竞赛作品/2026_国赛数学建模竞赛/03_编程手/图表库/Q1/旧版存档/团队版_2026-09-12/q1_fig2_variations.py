"""
Fig2 Jung反例 - 配色方案迭代（信息图专家设计）
使用设计迭代方法生成3个配色变体，对比视觉效果

设计目标：测试不同配色对"失败vs成功"对比度的影响
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon as MplPolygon, Arc, ConnectionPatch
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import os

# ============================================================================
# 三套配色方案
# ============================================================================

SCHEMES = {
    "ink_ochre": {
        "name": "Ink & Ochre (baseline)",
        "ink": "#1C1C1C",
        "slate": "#5B6B73",
        "paper": "#F7F4EE",
        "field": "#C5D4E0",
        "geometry": "#2C4A6E",
        "ochre": "#C47B2B",
        "failure": "#8C3A2A",  # rust
        "success": "#4F6F5C",  # sage
    },
    "teal_coral": {
        "name": "Teal & Coral",
        "ink": "#1C1C1C",
        "slate": "#5B6B73",
        "paper": "#F5F5F0",
        "field": "#B8D4D8",
        "geometry": "#3D5A80",
        "ochre": "#E07A5F",  # coral for emphasis
        "failure": "#E07A5F",  # coral
        "success": "#3D5A80",  # teal
    },
    "violet_amber": {
        "name": "Violet & Amber",
        "ink": "#2B2B2B",
        "slate": "#6B6B6B",
        "paper": "#F9F6F0",
        "field": "#D4C5E0",
        "geometry": "#7B68A6",
        "ochre": "#F4A261",  # amber for emphasis
        "failure": "#D96459",  # warm red
        "success": "#7B68A6",  # violet
    }
}

LW = {'main': 2.2, 'theory': 1.4, 'aux': 0.7}
DPI = 300

