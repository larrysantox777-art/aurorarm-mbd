import numpy as np, math, json, os, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import params as P, refmodel as RM, sil, identification as ID
F='../figs/'; d=RM.design()[0]
plt.rcParams.update({'font.size':9,'figure.dpi':130})
# 1 degraus
fig,ax=plt.subplots(1,3,figsize=(11,3.2))
for a in (2,5,10,15):
    cc=sil.CCtrl('/tmp/aurora_v1.so',False); o=RM.closed_loop(d,lambda t:a,T=0.5,ctrl=cc,collab=False)
    ax[0].plot(o['t']*1e3,o['th']/a,label=f'{a} rad'); ax[1].plot(o['t']*1e3,o['i']); ax[2].plot(o['t']*1e3,o['u'])
ax[0].axhline(1.08,ls='--',c='r',lw=.8); ax[0].axhline(0.98,c='gray',lw=.5); ax[0].axhline(1.02,c='gray',lw=.5); ax[0].axvline(300,ls='--',c='r',lw=.8)
ax[0].set_title('Posição normalizada (limites 8 % / 300 ms)'); ax[0].legend(); ax[0].set_xlabel('t [ms]'); ax[0].set_ylim(0,1.15)
ax[1].axhline(8,ls='--',c='r',lw=.8); ax[1].set_title('Corrente [A] (limite 8 A)'); ax[1].set_xlabel('t [ms]')
ax[2].axhline(48,ls='--',c='r',lw=.8); ax[2].set_title('Tensão [V] (limite 48 V)'); ax[2].set_xlabel('t [ms]')
plt.tight_layout(); plt.savefig(F+'fig_step.png'); plt.close()
# 2 anti-windup
fig,ax=plt.subplots(1,2,figsize=(8,3.2))
for aw,l in ((True,'com anti-windup'),(False,'sem anti-windup')):
    o=RM.closed_loop(d,lambda t:10,T=1.0,collab=False,use_aw=aw); ax[0].plot(o['t'],o['th'],label=l); ax[1].plot(o['t'],o['u'],label=l)
ax[0].axhline(10,c='k',lw=.5); ax[0].set_title('Posição, degrau 10 rad'); ax[0].legend(); ax[1].set_title('Tensão [V]'); 
for x in ax: x.set_xlabel('t [s]')
plt.tight_layout(); plt.savefig(F+'fig_antiwindup.png'); plt.close()
# 3 cruzeiro
cc=sil.CCtrl('/tmp/aurora_v1.so',False); o=RM.closed_loop(d,sil.cruise_traj,T=2.5,ctrl=cc,collab=False)
fig,ax=plt.subplots(1,3,figsize=(11,3.2))
ax[0].plot(o['t'],o['w']); ax[0].axhline(450,ls='--',c='r',lw=.8); ax[0].set_title('ω [rad/s]')
ax[1].plot(o['t'],o['i']); ax[1].axhline(3.735,ls='--',c='g',lw=.8); ax[1].axhline(8,ls='--',c='r',lw=.8); ax[1].set_title('i [A]')
ax[2].plot(o['t'],o['u']); ax[2].axhline(41.238,ls='--',c='g',lw=.8); ax[2].axhline(48,ls='--',c='r',lw=.8); ax[2].set_title('u [V] (regime 41,24 V; limite 48 V)')
for x in ax: x.set_xlabel('t [s]')
plt.tight_layout(); plt.savefig(F+'fig_cruise.png'); plt.close()
# 4 colaborativo: parada e rearme
cc=sil.CCtrl('/tmp/aurora_v1.so',True)
o=RM.closed_loop(d,lambda t:30.0,T=2.0,prox_fun=lambda t:0.30<=t<0.9,sensor_delay=0.02,rearm_fun=lambda t:t>=1.0,ctrl=cc,collab=True)
fig,ax=plt.subplots(1,3,figsize=(11,3.2))
ax[0].plot(o['t'],o['th'],label='θ'); ax[0].plot(o['t'],o['rl'],'--',label='ref limitada'); ax[0].axhline(30,c='k',lw=.4); ax[0].legend(); ax[0].set_title('Posição [rad]: parada, rearme, retomada')
ax[1].plot(o['t'],o['i']); ax[1].set_title('i [A]'); ax[1].axvline(0.30,c='r',ls=':'); ax[1].axvline(0.32,c='g',ls=':')
ax[2].step(o['t'],o['sup'],where='post'); ax[2].set_yticks([0,1,2]); ax[2].set_yticklabels(['MOVING','SAFE_STOP','WAIT_REARM']); ax[2].set_title('Estado do supervisor')
for x in ax: x.set_xlabel('t [s]')
plt.tight_layout(); plt.savefig(F+'fig_collab.png'); plt.close()
# 5 varredura
arr=np.load('../results/sweep.npy')
fig,ax=plt.subplots(1,2,figsize=(9,3.2))
for n,c in ((0,'C0'),(1,'C1'),(2,'C2')):
    m=arr[:,2]==n; ax[0].scatter(arr[m,0]+0.04*n,arr[m,3],s=6,c=c,label=f'{n} ciclo(s) perdido(s)')
ax[0].axhline(100,c='r',ls='--'); ax[0].set_xlabel('atraso do sensor [ms]'); ax[0].set_ylabel('tempo até torque zero [ms]'); ax[0].legend(fontsize=7); ax[0].set_ylim(0,110)
ax[1].hist(arr[:,3],bins=30); ax[1].axvline(100,c='r',ls='--'); ax[1].set_xlabel('t torque zero [ms]'); ax[1].set_title('504 combinações')
plt.tight_layout(); plt.savefig(F+'fig_sweep.png'); plt.close()
# 6 identificacao
r,(u2,Y2,X2,pred,Ytrue,pred20)=ID.run()
fig,ax=plt.subplots(1,2,figsize=(9,3)); n=600
ax[0].plot(Y2[1:n,1],lw=.5,c='gray',label='medido (ruidoso)'); ax[0].plot(Ytrue[:n,1],label='real'); ax[0].plot(pred20[:n,1],'--',label='modelo identificado'); ax[0].set_title('ω validação (pred. 20 ms)'); ax[0].legend(fontsize=7)
ax[1].plot(Ytrue[:n,0],label='real'); ax[1].plot(pred20[:n,0],'--',label='identificado'); ax[1].set_title('i validação'); ax[1].legend(fontsize=7)
for x in ax: x.set_xlabel('amostra (1 ms)')
plt.tight_layout(); plt.savefig(F+'fig_ident.png'); plt.close()
json.dump(r,open('../results/identification.json','w'),indent=1)
# 7 FSM
fig,ax=plt.subplots(figsize=(8,3.6)); ax.axis('off'); ax.set_xlim(0,10); ax.set_ylim(0,4.4)
pos={'MOVING':(1.5,2.2),'SAFE_STOP':(5,3.4),'WAIT_REARM':(8.5,2.2)}
for k,(x,y) in pos.items():
    ax.add_patch(FancyBboxPatch((x-1.1,y-.4),2.2,.8,boxstyle='round,pad=0.05',fc='#dbe9f7',ec='k')); ax.text(x,y,k,ha='center',va='center',weight='bold')
def arr_(a,b,txt,rad=0.2,off=(0,0)):
    p=FancyArrowPatch(pos[a],pos[b],connectionstyle=f'arc3,rad={rad}',arrowstyle='-|>',mutation_scale=12,shrinkA=38,shrinkB=38); ax.add_patch(p)
    mx=(pos[a][0]+pos[b][0])/2+off[0]; my=(pos[a][1]+pos[b][1])/2+off[1]; ax.text(mx,my,txt,ha='center',fontsize=7.5,bbox=dict(fc='w',ec='none',pad=1))
arr_('MOVING','SAFE_STOP','T1: prox ∨ overspeed\n/ stop_cnt:=0',-0.25,(-0.9,0.5))
arr_('SAFE_STOP','WAIT_REARM','T2: ¬prox ∧ stop_cnt ≥ 5',-0.25,(0.9,0.55))
arr_('WAIT_REARM','SAFE_STOP','T3: prox / stop_cnt:=0',-0.25,(0.9,-0.1))
arr_('WAIT_REARM','MOVING','T4: ¬prox ∧ rearm',0.0,(0,-0.55))
ax.text(5,0.5,'Ciclo = 2 ms. Em SAFE_STOP/WAIT_REARM: u = Ke·ω (corrente decai); freio quando stop_cnt ≥ 5.',ha='center',fontsize=8)
plt.savefig(F+'fig_fsm.png',bbox_inches='tight'); plt.close()
# 8 arquitetura
fig,ax=plt.subplots(figsize=(10,3.2)); ax.axis('off'); ax.set_xlim(0,12); ax.set_ylim(0,4)
boxes=[(0.2,'Gerador de\ntrajetória\n(vmax, amax)'),(2.7,'Lei de controle\nu=-Kx+Kz·z\n+ clamp V e i\n+ anti-windup'),(5.2,'Driver +\nmotor CC\n(A,B)'),(7.7,'Junta\n100:1 + freio')]
for x,t in boxes:
    ax.add_patch(FancyBboxPatch((x,1.6),2.0,1.4,boxstyle='round,pad=0.05',fc='#e8f3e8',ec='k')); ax.text(x+1,2.3,t,ha='center',va='center',fontsize=8)
for x in (2.25,4.75,7.25): ax.annotate('',xy=(x+0.4,2.3),xytext=(x,2.3),arrowprops=dict(arrowstyle='-|>'))
ax.add_patch(FancyBboxPatch((2.7,0.2),2.0,0.9,boxstyle='round,pad=0.05',fc='#fde8d8',ec='k')); ax.text(3.7,0.65,'Supervisor\n(FSM 3 estados)',ha='center',va='center',fontsize=8)
ax.add_patch(FancyBboxPatch((9.9,1.6),1.9,1.4,boxstyle='round,pad=0.05',fc='#f5f5d0',ec='k')); ax.text(10.85,2.3,'Sensores:\ni, ω, θ, prox\n(atraso ≤ 20 ms)',ha='center',va='center',fontsize=8)
ax.annotate('',xy=(9.9,2.3),xytext=(9.7,2.3),arrowprops=dict(arrowstyle='<|-'))
ax.annotate('',xy=(3.7,1.6),xytext=(3.7,1.1),arrowprops=dict(arrowstyle='<|-'))
ax.text(6,3.6,'Fluxo MBD: parâmetros → (A,B,C,D) → projeto de K → modelo de referência → verificação → geração de C → SIL',ha='center',fontsize=8.5)
plt.savefig(F+'fig_arch.png',bbox_inches='tight'); plt.close()
print('figs ok')
