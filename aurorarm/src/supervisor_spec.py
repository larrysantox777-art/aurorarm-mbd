"""Especificacao unica do supervisor de seguranca (nivel de ciclo de 2 ms).
Esta tabela e a FONTE DA VERDADE: (i) o verificador (verify_supervisor.py) a executa
no modelo temporizado; (ii) o gerador (codegen.py) a traduz para C.
Guardas usam subconjunto comum Python/C ('and','or','not').
Trace: REQ-SAFE-AA-001..004 -> MOD-SUP -> aurora_ctrl.c (aurora_supervisor_step) -> TST-SUP-*
"""
STATES = ["MOVING", "SAFE_STOP", "WAIT_REARM"]
STOP_CYCLES = 5     # ciclos em SAFE_STOP antes de aceitar WAIT_REARM (>= tempo de decaimento da corrente)

def spec(version="v1"):
    """version: 'v1' (corrigido), 'v0_edge' (preliminar: deteccao por borda),
    'v0_stale_rearm' (preliminar: rearme memorizado fora de WAIT_REARM)."""
    if version == "v1":
        return dict(
            version=version, uses_prev=False, uses_latch=False, prev_update_in=[],
            transitions=[
                ("MOVING",     "SAFE_STOP",  "prox or overspeed",         ["stop_cnt = 0"]),
                ("SAFE_STOP",  "WAIT_REARM", "(not prox) and stop_cnt >= STOP_CYCLES", []),
                ("WAIT_REARM", "SAFE_STOP",  "prox",                      ["stop_cnt = 0"]),
                ("WAIT_REARM", "MOVING",     "(not prox) and rearm",      []),
            ])
    if version == "v0_edge":     # erro: borda de subida em vez de nivel; prev so atualizado em MOVING
        return dict(
            version=version, uses_prev=True, uses_latch=False, prev_update_in=["MOVING"],
            transitions=[
                ("MOVING",     "SAFE_STOP",  "(prox and not prev_prox) or overspeed", ["stop_cnt = 0"]),
                ("SAFE_STOP",  "WAIT_REARM", "(not prox) and stop_cnt >= STOP_CYCLES", []),
                ("WAIT_REARM", "SAFE_STOP",  "prox",                      ["stop_cnt = 0"]),
                ("WAIT_REARM", "MOVING",     "(not prox) and rearm",      []),
            ])
    if version == "v0_stale_rearm":  # erro: rearme pressionado em qualquer estado fica memorizado
        return dict(
            version=version, uses_prev=False, uses_latch=True, prev_update_in=[],
            transitions=[
                ("MOVING",     "SAFE_STOP",  "prox or overspeed",         ["stop_cnt = 0"]),
                ("SAFE_STOP",  "WAIT_REARM", "(not prox) and stop_cnt >= STOP_CYCLES", []),
                ("WAIT_REARM", "SAFE_STOP",  "prox",                      ["stop_cnt = 0"]),
                ("WAIT_REARM", "MOVING",     "(not prox) and latch",      []),
            ])
    raise ValueError(version)
