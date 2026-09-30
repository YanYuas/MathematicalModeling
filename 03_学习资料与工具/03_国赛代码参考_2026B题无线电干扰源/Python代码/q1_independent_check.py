"""局部校验脚本：屏蔽 matplotlib 的绘图依赖，只执行计算与断言部分。"""
import sys, types, math, io, os, runpy

# ---- 桩 matplotlib ----
class _Noop:
    def __getattr__(self, name): return self
    def __getitem__(self, key): return self
    def __setitem__(self, key, value): return None
    def __call__(self, *a, **k): return self
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def __iter__(self): return iter([self, self])

mpl = types.ModuleType("matplotlib")
plt_mod = _Noop()
mpl.pyplot = plt_mod
sys.modules["matplotlib"] = mpl
sys.modules["matplotlib.pyplot"] = plt_mod
for sub in ("patches", "collections", "lines", "cm", "ticker", "colors"):
    sys.modules["matplotlib." + sub] = _Noop()

TARGET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "q1_main.py")
src = open(TARGET, encoding="utf-8").read()

g = {"__name__": "__main__", "__file__": TARGET}
exec(compile(src, TARGET, "exec"), g)

print()
print("=" * 60)
print("独立复核：解析值 vs 程序运行值")
print("=" * 60)

ang = g["angdiff"]
np = g["np"]
uv = g["unit_vector"]
bw = g["build_wedges"]
cv = g["candidate_vertices"]
ch = g["convex_hull"]
db = g["diameter_bruteforce"]
mb = g["mec_bruteforce"]
cov = g["covers"]
ap = g["all_diameter_pairs"]

# --- 复核 A：四舍五入角 vs 精确角 ---
print("\n[A] 四舍五入角 (59.036°, 120.964°) vs 精确角 atan2(500,±300)")
S = [np.array([0.0, 0.0]), np.array([600.0, 0.0])]
exact1 = math.degrees(math.atan2(500, 300))
exact2 = math.degrees(math.atan2(500, -300))
print(f"    精确角 = ({exact1:.9f}°, {exact2:.9f}°)")
for label, th in (("四舍五入", [59.036, 120.964]), ("精确", [exact1, exact2])):
    w = bw(S, th, 1.0)
    V = ch(cv(w))
    D, (p, q) = db(V)
    c, R = mb(V.vertices)
    ys = sorted(round(float(v[1]), 6) for v in V.vertices)
    print(f"  {label:>8}: D={D:.6f}  R_MEC={R:.6f}  γ={R/(D/2):.6f}")
    print(f"            顶点 y 值 = {ys}")
    print(f"            直径端点 = ({p[0]:.3f},{p[1]:.3f}) ↔ ({q[0]:.3f},{q[1]:.3f})")

# --- 复核 B：Jung 界断言，独立复算 ---
print("\n[B] Jung 界独立复算")
w = bw(S, [exact1, exact2], 1.0)
V = ch(cv(w))
D, _ = db(V)
c, R = mb(V.vertices)
print(f"    D/2      = {D/2:.6f}")
print(f"    R_MEC    = {R:.6f}")
print(f"    D/√3     = {D/math.sqrt(3):.6f}")
print(f"    D/2 ≤ R ≤ D/√3 ?  {D/2 - 1e-9 <= R <= D/math.sqrt(3) + 1e-9}")

# --- 复核 C：正交最优配置 ---
print("\n[C] 正交配置复核 S1=(0,0), S2=(500,500), G=(500,0)")
S3 = [np.array([0.0, 0.0]), np.array([500.0, 500.0])]
t1 = math.degrees(math.atan2(0, 500))
t2 = math.degrees(math.atan2(0 - 500, 500 - 500))
w3 = bw(S3, [t1, t2], 1.0)
V3 = ch(cv(w3))
D3, _ = db(V3)
c3, R3 = mb(V3.vertices)
gvec = np.array([500.0, 0.0])
cosphi = np.dot(gvec - S3[0], gvec - S3[1]) / (
    np.linalg.norm(gvec - S3[0]) * np.linalg.norm(gvec - S3[1]))
print(f"    θ1={t1:.6f}  θ2={t2:.6f}   交会角 φ={math.degrees(math.acos(cosphi)):.4f}°")
print(f"    D={D3:.6f}  R_MEC={R3:.6f}")
