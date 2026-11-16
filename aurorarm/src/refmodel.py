"""Modelo de referencia do controlador (lei de controle + supervisor), projeto do ganho e simulacao em malha fechada.
Trace: REQ-CTRL-AA-001..004, REQ-SAFE-AA-001..004 -> MOD-CTRL / MOD-SUP -> codegen.py
Estados medidos: i (A), w (rad/s), theta (rad no eixo do motor). Referencia r em rad (eixo do motor).
"""
import json, os
import numpy as np
from scipy.signal import place_poles
import params as P
from plant import continuous_matrices, zoh
from supervisor_spec import spec, STOP_CYCLES, STATES

POLES_CT = [-450.0, -60+30j, -60-30j, -100.0]   # polos de malha fechada desejados (continuo)
RATE_MAX = 0.8*P.V_TIP_MAX/P.R_PAYLOAD*P.N       # rad/s motor (80% do limite SAFE-004)
A_REF = 500.0                                    # rad/s^2 (motor) limite de aceleracao do gerador de trajetoria
W_OVERSPEED = P.V_TIP_MAX/P.R_PAYLOAD*P.N        # rad/s motor = limite 250 mm/s

def design():
    A3,B3,C3,D3,E3 = continuous_matrices(True)
    Ad,Bd = zoh(A3,B3,P.TS); _,Ed = zoh(A3,E3,P.TS)
    Aa = np.block([[Ad, np.zeros((3,1))],[-P.TS*C3, np.eye(1)]]); Ba = np.vstack([Bd,np.zeros((1,1))])
    K = place_poles(Aa,Ba,np.exp(np.array(POLES_CT)*P.TS)).gain_matrix[0]
    ev_d = np.linalg.eigvals(Aa-Ba@K.reshape(1,-1))
    d = dict(K_I=K[0],K_W=K[1],K_TH=K[2],K_Z=-K[3],
             K_AW=1.0/abs(K[3]),A11=Ad[0,0],A12=Ad[0,1],B1=Bd[0,0],
             ILIM=P.I_LIM_DESIGN,VMAX=P.VMAX,TS=P.TS,RATE=RATE_MAX,AREF=A_REF,TWOA=2*A_REF,DV=A_REF*P.TS,WOVER=W_OVERSPEED,
             poles_ct=[complex(p).real if abs(complex(p).imag)<1e-12 else [complex(p).real,complex(p).imag] for p in POLES_CT],
             poles_dt_abs=sorted(np.abs(ev_d).tolist()),KE=P.Ke,STOP_CYCLES=STOP_CYCLES)
    return d, (Ad,Bd,Ed)

class CtrlRef:
    """Referencia em ponto flutuante de tipo dt (float64 ou float32), mesma ordem de operacoes do C gerado."""
    def __init__(self, d, dt=np.float64, version="v1", collab=True):
        self.dt=dt; f=dt; self.f=f
        self.c={k:f(d[k]) for k in ['K_I','K_W','K_TH','K_Z','K_AW','A11','A12','B1','ILIM','VMAX','TS','RATE','TWOA','DV','WOVER','KE']}
        self.sp=spec(version); self.collab=collab
        self.z=f(0); self.rl=f(0); self.v=f(0); self.sup=0; self.stop_cnt=0; self.prev=0; self.latch=0; self.rl_init=False
        self.trans=[(s,dd,compile(g.replace('STOP_CYCLES',str(STOP_CYCLES)),'g','eval'),acts) for s,dd,g,acts in self.sp['transitions']]
    def supervisor(self, prox, rearm, overspeed):
        cur=STATES[self.sup]; env=dict(prox=bool(prox),rearm=bool(rearm),overspeed=bool(overspeed),prev_prox=bool(self.prev),latch=bool(self.latch),stop_cnt=self.stop_cnt)
        if self.sp['uses_latch'] and rearm: self.latch=1; env['latch']=True
        new=cur; fired=False
        for s,dd,g,acts in self.trans:
            if s==cur and eval(g,{},env):
                new=dd; fired=True
                loc={'stop_cnt':self.stop_cnt}
                for a in acts: exec(a,{},loc)
                self.stop_cnt=loc['stop_cnt']; break
        if not fired and cur=="SAFE_STOP" and self.stop_cnt<STOP_CYCLES: self.stop_cnt+=1
        if cur in self.sp['prev_update_in']: self.prev=int(prox)
        if new=="MOVING" and cur!="MOVING" and self.sp['uses_latch']: self.latch=0
        self.sup=STATES.index(new); return cur,new
    def step(self, r, th, w, i, prox, rearm):
        f=self.f; c=self.c
        th,w,i,r=f(th),f(w),f(i),f(r)
        over = (abs(w) > c['WOVER']) if self.collab else False
        prev_state,new_state=self.supervisor(prox,rearm,over)
        brake = 1 if (self.sup!=0 and self.stop_cnt>=STOP_CYCLES) else 0
        if self.sup==0:
            # gerador de trajetoria (zona colaborativa): |v|<=RATE, |a|<=AREF; fora da zona: rl=r
            if self.collab:
                e=r-self.rl
                vd=np.sqrt(c['TWOA']*abs(e))
                if vd>c['RATE']: vd=c['RATE']
                if e<0: vd=-vd
                dv=vd-self.v
                if dv>c['DV']: dv=c['DV']
                if dv<-c['DV']: dv=-c['DV']
                self.v=self.v+dv
                rn=self.rl+self.v*c['TS']
                if (r-rn)*e<=0: rn=r; self.v=f(0)
                self.rl=rn
            else:
                self.rl=r; self.v=f(0)
            uu=((-c['K_I']*i - c['K_W']*w) - c['K_TH']*th) + c['K_Z']*self.z
            us=uu
            if us>c['VMAX']: us=c['VMAX']
            if us<-c['VMAX']: us=-c['VMAX']
            lo=(-c['ILIM'] - c['A11']*i - c['A12']*w)/c['B1']
            hi=( c['ILIM'] - c['A11']*i - c['A12']*w)/c['B1']
            if us>hi: us=hi
            if us<lo: us=lo
            self.z=self.z + c['TS']*(self.rl-th) + c['K_AW']*(us-uu)
            u=us
        else:
            u=c['KE']*w          # parada segura: anula f.c.e.m. -> corrente decai (torque -> 0)
            if u>c['VMAX']: u=c['VMAX']
            if u<-c['VMAX']: u=-c['VMAX']
            if brake: u=f(0)
            self.rl=th; self.v=f(0)     # mantem referencia na posicao atual; ao rearmar a trajetoria parte daqui rumo ao alvo original
        return u, self.sup, brake, self.rl

def plant_sim_factory(d=None, params_scale=None):
    """Planta continua exata por substeps de Ts/10; params_scale: dict para perturbar R,L,Kt,Ke,J,b."""
    sc=dict(R=1,L=1,Kt=1,Ke=1,J=1,b=1); 
    if params_scale: sc.update(params_scale)
    R=P.R*sc['R'];L=P.L*sc['L'];Kt=P.Kt*sc['Kt'];Ke=P.Ke*sc['Ke'];J=P.J*sc['J'];b=P.b*sc['b']
    A3=np.array([[-R/L,-Ke/L,0],[Kt/J,-b/J,0],[0,1,0]]); B3=np.array([[1/L],[0],[0]]); E3=np.array([[0],[-1/J],[0]])
    n=10; h=P.TS/n
    Ah,Bh=zoh(A3,B3,h); _,Eh=zoh(A3,E3,h)
    return Ah,Bh[:,0],Eh[:,0],n,h

def closed_loop(d, r_fun, T=0.6, load=P.T_LOAD, version="v1", prox_fun=None, rearm_fun=None, lost_cycles=(), sensor_delay=0.0,
                use_aw=True, pscale=None, ctrl=None, x0=None, dt=np.float64, collab=True):
    """Simulacao em malha fechada: controlador a cada Ts (500 Hz), planta a Ts/10. 
    prox_fun(t)->bool presenca fisica da mao; sensor tem atraso fixo sensor_delay. Ciclos perdidos: indices k.
    Retorna dict de arrays por substep."""
    Ah,Bh,Eh,n,h=plant_sim_factory(d,pscale)
    c=ctrl or CtrlRef(d,dt,version,collab)
    if not use_aw: c.c['K_AW']=c.f(0)
    x=np.zeros(3) if x0 is None else np.array(x0,float)
    steps=int(round(T/P.TS)); u=0.0; T_=[];TH=[];I=[];W=[];U=[];SUP=[];BR=[];RL=[]
    brake=0
    for k in range(steps):
        t=k*P.TS
        prox_phys = prox_fun(t) if prox_fun else False
        prox_meas = prox_fun(max(t-sensor_delay,0.0)) if prox_fun else False
        rearm = rearm_fun(t) if rearm_fun else False
        if k in lost_cycles:
            pass   # ciclo perdido: nenhum calculo; u anterior mantido
        else:
            u,sup,brake,rl = c.step(r_fun(t),x[2],x[1],x[0],prox_meas,rearm)
        for s in range(n):
            tt=t+s*h
            if brake: x=np.array([0.0,0.0,x[2]])    # freio mecanico retem (apos torque zero confirmado)
            else: x=Ah@x+Bh*float(u)+Eh*load
            T_.append(tt+h);TH.append(x[2]);I.append(x[0]);W.append(x[1]);U.append(float(u));SUP.append(c.sup);BR.append(brake);RL.append(float(c.rl))
    return {k:np.array(v) for k,v in dict(t=T_,th=TH,i=I,w=W,u=U,sup=SUP,brake=BR,rl=RL).items()}

def step_metrics(o, step, band=0.02):
    th=o['th']; t=o['t']
    os=max(0.0,(th.max()-step)/step*100)
    out=np.abs(th-step)>band*step
    ts=t[np.where(out)[0][-1]]+P.TS if out.any() else 0.0
    return dict(overshoot_pct=os, settling_s=ts, ess=abs(th[-1]-step), imax=np.abs(o['i']).max(), umax=np.abs(o['u']).max())

if __name__=="__main__":
    d,(Ad,Bd,Ed)=design(); print(json.dumps(d,indent=1,default=str))
    for step in [1,2,5,10]:
        o=closed_loop(d, lambda t: step*(t>=0), T=0.6, version="v1")
        # sem limitador: usar RATE alto
    print("ok")
