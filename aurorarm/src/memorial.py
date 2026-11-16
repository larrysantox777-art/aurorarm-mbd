"""Memorial de calculo (itens a-d; item e em sil_equivalence.py). Gera results/memorial.json e imprime passo a passo.
Trace: MEM-A..MEM-D. Cada numero aqui e citado no relatorio (secao 'Memorial' e Anexo A).
"""
import json, math, numpy as np
import params as P
from plant import continuous_matrices, zoh, ctrb, obsv
import refmodel as RM
import verify_supervisor as V

def item_a():
    A,B,C,D=continuous_matrices(); ev,evec=np.linalg.eig(A)
    ev=np.sort(ev.real)   # [-644.4, -22.6]
    tau=[-1/e for e in ev]
    Wc=ctrb(A,B); Wo=obsv(A,C)
    tr=A[0,0]+A[1,1]; det=A[0,0]*A[1,1]-A[0,1]*A[1,0]
    disc=tr**2-4*det
    # aproximacao de ordem reduzida (L->0): tau_m ~ J*R/(R*b+Kt*Ke)
    tau_m_red=P.J*P.R/(P.R*P.b+P.Kt*P.Ke)
    return dict(A=A.tolist(),B=B.tolist(),C=C.tolist(),trace=tr,det=det,disc=disc,eig=ev.tolist(),
        tau_fast_s=tau[0],tau_slow_s=tau[1],ratio=tau[1]/tau[0],tau_e_RL=P.L/P.R,tau_m_reduced=tau_m_red,
        R_over_L=P.R/P.L,Ke_over_L=P.Ke/P.L,Kt_over_J=P.Kt/P.J,b_over_J=P.b/P.J,B1=1/P.L,
        Wc=Wc.tolist(),Wo=Wo.tolist(),det_Wc=float(np.linalg.det(Wc)),det_Wo=float(np.linalg.det(Wo)),
        rank_Wc=int(np.linalg.matrix_rank(Wc)),rank_Wo=int(np.linalg.matrix_rank(Wo)),
        sv_Wc=np.linalg.svd(Wc,compute_uv=False).tolist(),sv_Wo=np.linalg.svd(Wo,compute_uv=False).tolist())

def item_b():
    iss=(P.b*P.W_SS+P.T_LOAD)/P.Kt
    vss=P.R*iss+P.Ke*P.W_SS
    T_payload=P.M_PAYLOAD*P.G*P.R_PAYLOAD/P.N
    iss_p=(P.b*P.W_SS+T_payload)/P.Kt; vss_p=P.R*iss_p+P.Ke*P.W_SS
    return dict(T_visc=P.b*P.W_SS,T_total=P.b*P.W_SS+P.T_LOAD,iss=iss,Vres=P.R*iss,Vemf=P.Ke*P.W_SS,vss=vss,
        folga_V=P.VMAX-vss,folga_pct=(P.VMAX-vss)/P.VMAX*100,folga_i=P.IMAX-iss,w_noload=P.VMAX/P.Ke,
        w_max_loaded=(P.VMAX-P.R*P.T_LOAD/P.Kt)/(P.Ke+P.R*P.b/P.Kt),
        P_mech=(P.Kt*iss-P.b*P.W_SS)*P.W_SS, P_elec=vss*iss, eta=((P.Kt*iss-P.b*P.W_SS)*P.W_SS)/(vss*iss),
        T_payload_joint=P.M_PAYLOAD*P.G*P.R_PAYLOAD,T_payload_motor=T_payload,ratio_load_vs_payload=P.T_LOAD/T_payload,
        iss_payload=iss_p,vss_payload=vss_p,a_max=P.Kt*P.IMAX/P.J,T_max=P.Kt*P.IMAX,
        a_net_ilim=(P.Kt*P.I_LIM_DESIGN-P.b*P.W_SS-P.T_LOAD)/P.J,a_net_imax=(P.Kt*P.IMAX-P.b*P.W_SS-P.T_LOAD)/P.J,t_accel_to_450=P.W_SS/((P.Kt*P.I_LIM_DESIGN-P.b*P.W_SS-P.T_LOAD)/P.J),
        w_joint=P.W_SS/P.N,v_tip_at_450=P.W_SS/P.N*P.R_PAYLOAD,
        w_collab_motor=P.V_TIP_MAX/P.R_PAYLOAD*P.N)

def item_c(a):
    tau_m=a['tau_slow_s']; tau_e=a['tau_fast_s']
    d,_=RM.design(); wn=None
    # polos dominantes do projeto
    dom=[-60+30j,-60-30j]; sigma=60; wd=30
    return dict(Ts=P.TS,tau_m=tau_m,tau_e=tau_e,samples_per_tau_m=tau_m/P.TS,samples_per_tau_e=tau_e/P.TS,
        samples_per_settle=0.300/P.TS,fs=1/P.TS,
        fs_over_bw=(1/P.TS)/(np.linalg.norm([60,30])/(2*math.pi)),
        wn_dom=float(np.hypot(60,30)),zeta_dom=float(60/np.hypot(60,30)),
        Ts_for_20_per_taum=tau_m/20,Ts_for_10_per_taum=tau_m/10,
        Ts_max_rule_closed_loop=(1/np.hypot(60,30))/ (6.0),   # ~6-10 amostras por 1/wn ... ver relatorio
        budget_cycle_us=200,duty_pct=200/(P.TS*1e6)*100)

def item_d():
    """Varredura exaustiva em malha fechada (SIL): atraso do sensor d in [0,20] ms (passo 1 ms), fase da chegada da mao
    em [0,2) ms (passo 0.25 ms), ciclos perdidos: nenhum / primeiro ciclo apos deteccao / dois consecutivos."""
    d,_=RM.design()
    rows=[]; worst=None
    thr=0.05
    for dly_ms in range(0,21):
        for ph in np.arange(0,2.0,0.25):
            for nlost in (0,1,2):
                t0=0.050+ph*1e-3            # a mao entra em t0
                dly=dly_ms*1e-3
                k_det=int(math.ceil((t0+dly)/P.TS-1e-9))
                lost=tuple(range(k_det,k_det+nlost))
                o=RM.closed_loop(d,lambda t: 400.0,T=0.25,prox_fun=lambda t: t>=t0,sensor_delay=dly,lost_cycles=lost,
                                 x0=[0,0,0],collab=True)
                # torque zero = |i| < thr de forma permanente apos t0
                idx=np.where(o['t']>=t0)[0]; i=np.abs(o['i'][idx]); t=o['t'][idx]
                bad=np.where(i>=thr)[0]; tz=(t[bad[-1]] if len(bad) else t[0])-t0
                # tz pode incluir a corrente ja baixa antes (ok)
                rows.append((dly_ms,float(ph),nlost,float(tz*1e3),float(o['i'][np.searchsorted(o['t'],t0)])))
                if worst is None or tz*1e3>worst[3]: worst=rows[-1]
    arr=np.array(rows)
    res=dict(n_comb=len(rows),worst=dict(delay_ms=worst[0],phase_ms=worst[1],lost=worst[2],t_zero_ms=worst[3]),
        max_by_lost={int(n):float(arr[arr[:,2]==n,3].max()) for n in (0,1,2)},
        min_all=float(arr[:,3].min()),n_violations=int((arr[:,3]>100).sum()),
        margin_ms=100-float(arr[arr[:,2]<=1,3].max()))
    # modelo analitico de pior caso
    res['analytic_worst_ms']=P.T_SENSOR*1e3+P.TS*1e3*(1+1)+ (1+V.decay_cycles())*P.TS*1e3
    return res,arr

if __name__=="__main__":
    a=item_a(); b=item_b(); c=item_c(a); dres,arr=item_d()
    out=dict(a=a,b=b,c=c,d=dres)
    json.dump(out,open('../results/memorial.json','w'),indent=1)
    np.save('../results/sweep.npy',arr)
    print(json.dumps(out,indent=1)[:6000])
