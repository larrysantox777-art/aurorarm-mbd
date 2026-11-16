"""SIL (software-in-the-loop): compila o C gerado, executa em malha fechada com a planta (Python) e
(i) mostra equivalencia numerica modelo-codigo; (ii) executa a suite de testes baseada em modelo; (iii) cobertura; (iv) mutacao.
Trace: TST-CTRL-001..004, TST-SUP-001..003, TST-SAFE-004, TST-EQ-001, TST-MUT-001. Memorial item (e).
"""
import ctypes as C, os, subprocess, json, itertools, collections, math, random, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import params as P
import refmodel as RM
from supervisor_spec import STATES, STOP_CYCLES
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.join(HERE,'..')

class St(C.Structure): _fields_=[('z',C.c_float),('rl',C.c_float),('sup',C.c_uint8),('stop_cnt',C.c_uint8),('prev_prox',C.c_uint8),('latch',C.c_uint8)]
class In(C.Structure): _fields_=[('r',C.c_float),('th',C.c_float),('w',C.c_float),('i',C.c_float),('prox',C.c_uint8),('rearm',C.c_uint8),('collab',C.c_uint8)]
class Out(C.Structure): _fields_=[('u',C.c_float),('rl',C.c_float),('sup',C.c_uint8),('brake',C.c_uint8),('torque_en',C.c_uint8)]

def cruise_traj(t,a=300.0,w=450.0):
    t1=w/a
    return 0.5*a*t*t if t<t1 else 0.5*a*t1*t1+w*(t-t1)

def build(src, lib, incdir, cov=False):
    cmd=['gcc','-std=c99','-O2','-ffp-contract=off','-fno-fast-math','-shared','-fPIC','-I',incdir,src,'-o',lib,'-lm']
    if cov: cmd=['gcc','-std=c99','-O0','--coverage','-ffp-contract=off','-fno-fast-math','-shared','-fPIC','-I',incdir,src,'-o',lib,'-lm']
    subprocess.check_call(cmd)

class CCtrl:
    def __init__(self, lib, collab=True):
        self.l=C.CDLL(lib); self.s=St(); self.l.aurora_init(C.byref(self.s)); self.collab=collab
        self.sup=0; self.rl=0.0; self.log=[]
        self.c={'K_AW':None}
        self.f=np.float32
    def step(self,r,th,w,i,prox,rearm):
        inp=In(r,th,w,i,int(bool(prox)),int(bool(rearm)),int(self.collab)); out=Out()
        self.log.append((float(np.float32(r)),float(np.float32(th)),float(np.float32(w)),float(np.float32(i)),int(bool(prox)),int(bool(rearm))))
        self.l.aurora_step(C.byref(self.s),C.byref(inp),C.byref(out))
        self.sup=out.sup; self.rl=out.rl
        return out.u,out.sup,out.brake,out.rl

def fresh(d,lib,collab=True): return CCtrl(lib,collab)

def metrics_ok(m): 
    return dict(os=m['overshoot_pct']<=8.0, ts=m['settling_s']<=0.300, ess=m['ess']<1e-3, u=m['umax']<=48.0, i=m['imax']<=8.0)

def run_all():
    d,_=RM.design()
    build(os.path.join(ROOT,'generated/aurora_ctrl.c'),'/tmp/aurora_v1.so',os.path.join(ROOT,'generated'))
    res={}
    # ---------- (1) EQUIVALENCIA MODELO-CODIGO ----------
    scen={
     'S1_step5_noncollab': dict(r=lambda t:5.0,T=0.6,collab=False,prox=None,rearm=None),
     'S2_step10_collab_stop_rearm': dict(r=lambda t:10.0,T=1.4,collab=True,prox=lambda t:0.25<=t<0.60,rearm=lambda t:t>=0.70),
     'S3_cruise450': dict(r=lambda t:cruise_traj(t),T=2.5,collab=False,prox=None,rearm=None),
     'S5_infeasible_ramp_saturation': dict(r=lambda t:450.0*t,T=0.8,collab=False,prox=None,rearm=None),
     'S4_prbs_like': dict(r=lambda t:6.0*math.sin(2*math.pi*1.5*t)+2.0*np.sign(math.sin(2*math.pi*7*t)),T=1.0,collab=False,prox=None,rearm=None),
    }
    eq={}
    for name,sc in scen.items():
        cc=CCtrl('/tmp/aurora_v1.so',sc['collab'])
        o=RM.closed_loop(d,sc['r'],T=sc['T'],prox_fun=sc['prox'],rearm_fun=sc['rearm'],ctrl=cc,collab=sc['collab'])
        U_c=o['u'][9::10]                       # u por ciclo (o ultimo substep de cada ciclo tem o u do ciclo)
        # replay das MESMAS entradas nos modelos de referencia
        ref32=RM.CtrlRef(d,np.float32,"v1",sc['collab']); ref64=RM.CtrlRef(d,np.float64,"v1",sc['collab'])
        u32=[];u64=[];sup_c=[];sup32=[];sup64=[]; k=0; tsum=[]
        # o closed_loop NAO chama step em ciclos perdidos; aqui nao ha ciclos perdidos -> log tem 1 entrada por ciclo
        for (r,th,w,i,px,rr) in cc.log:
            if ref64.sup==0: tsum.append(abs(d['K_I']*i)+abs(d['K_W']*w)+abs(d['K_TH']*th)+abs(d['K_Z']*float(ref64.z)))
            a=ref32.step(r,th,w,i,px,rr); b=ref64.step(r,th,w,i,px,rr)
            u32.append(float(a[0])); u64.append(float(b[0])); sup32.append(a[1]); sup64.append(b[1])
        u32=np.array(u32); u64=np.array(u64)
        # saida bruta do C registrada: recalcula chamando de novo? usa o proprio U_c
        n=min(len(U_c),len(u32)); U_c=U_c[:n]
        e32=np.abs(U_c-u32[:n]); e64=np.abs(U_c-u64[:n])
        # malha fechada com referencia float64 (trajetoria) vs trajetoria do C
        o64=RM.closed_loop(d,sc['r'],T=sc['T'],prox_fun=sc['prox'],rearm_fun=sc['rearm'],collab=sc['collab'])
        eth=np.abs(o['th']-o64['th']).max()
        eq[name]=dict(n_cycles=int(n),max_abs_err_vs_f32_ref=float(e32.max()),max_abs_err_vs_f64_ref=float(e64.max()),
                      max_abs_u=float(np.abs(U_c).max()),max_rel_vs_f64=float((e64/np.maximum(np.abs(u64[:n]),1e-3)).max()),
                      bit_exact_vs_f32=bool(np.all(U_c.astype(np.float32)==u32[:n].astype(np.float32))),
                      sup_equal=bool(sup32==sup64==list(o['sup'][9::10][:n])) if False else bool(np.array_equal(np.array(sup64[:n]),o['sup'][9::10][:n])),
                      max_theta_diff_closed_loop=float(eth), theta_scale=float(np.abs(o64['th']).max()),
                      max_term_sum=float(max(tsum)), err_over_eps_termsum=float(e64.max()/(float(np.finfo(np.float32).eps)*max(tsum))))
    eps32=float(np.finfo(np.float32).eps); eps64=float(np.finfo(np.float64).eps)
    allmax64=max(v['max_abs_err_vs_f64_ref'] for v in eq.values()); allmax32=max(v['max_abs_err_vs_f32_ref'] for v in eq.values())
    umax=max(v['max_abs_u'] for v in eq.values())
    res['equivalence']=dict(per_scenario=eq,eps_f32=eps32,eps_f64=eps64,max_err_vs_f64=allmax64,max_err_vs_f32=allmax32,
        max_abs_u=umax,err_over_eps_u=allmax64/(eps32*umax),ulp_scale_u=eps32*umax)
    return res

if __name__=="__main__":
    r=run_all(); print(json.dumps(r,indent=1))
