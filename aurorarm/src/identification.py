"""Identificacao + validacao da planta (metodo demonstrado com DADOS SINTETICOS de bancada).
Nao ha dados reais no enunciado: simula-se uma bancada (planta 'verdadeira' ligeiramente diferente da nominal,
ruido de sensor, PRBS de tensao a 1 kHz) e mostra-se o procedimento: regressao de minimos quadrados em x[k+1]=Phi x[k]+Gam u[k]+g0
(estados medidos i, w), conversao para (A,B) continuos e parametros fisicos, validacao em conjunto independente.
Trace: MEM-A -> MOD-PLANT -> TST-ID-001
"""
import numpy as np, json
from scipy.linalg import logm, expm
import params as P
from plant import continuous_matrices, zoh

def true_plant():
    s=dict(R=1.04,L=0.95,Kt=1.02,Ke=0.98,J=1.05,b=1.10)   # desvios do 'real' em relacao ao nominal
    R=P.R*s['R'];L=P.L*s['L'];Kt=P.Kt*s['Kt'];Ke=P.Ke*s['Ke'];J=P.J*s['J'];b=P.b*s['b']
    return np.array([[-R/L,-Ke/L],[Kt/J,-b/J]]),np.array([[1/L],[0]]),dict(R=R,L=L,Kt=Kt,Ke=Ke,J=J,b=b)

def prbs(n,seed,amp,hold=3):
    rng=np.random.default_rng(seed); bits=rng.integers(0,2,n//hold+1)*2-1
    return amp*np.repeat(bits,hold)[:n]

def experiment(seed,n=4000,h=1e-3,sig_i=0.02,sig_w=0.5,Tl=0.05):
    A,B,_=true_plant(); Phi=expm(A*h); Gam=np.linalg.solve(A,(Phi-np.eye(2)))@B
    E=np.array([[0],[-1/P.J]]); Gl=np.linalg.solve(A,(Phi-np.eye(2)))@E
    u=prbs(n,seed,10.0); x=np.zeros(2); X=[x.copy()]
    for k in range(n):
        x=Phi@x+Gam[:,0]*u[k]+Gl[:,0]*Tl; X.append(x.copy())
    X=np.array(X); rng=np.random.default_rng(seed+100)
    Y=X+rng.normal(0,1,X.shape)*np.array([sig_i,sig_w])
    return u,Y,X

def identify(u,Y,h=1e-3):
    Xk=Y[:-1]; Xk1=Y[1:]
    Z=np.hstack([Xk,u[:,None],np.ones((len(u),1))])
    Theta,*_=np.linalg.lstsq(Z,Xk1,rcond=None); Theta=Theta.T
    Phi=Theta[:,:2]; Gam=Theta[:,2:3]
    A=np.real(logm(Phi))/h; B=A@np.linalg.solve(Phi-np.eye(2),Gam)
    L=1/B[0,0]; R=-A[0,0]*L; Ke=-A[0,1]*L; Kt_J=A[1,0]
    return A,B,dict(L=L,R=R,Ke=Ke,Kt_over_J=Kt_J,b_over_J=-A[1,1],Theta=Theta)

def simulate(A,B,u,h,x0,Tl_term=None):
    Phi=expm(A*h); Gam=np.linalg.solve(A,(Phi-np.eye(2)))@B
    x=np.array(x0,float); out=[x.copy()]
    for k in range(len(u)): x=Phi@x+Gam[:,0]*u[k]; out.append(x.copy())
    return np.array(out)

def run():
    h=1e-3
    u1,Y1,_=experiment(1); u2,Y2,X2=experiment(2)
    A,B,est=identify(u1,Y1,h)
    # validacao no conjunto 2: predicao livre da velocidade e corrente (sem termo de carga, so dinamica de tensao)
    A0,B0,_,_=continuous_matrices()
    def nrmse(y,yh): return 100*(1-np.linalg.norm(y-yh)/np.linalg.norm(y-np.mean(y)))
    Phi=expm(A*h); Gam=np.linalg.solve(A,(Phi-np.eye(2)))@B
    g0=est['Theta'][:,3]
    # simula com termo constante identificado
    x=Y2[0].copy(); pred=[x.copy()]
    for k in range(len(u2)): x=Phi@x+Gam[:,0]*u2[k]+g0; pred.append(x.copy())
    pred=np.array(pred)
    # predicao 'multi-passos' de 20 ms (janelas): re-inicializa a cada 20 amostras
    pred20=[]; 
    for k0 in range(0,len(u2),20):
        x=Y2[k0].copy()
        for k in range(k0,min(k0+20,len(u2))): x=Phi@x+Gam[:,0]*u2[k]+g0; pred20.append(x.copy())
    pred20=np.array(pred20)
    Ytrue=X2[1:len(pred20)+1]
    fit_w=nrmse(Ytrue[:,1],pred20[:,1]); fit_i=nrmse(Ytrue[:,0],pred20[:,0])
    # fit do modelo NOMINAL (enunciado) no mesmo conjunto, p/ comparacao
    Ph0=expm(A0*h); G0=np.linalg.solve(A0,(Ph0-np.eye(2)))@B0
    pn=[]
    for k0 in range(0,len(u2),20):
        x=Y2[k0].copy()
        for k in range(k0,min(k0+20,len(u2))): x=Ph0@x+G0[:,0]*u2[k]+g0; pn.append(x.copy())
    pn=np.array(pn)
    fit_w0=nrmse(Ytrue[:,1],pn[:,1]); fit_i0=nrmse(Ytrue[:,0],pn[:,0])
    _,_,tp=true_plant()
    Kt_id=P.Kt   # Kt = Ke (SI) assumido; J_id = Kt/(Kt/J)
    J_id=est['Ke']/est['Kt_over_J']; b_id=est['b_over_J']*J_id
    res=dict(R_id=est['R'],L_id=est['L'],Ke_id=est['Ke'],J_id=J_id,b_id=b_id,
             R_true=tp['R'],L_true=tp['L'],Ke_true=tp['Ke'],J_true=tp['J'],b_true=tp['b'],
             fit_w_pct=fit_w,fit_i_pct=fit_i,fit_w_nominal_pct=fit_w0,fit_i_nominal_pct=fit_i0)
    return res,(u2,Y2,X2,pred,Ytrue,pred20)
if __name__=="__main__":
    r,_=run(); print(json.dumps(r,indent=1))
