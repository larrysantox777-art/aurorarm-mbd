# AuroraArm — junta do cotovelo: pacote de projeto baseado em modelos

Trabalho "Operação Linha Viva" (UniFECAF, Model Based Design for Cyber-Physical Systems).
Planta: motor CC de ímã permanente 48 V + redução harmônica 100:1. Tudo é reproduzível com `make all`.

## Estrutura
| Caminho | Conteúdo |
|---|---|
| `src/params.py` | parâmetros do enunciado e limites de projeto |
| `src/plant.py` | matrizes A, B, C, D (2 estados: i, ω; 3 estados com θ), discretização ZOH, posto de controlabilidade/observabilidade |
| `src/identification.py` | identificação por mínimos quadrados + validação (dados **sintéticos** de bancada) |
| `src/refmodel.py` | projeto do controlador (alocação de polos, Ts = 2 ms), modelo de referência (float64/float32), planta e simulação em malha fechada |
| `src/supervisor_spec.py` | tabela do supervisor de segurança (fonte única: verificação **e** geração de código) |
| `src/verify_supervisor.py` | verificador exaustivo de estados explícitos (autômato temporizado digitalizado) |
| `src/codegen.py` | gerador de código C a partir do modelo → `generated/aurora_ctrl.{h,c}` (cabeçalho de rastreabilidade) |
| `src/sil.py`, `src/sil_tests.py` | SIL: equivalência modelo-código, testes por grafo de estados, propriedades, mutação |
| `src/memorial.py` | memorial de cálculo (a)–(d); (e) em `sil.py` |
| `src/traceability.py` | matriz requisito → modelo → código → teste → resultado |
| `tests/mutants/` | versões preliminares (com erro) geradas do modelo, usadas para provar que a suíte detecta defeitos |
| `results/`, `figs/`, `docs/` | evidências (JSON, gcov), figuras, matriz, relatório e roteiro do vídeo |

## Reprodução
```
python3 src/run_all.py      # ou: make all   (requer numpy, scipy, matplotlib, gcc)
make test                   # regenera C, equivalência SIL e suíte
```
Compilação do C gerado: `gcc -std=c99 -Wall -Wextra -pedantic -O2 -ffp-contract=off -fno-fast-math -c generated/aurora_ctrl.c`

## Limites declarados
Ver seção 6 do relatório (`docs/AuroraArm_Relatorio_Tecnico.pdf`): dados de identificação sintéticos, gerador de código não qualificado,
sem HIL/WCET no alvo, verificador próprio (recomenda-se checagem cruzada com UPPAAL), sem análise de falhas de hardware (IEC 61508/ISO 26262).
