"""Verificador exaustivo (model checker de estados explicitos) do supervisor de seguranca
composto com ambiente temporizado: sensor com atraso <= 20 ms, ciclos perdidos por jitter,
mao que entra/sai a qualquer instante, rearme nao deterministico.
Tempo discretizado em ticks (digitalizacao de automato temporizado com restricoes fechadas e
constantes inteiras => preserva alcancabilidade; Henzinger, Manna, Pnueli 1992).
Trace: REQ-SAFE-AA-001..003 -> MOD-SUP -> TST-VER-*
"""
import sys, json, itertools, collections, time
sys.path.insert(0, __file__.rsplit('/',1)[0])
import numpy as np
from supervisor_spec import spec, STOP_CYCLES
import params as P
from plant import continuous_matrices, zoh

def decay_cycles(i0=P.I_LIM_DESIGN, thr=0.05):
    """Ciclos de 2 ms para |i| < thr (0,6% do torque max) apos comando de parada
    (u = Ke*w cancela f.c.e.m.; i decai com exp(-R*Ts/L)) -- calculado do modelo discreto."""
    A,B,C,D = continuous_matrices(); Ad,Bd = zoh(A,B,P.TS)
    # i' = -R/L i + (u-Ke w)/L ; com u = Ke*w : decai a taxa -R/L
    a = np.exp(-P.R/P.L*P.TS); i=i0; n=0
    while abs(i) >= thr: i*=a; n+=1
    return n

def make_model(version, tick_ms=1, K_skip=1, sensor_ms=20, t_safe_ms=100, cyc_ms=2, t_act_cycles=None):
    sp = spec(version)
    Pc = cyc_ms*tick_ms; DS = sensor_ms*tick_ms; DL = t_safe_ms*tick_ms
    if t_act_cycles is None: t_act_cycles = 1 + decay_cycles()   # 1 ciclo ZOH + decaimento
    TACT = t_act_cycles*Pc
    trans = [(s,d,compile(g.replace('STOP_CYCLES',str(STOP_CYCLES)),'g','eval'),acts) for s,d,g,acts in sp['transitions']]
    M = dict(sp=sp,Pc=Pc,DS=DS,DL=DL,TACT=TACT,K=K_skip,trans=trans,tick_ms=tick_ms)
    return M

# estado: (hand,sens,pend,phase,skip,sup,prev,latch,scnt,tact,hclk,viol2)
# sup: 0 MOVING, 1 SAFE_STOP, 2 WAIT_REARM ; torque ligado <=> sup==MOVING ou tact>0 (derivado)
SUPN = {"MOVING":0,"SAFE_STOP":1,"WAIT_REARM":2}
IH,IS,IP,IPH,ISK,ISUP,IPREV,ILATCH,ISCNT,ITACT,IHC,IV2 = range(12)
def torque_on(st): return st[ISUP]==0 or st[ITACT]>0

def exec_cycle(M, sup, prev, latch, stopcnt, prox, rearm):
    sp = M['sp']; names = ["MOVING","SAFE_STOP","WAIT_REARM"]
    cur = names[sup]; env = dict(prox=bool(prox), rearm=bool(rearm), overspeed=False,
                                 prev_prox=bool(prev), latch=bool(latch), stop_cnt=stopcnt)
    if sp['uses_latch'] and rearm: latch = 1; env['latch']=True   # BUG v0_stale: memoriza em qualquer estado
    new = cur; ns = stopcnt; fired=False
    for s,d,g,acts in M['trans']:
        if s==cur and eval(g,{}, env):
            new=d; fired=True
            loc={'stop_cnt':stopcnt}
            for a in acts: exec(a,{},loc)
            ns=loc['stop_cnt']; break
    if not fired and cur=="SAFE_STOP": ns=min(stopcnt+1, STOP_CYCLES)
    if new!="SAFE_STOP": ns = 0 if new!="SAFE_STOP" and not (cur=="SAFE_STOP" and not fired) else ns
    nprev = int(prox) if cur in sp['prev_update_in'] else prev
    entered = (cur!="MOVING" and new=="MOVING"); left=(cur=="MOVING" and new!="MOVING")
    viol2 = 1 if (entered and not (cur=="WAIT_REARM" and rearm)) else 0   # SAFE-002
    if entered and sp['uses_latch']: latch = 0
    return SUPN[new], nprev, latch, ns, left, entered, viol2

def init_state(M):
    return (0,0,-1,0,0,0,0,0,0,-1,0,0)

def successors(M, st, rearm_set=(0,1), hand_fixed=None):
    hand,sens,pend,phase,skip,sup,prev,latch,scnt,tact,hclk,v2 = st
    Pc,DS,TACT,K,DL = M['Pc'],M['DS'],M['TACT'],M['K'],M['DL']
    out=[]
    for th in ((0,1) if hand_fixed is None else (0,)):
        h2 = hand^th
        s2,p2 = sens,pend
        if p2==-1 and s2!=h2:
            sens_choices=[(h2,-1)]+[(s2,d) for d in range(1,DS+1)]
        elif p2>=0:
            p2-=1
            sens_choices=[(h2,-1)] if p2<=0 else [(s2,p2)]
        else: sens_choices=[(s2,p2)]
        for (s3,p3) in sens_choices:
            if phase==0:
                opts=[('exec',r) for r in rearm_set]
                if skip<K: opts.append(('skip',0))
            else: opts=[('none',0)]
            for o,rr in opts:
                sup2,prev2,latch2,scnt2,sk2,ta2,v2n = sup,prev,latch,scnt,skip,tact,v2
                if o=='exec':
                    sup2,prev2,latch2,scnt2,left,entered,vv = exec_cycle(M,sup,prev,latch,scnt,s3,rr)
                    sk2=0; v2n = v2 or vv
                    if left: ta2=TACT
                    if entered: ta2=-1
                elif o=='skip': sk2=skip+1
                if ta2>0:
                    ta2-=1
                    if ta2==0: ta2=-1
                if h2: hc = 0 if not hand else min(hclk+1, DL+1)
                else: hc=0
                out.append(((h2,s3,p3,(phase+1)%Pc,sk2,sup2,prev2,latch2,scnt2,ta2,hc,v2n),
                            dict(hand=h2,sens=s3,sup=sup2,cyc=o,rearm=rr)))
    return out

def explore(M, max_states=3_000_000):
    s0=init_state(M); parent={s0:None}; q=collections.deque([s0]); edges=0
    viol={'SAFE-001':None,'SAFE-002':None}; maxlat=0; maxlat_state=None
    while q:
        st=q.popleft()
        if st[IH] and torque_on(st) and st[IHC]>maxlat: maxlat=st[IHC]; maxlat_state=st
        if st[IH] and torque_on(st) and st[IHC]>M['DL'] and viol['SAFE-001'] is None: viol['SAFE-001']=st
        if st[IV2] and viol['SAFE-002'] is None: viol['SAFE-002']=st
        for ns,lab in successors(M,st):
            edges+=1
            if ns not in parent:
                parent[ns]=(st,lab); q.append(ns)
                if len(parent)>max_states: raise RuntimeError("estouro")
    return parent,viol,maxlat,maxlat_state,edges

def trace_to(parent, st):
    tr=[]
    while parent[st] is not None:
        p,lab=parent[st]; tr.append((p,lab,st)); st=p
    return list(reversed(tr))

def liveness(M, parent):
    """SAFE-003: A = (sup in {SAFE_STOP,WAIT_REARM}) com mao ausente e sensor limpo... ao longo do tempo
    (mao fica fora, rearme mantido). Procura (i) ciclo que nunca chega a MOVING; (ii) latencia maxima."""
    import sys; sys.setrecursionlimit(1_000_000)
    names=['MOVING','SAFE_STOP','WAIT_REARM']
    memo={}; onstack=set(); res={'cycle':False,'maxlat':0,'nA':0}
    def succ_restricted(st):
        # ambiente restrito: mao fica 0, rearme fica 1
        return [ns for ns,lab in successors(M,st,rearm_set=(1,),hand_fixed=0)]
    def longest(st):
        if st[ISUP]==0: return 0
        if st in memo: return memo[st]
        if st in onstack: res['cycle']=True; return 0
        onstack.add(st); best=0
        for ns in succ_restricted(st):
            if ns==st: res['cycle']=True; continue
            best=max(best,1+longest(ns))
        onstack.discard(st); memo[st]=best; return best
    A=[s for s in parent if s[ISUP]!=0 and s[IH]==0]
    for s in A:
        res['nA']+=1
        res['maxlat']=max(res['maxlat'],longest(s))
    return res

def fmt_state(st):
    names=['MOVING','SAFE_STOP','WAIT_REARM']
    return dict(mao=st[IH],sensor=st[IS],sup=names[st[ISUP]],cnt_stop=st[ISCNT],torque=int(torque_on(st)),hclk=st[IHC])

def run(version, tick_ms=1, K=1, verbose=True):
    M=make_model(version,tick_ms=tick_ms,K_skip=K)
    t0=time.time(); parent,viol,maxlat,mls,edges=explore(M)
    r=dict(version=version,tick_ms=tick_ms,K_skip=K,states=len(parent),edges=edges,
           max_latency_ms=maxlat/tick_ms, deadline_ms=M['DL']/tick_ms, t_act_ms=M['TACT']/tick_ms,
           safe001_holds=viol['SAFE-001'] is None, safe002_holds=viol['SAFE-002'] is None, seconds=round(time.time()-t0,1))
    if viol['SAFE-001'] is not None: r['cex_safe001']=[ (fmt_state(a),l,fmt_state(b)) for a,l,b in trace_to(parent,viol['SAFE-001'])]
    if viol['SAFE-002'] is not None: r['cex_safe002']=[ (fmt_state(a),l,fmt_state(b)) for a,l,b in trace_to(parent,viol['SAFE-002'])]
    if version=='v1':
        lv=liveness(M,parent); r['liveness']=dict(cycle_without_moving=lv['cycle'],max_cycles_ticks=lv['maxlat'],max_ms=lv['maxlat']/tick_ms,states_in_A=lv['nA'])
    return r

if __name__=="__main__":
    print("decay cycles:",decay_cycles())
    for v in ["v1"]:
        r=run(v); print({k:v_ for k,v_ in r.items() if not k.startswith('cex')})
