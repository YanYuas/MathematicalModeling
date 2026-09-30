# -*- coding: utf-8 -*-
"""精度核对：P4 的 y 坐标、D、R_MEC 的高精度值与两个文献口径的差。"""
from fractions import Fraction
import math
from decimal import Decimal, getcontext
getcontext().prec = 50

# tan(59.0362435deg) 由 G=(300,500) 定义：t0 = 500/300
t0 = Fraction(500,300)
print("theta1 =", math.degrees(math.atan2(500,300)))
print("t0 = 500/300 =", float(t0))

# P4 = 交点( S1 射线 60.0362435度 , x=300 因对称 )
# 用高精度: tan(a+b)
import mpmath as mp
print("mpmath:", mp.__version__)
mp.mp.dps = 40
th1 = mp.atan2(500,300)
th2 = mp.atan2(500,-300)
eps = mp.pi/180
P4y = 300*mp.tan(th1+eps)
P2y = 300*mp.tan(th1-eps)
print("P4y high =", mp.nstr(P4y, 20))
print("P2y high =", mp.nstr(P2y, 20))
D = P4y-P2y
print("D high   =", mp.nstr(D, 20))
R = D/2
print("R_MEC    =", mp.nstr(R, 20))
print("D/sqrt3  =", mp.nstr(D/mp.sqrt(3), 20))
print()
print("doc P4 = 520.3752 ; computed =", mp.nstr(P4y,8), " diff =", mp.nstr(P4y-mp.mpf('520.3752'),5))
print("doc D  = 39.5983  ; computed =", mp.nstr(D,8),   " diff =", mp.nstr(D-mp.mpf('39.5983'),5))
print("doc R  = 19.7992  ; computed =", mp.nstr(R,8),   " diff =", mp.nstr(R-mp.mpf('19.7992'),5))
