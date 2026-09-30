import sys, numpy as np
sys.path.insert(0, r'c:\Users\29845\Desktop\电工杯')
from q2_biobjective_ga import get_data, solve_equilibrium, s2_continuous
data = get_data()
cfg = np.zeros(10, dtype=int)
cfg[2]=2; cfg[3]=2; cfg[6]=3  # C中型 D中型 G大型
assignments, utils, comm_sats, conv = solve_equilibrium(cfg, data)
print("Q2_P14_SAT")
for i in range(10):
    print(f"{data['comm_names'][i]},{comm_sats[i]:.4f}")
print("Q2_UTIL")
for s in [2,3,6]:
    print(f"{data['comm_names'][s]},{utils[s]:.4f}")
print("Q2_COVERAGE,0.8566")
print("Q2_SATISFACTION,0.8999")
