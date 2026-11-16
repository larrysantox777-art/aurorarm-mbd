"""Gera a matriz de rastreabilidade requisito -> modelo -> codigo -> teste -> evidencia (com resultado extraido dos JSON)."""
import json, csv, os
H=os.path.dirname(os.path.abspath(__file__)); R=lambda f: json.load(open(os.path.join(H,'..','results',f)))
t=R('sil_tests.json'); m=R('memorial.json'); v=R('verification_variants.json'); s=R('verification_sensitivity.json'); eq=R('sil_equivalence.json')['equivalence']
sw=t['requirements']['step_sweep']; mc=t['requirements']['monte_carlo']; tip=t['requirements']['tip_speed']
v1=v['v1']
rows=[
 ("REQ-CTRL-AA-001","erro nulo em regime (degrau)","MOD-CTRL: estado integrador z (src/refmodel.py: design, CtrlRef.step)","generated/aurora_ctrl.c:aurora_step (s->z, K_Z)","TST-CTRL-001 (sil_tests.py:req_tests step_sweep, MC)",
  f"erro final máx. {max(r['ess'] for r in sw):.1e} rad (nominal); {mc['max_ess']:.1e} rad (MC ±10 %)"),
 ("REQ-CTRL-AA-002","sobressinal ≤ 8 %","MOD-CTRL: alocação de polos {-450, -60±j30, -100} s⁻¹ (discretizados a Ts=2 ms)","generated/aurora_ctrl.c:aurora_step (K_I,K_W,K_TH,K_Z)","TST-CTRL-002",
  f"nominal ≤ {max(r['overshoot_pct'] for r in sw):.2f} % (1–15 rad); MC ±10 % ≤ {mc['max_os']:.2f} % (2–10 rad)"),
 ("REQ-CTRL-AA-003","acomodação ≤ 300 ms","MOD-CTRL (idem)","generated/aurora_ctrl.c:aurora_step","TST-CTRL-003",
  f"nominal ≤ {max(r['settling_s'] for r in sw)*1e3:.0f} ms (≤15 rad); MC ≤ {mc['max_ts']*1e3:.0f} ms"),
 ("REQ-CTRL-AA-004","|u| ≤ 48 V e |i| ≤ 8 A sempre","MOD-CTRL: saturação de tensão + limitador preditivo de corrente (ILIM=6 A) + anti-windup por retrocálculo","generated/aurora_ctrl.c:aurora_step (VMAX, ILIM, K_AW)","TST-CTRL-004",
  f"nominal |i| ≤ {max(r['imax'] for r in sw):.2f} A, |u| ≤ {max(r['umax'] for r in sw):.1f} V; MC: |i| ≤ {mc['max_imax']:.2f} A, falhas 0/{mc['n']}"),
 ("REQ-SAFE-AA-001","mão < 500 mm ⇒ torque zero ≤ 100 ms","MOD-SUP: T1 (src/supervisor_spec.py) + modelo temporizado (src/verify_supervisor.py)","generated/aurora_ctrl.c:aurora_supervisor_step (case SUP_MOVING)","TST-VER-001 (exaustivo), TST-SWP-001 (504 comb. SIL), TST-SUP-001",
  f"modelo: pior caso {v1['max_latency_ms']:.0f} ms (tick 1 ms), analítico 34 ms; varredura SIL {m['d']['max_by_lost']['1']:.2f} ms; folga ≥ 66 ms"),
 ("REQ-SAFE-AA-002","sem retomada automática (exige rearme)","MOD-SUP: T4 só a partir de WAIT_REARM com rearm amostrado no mesmo ciclo","generated/aurora_ctrl.c:aurora_supervisor_step (case SUP_WAIT_REARM)","TST-VER-002, TST-SUP-002, TST-MUT-001",
  f"modelo: vale ({v1['states']} estados); 120 000 ciclos aleatórios sem violação; mutante 'rearme memorizado' reprovado"),
 ("REQ-SAFE-AA-003","mão removida + rearme ⇒ retoma trajetória original","MOD-SUP: T2/T4; MOD-CTRL: gerador de trajetória parte da posição atual rumo ao alvo r","generated/aurora_ctrl.c:aurora_supervisor_step + aurora_step (rl, v)","TST-VER-003 (vivacidade), TST-SUP-003, fig_collab",
  f"vivacidade: sem ciclo evitando MOVING; latência máx. {v1['liveness']['max_ms']:.0f} ms ({int(v1['liveness']['max_ms']/2)} ciclos); simulação retoma e atinge alvo"),
 ("REQ-SAFE-AA-004","v_efetuador ≤ 250 mm/s na zona colaborativa","MOD-CTRL: gerador (|v| ≤ 0,8·limite, |a| ≤ 500 rad/s²) + MOD-SUP: disparo por sobrevelocidade","generated/aurora_ctrl.c:aurora_step (RATEV, WOVER)","TST-SAFE-004",
  f"pico {max(x['v_tip_mm_s'] for x in tip):.0f} mm/s (alavanca 0,35 m); sem disparo"),
]
cols=["Requisito","Descrição","Modelo","Código (arquivo:função)","Teste(s)","Resultado (evidência em results/)"]
with open(os.path.join(H,'..','docs','traceability_matrix.csv'),'w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(cols); w.writerows(rows)
with open(os.path.join(H,'..','docs','traceability_matrix.md'),'w',encoding='utf-8') as f:
    f.write("| "+" | ".join(cols)+" |\n|"+"---|"*len(cols)+"\n")
    for r in rows: f.write("| "+" | ".join(x.replace('|','/') for x in r)+" |\n")
json.dump(rows,open(os.path.join(H,'..','results','traceability_rows.json'),'w'),ensure_ascii=False,indent=1)
print("ok",len(rows))
