# -*- coding: utf-8 -*-
"""接近等边三角形族: gamma 与顶点角随形状的连续过渡。
用途: 证明 gamma=1 是"退化"特例, 一般三角形 gamma>1 且直径圆不覆盖。"""
import q1_geometry_core as q

print(f"{'apex(deg)':>10} {'D':>9} {'R_MEC':>9} {'D/2':>9} {'D/sqrt3':>9} {'gamma':>8} {'min_ang':>8} {'covered':>8}")
print("-" * 82)
for d in (-40, -20, -10, -5, -1, 0, 1, 5, 10, 20, 40):
    t = q.near_equilateral(d)
    print(f"{t['apex_deg']:>10.1f} {t['D']:>9.4f} {t['R_MEC']:>9.4f} {t['jung_lo']:>9.4f} "
          f"{t['jung_hi']:>9.4f} {t['gamma']:>8.4f} {t['min_angle']:>8.2f} {str(t['covers']):>8}")

e = q.equilateral(1.0)
print()
print("等边三角形(顶角60):", "D=%.4f R=%.4f D/2=%.4f D/sqrt3=%.4f gamma=%.4f min_ang=%.2f covered=%s"
      % (e['D'], e['R_MEC'], e['jung_lo'], e['jung_hi'], e['gamma'], e['min_angle'], e['covers']))
