# -*- coding: utf-8 -*-
import json, os, math
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, Preformatted
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
FD='/usr/share/fonts/truetype/dejavu/'
pdfmetrics.registerFont(TTFont('DV',FD+'DejaVuSans.ttf')); pdfmetrics.registerFont(TTFont('DV-B',FD+'DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DV-I',FD+'DejaVuSans-Oblique.ttf')); pdfmetrics.registerFont(TTFont('DV-BI',FD+'DejaVuSans-BoldOblique.ttf'))
pdfmetrics.registerFont(TTFont('DVM',FD+'DejaVuSansMono.ttf'))
from reportlab.pdfbase.pdfmetrics import registerFontFamily
registerFontFamily('DV',normal='DV',bold='DV-B',italic='DV-I',boldItalic='DV-BI')
H=os.path.dirname(os.path.abspath(__file__)); RES=lambda f: json.load(open(os.path.join(H,'..','results',f)))
M=RES('memorial.json'); T=RES('sil_tests.json'); EQ=RES('sil_equivalence.json')['equivalence']; V=RES('verification_variants.json'); S=RES('verification_sensitivity.json'); ID=RES('identification.json'); D=json.load(open(os.path.join(H,'..','generated','manifest.json')))
TR=RES('traceability_rows.json'); a=M['a']; b=M['b']; c=M['c']; d=M['d']
FIG=os.path.join(H,'..','figs')

st=dict(
 body=ParagraphStyle('b',fontName='DV',fontSize=9,leading=12.6,alignment=TA_JUSTIFY,spaceAfter=5),
 h1=ParagraphStyle('h1',fontName='DV-B',fontSize=14,leading=18,spaceBefore=12,spaceAfter=6,textColor=colors.HexColor('#0b3d6e')),
 h2=ParagraphStyle('h2',fontName='DV-B',fontSize=11,leading=14,spaceBefore=9,spaceAfter=4,textColor=colors.HexColor('#0b3d6e')),
 h3=ParagraphStyle('h3',fontName='DV-B',fontSize=9.5,leading=12,spaceBefore=6,spaceAfter=3),
 cap=ParagraphStyle('cap',fontName='DV-I',fontSize=8,leading=10,alignment=TA_CENTER,spaceAfter=7),
 cell=ParagraphStyle('cell',fontName='DV',fontSize=7.4,leading=9.2),
 cellb=ParagraphStyle('cellb',fontName='DV-B',fontSize=7.4,leading=9.2),
 eq=ParagraphStyle('eq',fontName='DV',fontSize=9,leading=13,leftIndent=18,spaceAfter=3),
 code=ParagraphStyle('code',fontName='DVM',fontSize=7,leading=8.6,leftIndent=10),
 title=ParagraphStyle('t',fontName='DV-B',fontSize=22,leading=27,alignment=TA_CENTER,textColor=colors.HexColor('#0b3d6e')),
 sub=ParagraphStyle('s',fontName='DV',fontSize=12,leading=16,alignment=TA_CENTER),
)
def P(t,s='body'): return Paragraph(t,st[s])
def tbl(rows,widths,head=True,fs=None):
    data=[[Paragraph(str(x),st['cellb'] if (head and i==0) else st['cell']) for x in r] for i,r in enumerate(rows)]
    t=Table(data,colWidths=widths,repeatRows=1 if head else 0)
    sty=[('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#9aa5b1')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]
    if head: sty.append(('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e3ecf5')))
    t.setStyle(TableStyle(sty)); return t
def fig(name,w,cap):
    from PIL import Image as PI
    im=PI.open(os.path.join(FIG,name)); r=im.size[1]/im.size[0]
    return KeepTogether([Image(os.path.join(FIG,name),width=w,height=w*r),P(cap,'cap')])
def f(x,n=3): return f"{x:.{n}f}".replace('.',',')
def fe(x): return f"{x:.2e}".replace('.',',')

W=A4[0]-4*cm
S_=[]
# ---------------- capa
S_+= [Spacer(1,3*cm),P('Operação Linha Viva','title'),Spacer(1,6),P('O desafio do braço colaborativo AuroraArm','sub'),Spacer(1,10),
 P('Pacote técnico de design baseado em modelos para a junta do cotovelo:<br/>modelagem, controle, verificação formal, geração de código e rastreabilidade','sub'),Spacer(1,1.2*cm),
 P('Relatório técnico (parte teórica e prática) com memorial de cálculo anexo','sub'),Spacer(1,2*cm),
 tbl([['Disciplina','Model Based Design for Cyber-Physical Systems — UniFECAF'],['Contratante (fictício)','Aurora Robótica'],['Papel','Engenheiro(a) de design baseado em modelos'],
      ['Repositório (Git)','[INSERIR LINK DO REPOSITÓRIO ANTES DA SUBMISSÃO]'],['Vídeo (≤ 5 min)','[INSERIR LINK DO VÍDEO NÃO LISTADO ANTES DA SUBMISSÃO]'],
      ['Reprodução','<font name="DVM">python3 src/run_all.py</font> (ou <font name="DVM">make all</font>)']],[4.2*cm,W-4.2*cm],head=False),
 Spacer(1,1.5*cm)]
S_.append(P('<b>Nota de leitura.</b> Todo número deste relatório é produzido por código do repositório e está em <font name="DVM">results/*.json</font>. Caminhos de arquivo entre <font name="DVM">fonte mono</font> são relativos à raiz do repositório. O enunciado menciona o exemplo "NexaBot" da disciplina; o método aqui seguido é o das quatro unidades (modelagem → controle → verificação → código/rastreabilidade).'))
S_.append(PageBreak())

# ---------------- resumo
S_.append(P('Resumo executivo','h1'))
S_.append(P(f"Foi construído, para a junta do cotovelo do AuroraArm, um pacote reprodutível em quatro blocos. <b>(1) Modelo:</b> espaço de estados <i>x</i> = [<i>i</i>, ω]<super>T</super> com autovalores −22,6 e −644,4 s<super>−1</super> (τ<sub>m</sub> = {f(a['tau_slow_s']*1e3,1)} ms, τ<sub>e</sub> = {f(a['tau_fast_s']*1e3,2)} ms), controlável e observável; no ponto crítico (450 rad/s, 0,25 N·m) a junta exige <b>{f(b['iss'])} A e {f(b['vss'],2)} V</b>, folga de {f(b['folga_V'],2)} V ({f(b['folga_pct'],1)} %) sobre os 48 V. "
 f"<b>(2) Controle:</b> realimentação de estados com integrador, discretizada a T<sub>s</sub> = 2 ms (22 amostras por τ<sub>m</sub>), saturação de tensão, limitador preditivo de corrente e anti-windup por retrocálculo; sem anti-windup o sobressinal chega a {f(min(x['os_no_aw'] for x in T['requirements']['no_antiwindup']),0)}–{f(max(x['os_no_aw'] for x in T['requirements']['no_antiwindup']),0)} %. "
 f"<b>(3) Verificação:</b> verificador exaustivo de estados explícitos sobre o supervisor de 3 estados com sensor de até 20 ms, ciclo perdido e fase de amostragem; o prazo de 100 ms é cumprido com pior caso de {f(V['v1']['max_latency_ms'],0)} ms no modelo discreto (limite analítico 34 ms); a versão preliminar (detecção por borda) produziu contraexemplo, reproduzindo o quase-acidente. "
 f"<b>(4) Código:</b> C em ponto flutuante simples gerado por <font name='DVM'>src/codegen.py</font> a partir do mesmo modelo; no SIL o erro é <b>exatamente zero</b> contra o modelo float32 e ≤ {f(EQ['per_scenario']['S3_cruise450']['err_over_eps_termsum'],1)}·ε·Σ|termos| contra float64; matriz de rastreabilidade cobre os 8 requisitos."))
S_.append(P("<b>Resultados que merecem atenção do leitor</b> (detalhados nas seções 3 a 6): (i) o limite de corrente de projeto foi reduzido de 7,6 A para 6,0 A porque, sob ±10 % de incerteza paramétrica, 7,6 A levava a picos de 9,4 A (violação de REQ-CTRL-AA-004); (ii) REQ-CTRL-AA-002/003 são verificados para degraus de até 10 rad no eixo do motor (0,10 rad na junta) sob incerteza, e até 15 rad no modelo nominal; (iii) o torque de carga fornecido (0,25 N·m) é 3,6 vezes o torque do payload ideal (0,069 N·m), logo é tratado como premissa conservadora; (iv) a identificação usa dados <b>sintéticos</b>, pois o enunciado não traz dados de bancada brutos; (v) o pacote <b>não</b> equivale a certificação (seção 6)."))
S_.append(P('Sumário','h2'))
for t in ['1. Contexto, premissas e leitura crítica do enunciado','2. Parte teórica','3. Parte prática: projeto e resultados','4. Verificação formal do supervisor','5. Código gerado, testes e rastreabilidade','6. Honestidade técnica: o que o pacote sustenta e o que não sustenta','7. Referências','Anexo A — Memorial de cálculo (a)–(e)','Anexo B — Links de entrega']:
    S_.append(P(t))
S_.append(PageBreak())

# ---------------- 1
S_.append(P('1. Contexto, premissas e leitura crítica do enunciado','h1'))
S_.append(P("A Aurora Robótica pretende liberar uma célula sem cerca física. Um protótipo anterior sofreu um quase-acidente porque o firmware manual não tratava a borda entre os estados de movimento e de parada de segurança, e não havia evidência reprodutível. O objetivo é substituir o projeto manual por um fluxo em que o <b>mesmo modelo</b> alimenta a simulação, a verificação e a geração de código (Unidades 1 a 4)."))
S_.append(P('Premissas adotadas (todas declaradas também no código)','h3'))
S_.append(tbl([['#','Premissa','Justificativa / efeito'],
 ['P1','Estados medidos: <i>i</i> (sensor de corrente), ω e θ (encoder, velocidade derivada). Sem ruído de medição no SIL.','Escopo do enunciado; ruído e filtragem ficam como trabalho futuro (seção 6).'],
 ['P2','θ é o ângulo do eixo do motor; ângulo da junta = θ/100. Alavanca do efetuador = 0,35 m (dado do payload).','Se o efetuador estiver mais longe do cotovelo, a velocidade linear sobe proporcionalmente e o limite de REQ-SAFE-AA-004 em rad/s cai.'],
 ['P3',f"Torque de carga = 0,25 N·m (dado). Payload ideal: 2·9,81·0,35/100 = {f(b['T_payload_motor'],4)} N·m (razão {f(b['ratio_load_vs_payload'],2)}×).",'O dado fornecido é tratado como carga total refletida (payload + atrito + folga de projeto), pior caso. Se fosse só o payload, a tensão exigida cairia de 41,24 V para 39,53 V.'],
 ['P4','O ponto de 450 rad/s no motor equivale a 4,5 rad/s na junta e 1,575 m/s no efetuador (≫ 250 mm/s).','Esse ponto <b>não pode ocorrer na zona colaborativa</b>. Por isso o controlador tem dois modos: <i>não colaborativo</i> (sem gerador de trajetória; usado para verificar REQ-CTRL e o ponto crítico) e <i>colaborativo</i> (gerador de trajetória + disparo por sobrevelocidade; limite de motor 71,4 rad/s).'],
 ['P5','"Torque zero" = comando de corrente nula: |<i>i</i>| &lt; 0,05 A (0,6 % do torque máx.), obtido com <i>u</i> = K<sub>e</sub>ω (cancela a f.c.e.m.). Freio mecânico retém a junta depois da confirmação.','Com <i>u</i> = 0 a f.c.e.m. geraria frenagem dinâmica, não torque zero. O freio é necessário porque a carga constante moveria a junta; ele é <b>premissa de hardware</b>, não verificado aqui.'],
 ['P6','Atuação: 1 ciclo de retenção (ZOH) + 4 ciclos de decaimento = 10 ms, calculados em <font name="DVM">verify_supervisor.py:decay_cycles</font>.','Entra como constante T<sub>act</sub> no modelo temporizado.'],
 ['P7','Hipóteses de ambiente do supervisor: atraso do sensor 0–20 ms; no máximo K ciclos consecutivos perdidos (K = 1 no enunciado; sensibilidade em 4.3).','Se a hipótese for violada, a garantia de 100 ms deixa de valer; por isso é reportada a margem.']],
 [0.8*cm,6.6*cm,W-7.4*cm]))
S_.append(Spacer(1,4))
S_.append(P("<b>Nota normativa.</b> O enunciado cita a ISO/TS 15066:2016. Em 2025 foram publicadas as novas ISO 10218-1 e 10218-2, e a parte 2 incorporou a maior parte dos requisitos da TS 15066 [8]. A especificação usada aqui (100 ms, 500 mm, 250 mm/s) é a do enunciado; os limites biomecânicos por região do corpo e massa efetiva da TS 15066 não foram avaliados e seriam indispensáveis para justificar o valor de 250 mm/s numa auditoria real."))
S_.append(P("<b>Caso real consultado (fonte 7).</b> A integração de um UR5 em linha de eletrônicos da Melecs EWS, relatada pela Universal Robots [9], é um relato público e identificável: a célula empacota placas de circuito, e o relato afirma que a operação colaborativa em proximidade só foi liberada após avaliação de risco. O relato é comercial e <b>não traz detalhes de controle ou de verificação</b>; foi usado apenas como contexto de processo (avaliação de risco antes da liberação, escâneres de segurança no efetuador). Nenhum dado numérico do relato foi usado no projeto. Recomenda-se que o aluno substitua ou complemente com relato técnico de maior profundidade, se disponível na disciplina."))
S_.append(PageBreak())

# ---------------- 2
S_.append(P('2. Parte teórica','h1'))
S_.append(P('2.1 Modelagem física a partir das leis de conservação','h2'))
S_.append(P("<b>Equação elétrica (lei das malhas, conservação de energia por carga):</b>"))
S_.append(P("<i>L</i> d<i>i</i>/d<i>t</i> = <i>V</i> − <i>R i</i> − <i>K</i><sub>e</sub> ω","eq"))
S_.append(P("<b>Equação mecânica (conservação do momento angular no eixo do motor, inércia e atrito refletidos pela redução):</b>"))
S_.append(P("<i>J</i> dω/d<i>t</i> = <i>K</i><sub>t</sub> <i>i</i> − <i>b</i> ω − <i>T</i><sub>carga</sub>","eq"))
S_.append(P("<b>Escolha das variáveis de estado.</b> <i>x</i> = [<i>i</i>, ω]<super>T</super> porque são as duas variáveis que armazenam energia (indutância e inércia), cada equação acima é de primeira ordem em uma delas, ambas são medidas diretamente e <i>i</i> é a grandeza que a restrição de 8 A limita. A saída de velocidade é <i>C</i> = [0 1]. Para o laço de posição acrescenta-se θ (dθ/d<i>t</i> = ω), obtendo <i>x</i><sub>3</sub> = [<i>i</i>, ω, θ]<super>T</super>; o torque de carga entra como perturbação constante com ganho −1/<i>J</i> na segunda linha. A tensão <i>V</i> é a entrada <i>u</i>."))
S_.append(P("<i>A</i> = [[−<i>R</i>/<i>L</i>, −<i>K</i><sub>e</sub>/<i>L</i>],[<i>K</i><sub>t</sub>/<i>J</i>, −<i>b</i>/<i>J</i>]],  <i>B</i> = [1/<i>L</i>, 0]<super>T</super>. Substituição e autovalores no Anexo A(a). Resultado central: separação de escalas de tempo de 28,5×, que justifica tratar a corrente como dinâmica rápida e a velocidade como dinâmica dominante, e também implica que T<sub>s</sub> = 2 ms (maior que τ<sub>e</sub>) exige discretização exata (ZOH) e não aproximação de Euler.","eq"))
S_.append(fig('fig_arch.png',W*0.95,'Figura 1 — Arquitetura do pacote: trajetória → lei de controle (com limitadores e anti-windup) → driver/motor/junta; supervisor de segurança em paralelo; sensores com atraso.'))

S_.append(P('2.2 Identificação e validação','h2'))
S_.append(P(f"Como o enunciado só fornece os parâmetros identificados, não os dados brutos, o procedimento foi <b>demonstrado com dados sintéticos</b> (<font name='DVM'>src/identification.py</font>): uma planta \"verdadeira\" com desvios de −5 % a +10 % em relação ao nominal, PRBS de ±10 V a 1 kHz, ruído de 0,02 A em <i>i</i> e 0,5 rad/s em ω. A regressão de mínimos quadrados <i>x</i>[<i>k</i>+1] = Φ<i>x</i>[<i>k</i>] + Γ<i>u</i>[<i>k</i>] + <i>g</i><sub>0</sub> recupera R = {f(ID['R_id'],4)} Ω (real {f(ID['R_true'],4)}), L = {f(ID['L_id']*1e3,3)} mH (real {f(ID['L_true']*1e3,3)}), K<sub>e</sub> = {f(ID['Ke_id'],4)} (real {f(ID['Ke_true'],4)}); J com erro de {f(abs(ID['J_id']/ID['J_true']-1)*100,1)} %. O atrito viscoso <i>b</i> <b>não é bem identificável</b> com este experimento (erro de ordem 190 %), mas sua influência é desprezível: <i>b</i>/<i>J</i> = 0,357 s<super>−1</super> frente ao polo lento de 22,6 s<super>−1</super>. Validação em conjunto independente, predição de 20 ms: ajuste de {f(ID['fit_w_pct'],1)} % em ω e {f(ID['fit_i_pct'],1)} % em <i>i</i> (o modelo nominal, sem reidentificar, obtém {f(ID['fit_w_nominal_pct'],1)} % e {f(ID['fit_i_nominal_pct'],1)} %). Com dados reais, o mesmo código seria alimentado com as séries da bancada; os limites do método (viés por ruído nas variáveis regressoras, K<sub>t</sub> = K<sub>e</sub> assumido) estão no código."))
S_.append(fig('fig_ident.png',W*0.8,'Figura 2 — Validação em conjunto independente (dados sintéticos): real × modelo identificado, predição de 20 ms.'))

S_.append(P('2.3 Requisitos de desempenho × requisitos de segurança colaborativa','h2'))
S_.append(P("Os requisitos de <b>desempenho</b> (REQ-CTRL) descrevem a <i>qualidade da resposta de um sistema contínuo</i> a uma entrada específica (degrau): erro, sobressinal, tempo de acomodação, limites de sinal. Verifica-se por análise e simulação com métricas numéricas, para entradas representativas e com margens de robustez; a evidência é <i>amostral</i> (valores de amplitude, perturbações) e contínua nos sinais. Os requisitos de <b>segurança colaborativa</b> (REQ-SAFE) são afirmações sobre <i>todas as execuções</i> de um sistema de eventos discretos com tempo (estados do supervisor, atrasos, ciclos perdidos): qualquer ordem de eventos permitida pelo ambiente deve satisfazê-los. Por isso exigem verificação exaustiva (<i>model checking</i>), não amostragem; um único comportamento ruim, mesmo improvável em testes, invalida o requisito. Esta é a lição do protótipo anterior: a falha estava numa borda de estados que nenhum teste de resposta ao degrau exercitaria."))
S_.append(P("<b>Classificação.</b> Segurança (\"algo ruim nunca acontece\") é refutada por um prefixo finito de execução; vivacidade (\"algo bom eventualmente acontece\") só é refutada por uma execução infinita (um laço em que o bem nunca ocorre)."))
S_.append(tbl([['Requisito','Classe','Justificativa'],
 ['REQ-SAFE-AA-001 (torque zero em ≤ 100 ms após mão &lt; 500 mm)','<b>Segurança</b> (com prazo)','Sem o prazo seria "eventualmente torque zero" (vivacidade). Com prazo de 100 ms vira resposta limitada, que é segurança: a violação é um prefixo finito (mão presente, torque ligado, relógio &gt; 100 ms). Formalmente: AG ¬(mão ∧ torque ∧ <i>x</i> &gt; 100 ms).'],
 ['REQ-SAFE-AA-002 (sem retomada automática)','<b>Segurança</b>','"Nunca entrar em MOVING sem rearme explícito": o contraexemplo é uma única transição proibida.'],
 ['REQ-SAFE-AA-003 (mão removida + rearme ⇒ retoma a trajetória)','<b>Vivacidade</b>','"Eventualmente retoma": só se refuta com laço infinito em que o braço nunca volta a MOVING mesmo com mão fora e rearme confirmado. Depende de <b>justiça</b> (o supervisor executa; ciclos perdidos não são infinitos). Verificada por ausência de laço e também na forma limitada (≤ 30 ms).'],
 ['REQ-SAFE-AA-004 (velocidade do efetuador ≤ 250 mm/s)','<b>Segurança</b> (invariante)','"Nunca exceder": vale em todo instante; a violação é uma amostra. Garantida por projeto (gerador de trajetória a 80 % do limite) e por monitor (disparo por sobrevelocidade); evidência por simulação, pois envolve dinâmica contínua (limitação: seção 6).'],
 ['REQ-CTRL-AA-001..003','Desempenho (quantitativo de regime/transitório)','001 é assintótica (erro → 0): análoga à vivacidade; 002 e 003 são limites de resposta ao degrau.'],
 ['REQ-CTRL-AA-004 (|u| ≤ 48 V, |i| ≤ 8 A)','Desempenho com natureza de <b>segurança</b> (invariante de sinal)','Vale "em nenhum instante"; verificado por simulação, inclusive com incerteza de ±10 % (a verificação exaustiva de sinais contínuos exigiria análise de alcançabilidade híbrida, não feita).']],
 [4.3*cm,2.6*cm,W-6.9*cm]))
S_.append(P('2.4 Fundamentação das escolhas','h2'))
S_.append(P("<b>Controle (Unidades 1 e 2).</b> A planta de posição é tipo 1 (integrador em θ), mas a carga constante produz erro permanente com ação só proporcional; REQ-CTRL-AA-001 exige, portanto, ação integral. Optou-se por realimentação de estados com integrador do erro (estrutura I-P) porque (i) os três estados são medidos; (ii) a alocação de polos dá controle direto de sobressinal e acomodação, sem zeros no caminho da referência (o sobressinal medido fica abaixo de 2,3 %); (iii) o projeto é feito diretamente no domínio discreto sobre o modelo ZOH exato, com T<sub>s</sub> = 2 ms [3]. Polos contínuos desejados {−450, −60±j30, −100} s<super>−1</super> (ω<sub>n</sub> = 67 rad/s, ζ = 0,89 no par dominante); o polo rápido fica uma ordem de grandeza acima da banda do laço e abaixo do polo elétrico de −644 s<super>−1</super>, para não exigir ganho excessivo sobre uma dinâmica que o período de amostragem mal resolve. A saturação é tratada em duas camadas: tensão (±48 V) e <b>limitador preditivo de corrente</b>, que usa o modelo discreto exato para impedir que <i>i</i>[<i>k</i>+1] ultrapasse ±I<sub>lim</sub>. Quando o atuador satura, o integrador acumula o que o atuador não entrega (<i>windup</i>); o anti-windup por <b>retrocálculo</b> (<i>z</i> ← <i>z</i> + T<sub>s</sub> <i>e</i> + K<sub>aw</sub>(<i>u</i><sub>sat</sub> − <i>u</i>)) o descarrega. Em zona colaborativa, um gerador de trajetória com limites de velocidade e aceleração evita o degrau bruto de referência."))
S_.append(P("<b>Verificação (Unidade 3).</b> O supervisor é uma máquina de estados finitos de 3 estados executada a cada 2 ms. O ambiente (sensor com atraso variável, ciclos perdidos, mão que entra e sai, rearme arbitrário) é composto com ele e o tempo é discretizado em ticks; como todas as constantes (2, 10, 20, 100 ms) são inteiras no tick escolhido e as restrições são fechadas, a digitalização preserva a alcançabilidade de autômatos temporizados [5], de modo que a exploração exaustiva do espaço de estados discreto decide as propriedades de segurança. A vivacidade é verificada por busca de laços no subgrafo em que o ambiente mantém a mão fora e o rearme ativo, com justiça codificada no contador de ciclos perdidos consecutivos. O contraexemplo da versão preliminar vem da própria exploração (trilha mínima por busca em largura)."))
S_.append(P("<b>Geração de código (Unidade 4).</b> O C é produzido por um gerador por modelos (<font name='DVM'>src/codegen.py</font>) a partir de duas fontes: os ganhos do projeto e a tabela de transições do supervisor. A tabela é a <i>mesma</i> executada pelo verificador, o que fecha a lacuna entre o que é verificado e o que é embarcado. O código é auto-contido, sem alocação dinâmica, em <i>float</i> (a FPU do Cortex-M4 é de precisão simples), com bloco de rastreabilidade no cabeçalho. A equivalência é demonstrada em SIL: compila-se o C e comparam-se suas saídas com modelos de referência em float32 (mesma ordem de operações; deve ser exata) e em float64 (diferença esperada por arredondamento). A segurança funcional de um tal supervisor, num contexto de certificação, é regida pela IEC 61508 [4] (ou ISO 26262 no setor automotivo), que exige qualificação de ferramenta e independência de verificação — tratadas na seção 6."))
S_.append(PageBreak())

# ---------------- 3
S_.append(P('3. Parte prática: projeto e resultados','h1'))
S_.append(P('3.1 Repositório','h2'))
S_.append(tbl([['Item exigido','Arquivo no repositório'],
 ['Modelo da planta (A, B, C, D)','<font name="DVM">src/plant.py:continuous_matrices</font>; parâmetros em <font name="DVM">src/params.py</font>'],
 ['Controlador (estados + integrador, anti-windup)','<font name="DVM">src/refmodel.py:design, CtrlRef.step</font>'],
 ['Propriedades formais e contraexemplo','<font name="DVM">src/supervisor_spec.py</font>, <font name="DVM">src/verify_supervisor.py</font>, <font name="DVM">results/verification_variants.json</font>'],
 ['Suíte de testes e cobertura','<font name="DVM">src/sil_tests.py</font>, <font name="DVM">results/sil_tests.json</font>, <font name="DVM">results/aurora_ctrl.c.gcov</font>'],
 ['Código gerado com rastreabilidade','<font name="DVM">generated/aurora_ctrl.h/.c</font> (gerado por <font name="DVM">src/codegen.py</font>)'],
 ['Equivalência SIL','<font name="DVM">src/sil.py</font>, <font name="DVM">results/sil_equivalence.json</font>'],
 ['Matriz de rastreabilidade','<font name="DVM">docs/traceability_matrix.csv/.md</font> (gerada por <font name="DVM">src/traceability.py</font>)'],
 ['Memorial de cálculo','<font name="DVM">src/memorial.py</font>, <font name="DVM">results/memorial.json</font>; Anexo A deste PDF']],[6*cm,W-6*cm]))
S_.append(P('3.2 Controlador projetado','h2'))
dd=json.load(open(os.path.join(H,'..','results','memorial.json')))
S_.append(P(f"Lei de controle (por ciclo, <font name='DVM'>aurora_step</font>): <i>u</i> = −K<sub>I</sub> <i>i</i> − K<sub>W</sub> ω − K<sub>TH</sub> θ + K<sub>Z</sub> <i>z</i>, com K<sub>I</sub> = 0,0963 V/A, K<sub>W</sub> = 0,620 V·s/rad, K<sub>TH</sub> = 47,40 V/rad, K<sub>Z</sub> = 1159 V/(rad·s) (valores exatos e hexadecimais no <font name='DVM'>aurora_ctrl.c</font>). O polo discreto mais lento tem módulo 0,887 (τ ≈ 16,7 ms). Limites: V<sub>max</sub> = 48 V; I<sub>lim</sub> = 6,0 A (75 % de 8 A). <b>Por que 6,0 A:</b> com I<sub>lim</sub> = 7,6 A o pico nominal ficou em 7,69 A, mas na simulação de Monte Carlo (planta com ±10 % uniforme em R, L, K<sub>t</sub>, K<sub>e</sub>, J, b) 68 de 120 execuções ultrapassaram 8 A (máximo 9,36 A), porque o limitador preditivo usa o modelo nominal. Com 6,0 A o máximo sob incerteza caiu para {f(T['requirements']['monte_carlo']['max_imax'],2)} A em 300 execuções, ao custo de acomodação mais lenta em degraus grandes."))
sw=T['requirements']['step_sweep']
S_.append(tbl([['Degrau (eixo do motor)','Junta','Sobressinal','Acomodação (2 %)','Erro final','|i| máx.','|u| máx.','OK?']]+
  [[f"{r['amp_motor_rad']} rad",f"{f(r['amp_joint_deg'],2)}°",f"{f(r['overshoot_pct'],2)} %",f"{f(r['settling_s']*1e3,0)} ms",fe(r['ess'])+' rad',f"{f(r['imax'],2)} A",f"{f(r['umax'],1)} V",'sim' if all(v for k,v in r.items() if k.startswith('ok_')) else 'NÃO'] for r in sw],
  [3.2*cm,1.6*cm,2*cm,2.4*cm,2.3*cm,1.7*cm,1.7*cm,W-14.9*cm]))
S_.append(P("Tabela 1 — Resposta ao degrau do <b>código C gerado</b> em malha fechada (modo não colaborativo, carga de 0,25 N·m presente). Limites: 8 %, 300 ms, 48 V, 8 A.","cap"))
mc=T['requirements']['monte_carlo']
S_.append(P(f"<b>Robustez.</b> Monte Carlo com {mc['n']} execuções (100 plantas × degraus de 2, 5 e 10 rad, ±10 % em seis parâmetros): sobressinal máx. {f(mc['max_os'],2)} %, acomodação máx. {f(mc['max_ts']*1e3,0)} ms, |i| máx. {f(mc['max_imax'],2)} A, |u| máx. {f(mc['max_umax'],1)} V, nenhuma falha. Com ±15 % o pico de corrente sobe a cerca de 7,97 A, sem margem; ±10 % é, portanto, o envelope declarado. Para o degrau de 15 rad sob incerteza, a acomodação ultrapassa 300 ms (até 312 ms em testes de exploração), logo <b>o envelope garantido sob incerteza é de 10 rad (0,1 rad na junta)</b>."))
S_.append(fig('fig_step.png',W,'Figura 3 — Degraus de 2, 5, 10 e 15 rad: posição normalizada, corrente e tensão (código C em malha fechada). A corrente fica limitada; a tensão nunca satura nos degraus.'))
ab=T['requirements']['no_antiwindup']
S_.append(P(f"<b>Saturação e windup.</b> Nos degraus quem satura é a <i>corrente</i> (6 A), não a tensão: o torque de aceleração é limitado a 0,51 N·m. Sem anti-windup o integrador acumula durante a saturação e o sobressinal sobe para {', '.join(f(x['os_no_aw'],0)+' % ('+str(x['amp'])+' rad)' for x in ab)}, violando REQ-CTRL-AA-002 por ordens de grandeza (Figura 4). Com anti-windup, no máximo 2,3 %."))
S_.append(fig('fig_antiwindup.png',W*0.75,'Figura 4 — Efeito do anti-windup (degrau de 10 rad): sem ele, a posição oscila e satura por mais de 1 s.'))
cr=T['requirements']['cruise450']
S_.append(P(f"<b>Ponto crítico em malha fechada.</b> Com trajetória de aceleração de 300 rad/s² até 450 rad/s, o código gerado estabiliza em ω = {f(cr['w_final'],2)} rad/s, <i>i</i> = {f(cr['i_final'],3)} A e <i>u</i> = {f(cr['u_final'],2)} V, em concordância com o memorial (3,735 A; 41,238 V), sem saturar a tensão (|u| máx. {f(cr['umax'],1)} V). Observação importante: a aceleração líquida disponível com I<sub>lim</sub> = 6 A é {f(b['a_net_ilim'],0)} rad/s² (863 rad/s² com 8 A); uma rampa mais agressiva é infactível e foi usada, de propósito, no cenário S5 de equivalência para exercitar a saturação de tensão. <b>Limitação conhecida:</b> a estrutura I-P tem atraso de posição constante em velocidade constante, <i>e</i> = K<sub>TH</sub>ω/K<sub>Z</sub> = 40,9 ms × ω (18,4 rad a 450 rad/s; 2,3 rad a 57 rad/s). Nenhum requisito pede seguimento de rampa; uma antecipação de velocidade eliminaria o atraso (trabalho futuro)."))
S_.append(fig('fig_cruise.png',W,'Figura 5 — Ponto crítico: ω estabiliza em 450 rad/s com 41,24 V e 3,73 A (linhas verdes: valores do memorial).'))

# ---------------- 4
S_.append(P('4. Verificação formal do supervisor','h1'))
S_.append(P('4.1 Modelo','h2'))
S_.append(fig('fig_fsm.png',W*0.8,'Figura 6 — Supervisor (fonte única em supervisor_spec.py): T1 detecção, T2 confirmação de torque zero, T3 reentrada da mão, T4 rearme explícito.'))
S_.append(P("O ambiente é não determinístico: a mão entra e sai a qualquer tick; o sensor reflete a mão com atraso escolhido entre 0 e 20 ms; a cada ciclo de 2 ms o supervisor pode ser pulado (até K consecutivos); o rearme é arbitrário. Tick de 1 ms (verificação de referência) e de 0,5 ms (checagem de convergência). A propriedade REQ-SAFE-AA-001 é monitorada por um relógio que conta o tempo desde a última entrada da mão e é violada se, com a mão presente e o torque ligado, o relógio passa de 100 ms. REQ-SAFE-AA-002 é monitorada na transição para MOVING (exige origem em WAIT_REARM e rearme amostrado no mesmo ciclo)."))
S_.append(P('4.2 Resultados','h2'))
v1=V['v1']; v0=V['v0_edge']; vs=V['v0_stale_rearm']; t05=S['tick05']
S_.append(tbl([['Modelo','Estados','SAFE-001 (100 ms)','SAFE-002','Pior latência','Observação'],
 ['v1 (corrigido)',str(v1['states']),'<b>vale</b>','<b>vale</b>',f"{f(v1['max_latency_ms'],0)} ms",'vivacidade: sem laço; latência máx. de retomada 30 ms'],
 ['v1, tick 0,5 ms',str(t05['states']),'vale','vale',f"{f(t05['max_latency_ms'],1)} ms",'converge ao limite analítico de 34 ms'],
 ['v0_edge (preliminar)',str(v0['states']),'<b>VIOLADA</b>','vale','&gt; 100 ms','contraexemplo (4.3)'],
 ['v0_stale_rearm (preliminar)',str(vs['states']),'vale','<b>VIOLADA</b>','31 ms','contraexemplo de 15 passos']],[3.5*cm,1.6*cm,2.5*cm,1.8*cm,2.1*cm,W-11.5*cm]))
S_.append(P("Tabela 2 — Verificação exaustiva (K = 1 ciclo perdido). O pior caso analítico, T<sub>sensor</sub> + T<sub>c</sub>(1+K) + T<sub>act</sub> = 20 + 2·2 + 10 = 34 ms, é um supremo contínuo; a digitalização em tick de 1 ms atinge 31 ms e em 0,5 ms atinge 32,5 ms (a diferença, menor que um tick, é o efeito da grade).","cap"))
S_.append(P('4.3 Contraexemplo da versão preliminar (reproduz o quase-acidente)','h2'))
S_.append(P("Na versão preliminar a detecção era por <b>borda de subida</b> (<font name='DVM'>prox ∧ ¬prev_prox</font>) e <font name='DVM'>prev_prox</font> só era atualizado em MOVING — o erro típico de um tratamento manual da borda entre movimento e parada. Trilha mínima encontrada pelo verificador (relógio em ms desde a última entrada da mão):"))
S_.append(tbl([['Passo','t (ms)','Evento','Estado do supervisor','Torque'],
 ['1','—','mão entra, sensor reage; borda detectada (prev_prox ← 1)','MOVING → SAFE_STOP','desliga'],
 ['2','0','mão sai e <b>volta a entrar</b> antes de o sensor refletir (sensor ainda em 0)','SAFE_STOP','—'],
 ['3','7–10','sensor "limpo" (obsoleto) ⇒ T2 vale: torque zero confirmado','SAFE_STOP → WAIT_REARM','0'],
 ['4','12','operador pressiona rearme (mão ainda na zona)','WAIT_REARM → MOVING','<b>liga</b>'],
 ['5','13','sensor sobe para 1, mas prev_prox já era 1 ⇒ <b>sem borda</b>','MOVING (permanece)','ligado'],
 ['6','&gt; 100','mão continua na zona, torque ligado, nenhum evento de parada jamais ocorre','MOVING','<b>ligado: SAFE-001 violada</b>']],[1.2*cm,1.5*cm,7.6*cm,3.7*cm,W-14*cm]))
S_.append(P("Correção (v1): detecção por <b>nível</b> (<font name='DVM'>prox</font> amostrado a cada ciclo em MOVING e em WAIT_REARM, sem memória de borda). A mesma busca no modelo corrigido não encontra violação. O contraexemplo da segunda variante (rearme memorizado fora de WAIT_REARM) mostra um rearme pressionado antes da liberação da mão que retoma o movimento automaticamente, violando REQ-SAFE-AA-002."))
S_.append(P('4.4 Sensibilidade ao número de ciclos perdidos','h2'))
sk=[(k,l) for k,l,ok,n in S['sens_K']]
S_.append(P(f"O enunciado admite um ciclo perdido (K = 1). Variando K, a pior latência cresce 2 ms por ciclo: {', '.join(f'K={k}: {f(l,0)} ms' for k,l in sk if k in (0,1,2,10,20,30))}. Pela fórmula analítica 20 + 2(1+K) + 10 ≤ 100, a garantia de 100 ms resiste a até <b>K = 34 ciclos consecutivos perdidos</b> (68 ms de jitter), com margem de 66 ms para K = 1. A grade discreta indica 35 por estar um tick otimista; adota-se o valor analítico, conservador."))
S_.append(fig('fig_sweep.png',W*0.9,'Figura 7 — Varredura em malha fechada com o controlador (504 combinações): tempo até corrente &lt; 0,05 A. Nenhuma passa de 36 ms.'))
S_.append(P(f"<b>Varredura em malha fechada (memorial d).</b> 504 combinações (21 atrasos de sensor de 0 a 20 ms × 8 fases de chegada da mão dentro do ciclo × 0, 1 ou 2 ciclos perdidos), simuladas com a planta contínua: máximo {f(d['max_by_lost']['0'],2)} ms (sem perda), {f(d['max_by_lost']['1'],2)} ms (1 perda), {f(d['max_by_lost']['2'],2)} ms (2 perdas); nenhuma violação. Com o código C no laço (30 combinações), o pior caso foi {f(T['latency_c']['worst_ms'],1)} ms."))
S_.append(fig('fig_collab.png',W,'Figura 8 — Cenário colaborativo (código C): mão entra em 0,30 s (sensor +20 ms), corrente zera em ~33 ms, freio retém; mão sai, rearme em 1,0 s; trajetória parte da posição atual e atinge o alvo original (30 rad).'))

# ---------------- 5
S_.append(P('5. Código gerado, testes e rastreabilidade','h1'))
S_.append(P('5.1 Código gerado','h2'))
S_.append(P(f"<font name='DVM'>generated/aurora_ctrl.c</font> ({sum(1 for _ in open(os.path.join(H,'..','generated','aurora_ctrl.c')))} linhas) e <font name='DVM'>aurora_ctrl.h</font> são produzidos por <font name='DVM'>src/codegen.py</font>; o digest do modelo ({D['v1']['digest']}) está no cabeçalho, junto com o bloco de rastreabilidade requisito → modelo → função → teste. Compila sem avisos com <font name='DVM'>gcc -std=c99 -Wall -Wextra -pedantic</font>. Tamanho do objeto: 1 038 bytes de código em x86-64 com <font name='DVM'>-Os</font> (indicativo, <b>não medido no alvo ARM</b>; o orçamento é 256 KB), sem dados estáticos além da estrutura de estado de 16 bytes. O tempo de execução (≈ 25 operações em ponto flutuante, 2 divisões e 1 raiz quadrada por ciclo) tende a ficar em poucos microssegundos num Cortex-M4F, muito abaixo do orçamento de 200 µs, mas <b>isto é estimativa por contagem de operações, não medição</b>."))
S_.append(P('5.2 Suíte de testes gerados do modelo e cobertura','h2'))
tt=T['transition_tests']; pr=T['properties']; mu=T['mutation']
S_.append(tbl([['Tipo de teste','Origem','Quantidade','Resultado'],
 ['Percurso do grafo de estados (cada aresta estado×entrada)','grafo abstrato (sup, stop_cnt) gerado do modelo de referência',f"{tt['n_tests']} testes ({tt['abstract_states']} estados, {tt['abstract_edges']} arestas)",f"{tt['n_pass']}/{tt['n_tests']} aprovados; cobertura de estados e de transições 100 %"],
 ['Propriedades em sequências aleatórias (SAFE-001/002/003 ao nível de ciclo, invariantes de freio)','propriedades do supervisor',f"{pr['cycles']:,} ciclos".replace(',',' '),'0 violações'],
 ['Requisitos de resposta em malha fechada','TST-CTRL-001..004','5 amplitudes + 300 execuções Monte Carlo','aprovados no envelope declarado'],
 ['Velocidade na zona colaborativa','TST-SAFE-004','degraus de 5, 10, 30, 60 rad',f"pico {f(max(x['v_tip_mm_s'] for x in T['requirements']['tip_speed']),0)} mm/s (&lt; 250), sem disparo"],
 ['Teste de mutação','v0_edge, v0_stale_rearm gerados do modelo','2 mutantes','2/2 detectados pelas propriedades; v0_edge também pelo teste dirigido']],[5*cm,4.4*cm,3.3*cm,W-12.7*cm]))
S_.append(P("<b>Cobertura de código (gcov, suíte completa executada sobre o C gerado):</b> 98,33 % das linhas (59 de 60), 100 % dos ramos executados, 85,48 % dos ramos tomados ao menos uma vez. A única linha não executada é o <font name='DVM'>default</font> defensivo do <font name='DVM'>switch</font> (estado ilegal → parada segura), inalcançável por construção. Cobertura de transições do <i>supervisor</i> (modelo): 36/36 arestas, 9/9 estados abstratos. Relatório bruto: <font name='DVM'>results/aurora_ctrl.c.gcov</font>."))
S_.append(P('5.3 Equivalência modelo–código (memorial e)','h2'))
rows=[['Cenário','Ciclos','Erro vs float32','Erro máx. vs float64','Σ|termos| (V)','Erro/(ε·Σ)','Δθ malha fechada']]
for k,v in EQ['per_scenario'].items():
    rows.append([k.replace('_',' '),str(v['n_cycles']),'0 (bit-a-bit)' if v['bit_exact_vs_f32'] else fe(v['max_abs_err_vs_f32_ref']),fe(v['max_abs_err_vs_f64_ref'])+' V',f"{v['max_term_sum']:.0f}".replace(',',' '),f(v['err_over_eps_termsum'],1),fe(v['max_theta_diff_closed_loop'])+' rad'])
S_.append(tbl(rows,[4.2*cm,1.3*cm,2.2*cm,2.6*cm,2.0*cm,1.8*cm,W-14.1*cm]))
S_.append(P(f"Tabela 3 — ε<sub>float32</sub> = {fe(EQ['eps_f32'])}. Entradas idênticas (registradas do laço fechado com o C) foram reproduzidas nos modelos de referência.","cap"))
S_.append(P(f"<b>Conclusão.</b> Contra o modelo em float32 com a mesma ordem de operações, o erro é <b>exatamente 0</b> em todos os ciclos de todos os cenários: não há evidência de defeito de geração. Contra float64, o maior erro absoluto é {fe(EQ['max_err_vs_f64'])} V (cenário de cruzeiro), ou {f(EQ['err_over_eps_u'],0)}·ε·|u|<sub>max</sub>. Esse número, comparado ingenuamente ao ε, pareceria alto; ele é explicado pelo <b>condicionamento</b>: <i>u</i> é diferença de termos de até {EQ['per_scenario']['S3_cruise450']['max_term_sum']:.0f} V (K<sub>TH</sub>θ e K<sub>Z</sub><i>z</i> crescem com θ ≈ 800 rad e se cancelam), e o erro relativo à soma dos módulos é ≤ {f(max(v['err_over_eps_termsum'] for v in EQ['per_scenario'].values()),1)}·ε. O efeito na planta é irrelevante (Δθ ≤ {fe(max(v['max_theta_diff_closed_loop'] for v in EQ['per_scenario'].values()))} rad). Veredito: <b>equivalência aceitável</b>. Lição de projeto: para trajetórias longas, reescrever o integrador em coordenadas de erro reduz a magnitude dos termos e o erro de arredondamento."))
S_.append(P('5.4 Matriz de rastreabilidade (requisito → modelo → código → teste)','h2'))
S_.append(tbl([['Requisito','Modelo','Código','Teste','Resultado']]+[[r[0]+'<br/>'+r[1],r[2],r[3],r[4],r[5]] for r in TR],[2.7*cm,3.6*cm,3.0*cm,2.4*cm,W-11.7*cm]))
S_.append(P("Tabela 4 — Também em <font name='DVM'>docs/traceability_matrix.csv</font>, gerada automaticamente dos resultados.","cap"))
S_.append(PageBreak())

# ---------------- 6
S_.append(P('6. Honestidade técnica: o que o pacote sustenta e o que não sustenta','h1'))
S_.append(P('<b>O que o pacote de evidências sustenta perante a auditoria da Aurora Robótica</b>','h3'))
for t in ["Uma cadeia rastreável e reprodutível (<font name='DVM'>make all</font>) de requisito a teste, em que o supervisor verificado e o supervisor embarcado vêm da <i>mesma tabela</i>.",
 "Verificação <b>exaustiva</b>, sob as hipóteses P7 declaradas, de que o prazo de 100 ms é cumprido (pior caso 34 ms analítico), de que não há retomada automática e de que a retomada ocorre quando as condições valem; e prova por contraexemplo de que o método <i>teria</i> detectado o defeito do protótipo anterior.",
 "Desempenho de posição conforme REQ-CTRL-AA-001..004 no código C gerado, com tratamento explícito de saturação e windup, no envelope e com a incerteza de ±10 % declarados.",
 "Equivalência numérica demonstrada entre modelo e código (zero contra float32; explicada contra float64), com cobertura de 98,3 % das linhas e 100 % das transições do supervisor."]:
    S_.append(P('• '+t))
S_.append(P('<b>O que ainda exigiria processo formal de certificação (IEC 61508 [4]; ISO 26262 ou norma equivalente do setor)</b>','h3'))
for t in ["<b>Qualificação de ferramentas.</b> O gerador de código (<font name='DVM'>codegen.py</font>), o verificador próprio (<font name='DVM'>verify_supervisor.py</font>) e o compilador não são qualificados; a classificação de confiança da ferramenta e a validação do gerador por casos de teste independentes não foram feitas. O verificador foi validado apenas por dois mutantes; recomenda-se checagem cruzada com UPPAAL ou nuXmv.",
 "<b>Independência de verificação.</b> Projeto, verificação e testes foram feitos pelo mesmo autor, com o mesmo modelo de planta; normas de segurança funcional exigem verificação por pessoa/equipe independente conforme o nível de integridade.",
 "<b>Alocação de integridade e análise de falhas.</b> Não houve alocação de SIL/PL nem análise de modos de falha (sensor travado, perda de comunicação, falha do freio, falha comum), diagnósticos, <i>watchdog</i>, canal duplo ou desligamento seguro de torque em hardware. Um supervisor em software num único microcontrolador não alcança, sozinho, nível de integridade elevado.",
 "<b>Sistema real.</b> Não houve HIL nem medição de WCET/consumo de memória no Cortex-M4; o tempo de resposta do RTOS e a jitter foram modelados apenas como ciclos perdidos. Não houve análise estática (MISRA), cobertura MC/DC, nem análise de pilha.",
 "<b>Dados e modelos.</b> A identificação usou dados sintéticos; incerteza paramétrica foi explorada por Monte Carlo (evidência estatística, não prova); o atrito não linear, a folga e a elasticidade da transmissão harmônica, a gravidade dependente da posição e o ruído de medição não foram modelados. O limite de corrente em sinais contínuos foi verificado por simulação, não por análise de alcançabilidade híbrida.",
 "<b>Segurança colaborativa.</b> Não foram avaliados os limites biomecânicos por região do corpo, massa efetiva nem pressão de contato (ISO/TS 15066, hoje incorporada à ISO 10218-2:2025 [8]); o limite de 250 mm/s é o do enunciado, calculado com alavanca de 0,35 m; as demais juntas, o sensor de proximidade (probabilidade de falha de detecção) e o escâner são <b>premissas</b>. O freio mecânico é premissa de hardware.",
 "<b>Limitações de projeto reconhecidas:</b> atraso constante de posição em rampas (estrutura I-P); envelope de 10 rad sob incerteza; cobertura de ramos tomados de 85 %."]:
    S_.append(P('• '+t))

# ---------------- 7 refs
S_.append(P('7. Referências','h1'))
refs=["[1] Material da disciplina: aulas 1 a 16 — Unidade 1 (modelagem em espaço de estados, identificação, controlabilidade e observabilidade), Unidade 2 (PID, discretização, saturação e anti-windup, co-simulação), Unidade 3 (formalização de requisitos, model checking, autômatos temporizados, testes baseados em modelo), Unidade 4 (geração de código, SIL/HIL, rastreabilidade e certificação).",
"[2] INTERNATIONAL ORGANIZATION FOR STANDARDIZATION. <b>ISO/TS 15066</b>: Robots and robotic devices — Collaborative robots. Geneva: ISO, 2016.",
"[3] SICILIANO, Bruno; SCIAVICCO, Lorenzo; VILLANI, Luigi; ORIOLO, Giuseppe. <b>Robotics</b>: Modelling, Planning and Control. London: Springer-Verlag, 2010.",
"[4] INTERNATIONAL ELECTROTECHNICAL COMMISSION. <b>IEC 61508</b>: Functional safety of electrical/electronic/programmable electronic safety-related systems. Parts 1-7. Geneva: IEC, 2010.",
"[5] BAIER, Christel; KATOEN, Joost-Pieter. <b>Principles of Model Checking</b>. Cambridge: MIT Press, 2008. (Digitalização de relógios: HENZINGER, T. A.; MANNA, Z.; PNUELI, A. What good are digital clocks? In: ICALP, 1992. Lecture Notes in Computer Science, v. 623. Berlin: Springer, 1992. p. 545-558.)",
"[6] MODELICA ASSOCIATION. <b>Functional Mock-up Interface Specification</b>, version 3.0, 2022. (Não utilizada: a co-simulação foi feita em Python/C via ctypes, sem FMI.)",
"[7] INTERNATIONAL ORGANIZATION FOR STANDARDIZATION. <b>ISO 26262</b>: Road vehicles — Functional safety. Geneva: ISO, 2018. (Citada como norma equivalente do setor, conforme o enunciado.)",
"[8] A3 ANNOUNCES revised standard for industrial robot safety. <b>Manufacturing.net</b>, 2025. Disponível em: https://www.manufacturing.net/operations/news/22933643/a3-announces-revises-standard-for-industrial-robot-safety. Acesso em: 4 nov. 2026.",
"[9] UNIVERSAL ROBOTS. <b>UR cobot packs two million circuit boards</b>: Melecs EWS. [S.l.]: Universal Robots, [s.d.]. Disponível em: https://www.universal-robots.com/case-stories/melecs-ews/. Acesso em: 4 nov. 2026."]
for r in refs: S_.append(P(r))
S_.append(P("As fontes 2, 3 e 4 do enunciado foram mantidas como o conjunto mínimo de fontes técnicas primárias. As referências [2] e [4] a [7] foram usadas como indicadas no enunciado; o conteúdo das normas pagas não foi consultado diretamente nesta elaboração, de modo que afirmações sobre elas se limitam ao que consta do enunciado e do domínio público."))
S_.append(PageBreak())

# ---------------- Anexo A
S_.append(P('Anexo A — Memorial de cálculo','h1'))
S_.append(P("Cada item traz fórmula, substituição, premissas e resultado. Código: <font name='DVM'>src/memorial.py</font> (a–d) e <font name='DVM'>src/sil.py</font> (e); valores em <font name='DVM'>results/memorial.json</font> e <font name='DVM'>results/sil_equivalence.json</font>."))
S_.append(P('(a) Modelo em espaço de estados e constantes de tempo','h2'))
S_.append(P("<b>Premissas:</b> parâmetros da tabela do enunciado; <i>K</i><sub>t</sub> = <i>K</i><sub>e</sub>; inércia e atrito refletidos no eixo do motor; <i>x</i> = [<i>i</i>, ω]<super>T</super>, saída <i>y</i> = ω."))
S_.append(P("<b>Fórmulas:</b> <i>A</i> = [[−<i>R</i>/<i>L</i>, −<i>K</i><sub>e</sub>/<i>L</i>],[<i>K</i><sub>t</sub>/<i>J</i>, −<i>b</i>/<i>J</i>]]; <i>B</i> = [1/<i>L</i>; 0]."))
S_.append(P(f"<b>Substituição:</b> <i>R</i>/<i>L</i> = 0,8/1,2·10<super>−3</super> = {f(a['R_over_L'],2)} s<super>−1</super>; <i>K</i><sub>e</sub>/<i>L</i> = 0,085/1,2·10<super>−3</super> = {f(a['Ke_over_L'],3)} (A/s)/(rad/s); <i>K</i><sub>t</sub>/<i>J</i> = 0,085/4,2·10<super>−4</super> = {f(a['Kt_over_J'],2)}; <i>b</i>/<i>J</i> = 1,5·10<super>−4</super>/4,2·10<super>−4</super> = {f(a['b_over_J'],4)} s<super>−1</super>; 1/<i>L</i> = {f(a['B1'],2)}."))
S_.append(P(f"<i>A</i> = [[−666,67, −70,833],[202,38, −0,3571]], <i>B</i> = [833,33; 0].","eq"))
S_.append(P(f"<b>Autovalores:</b> det(λ<i>I</i> − <i>A</i>) = λ² − tr(<i>A</i>)λ + det(<i>A</i>) = λ² + {f(-a['trace'],3)}λ + {f(a['det'],1)}; discriminante Δ = {f(a['trace'],3)}² − 4·{f(a['det'],1)} = {f(a['disc'],0)}; √Δ = {f(math.sqrt(a['disc']),2)}. λ = (−667,024 ± 621,79)/2 ⇒ <b>λ<sub>1</sub> = {f(a['eig'][0],2)} s<super>−1</super></b>, <b>λ<sub>2</sub> = {f(a['eig'][1],2)} s<super>−1</super></b> (reais, negativos: estável, sem oscilação)."))
S_.append(P(f"<b>Constantes de tempo:</b> τ<sub>e</sub> = 1/|λ<sub>1</sub>| = <b>{f(a['tau_fast_s']*1e3,3)} ms</b> (compare <i>L</i>/<i>R</i> = {f(a['tau_e_RL']*1e3,2)} ms); τ<sub>m</sub> = 1/|λ<sub>2</sub>| = <b>{f(a['tau_slow_s']*1e3,2)} ms</b> (ordem reduzida, <i>L</i> → 0: <i>JR</i>/(<i>Rb</i> + <i>K</i><sub>t</sub><i>K</i><sub>e</sub>) = {f(a['tau_m_reduced']*1e3,2)} ms). Razão τ<sub>m</sub>/τ<sub>e</sub> = <b>{f(a['ratio'],1)}</b>. <b>Discussão:</b> a separação de uma ordem de grandeza permite ver a corrente como dinâmica rápida (quase-estática para o laço de velocidade/posição) e a velocidade como dinâmica dominante; o modelo de ordem reduzida acerta τ<sub>m</sub> com erro de 3 %. Como τ<sub>e</sub> &lt; T<sub>s</sub>, a discretização deve ser exata."))
S_.append(P(f"<b>Controlabilidade:</b> 𝒞 = [<i>B</i>  <i>AB</i>] = [[833,33, −555 556],[0, 168 651]]; det 𝒞 = {fe(a['det_Wc'])} ≠ 0 ⇒ posto = <b>{a['rank_Wc']}</b> (completo)."))
S_.append(P(f"<b>Observabilidade (C = [0 1]):</b> 𝒪 = [<i>C</i>; <i>CA</i>] = [[0, 1],[202,38, −0,3571]]; det 𝒪 = −<i>K</i><sub>t</sub>/<i>J</i> = {f(a['det_Wo'],2)} ≠ 0 ⇒ posto = <b>{a['rank_Wo']}</b>. <b>Conclusão:</b> a junta é completamente controlável e observável; a tensão acessa as duas dinâmicas e ω permite reconstruir <i>i</i>. (Os valores singulares de 𝒞, 5,8·10<super>5</super> e 242, mostram controlabilidade numericamente fraca em escala bruta, por causa das unidades; é por isso que o projeto usa o modelo discretizado.)"))
S_.append(P('(b) Ponto de operação crítico','h2'))
S_.append(P("<b>Premissas:</b> regime permanente (d<i>i</i>/d<i>t</i> = 0, dω/d<i>t</i> = 0); ω<sub>ss</sub> = 450 rad/s; <i>T</i><sub>carga</sub> = 0,25 N·m (dado do enunciado, tratado como carga total refletida)."))
S_.append(P("<b>Fórmulas:</b> <i>K</i><sub>t</sub> <i>i</i><sub>ss</sub> = <i>b</i> ω<sub>ss</sub> + <i>T</i><sub>carga</sub>;   <i>V</i><sub>ss</sub> = <i>R i</i><sub>ss</sub> + <i>K</i><sub>e</sub> ω<sub>ss</sub>."))
S_.append(P(f"<b>Substituição:</b> <i>b</i>ω = 1,5·10<super>−4</super>·450 = {f(b['T_visc'],4)} N·m; torque total = {f(b['T_total'],4)} N·m; <i>i</i><sub>ss</sub> = {f(b['T_total'],4)}/0,085 = <b>{f(b['iss'],4)} A</b> (folga de {f(b['folga_i'],2)} A até 8 A, {f(b['folga_i']/8*100,0)} %). <i>R i</i> = 0,8·{f(b['iss'],4)} = {f(b['Vres'],3)} V; <i>K</i><sub>e</sub>ω = 0,085·450 = {f(b['Vemf'],2)} V; <i>V</i><sub>ss</sub> = {f(b['Vres'],3)} + {f(b['Vemf'],2)} = <b>{f(b['vss'],3)} V</b>. <b>Folga:</b> 48 − {f(b['vss'],3)} = <b>{f(b['folga_V'],3)} V ({f(b['folga_pct'],1)} %)</b>."))
S_.append(P(f"<b>Verificações complementares:</b> velocidade a vazio ({f(b['w_noload'],1)} rad/s) e velocidade máxima com a carga ({f(b['w_max_loaded'],1)} rad/s); potência mecânica {f(b['P_mech'],1)} W e elétrica {f(b['P_elec'],1)} W (η = {f(b['eta']*100,0)} %). 450 rad/s é 80 % da velocidade a vazio, em regime de <i>f.c.e.m.</i> dominante (92,8 % da tensão)."))
S_.append(P(f"<b>Implicação.</b> A folga de 14 % é pequena: qualquer transitório que peça mais de {f(b['folga_V'],2)} V além do regime (um degrau de referência, um aumento de carga) leva o comando a 48 V. Logo (i) a tensão <i>pode</i> saturar quando o controlador opera perto do ponto crítico, e (ii) o torque de aceleração nesse regime é pequeno (aceleração líquida {f(b['a_net_imax'],0)} rad/s² com 8 A; {f(b['a_net_ilim'],0)} com 6 A), de modo que referências agressivas saturam por longos intervalos. Com ação integral, saturação prolongada gera windup; <b>anti-windup é necessário</b>. A ablação (Seção 3.2) confirma: sem ele o sobressinal vai de {f(min(x['os_no_aw'] for x in ab),0)} a {f(max(x['os_no_aw'] for x in ab),0)} %. Além disso, a corrente de 3,735 A não é o limite: o limitante é o <b>comando de tensão</b> em regime e a <b>corrente</b> em transitório. <b>Observação sobre o payload:</b> 2·9,81·0,35 = {f(b['T_payload_joint'],3)} N·m na junta, {f(b['T_payload_motor'],4)} N·m no motor; com apenas essa carga, <i>V</i><sub>ss</sub> = {f(b['vss_payload'],2)} V. O enunciado fornece 0,25 N·m ({f(b['ratio_load_vs_payload'],2)}× maior), adotado por ser o pior caso."))
c_=c
S_.append(P('(c) Escolha do período de amostragem','h2'))
S_.append(P(f"<b>Fórmula:</b> <i>N</i><sub>τ</sub> = τ<sub>m</sub>/<i>T</i><sub>s</sub>.  <b>Substituição:</b> {f(c_['tau_m']*1e3,2)} ms / 2 ms = <b>{f(c_['samples_per_tau_m'],1)} amostras por τ<sub>m</sub></b>; para a constante elétrica, {f(c_['tau_e']*1e3,3)}/2 = {f(c_['samples_per_tau_e'],2)} amostra por τ<sub>e</sub>; em 300 ms (acomodação exigida) cabem {f(c_['samples_per_settle'],0)} amostras. Frequência de amostragem 500 Hz; banda do par dominante de malha fechada ω<sub>n</sub> = {f(c_['wn_dom'],1)} rad/s ⇒ ω<sub>n</sub>T<sub>s</sub> = {f(c_['wn_dom']*0.002,3)} (≈ 47 amostras por período de ω<sub>n</sub>)."))
S_.append(P(f"<b>Critério:</b> regra prática de 10 a 20 amostras por constante de tempo dominante (e T<sub>s</sub> ≤ τ<sub>cl</sub>/10) para que o controlador discreto se comporte como o contínuo. Valores: 10 amostras ⇒ T<sub>s</sub> ≤ {f(c_['Ts_for_10_per_taum']*1e3,2)} ms; 20 amostras ⇒ T<sub>s</sub> ≤ {f(c_['Ts_for_20_per_taum']*1e3,2)} ms. <b>Conclusão:</b> T<sub>s</sub> = 2 ms é <b>adequado</b> para o laço de posição (22 amostras/τ<sub>m</sub> ≥ 20), levemente conservador em relação ao mínimo de 10 amostras (poderia chegar a ≈ 4,4 ms), mas esse conservadorismo é útil: cada ciclo adicional soma T<sub>s</sub> à latência de segurança, e a taxa de 500 Hz é também imposta pela restrição do enunciado. É <b>insuficiente</b> para fechar a malha de corrente (τ<sub>e</sub> &lt; T<sub>s</sub>); por isso o modelo discreto é exato (ZOH) e a corrente é protegida por limitador preditivo, enquanto a regulação rápida de corrente caberia ao driver. Orçamento: 200 µs por ciclo = {f(c_['duty_pct'],0)} % do período."))
S_.append(P('(d) Verificação do prazo de segurança','h2'))
S_.append(P(f"<b>Fórmula (pior caso analítico):</b> <i>t</i><sub>zero</sub> = <i>T</i><sub>sensor</sub> + <i>T</i><sub>c</sub>(1 + <i>K</i>) + <i>T</i><sub>act</sub>, em que <i>T</i><sub>c</sub> = 2 ms (espera pelo próximo ciclo, até um período; e cada ciclo perdido soma um período), <i>T</i><sub>act</sub> = 1 ciclo de retenção + decaimento da corrente. Decaimento: com <i>u</i> = <i>K</i><sub>e</sub>ω, <i>i</i>[<i>k</i>+1] = e<super>−RT<sub>s</sub>/L</super> <i>i</i>[<i>k</i>] = 0,2636 <i>i</i>[<i>k</i>]; de 6,0 A a 0,05 A: ln(6/0,05)/1,333 = 3,6 ⇒ 4 ciclos = 8 ms; <i>T</i><sub>act</sub> = 2 + 8 = 10 ms. <b>Substituição:</b> 20 + 2·(1+1) + 10 = <b>34 ms</b> &lt; 100 ms; folga de 66 ms."))
S_.append(P(f"<b>Verificação exaustiva (a):</b> varredura de {d['n_comb']} combinações (atraso 0–20 ms em passos de 1 ms × fase 0–1,75 ms em passos de 0,25 ms × 0/1/2 ciclos perdidos) em malha fechada: máximo {f(d['max_by_lost']['0'],2)} / {f(d['max_by_lost']['1'],2)} / {f(d['max_by_lost']['2'],2)} ms; a combinação mais lenta é atraso = 20 ms, fase = 0,25 ms, 2 ciclos perdidos ({f(d['worst']['t_zero_ms'],2)} ms); <b>nenhuma</b> combinação viola 100 ms ({d['n_violations']} violações). <b>Verificação exaustiva (b):</b> autômato do supervisor × ambiente temporizado: {v1['states']} estados, {v1['edges']} transições, pior latência {f(v1['max_latency_ms'],0)} ms; propriedade vale. Os três resultados (34 ms analítico, 33,75 ms varredura, 31–32,5 ms modelo digitalizado) são coerentes: o analítico é o supremo; os demais são alcançados em grade discreta. <b>Conclusão:</b> o prazo de 100 ms é cumprido em todas as combinações consideradas; a combinação que mais se aproxima é atraso máximo do sensor com perda do primeiro ciclo de detecção, ainda 66 ms abaixo do limite."))
S_.append(P('(e) Equivalência modelo–código','h2'))
S_.append(P(f"<b>Fórmula:</b> <i>e</i><sub>max</sub> = max<sub><i>k</i></sub> |<i>u</i><sub>C</sub>[<i>k</i>] − <i>u</i><sub>ref</sub>[<i>k</i>]|, comparado a ε<sub>float32</sub> = 2<super>−23</super> = {fe(EQ['eps_f32'])} (ε<sub>float64</sub> = {fe(EQ['eps_f64'])}).  <b>Dados:</b> 5 sequências de teste (degrau, cenário colaborativo com parada/rearme, cruzeiro de 450 rad/s, rampa infactível com saturação, senoidal com chaveamento), {sum(v['n_cycles'] for v in EQ['per_scenario'].values())} ciclos no total, mesmas entradas registradas do laço fechado com o C.  <b>Resultado:</b> <i>e</i><sub>max</sub>(vs float32) = <b>{fe(EQ['max_err_vs_f32'])}</b> (igual a zero, bit-a-bit; ≤ ε); <i>e</i><sub>max</sub>(vs float64) = {fe(EQ['max_err_vs_f64'])} V, que equivale a {f(EQ['err_over_eps_u'],0)}·ε·|u|<sub>max</sub> mas a apenas {f(max(v['err_over_eps_termsum'] for v in EQ['per_scenario'].values()),1)}·ε·Σ|termos| (escala natural da soma com cancelamento). <b>Conclusão:</b> equivalência aceitável; nenhuma evidência de defeito de geração (um defeito, como sinal trocado ou constante errada, produziria erros de ordem 1 e não 10<super>−3</super> V). Os estados do supervisor coincidiram em todos os ciclos."))
S_.append(P('Anexo B — Links de entrega','h1'))
S_.append(tbl([['Item','Link'],['Repositório Git','[INSERIR LINK DO REPOSITÓRIO — conteúdo: pasta aurorarm/ entregue em anexo, com histórico Git]'],['Vídeo (YouTube, não listado)','[INSERIR LINK DO VÍDEO — roteiro em docs/roteiro_video.md]']],[5*cm,W-5*cm]))
S_.append(P("Antes de submeter: abrir cada link em janela anônima e confirmar o acesso.","cap"))

def pagefoot(canv,doc):
    canv.saveState(); canv.setFont('DV',7.5); canv.setFillColor(colors.grey)
    canv.drawString(2*cm,1.2*cm,'AuroraArm — Operação Linha Viva — Relatório técnico'); canv.drawRightString(A4[0]-2*cm,1.2*cm,f'Página {doc.page}'); canv.restoreState()
out=os.path.join(H,'AuroraArm_Relatorio_Tecnico.pdf')
doc=SimpleDocTemplate(out,pagesize=A4,leftMargin=2*cm,rightMargin=2*cm,topMargin=1.8*cm,bottomMargin=1.8*cm,title='Operação Linha Viva — AuroraArm',author='Aluno(a)')
doc.build(S_,onFirstPage=pagefoot,onLaterPages=pagefoot)
print(out)
