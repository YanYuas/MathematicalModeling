"""Get satisfaction decomposition for TOPSIS P9 solution."""
import sys, os, json
os.chdir(r'c:\Users\29845\Desktop\电工杯')
sys.path.insert(0, r'c:\Users\29845\Desktop\电工杯')
import numpy as np
from q2_biobjective_ga import get_data, solve_equilibrium, s2_continuous

data = get_data()
comm_names = data['comm_names']

# P9: D(中型)-E(小型)-F(小型)-G(小型)-J(中型)
cfg = np.zeros(10, dtype=int)
cfg[3] = 2  # D 中型
cfg[4] = 1  # E 小型
cfg[5] = 1  # F 小型
cfg[6] = 1  # G 小型
cfg[9] = 2  # J 中型

assignments, utils, comm_sats, converged = solve_equilibrium(cfg, data)
S1 = data['S1']

print("小区,分配站,S1,S2,S3,综合满意度")
for i in range(10):
    s = assignments[i]
    if s >= 0:
        s1_val = S1[i, s]
        s2_val = s2_continuous(utils[s])
        s3_val = 1.0  # Q2 assumes benchmark pricing
        total = 0.2*s1_val + 0.3*s2_val + 0.5*s3_val
        print(f"{comm_names[i]},{comm_names[s]},{s1_val:.4f},{s2_val:.4f},{s3_val:.4f},{total:.4f}")
    else:
        print(f"{comm_names[i]},无,0,0,0,0")
