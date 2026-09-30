"""
Q4 GA全场景 — 复用NSGA-II, 3场景+基线
==========================================
"""
import numpy as np, os, sys, json, time
sys.path.insert(0, r'C:/Users/29845/Desktop/电工杯')
from q2_biobjective_ga import (get_data as q2_get_data, solve_equilibrium,
    s2_continuous, evaluate_config, non_dominated_sort, crowding_distance)

COMM = list('ABCDEFGHIJ'); SVC = ['助餐','日间照料','上门护理','康复理疗','助浴','紧急救助']
BP = np.array([10,20,30,28,25,0]); DC = np.array([8,16,24,23,20,8]); NE = [0,1,2,3,4]
INCOME = np.array([3400,3100,3800,2900,3500,2700,3600,3000,3300,3200])
CR = np.array([0.20,0.25,0.30])
DPP = np.array([[14,20,22],[8,14,18],[0,6,12],[2,4,6],[0,2,4],[0.15,1,3]])
DIST = np.array([[0,600,1200,900,1500,1800,1300,700,1100,500],[600,0,800,500,1100,1400,900,400,700,300],[1200,800,0,700,600,900,500,900,600,700],[900,500,700,0,800,1100,600,300,500,400],[1500,1100,600,800,0,500,400,1000,500,800],[1800,1400,900,1100,500,0,500,1200,700,1100],[1300,900,500,600,400,500,0,800,400,600],[700,400,900,300,1000,1200,800,0,600,300],[1100,700,600,500,500,700,400,600,0,400],[500,300,700,400,800,1100,600,300,400,0]])
RAW = np.array([[496,152,64],[408,136,64],[632,208,80],[368,120,56],[536,176,72],[328,104,40],[592,192,80],[392,128,48],[504,168,64],[456,144,56]],dtype=float)


def q1_markov(lam,Pa,Pb,d=0.05,y=5):
    P=np.array([[(1-d)*(1-Pa)+lam,lam,lam],[(1-d)*Pa,(1-d)*(1-Pb),0],[0,(1-d)*Pb,(1-d)]])
    res=np.zeros((10,3,y+1))
    for c in range(10):
        N=RAW[c].copy(); res[c,:,0]=N
        for t in range(1,y+1):
            Nf=P@N; N=np.array([round(Nf[0]),round(Nf[1]),round(Nf[2])]); res[c,:,t]=N
    return res[:,:,y]


def build_data(N5, cost_m=1.0, budget=120):
    n=10; et=N5.sum(axis=1); ms=np.zeros((n,6)); mt=np.zeros(n)
    for i in range(n):
        caps=INCOME[i]*CR
        for t in range(3):
            nn=N5[i,t]
            if nn==0: continue
            th=DPP[:,t]; tc=(th*BP).sum()
            if tc<=caps[t]: con=np.round(nn*th)/nn
            else:
                r=caps[t]/tc; con=np.round(th*r)
                for _ in range(30):
                    if (con*BP).sum()<=caps[t]: break
                    ov=(con-th*r)*BP; w=np.argmax(ov)
                    if con[w]<=0: break; con[w]-=1
            ms[i]+=nn*con
        mt[i]=ms[i].sum()
    dd=mt/30; S1=np.zeros((n,n))
    for i in range(n):
        for j in range(n):
            d=DIST[i,j]
            if d<=300: S1[i,j]=1.
            elif d<=500: S1[i,j]=.9
            elif d<=650: S1[i,j]=.75
            elif d<=1000: S1[i,j]=.6
    return {'N5_raw':N5,'elderly_total':et,'total_elderly':et.sum(),'daily_demand':dd,
        'monthly_service_demand':ms,'dist':DIST,'S1':S1,'reachable':DIST<=1000,
        'n_comm':n,'comm_names':COMM,'scale_names':['小型','中型','大型'],
        'scale_capacity':np.array([1000,2000,3000]),'construct_cost':np.array([18,32,45]),
        'daily_operating':np.array([2000,3200,4400])*cost_m,'MAX_BUDGET':budget}


# ===== GA =====
def gen_cfg(data):
    while True:
        c=np.random.randint(0,4,10); cost=sum(data['construct_cost'][x-1] for x in c if x>0)
        if cost<=data['MAX_BUDGET'] and c.any(): return c

def repair(cfg,data):
    cc=data['construct_cost']; MB=data['MAX_BUDGET']
    tc=sum(cc[x-1] for x in cfg if x>0); sts=np.where(cfg>0)[0].tolist()
    while tc>MB and sts:
        idx=np.random.choice(sts)
        if cfg[idx]>1: tc-=cc[cfg[idx]-1]-cc[cfg[idx]-2]; cfg[idx]-=1
        else: tc-=cc[0]; cfg[idx]=0; sts=np.where(cfg>0)[0].tolist()
    if not cfg.any(): cfg[np.random.randint(10)]=1
    return cfg

def ga_run(data, pop=60, gen=50, elite=6):
    n=10; allC=[]; allS=[]; allCfg=[]
    for run in range(3):
        np.random.seed(run*137+42)
        pop_arr=np.array([gen_cfg(data) for _ in range(pop)])
        CV=np.zeros(pop); SV=np.zeros(pop)
        for i in range(pop): CV[i],SV[i],_,_,_,_=evaluate_config(pop_arr[i],data)
        for g in range(gen):
            fronts=non_dominated_sort(CV,SV)
            fr=np.full(pop,999)
            for rk,frnt in enumerate(fronts):
                for idx in frnt: fr[idx]=rk
            crwd={}
            for frnt in fronts:
                if len(frnt)>0: crwd.update(crowding_distance(frnt,CV,SV))
            order=sorted(range(pop),key=lambda i:(fr[i],-crwd.get(i,0)))[:elite]
            new_pop=np.zeros_like(pop_arr); new_pop[:elite]=pop_arr[order]
            for i in range(elite,pop):
                cand=np.random.choice(pop,5,replace=False)
                a=cand[0]; b=cand[0]
                for cc in cand[1:]:
                    if fr[cc]<fr[a] or (fr[cc]==fr[a] and crwd.get(cc,0)>crwd.get(a,0)): a=cc
                    if fr[cc]<fr[b] or (fr[cc]==fr[b] and crwd.get(cc,0)>crwd.get(b,0)): b=cc
                if np.random.rand()<0.8:
                    cp=np.random.randint(1,n); child=np.concatenate([pop_arr[a][:cp],pop_arr[b][cp:]])
                else: child=pop_arr[a].copy()
                if np.random.rand()<0.15: child[np.random.randint(n)]=np.random.randint(0,4)
                new_pop[i]=repair(child,data)
            pop_arr=new_pop
            for i in range(pop): CV[i],SV[i],_,_,_,_=evaluate_config(pop_arr[i],data)
        frts=non_dominated_sort(CV,SV)
        for idx in frts[0]: allC.append(CV[idx]); allS.append(SV[idx]); allCfg.append(pop_arr[idx].copy())
    # 合并去重
    allC=np.array(allC); allS=np.array(allS)
    uniq={}
    for i in range(len(allC)):
        k=(round(allC[i],6),round(allS[i],6))
        if k not in uniq: uniq[k]=allCfg[i]
    dC=np.array([k[0] for k in uniq]); dS=np.array([k[1] for k in uniq])
    dcfgs=list(uniq.values()); o=np.argsort(dC); dC=dC[o]; dS=dS[o]; dcfgs=[dcfgs[i] for i in o]
    # TOPSIS
    n2=len(dC)
    if n2<=1: ti=0
    else:
        m=np.column_stack([dC,dS]); nr=np.sqrt((m**2).sum(axis=0)); nr[nr==0]=1
        W=m/nr*np.array([0.5,0.5])
        dp=np.sqrt(((W-W.max(axis=0))**2).sum(axis=1))
        dn=np.sqrt(((W-W.min(axis=0))**2).sum(axis=1))
        ti=(dn/(dp+dn+1e-12)).argmax()
    best=dcfgs[ti]; st=np.where(best>0)[0]
    tc=sum(data['construct_cost'][x-1] for x in best if x>0)
    Cb,Sb,asgn,utils,csats,_=evaluate_config(best,data)
    return {'config':best,'stations':st,'n_stations':len(st),'cost':tc,
        'coverage':Cb,'satisfaction':Sb,'assignments':asgn,'utils':utils,
        'comm_sats':csats,'pareto_C':dC,'pareto_S':dS}


# ===== Q3 定价 (枚举, 快) =====
S3_COMBOS=[np.array([(c//(4**k))%4 for k in range(5)]) for c in range(1024)]

def s3r(lv,bp):
    if lv==0: return (bp*.5,bp)
    if lv==1: return (bp,bp*1.1)
    if lv==2: return (bp*1.1,bp*1.2)
    return (bp*1.2,bp*2.)

def st_profit(prices, scov, data, config, s):
    N5=data['N5_raw']; cap=data['scale_capacity'][config[s]-1]; m6=np.zeros(6)
    for ci in scov:
        caps=INCOME[ci]*CR
        for t in range(3):
            n=N5[ci,t]
            if n==0: continue
            th=DPP[:,t]; tc=(th*prices).sum()
            if tc<=caps[t]: con=np.round(n*th)/n
            else:
                r=caps[t]/tc; con=np.round(th*r)
                for _ in range(30):
                    if (con*prices).sum()<=caps[t]: break
                    ov=(con-th*r)*prices; w=np.argmax(ov)
                    if con[w]<=0: break; con[w]-=1
            m6+=n*con
    d6=m6/30; dt=d6.sum()
    if dt>cap: d6=d6*(cap/dt)
    et=d6.sum(); util=et/cap; s2=s2_continuous(util)
    s3a=np.ones(6)
    for k in range(6):
        b=BP[k]
        if b==0: s3a[k]=1.
        elif prices[k]<=b: s3a[k]=1.
        elif prices[k]<=b*1.1: s3a[k]=.9
        elif prices[k]<=b*1.2: s3a[k]=.75
        else: s3a[k]=.6
    S1=data['S1'][list(scov),s]; ec=data['elderly_total'][list(scov)]
    cs=np.zeros(len(scov))
    for ii in range(len(scov)):
        a3=(d6*s3a).sum()/d6.sum() if d6.sum()>0 else 1.
        cs[ii]=.2*S1[ii]+.3*s2+.5*a3
    sat=(cs*ec).sum()/ec.sum() if ec.sum()>0 else 0
    rev=(d6*prices).sum()*365; dcost=(d6*DC).sum()*365
    scaps={1:1000,2:1800,3:2600}
    dsr=d6[NE].sum()*2.; ds=min(dsr,scaps[config[s]])
    oper=data['daily_operating'][config[s]-1]*365; depr=data['construct_cost'][config[s]-1]*10000/20
    gross=rev-dcost; tc2=oper+depr; pr=(gross+ds*365-tc2)/tc2
    return pr,sat,s3a,ds,et,util,d6

def q3_opt(q2r, data):
    config=q2r['config']; sts=q2r['stations']; asgns=q2r['assignments']
    sc={s:np.where(asgns==s)[0] for s in sts}; results={}
    for s in sts:
        best={'satisfaction':0}
        for combo in S3_COMBOS:
            lo=np.zeros(6); hi=np.zeros(6)
            for k in range(5): lo[k],hi[k]=s3r(combo[k],BP[k])
            lo[5]=hi[5]=0
            prl,_,_,_,_,_,_=st_profit(lo,sc[s],data,config,s)
            prh,_,_,_,_,_,_=st_profit(hi,sc[s],data,config,s)
            if prl>.08 or prh<0: continue
            a,b=0.,1.; bp2=None
            for _ in range(40):
                m=(a+b)/2; mp=lo+m*(hi-lo); mp[5]=0
                prm,_,_,_,_,_,_=st_profit(mp,sc[s],data,config,s)
                if prm>.08: b=m
                elif prm<0: a=m
                else: bp2=mp.copy(); b=m
            if bp2 is not None:
                pf,sf,s3f,subf,efff,utilf,_=st_profit(bp2,sc[s],data,config,s)
                if sf>best['satisfaction']:
                    best.update({'s3_combo':combo,'prices':bp2.copy(),'profit_rate':pf,
                        'satisfaction':sf,'s3_vals':s3f,'daily_subsidy':subf,
                        'effective_total':efff,'utilization':utilf})
        results[s]=best
    return results


# ===== 主程序 =====
SEP55 = '='*55
def run_scene(name, lam, Pa, Pb, cm, budget, n5_override=None):
    print('\n' + SEP55)
    print(f'{name}: lam={lam} Pa={Pa} Pb={Pb} cost*{cm} budget={budget}')
    print(SEP55)
    t0=time.time()
    if n5_override is not None: N5=n5_override
    else: N5=q1_markov(lam,Pa,Pb)
    print(f'Q1: N5={N5.sum():.0f}')
    data=build_data(N5,cm,budget)
    q2=ga_run(data)
    ns = q2['n_stations']
    ct = q2['cost']
    cv = q2['coverage']
    sf = q2['satisfaction']
    print(f'Q2(GA): {ns}站 {ct}万 C={cv:.4f} S={sf:.4f} ({time.time()-t0:.0f}s)')
    for s in q2['stations']:
        cov=np.where(q2['assignments']==s)[0]
        sn = data['scale_names'][q2['config'][s]-1]
        cv_list = ','.join(COMM[c] for c in cov)
        u_val = q2['utils'][s]
        print(f'  站{COMM[s]}({sn}): {cv_list}, u={u_val:.3f}')
    q3=q3_opt(q2,data)
    for s in q2['stations']:
        r=q3[s]
        parts = []
        for k in range(5):
            parts.append(SVC[k] + '=' + f'{r["prices"][k]:.2f}')
        ps = ' '.join(parts)
        sc = str(r['s3_combo'])
        pr_val = r['profit_rate'] * 100
        sat_val = r['satisfaction']
        print(f'  Q3 {COMM[s]}: {ps} S3={sc} pr={pr_val:.1f}% sat={sat_val:.4f}')
    return {'N5':float(N5.sum()),'q2':q2,'q3':q3,'data':data}

# ===== 执行 =====
print('Q4 GA All Scenarios')
print(SEP55)
old_data=q2_get_data(); N5_old=old_data['N5_raw']
base=run_scene('BASELINE',0.07,0.045,0.10,1.0,120,N5_old)
A=run_scene('A_POP',0.08,0.055,0.095,1.0,120)
B=run_scene('B_COST',0.07,0.045,0.10,1.2,120,N5_old)
C=run_scene('C_BUDGET',0.07,0.045,0.10,1.0,140,N5_old)

print('\n' + SEP55)
print('对比表')
print(SEP55)
hdr = ['','基线','A人口','B成本','C预算']
row1 = ['站点数',str(base['q2']['n_stations']),str(A['q2']['n_stations']),str(B['q2']['n_stations']),str(C['q2']['n_stations'])]
row2 = ['成本',str(base['q2']['cost']),str(A['q2']['cost']),str(B['q2']['cost']),str(C['q2']['cost'])]
bC = base['q2']['coverage']; aC = A['q2']['coverage']; bC2 = B['q2']['coverage']; cC = C['q2']['coverage']
bS = base['q2']['satisfaction']; aS = A['q2']['satisfaction']; bS2 = B['q2']['satisfaction']; cS = C['q2']['satisfaction']
row3 = ['覆盖率', '{:.4f}'.format(bC), '{:.4f}'.format(aC), '{:.4f}'.format(bC2), '{:.4f}'.format(cC)]
row4 = ['满意度', '{:.4f}'.format(bS), '{:.4f}'.format(aS), '{:.4f}'.format(bS2), '{:.4f}'.format(cS)]
for r in [hdr,row1,row2,row3,row4]:
    print(f'{r[0]:<10} {r[1]:<10} {r[2]:<10} {r[3]:<10} {r[4]:<10}')

out='C:/Users/29845/Desktop/问题4'
for nm,r in [('ga_baseline',base),('ga_scenario_A',A),('ga_scenario_B',B),('ga_scenario_C',C)]:
    jd={'scenario':nm,'N5_total':r['N5'],
        'q2':{'n_stations':int(r['q2']['n_stations']),'cost':int(r['q2']['cost']),
              'coverage':float(r['q2']['coverage']),'satisfaction':float(r['q2']['satisfaction']),
              'stations':[{'name':COMM[s],'scale':r['data']['scale_names'][r['q2']['config'][s]-1]} for s in r['q2']['stations']]},
        'q3':{COMM[s]:{'prices':{SVC[k]:float(r['q3'][s]['prices'][k]) for k in range(5)},
                       's3_combo':[int(x) for x in r['q3'][s]['s3_combo']],
                       'profit_rate':float(r['q3'][s]['profit_rate']),
                       'satisfaction':float(r['q3'][s]['satisfaction'])} for s in r['q2']['stations']}}
    with open(f'{out}/{nm}.json','w',encoding='utf-8') as f: json.dump(jd,f,ensure_ascii=False,indent=2)

print(f'\nSaved to {out}/')
