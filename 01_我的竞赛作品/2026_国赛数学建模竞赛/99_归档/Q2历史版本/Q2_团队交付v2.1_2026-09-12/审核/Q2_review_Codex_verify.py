"""Independent numerical evidence for the Q2 review; standard library only."""
import math
import json
from pathlib import Path

eps = math.pi / 180
a, h = 752.5, 747.5
blo = h * math.tan(40 * eps)
bhi = math.sqrt(1000**2 - h**2)

def proxy(a, b, d):
    q = (d-a)**2+b*b
    return eps * math.sqrt((d*d+q)*q) / abs(b)

def geometry(a, b, d, alpha):
    t = alpha*eps
    distance = math.hypot(a-d*math.cos(t), b-d*math.sin(t))
    sine = abs(b*math.cos(t)-a*math.sin(t))/distance
    return dict(d2=distance, acute_angle=math.asin(min(1,sine))/eps)

def cross(u,v):
    return u[0]*v[1]-u[1]*v[0]

def exact_diameter(s2,g):
    # Intersect all pairs of wedge boundary rays and retain feasible vertices.
    stations = [(0.,0.),s2]
    bearings = [math.atan2(g[1]-s[1],g[0]-s[0]) for s in stations]
    vertices=[]
    for z in (-1,1):
        for w in (-1,1):
            u=(math.cos(bearings[0]+z*eps),math.sin(bearings[0]+z*eps))
            v=(math.cos(bearings[1]+w*eps),math.sin(bearings[1]+w*eps))
            det=cross(u,v)
            if abs(det)<1e-12: continue
            t=cross(s2,v)/det
            r=cross(s2,u)/det
            if min(t,r)<0: continue
            p=(t*u[0],t*u[1])
            if all(abs(math.atan2(math.sin(math.atan2(p[1]-s[1],p[0]-s[0])-beta),math.cos(math.atan2(p[1]-s[1],p[0]-s[0])-beta)))<=eps+1e-10 for s,beta in zip(stations,bearings)):
                vertices.append(p)
    return max(math.dist(p,q) for p in vertices for q in vertices)

nominal=exact_diameter((a,blo),(a,0))
far=exact_diameter((a,blo),(1500,0))
result={
    'baseline':dict(b_min=blo,b_max=bhi,phi_max=math.acos(h/1000)/eps,E_nominal=proxy(a,blo,a),move_min=math.hypot(a,blo),move_max=math.hypot(a,bhi)),
    'other_R_b_max':{str(r):math.sqrt(r*r-h*h) for r in (1250,1500)},
    'angular_counterexamples':{'lower_b_far_alpha_plus1':geometry(a,blo,1500,1),'upper_b_far_alpha_minus1':geometry(a,bhi,1500,-1),'upper_b_d1000_alpha_minus1':geometry(a,bhi,1000,-1)},
    'worst_E_midpoint':{'b_min':proxy(a,blo,1500),'b_max':proxy(a,bhi,1500)},
    'D_checks':{'Q1_baseline':exact_diameter((600,0),(300,500)),'nominal_D':nominal,'nominal_ratio':nominal/proxy(a,blo,a),'far_D':far,'far_ratio':far/proxy(a,blo,1500)},
    'singular_limit_at_a_equals_d':{'b_1e_minus6':proxy(a,1e-6,a),'limit':eps*a}
}
assert result['angular_counterexamples']['lower_b_far_alpha_plus1']['acute_angle']<40
assert result['angular_counterexamples']['upper_b_far_alpha_minus1']['d2']>1000
assert result['worst_E_midpoint']['b_max']<result['worst_E_midpoint']['b_min']
assert result['D_checks']['nominal_ratio']>2
assert abs(result['D_checks']['Q1_baseline']-39.598)<0.01
output=Path(__file__).with_name('Q2_review_Codex_evidence.json')
output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(output.read_text(encoding='utf-8'))
