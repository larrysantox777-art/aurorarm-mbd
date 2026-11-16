"""Parametros fisicos e requisitos do AuroraArm (junta do cotovelo).
Fonte: enunciado 'Operacao Linha Viva' (tabela de bancada). Unidades SI.
Trace: MEM-A, MEM-B (memorial), REQ-CTRL-AA-001..004.
"""
R = 0.8            # ohm
L = 1.2e-3         # H
Kt = 0.085         # N.m/A
Ke = 0.085         # V.s/rad
J = 4.2e-4         # kg.m^2 (refletida no eixo do motor)
b = 1.5e-4         # N.m.s/rad (refletido)
N = 100            # reducao
VMAX = 48.0        # V
IMAX = 8.0         # A
TS = 2e-3          # s

# Ponto de operacao critico
W_SS = 450.0       # rad/s (eixo do motor)
T_LOAD = 0.25      # N.m (torque de carga refletido, dado do enunciado)
M_PAYLOAD = 2.0    # kg
R_PAYLOAD = 0.35   # m
G = 9.81

# Seguranca colaborativa
V_TIP_MAX = 0.250  # m/s  (REQ-SAFE-AA-004)
D_PROX = 0.500     # m    (REQ-SAFE-AA-001)
T_SAFE = 0.100     # s    (REQ-SAFE-AA-001)
T_SENSOR = 0.020   # s    atraso de deteccao (pior caso)
T_JITTER = TS      # s    um ciclo perdido

# Margens de projeto (decisoes do autor, justificadas no relatorio)
I_LIM_DESIGN = 6.0   # A  (75% de IMAX: margem p/ erro de modelo; ver relatorio, Monte Carlo +-10%)
V_LIM_DESIGN = 48.0  # V
