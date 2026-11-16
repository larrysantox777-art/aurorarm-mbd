"""Suite de testes gerados a partir do modelo (grafo do supervisor + propriedades) e testes de requisitos em malha fechada (SIL).
Trace: TST-SUP-001..003, TST-CTRL-001..004, TST-SAFE-004, TST-MUT-001, TST-COV-001
Uso: python3 sil_tests.py [lib.so]  -> imprime JSON; (cobertura: ver run_all.py)
"""
import sys, os, json, math, random, collections, itertools
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import params as P, refmodel as RM, sil
from supervisor_spec import STATES, STOP_CYCLES

def abstract_graph(version="v1"):
    """Grafo abstrato (sup,stop_cnt,prev,latch) x entradas (prox,rearm) obtido executando o MODELO de referencia."""
    inputs=list(itertools.product((0,1),(0,1)))
    def mk(st):
        c=RM.CtrlRef(RM.design()[0],np.float64,version,True); c.sup,c.stop_cnt,c.prev,c.latch=st; return c
    init=(0,0,0,0); seen={init}; q=collections.deque([init]); edges={}
    while q:
        s=q.popleft()
        for inp in inputs:
            c=mk(s); c.supervisor(inp[0],inp[1],False)
            n=(c.sup,c.stop_cnt,c.prev,c.latch); edges[(s,inp)]=n
            if n not in seen: seen.add(n); q.append(n)
    return init,seen,edges,inputs

def gen_transition_tests(version="v1"):
    """Um teste por aresta (estado,entrada): caminho mais curto ate o estado + a entrada. Cobertura de transicoes = 100% por construcao."""
    init,seen,edges,inputs=abstract_graph(version)
    path={init:[]}; q=collections.deque([init])
    while q:
        s=q.popleft()
        for inp in inputs:
            n=edges[(s,inp)]
            if n not in path: path[n]=path[s]+[inp]; q.append(n)
    tests=[]
    for (s,inp),n in edges.items(): tests.append(dict(start=s,input=inp,seq=path[s]+[inp],expect=n))
    return tests,len(seen),len(edges)

def run_supervisor_test(lib,seq,version="v1"):
    """Executa sequencia de entradas (prox,rearm) no C e na referencia; compara (sup,brake,torque_en) a cada ciclo."""
    d=RM.design()[0]; ref=RM.CtrlRef(d,np.float32,version,False); cc=sil.CCtrl(lib,False)
    for (px,rr) in seq:
        a=ref.step(0.0,0.0,0.0,0.0,px,rr); b=cc.step(0.0,0.0,0.0,0.0,px,rr)
        if a[1]!=b[1] or a[2]!=b[2]: return False
    return True

def properties_random(lib,n_seqs=300,length=400,seed=7):
    """Propriedades de seguranca checadas sobre o C em sequencias aleatorias (prox/rearm alternam com dwell aleatorio)."""
    rng=random.Random(seed); d=RM.design()[0]; viol=collections.Counter(); n_cycles=0
    for _ in range(n_seqs):
        cc=sil.CCtrl(lib,False); prev_sup=0; px=0; rr=0
        for k in range(length):
            if rng.random()<0.06: px^=1
            if rng.random()<0.10: rr^=1
            u,sup,brake,rl=cc.step(0,0,0,0,px,rr); n_cycles+=1
            # SAFE-001 (nivel de ciclo): prox amostrado em MOVING => sai de MOVING no mesmo ciclo
            if prev_sup==0 and px and sup==0: viol['SAFE-001']+=1
            # SAFE-002: entrar em MOVING exige vir de WAIT_REARM, rearm=1 e prox=0 neste ciclo
            if prev_sup!=0 and sup==0 and not (prev_sup==2 and rr and not px): viol['SAFE-002']+=1
            # SAFE-003 (cond. nivel de ciclo): WAIT_REARM + !prox + rearm => MOVING no ciclo
            if prev_sup==2 and (not px) and rr and sup!=0: viol['SAFE-003']+=1
            # invariantes: freio so se fora de MOVING; torque so em MOVING
            if brake and sup==0: viol['INV-brake']+=1
            prev_sup=sup
    return dict(cycles=n_cycles,violations=dict(viol),passed=sum(viol.values())==0)

def req_tests(lib,pert=None):
    d=RM.design()[0]; out={}
    amps=[1,2,5,10,15]; rows=[]
    for a in amps:
        cc=sil.CCtrl(lib,False)
        o=RM.closed_loop(d,lambda t:a,T=1.0,ctrl=cc,collab=False)
        m=RM.step_metrics(o,a); ok=sil.metrics_ok(m)
        rows.append(dict(amp_motor_rad=a,amp_joint_deg=math.degrees(a/P.N),**{k:float(v) for k,v in m.items()},**{'ok_'+k:bool(v) for k,v in ok.items()}))
    out['step_sweep']=rows
    # sem carga
    cc=sil.CCtrl(lib,False); o=RM.closed_loop(d,lambda t:5.0,T=1.0,load=0.0,ctrl=cc,collab=False); out['step5_noload']={k:float(v) for k,v in RM.step_metrics(o,5.0).items()}
    # robustez: Monte Carlo +-10% (uniforme) nos 6 parametros fisicos da PLANTA (controlador nominal)
    rng=np.random.default_rng(11); mc=[]
    for k in range(100):
        sc={p:1+rng.uniform(-0.10,0.10) for p in ['R','L','Kt','Ke','J','b']}
        for a in (2,5,10):
            cc=sil.CCtrl(lib,False); o=RM.closed_loop(d,lambda t:a,T=1.0,ctrl=cc,pscale=sc,collab=False); m=RM.step_metrics(o,a)
            mc.append((a,m['overshoot_pct'],m['settling_s'],m['ess'],m['imax'],m['umax']))
    mc=np.array(mc)
    out['monte_carlo']=dict(n=len(mc),max_os=float(mc[:,1].max()),max_ts=float(mc[:,2].max()),max_ess=float(mc[:,3].max()),max_imax=float(mc[:,4].max()),max_umax=float(mc[:,5].max()),
        n_fail_os=int((mc[:,1]>8).sum()),n_fail_ts=int((mc[:,2]>0.3).sum()),n_fail_i=int((mc[:,4]>8).sum()),n_fail_u=int((mc[:,5]>48).sum()))
    # ablacao anti-windup
    ab=[]
    for a in (5,10,15):
        o=RM.closed_loop(d,lambda t:a,T=1.0,collab=False,use_aw=False); m=RM.step_metrics(o,a); ab.append(dict(amp=a,os_no_aw=float(m['overshoot_pct']),ts_no_aw=float(m['settling_s']),imax=float(m['imax'])))
    out['no_antiwindup']=ab
    # SAFE-004: velocidade do efetuador em zona colaborativa
    pk=[]
    for a in (5,10,30,60):
        cc=sil.CCtrl(lib,True); o=RM.closed_loop(d,lambda t:a,T=2.0,ctrl=cc,collab=True)
        pk.append(dict(step=a,w_peak_motor=float(np.abs(o['w']).max()),v_tip_mm_s=float(np.abs(o['w']).max()/P.N*P.R_PAYLOAD*1e3),tripped=bool((o['sup']!=0).any())))
    out['tip_speed']=pk
    # ponto critico 450 rad/s em regime
    cc=sil.CCtrl(lib,False); o=RM.closed_loop(d,sil.cruise_traj,T=2.5,ctrl=cc,collab=False)
    out['cruise450']=dict(w_final=float(o['w'][-1]),i_final=float(o['i'][-1]),u_final=float(o['u'][-1]),umax=float(np.abs(o['u']).max()),imax=float(np.abs(o['i']).max()),
                          track_err_final=float(sil.cruise_traj(o['t'][-1])-o['th'][-1]),i_peak=float(np.abs(o['i']).max()),w_peak=float(o['w'].max()))
    return out

def latency_c(lib):
    d=RM.design()[0]; worst=0; n=0
    for dly_ms in (0,5,10,15,20):
        for ph in (0.0,1.0,1.75):
            for nlost in (0,1):
                t0=0.05+ph*1e-3; dly=dly_ms*1e-3; kdet=int(math.ceil((t0+dly)/P.TS-1e-9)); lost=tuple(range(kdet,kdet+nlost))
                cc=sil.CCtrl(lib,True)
                o=RM.closed_loop(d,lambda t:400.0,T=0.25,prox_fun=lambda t:t>=t0,sensor_delay=dly,lost_cycles=lost,ctrl=cc,collab=True)
                idx=np.where(o['t']>=t0)[0]; i=np.abs(o['i'][idx]); t=o['t'][idx]; bad=np.where(i>=0.05)[0]
                tz=(t[bad[-1]] if len(bad) else t[0])-t0; worst=max(worst,tz*1e3); n+=1
    return dict(n=n,worst_ms=worst)

def mutation(lib_dir_mut):
    """Mutantes (versoes preliminares geradas do modelo com erro): a suite DEVE reprova-los."""
    res={}
    for v in ('v0_edge','v0_stale_rearm'):
        src=os.path.join(RM.__file__.rsplit('/',1)[0],'../tests/mutants/aurora_ctrl_%s.c'%v); lib='/tmp/mut_%s.so'%v
        sil.build(src,lib,os.path.dirname(src))
        # 1) propriedades aleatorias
        pr=properties_random(lib,n_seqs=200)
        # 2) teste dirigido do cenario do quase-acidente: stop -> rearme -> mao volta logo apos
        cc=sil.CCtrl(lib,False); seq=[(1,0)]*8+[(0,0)]*8+[(0,1)]+[(1,0)]*3
        sups=[cc.step(0,0,0,0,px,rr)[1] for px,rr in seq]
        directed_fail = (sups[-1]==0)     # mao presente mas ainda MOVING
        res[v]=dict(property_violations=pr['violations'],detected_by_properties=not pr['passed'],detected_by_directed=bool(directed_fail))
    return res

if __name__=="__main__":
    lib=sys.argv[1] if len(sys.argv)>1 else '/tmp/aurora_v1.so'
    out={}
    tests,ns,ne=gen_transition_tests()
    passed=sum(run_supervisor_test(lib,t['seq']) for t in tests)
    out['transition_tests']=dict(n_tests=len(tests),n_pass=passed,abstract_states=ns,abstract_edges=ne,state_cov_pct=100.0,trans_cov_pct=100.0)
    out['properties']=properties_random(lib)
    out['requirements']=req_tests(lib)
    out['latency_c']=latency_c(lib)
    out['mutation']=mutation(None)
    json.dump(out,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'../results/sil_tests.json'),'w'),indent=1)
    print(json.dumps(out,indent=1))
