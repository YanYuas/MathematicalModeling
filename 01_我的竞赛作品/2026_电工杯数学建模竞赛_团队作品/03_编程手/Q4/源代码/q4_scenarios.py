"""
Q4 灵敏度分析 — 直接复用Q2+Q3已有代码
=========================================
Scenarios: A(人口) B(成本) C(预算) vs 基线
只改参数构造, 不复写任何算法

Code: C:/Users/29845/Desktop/问题4
"""
import numpy as np, os, sys
sys.path.insert(0, r'C:/Users/29845/Desktop/电工杯')
sys.path.insert(0, r'C:/Users/29845/Desktop/电工杯/问题三/代码')

from q2_biobjective_ga import (get_data as q2_get_data, solve_equilibrium,
    s2_continuous, evaluate_config, non_dominated_sort)
from itertools import combinations

COMM_NAMES = list('ABCDEFGHIJ')
SVC_NAMES = ['助餐','日间照料','上门护理','康复理疗','助浴','紧急救助']
BASE_PRICE = np.array([10,20,30,28,25,0])
DIRECT_COST = np.array([8,16,24,23,20,8])
NON_EMERG = [0,1,2,3,4]

# ============================================================
# Q1: 参数化马尔可夫递推
# ============================================================
RAW_N0 = np.array([
    [496,152,64],[408,136,64],[632,208,80],[368,120,56],[536,176,72],
    [328,104,40],[592,192,80],[392,128,48],[504,168,64],[456,144,56],
], dtype=float)

INCOME_V = np.array([3400,3100,3800,2900,3500,2700,3600,3000,3300,3200])
CAP_RATIO_V = np.array([0.20,0.25,0.30])
DEMAND_PP = np.array([[14,20,22],[8,14,18],[0,6,12],[2,4,6],[0,2,4],[0.15,1,3]])
DIST = np.array([[0,600,1200,900,1500,1800,1300,700,1100,500],
    [600,0,800,500,1100,1400,900,400,700,300],[1200,800,0,700,600,900,500,900,600,700],
    [900,500,700,0,800,1100,600,300,500,400],[1500,1100,600,800,0,500,400,1000,500,800],
    [1800,1400,900,1100,500,0,500,1200,700,1100],[1300,900,500,600,400,500,0,800,400,600],
    [700,400,900,300,1000,1200,800,0,600,300],[1100,700,600,500,500,700,400,600,0,400],
    [500,300,700,400,800,1100,600,300,400,0]])

def run_markov(lam, Pa, Pb, d=0.05, years=5):
    P = np.array([[(1-d)*(1-Pa)+lam, lam, lam],
                  [(1-d)*Pa, (1-d)*(1-Pb), 0],
                  [0, (1-d)*Pb, (1-d)]])
    res = np.zeros((10,3,years+1), dtype=float)
    for c in range(10):
        N = RAW_N0[c].copy(); res[c,:,0] = N
        for t in range(1,years+1):
            Nf = P @ N
            N = np.array([round(Nf[0]), round(Nf[1]), round(Nf[2])])
            res[c,:,t] = N
    return res[:,:,years]


# ============================================================
# 构造Q2 data (参数化N5, cost_mult, budget)
# ============================================================
def build_data(N5, cost_mult=1.0, budget=120):
    n_comm = 10
    elderly_total = N5.sum(axis=1)
    monthly_svc = np.zeros((n_comm,6)); monthly_tot = np.zeros(n_comm)
    for i in range(n_comm):
        caps = INCOME_V[i] * CAP_RATIO_V
        for t in range(3):
            n = N5[i,t]
            if n==0: continue
            theo = DEMAND_PP[:,t]; tc = (theo * BASE_PRICE).sum()
            if tc <= caps[t]:
                con = np.round(n*theo)/n
            else:
                r = caps[t]/tc; con = np.round(theo*r)
                for _ in range(30):
                    if (con*BASE_PRICE).sum()<=caps[t]: break
                    ov = (con - theo*r)*BASE_PRICE; w = np.argmax(ov)
                    if con[w]<=0: break
                    con[w]-=1
            monthly_svc[i] += n*con
        monthly_tot[i] = monthly_svc[i].sum()
    daily_demand = monthly_tot/30

    S1 = np.zeros((n_comm,n_comm))
    for i in range(n_comm):
        for j in range(n_comm):
            d = DIST[i,j]
            if d<=300: S1[i,j]=1.0
            elif d<=500: S1[i,j]=0.9
            elif d<=650: S1[i,j]=0.75
            elif d<=1000: S1[i,j]=0.6

    return {
        'N5_raw':N5, 'elderly_total':elderly_total, 'total_elderly':elderly_total.sum(),
        'daily_demand':daily_demand, 'monthly_service_demand':monthly_svc,
        'dist':DIST, 'S1':S1, 'reachable':DIST<=1000,
        'n_comm':n_comm, 'comm_names':COMM_NAMES,
        'scale_names':['小型','中型','大型'],
        'scale_capacity':np.array([1000,2000,3000]),
        'construct_cost':np.array([18,32,45]),
        'daily_operating':np.array([2000,3200,4400])*cost_mult,
        'MAX_BUDGET':budget,
    }


# ============================================================
# Q2: 枚举 (复用evaluate_config)
# ============================================================
def _topsis_select(C,S):
    n=len(C)
    if n<=1: return 0
    m=np.column_stack([C,S]); nrm=np.sqrt((m**2).sum(axis=0)); nrm[nrm==0]=1
    W=m/nrm*np.array([0.5,0.5])
    dp=np.sqrt(((W-W.max(axis=0))**2).sum(axis=1))
    dn=np.sqrt(((W-W.min(axis=0))**2).sum(axis=1))
    return (dn/(dp+dn+1e-12)).argmax()

def enumerate_q2(data):
    n_comm=10; cc=data['construct_cost']; MB=data['MAX_BUDGET']
    cfgs=[]; CV=[]; SV=[]
    for k in range(1,min(6,MB//18)+1):
        for pos in combinations(range(n_comm),k):
            for sc in range(3**k):
                s=np.zeros(k,dtype=int); tmp=sc
                for si in range(k): s[si]=(tmp%3)+1; tmp//=3
                cfg=np.zeros(n_comm,dtype=int); tc=0
                for si in range(k): cfg[pos[si]]=s[si]; tc+=cc[s[si]-1]
                if tc<=MB: cfgs.append(cfg)
    print(f'    枚举{len(cfgs)}配置...')
    for cfg in cfgs:
        C,S,_,_,_,_ = evaluate_config(cfg, data)
        CV.append(C); SV.append(S)
    CV=np.array(CV); SV=np.array(SV)
    fronts=non_dominated_sort(CV,SV); pidx=fronts[0]
    pC=CV[pidx]; pS=SV[pidx]; pcfgs=[cfgs[i] for i in pidx]
    # 去重
    uniq={}
    for i in range(len(pC)):
        kk=(round(pC[i],6),round(pS[i],6))
        if kk not in uniq: uniq[kk]=pcfgs[i]
    dC=np.array([k[0] for k in uniq]); dS=np.array([k[1] for k in uniq])
    dcfgs=list(uniq.values()); o=np.argsort(dC); dC=dC[o]; dS=dS[o]; dcfgs=[dcfgs[i] for i in o]
    ti=_topsis_select(dC,dS); best=dcfgs[ti]
    st=np.where(best>0)[0]; tc=sum(cc[c-1] for c in best if c>0)
    Cb,Sb,asgn,utils,csats,_=evaluate_config(best,data)
    return {'config':best,'stations':st,'n_stations':len(st),'cost':tc,
            'coverage':Cb,'satisfaction':Sb,'assignments':asgn,
            'utils':utils,'comm_sats':csats,'pareto_C':dC,'pareto_S':dS}


# ============================================================
# Q3: 枚举定价 (复用Q3逻辑, 简化版)
# ============================================================
S3_COMBOS = []
for code in range(4**5):
    c=np.zeros(5,dtype=int); tmp=code
    for k in range(5): c[k]=tmp%4; tmp//=4
    S3_COMBOS.append(c)

def s3_range(lv,bp):
    if lv==0: return (bp*.5,bp)
    if lv==1: return (bp,bp*1.1)
    if lv==2: return (bp*1.1,bp*1.2)
    return (bp*1.2,bp*2.)

def station_profit(prices, scov, data, config, s):
    N5=data['N5_raw']; cap=data['scale_capacity'][config[s]-1]
    m6=np.zeros(6)
    for ci in scov:
        caps=INCOME_V[ci]*CAP_RATIO_V
        for t in range(3):
            n=N5[ci,t]
            if n==0: continue
            theo=DEMAND_PP[:,t]; tc=(theo*prices).sum()
            if tc<=caps[t]: con=np.round(n*theo)/n
            else:
                r=caps[t]/tc; con=np.round(theo*r)
                for _ in range(30):
                    if (con*prices).sum()<=caps[t]: break
                    ov=(con-theo*r)*prices; w=np.argmax(ov)
                    if con[w]<=0: break; con[w]-=1
            m6+=n*con
    d6=m6/30; dt=d6.sum()
    if dt>cap: d6=d6*(cap/dt)
    et=d6.sum(); util=et/cap; s2=s2_continuous(util)
    s3v=np.ones(6)
    for k in range(6):
        bp=BASE_PRICE[k]
        if bp==0: s3v[k]=1.
        elif prices[k]<=bp: s3v[k]=1.
        elif prices[k]<=bp*1.1: s3v[k]=.9
        elif prices[k]<=bp*1.2: s3v[k]=.75
        else: s3v[k]=.6
    S1v=data['S1'][list(scov),s]
    ecov=data['elderly_total'][list(scov)]
    csats=np.zeros(len(scov))
    for ii in range(len(scov)):
        a3=(d6*s3v).sum()/d6.sum() if d6.sum()>0 else 1.
        csats[ii]=.2*S1v[ii]+.3*s2+.5*a3
    sat=(csats*ecov).sum()/ecov.sum() if ecov.sum()>0 else 0
    rev=(d6*prices).sum()*365; dc=(d6*DIRECT_COST).sum()*365
    scaps={1:1000,2:1800,3:2600}
    dsr=d6[NON_EMERG].sum()*2.; ds=min(dsr,scaps[config[s]])
    oper=data['daily_operating'][config[s]-1]*365
    depr=data['construct_cost'][config[s]-1]*10000/20
    gross=rev-dc; tc=oper+depr; pr=(gross+ds*365-tc)/tc
    return pr,sat,s3v,ds,et,util,d6

def optimize_q3(q2r, data):
    config=q2r['config']; sts=q2r['stations']; asgns=q2r['assignments']
    sc={s: np.where(asgns==s)[0] for s in sts}
    results={}
    for s in sts:
        best={'satisfaction':0}
        for combo in S3_COMBOS:
            lo=np.zeros(6); hi=np.zeros(6)
            for k in range(5): lo[k],hi[k]=s3_range(combo[k],BASE_PRICE[k])
            lo[5]=hi[5]=0
            prl,_,_,_,_,_,_=station_profit(lo,sc[s],data,config,s)
            prh,_,_,_,_,_,_=station_profit(hi,sc[s],data,config,s)
            if prl>.08 or prh<0: continue
            a,b=0.,1.; bp=None
            for _ in range(40):
                m=(a+b)/2; mp=lo+m*(hi-lo); mp[5]=0
                prm,_,_,_,_,_,_=station_profit(mp,sc[s],data,config,s)
                if prm>.08: b=m
                elif prm<0: a=m
                else: bp=mp.copy(); b=m
            if bp is not None:
                pf,sf,s3f,subf,efff,utilf,_=station_profit(bp,sc[s],data,config,s)
                if sf>best['satisfaction']:
                    best.update({'s3_combo':combo,'prices':bp.copy(),'profit_rate':pf,
                        'satisfaction':sf,'s3_vals':s3f,'daily_subsidy':subf,
                        'effective_total':efff,'utilization':utilf})
        results[s]=best
    return results,sc


# ============================================================
# 主程序: 3场景 + 基线
# ============================================================
def run_scenario(name, lam, Pa, Pb, cost_mult, budget, N5_override=None):
    sep = '=' * 60
    print(f'\n{sep}')
    print(f'Q4 {name}')
    print(f'λ={lam}, Pα={Pa}, Pβ={Pb}, 成本×{cost_mult}, 预算={budget}万')
    print('='*60)
    if N5_override is not None:
        N5=N5_override
    else:
        N5=run_markov(lam,Pa,Pb)
    print(f'Q1: N5总老人={N5.sum():.0f}')
    data=build_data(N5,cost_mult,budget)
    q2=enumerate_q2(data)
    print(f'Q2: {q2["n_stations"]}站 {q2["cost"]}万 C={q2["coverage"]:.4f} S={q2["satisfaction"]:.4f}')
    for s in q2['stations']:
        cov=np.where(q2['assignments']==s)[0]
        print(f'  站{COMM_NAMES[s]}({data["scale_names"][q2["config"][s]-1]}): {",".join(COMM_NAMES[c] for c in cov)} u={q2["utils"][s]:.3f}')
    q3,sc=optimize_q3(q2,data)
    print('Q3 最优定价:')
    for s in q2['stations']:
        r=q3[s]; ps=' '.join(f'{SVC_NAMES[k]}={r["prices"][k]:.2f}' for k in range(5))
        print(f'  站{COMM_NAMES[s]}: {ps} S3={r["s3_combo"]} pr={r["profit_rate"]*100:.2f}% sat={r["satisfaction"]:.4f}')
    return {'N5_total':float(N5.sum()),'q2':q2,'q3':q3,'data':data,'sc':sc}

# ===== 运行 =====
print('Q4 灵敏度分析 — 复用Q2/Q3验证代码')
print('='*60)

# 基线: 直接用Q2原始data
data_old = q2_get_data()
N5_old = data_old['N5_raw']
baseline = run_scenario('基线 (原始Q2 data)', 0.07,0.045,0.10,1.0,120, N5_override=N5_old)

scenario_A = run_scenario('场景A 人口结构', 0.08,0.055,0.095,1.0,120)

scenario_B = run_scenario('场景B 成本变化', 0.07,0.045,0.10,1.2,120, N5_override=N5_old)

scenario_C = run_scenario('场景C 预算调整', 0.07,0.045,0.10,1.0,140, N5_override=N5_old)

# ===== 对比表 =====
print(f'\n{"="*60}')
print('Q4 新旧方案对比')
print('='*60)
print(f'{"指标":<20} {"基线":<15} {"A(人口)":<15} {"B(成本)":<15} {"C(预算)":<15}')
print('-'*75)
print(f'{"站点数":<20} {baseline["q2"]["n_stations"]:<15} {scenario_A["q2"]["n_stations"]:<15} {scenario_B["q2"]["n_stations"]:<15} {scenario_C["q2"]["n_stations"]:<15}')
print(f'{"建设成本(万)":<20} {baseline["q2"]["cost"]:<15} {scenario_A["q2"]["cost"]:<15} {scenario_B["q2"]["cost"]:<15} {scenario_C["q2"]["cost"]:<15}')
print(f'{"覆盖率":<20} {baseline["q2"]["coverage"]:<15.4f} {scenario_A["q2"]["coverage"]:<15.4f} {scenario_B["q2"]["coverage"]:<15.4f} {scenario_C["q2"]["coverage"]:<15.4f}')
print(f'{"满意度(Q2)":<20} {baseline["q2"]["satisfaction"]:<15.4f} {scenario_A["q2"]["satisfaction"]:<15.4f} {scenario_B["q2"]["satisfaction"]:<15.4f} {scenario_C["q2"]["satisfaction"]:<15.4f}')
print(f'{"站点布局":<20} {"C中D中G大":<15} —              —              —')

# 保存
import json
out = r'C:/Users/29845/Desktop/问题4'
for name,r in [('baseline',baseline),('scenario_A',scenario_A),('scenario_B',scenario_B),('scenario_C',scenario_C)]:
    jd = {
        'scenario':name,
        'N5_total':r['N5_total'],
        'q2':{'n_stations':int(r['q2']['n_stations']),'cost':int(r['q2']['cost']),
              'coverage':float(r['q2']['coverage']),'satisfaction':float(r['q2']['satisfaction']),
              'stations':[{'name':COMM_NAMES[s],'scale':r['data']['scale_names'][r['q2']['config'][s]-1]} for s in r['q2']['stations']]},
        'q3':{COMM_NAMES[s]:{'prices':{SVC_NAMES[k]:float(r['q3'][s]['prices'][k]) for k in range(5)},
                             's3_combo':[int(x) for x in r['q3'][s]['s3_combo']],
                             'profit_rate':float(r['q3'][s]['profit_rate']),
                             'satisfaction':float(r['q3'][s]['satisfaction'])} for s in r['q2']['stations']}
    }
    with open(f'{out}/{name}_result.json','w',encoding='utf-8') as f:
        json.dump(jd,f,ensure_ascii=False,indent=2)

print(f'\n结果JSON已保存到 {out}/')
