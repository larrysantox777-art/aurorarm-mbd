import numpy as np
from scipy.linalg import expm
from params import *

def continuous_matrices(with_position=False):
    A = np.array([[-R/L, -Ke/L],[Kt/J, -b/J]])
    B = np.array([[1/L],[0.0]])
    C = np.array([[0.0, 1.0]])
    D = np.array([[0.0]])
    if with_position:  # x = [i, w, theta_m]
        A3 = np.zeros((3,3)); A3[:2,:2] = A; A3[2,1] = 1.0
        B3 = np.vstack([B,[[0.0]]])
        E3 = np.array([[0.0],[-1.0/J],[0.0]])   # torque de carga entra em w com -1/J
        C3 = np.array([[0,0,1.0]])
        return A3, B3, C3, np.array([[0.0]]), E3
    return A, B, C, D

def zoh(A, B, Ts):
    n = A.shape[0]; m = B.shape[1]
    M = np.zeros((n+m, n+m)); M[:n,:n] = A*Ts; M[:n,n:] = B*Ts
    E = expm(M)
    return E[:n,:n], E[:n,n:]

def ctrb(A,B):
    n=A.shape[0]; cols=[B]
    for _ in range(n-1): cols.append(A@cols[-1])
    return np.hstack(cols)

def obsv(A,C):
    n=A.shape[0]; rows=[C]
    for _ in range(n-1): rows.append(rows[-1]@A)
    return np.vstack(rows)
