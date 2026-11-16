"""Reproduz todo o pacote de evidencias: python3 src/run_all.py  (ou: make all)"""
import subprocess, sys, os
H=os.path.dirname(os.path.abspath(__file__)); os.chdir(H)
steps=[("codegen.py","gera C a partir do modelo"),("memorial.py","memorial (a)-(d)"),("identification.py","identificacao"),
       ("sil.py > ../results/sil_equivalence.json","equivalencia SIL (e)"),("sil_tests.py","suite de testes"),("make_figures.py","figuras")]
for cmd,desc in steps:
    print(">>",desc); subprocess.check_call(f"{sys.executable} {cmd}"+("" if '>' in cmd else " > /dev/null"),shell=True)
print(">> verificacao formal (model checker)")
subprocess.check_call(f"{sys.executable} -c \"import verify_supervisor as V,json;r={{v:V.run(v) for v in ['v1','v0_edge','v0_stale_rearm']}};json.dump(r,open('../results/verification_variants.json','w'),indent=1,default=str);print({{k:(x['safe001_holds'],x['safe002_holds'],x['max_latency_ms']) for k,x in r.items()}})\"",shell=True)
print("OK")
