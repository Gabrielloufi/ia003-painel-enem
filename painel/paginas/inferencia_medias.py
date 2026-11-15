"""Painel 3b: inferência para médias (diferença entre as médias de dois grupos de escolas)."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy import stats as sps

from dados_painel import (AZUL, LARANJA, NEUTRO, VERDE_AGUA, amostra, br, parametros_amostra, populacao, tex,
                          valor_p_tex, valor_p_txt)
from hipoteses import GRUPOS, MEDIAS, HipoteseMedias
from inferencia import ALTERNATIVAS, NULAS, TesteDuasMedias, classificar_decisao, grupo, simular_duas_medias
from variaveis import rotulo

pop = populacao()
am = amostra()
par = parametros_amostra()
REGIAO_REJEICAO = "rgba(128, 128, 128, 0.28)"
LIMITE_EIXO_T = 7.5  # além disso, o t observado aparece na borda do gráfico


def grafico_t(t: TesteDuasMedias) -> go.Figure:
    xs = np.linspace(-LIMITE_EIXO_T, LIMITE_EIXO_T, 600)
    ys = sps.t.pdf(xs, t.gl)
    fig = go.Figure(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=NEUTRO, width=2), hoverinfo="skip",
                               name=f"t de Student com {br(t.gl, 1)} gl, se H₀ for verdadeira"))
    tc = t.t_critico
    regioes = {"menor": [xs <= tc], "maior": [xs >= tc], "diferente": [xs <= -tc, xs >= tc]}[t.alternativa]
    for i, m in enumerate(regioes):
        fig.add_trace(go.Scatter(x=xs[m], y=ys[m], fill="tozeroy", fillcolor=REGIAO_REJEICAO, mode="lines",
                                 line=dict(width=0), name="região de rejeição (α = 5%)", showlegend=i == 0,
                                 hoverinfo="skip"))
    # linhas de referência como séries com legenda (os rótulos colidem quando o t observado fica na borda)
    topo = float(ys.max()) * 1.05
    for i, tc_i in enumerate([tc] if t.alternativa != "diferente" else [-tc, tc]):
        fig.add_trace(go.Scatter(x=[tc_i, tc_i], y=[0, topo], mode="lines", line=dict(color=NEUTRO, width=1.5),
                                 name=f"t crítico: {br(abs(tc_i) if t.alternativa == 'diferente' else tc_i, 3)}"
                                      + (" (±)" if t.alternativa == "diferente" else ""),
                                 showlegend=i == 0, hoverinfo="skip"))
    fora = abs(t.t) > LIMITE_EIXO_T
    x_obs = float(np.sign(t.t) * LIMITE_EIXO_T) if fora else t.t
    fig.add_trace(go.Scatter(x=[x_obs, x_obs], y=[0, topo], mode="lines", line=dict(color=AZUL, width=3),
                             name=f"t observado: {br(t.t, 2)}" + (" (fora da escala, na borda)" if fora else ""),
                             hoverinfo="skip"))
    fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0), separators=",.", yaxis_title="densidade",
                      xaxis_title="estatística t", legend=dict(orientation="h", y=-0.25, yanchor="top", x=0))
    return fig


def grafico_medias(nomes: list[str], grupos: list, medias_pop: list[float], cores: list[str]) -> go.Figure:
    fig = go.Figure()
    for nome, g, mp, cor in zip(nomes, grupos, medias_pop, cores):
        lo, hi = g.ic()
        fig.add_trace(go.Scatter(x=[lo, hi], y=[nome, nome], mode="lines", line=dict(color=cor, width=8),
                                 showlegend=False, hovertemplate=f"IC de 95%: {br(lo, 1)} a {br(hi, 1)}<extra></extra>"))
        fig.add_trace(go.Scatter(x=[g.media], y=[nome], mode="markers", showlegend=False,
                                 marker=dict(color=cor, size=15, line=dict(color="white", width=2)),
                                 hovertemplate=f"média da amostra: {br(g.media, 1)}<extra></extra>"))
        fig.add_trace(go.Scatter(x=[mp], y=[nome], mode="markers", showlegend=False,
                                 marker=dict(color=LARANJA, size=13, symbol="diamond", line=dict(color="white", width=2)),
                                 hovertemplate=f"média da população: {br(mp, 1)}<extra></extra>"))
    # legenda das formas (cor neutra: a cor de cada grupo já está no eixo)
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="média da amostra e IC de 95%",
                             marker=dict(color=NEUTRO, size=12)))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="média da população",
                             marker=dict(color=LARANJA, size=12, symbol="diamond")))
    fig.update_layout(height=250, margin=dict(l=0, r=0, t=40, b=0), separators=",.",
                      xaxis_title="média geral no ENEM (pontos)", yaxis=dict(title=None, autorange="reversed"),
                      legend=dict(orientation="h", y=1.15, yanchor="bottom", x=0))
    return fig


def grafico_caixas(nomes: list[str], amostras: list[pd.Series], cores: list[str]) -> go.Figure:
    fig = go.Figure()
    for nome, v, cor in zip(nomes, amostras, cores):
        fig.add_trace(go.Box(x=v, name=nome, orientation="h", marker_color=cor, line_color=cor, boxmean=True,
                             fillcolor="rgba(0,0,0,0)", hoverinfo="x"))
    fig.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=0), separators=",.", showlegend=False,
                      xaxis_title="média geral no ENEM (pontos)", yaxis=dict(autorange="reversed"))
    return fig


@st.cache_data(show_spinner=False)
def simulacao(codigo: str) -> dict:
    h = next(m for m in MEDIAS if m.codigo == codigo)
    em_a, em_b = GRUPOS[h.grupo_a][1](pop), GRUPOS[h.grupo_b][1](pop)
    rotulos = np.where(em_a, "A", np.where(em_b, "B", ""))
    return simular_duas_medias(pop[h.variavel].to_numpy(), rotulos, par["n"], h.alternativa, h.alpha)


def grafico_simulacao(sim: dict, t: TesteDuasMedias, delta0: float) -> go.Figure:
    d = sim["diferencas"]
    contagem, bordas = np.histogram(d, bins=60)
    altura = 100 * contagem.max() / len(d) * 1.08
    fig = go.Figure(go.Histogram(x=d, histnorm="percent", marker_color=AZUL, opacity=0.85,
                                 xbins=dict(start=bordas[0], end=bordas[-1], size=bordas[1] - bordas[0]),
                                 name="diferença em cada amostra simulada",
                                 hovertemplate="%{x:.1f} pontos<br>%{y:.1f}% das amostras<extra></extra>"))
    refs = [(t.diferenca, f"nossa amostra: {br(t.diferenca, 1)}", "#0d366b"),
            (sim["diferenca_populacao"], f"diferença na população: {br(sim['diferenca_populacao'], 1)}", LARANJA)]
    if bordas[0] <= delta0 <= bordas[-1]:
        refs.append((delta0, f"δ₀ = {br(delta0, 0)}", NEUTRO))
    for x, nome, cor in refs:
        fig.add_trace(go.Scatter(x=[x, x], y=[0, altura], mode="lines", line=dict(color=cor, width=2.5), name=nome,
                                 hoverinfo="skip"))
    fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0), separators=",.", bargap=0.05,
                      xaxis_title="diferença entre as médias dos grupos (pontos)",
                      yaxis=dict(title="% das amostras", range=[0, altura]),
                      legend=dict(orientation="h", y=-0.28, yanchor="top", x=0))
    return fig


def mostrar(h: HipoteseMedias) -> None:
    (nome_a, filtro_a), (nome_b, filtro_b) = GRUPOS[h.grupo_a], GRUPOS[h.grupo_b]
    v = h.variavel
    pop_a, pop_b = pop.loc[filtro_a(pop), v].dropna(), pop.loc[filtro_b(pop), v].dropna()
    am_a, am_b = am.loc[filtro_a(am), v].dropna(), am.loc[filtro_b(am), v].dropna()
    ga, gb = grupo(am_a, len(pop_a)), grupo(am_b, len(pop_b))
    t = TesteDuasMedias(ga, gb, h.alternativa, delta0=h.delta0, alpha=h.alpha)
    mu_a, mu_b = float(pop_a.mean()), float(pop_b.mean())
    dif_pop = mu_a - mu_b
    lo, hi = t.ic
    sinal, nula = ALTERNATIVAS[h.alternativa], NULAS[h.alternativa]
    lado = {"menor": "unilateral à esquerda", "maior": "unilateral à direita", "diferente": "bilateral"}[h.alternativa]
    cores = [AZUL, VERDE_AGUA]

    st.header(f"Hipótese {h.codigo}: {h.titulo}")
    col_ctx, col_def = st.columns([3, 2], gap="large")
    with col_ctx:
        st.markdown(h.contexto)
        st.markdown(f"**Parâmetro e teste.** {h.porque}")
    with col_def:
        st.markdown("**Grupos**")
        st.markdown(
            f"- **A:** {nome_a.lower()}: {br(len(pop_a))} na população, {br(ga.n)} na amostra\n"
            f"- **B:** {nome_b.lower()}: {br(len(pop_b))} na população, {br(gb.n)} na amostra\n"
            f"- Variável: {rotulo(v)} (`{v}`)"
        )
        st.markdown("**Hipóteses**")
        st.latex(rf"H_0:\; \mu_A - \mu_B {nula} {tex(h.delta0, 0)} \qquad H_1:\; \mu_A - \mu_B {sinal} {tex(h.delta0, 0)}")
        st.markdown(f"- H₀: {h.h0}.\n- H₁: {h.h1}.\n- Nível de significância α = 5%; teste t de Welch {lado}.")

    st.subheader("Resultado")
    m1, m2, m3, m4, m5 = st.columns([1.1, 1.4, 1.1, 1, 1.4])
    m1.metric("Diferença estimada", f"{br(t.diferenca, 1)} pts", border=True,
              help=f"Média da amostra de A ({br(ga.media, 1)}) menos a de B ({br(gb.media, 1)}).")
    m2.metric("IC de 95% da diferença", f"{br(lo, 1)} a {br(hi, 1)}", border=True)
    m3.metric("Estatística t", br(t.t, 2), border=True, help=f"{br(t.gl, 1)} graus de liberdade (Welch).")
    m4.metric("Valor-p", valor_p_txt(t.p_valor), border=True)
    m5.metric("Decisão (α = 5%)", "Rejeita H₀" if t.rejeita else "Não rejeita H₀", border=True)

    col_est, col_teste = st.columns(2, gap="large")
    with col_est:
        st.markdown("**Médias dos grupos: intervalos de confiança de 95%**")
        st.latex(r"\bar x \pm t_{n-1}\,\frac{s}{\sqrt n}\sqrt{1-\frac{n}{N}}")
        tabela = pd.DataFrame([
            {"Grupo": rot, "n": br(g.n), "Média (x̄)": br(g.media, 1), "Desvio-padrão (s)": br(g.dp, 1),
             "IC de 95% da média": f"{br(g.ic()[0], 1)} a {br(g.ic()[1], 1)}"}
            for rot, g in ((f"A: {nome_a}", ga), (f"B: {nome_b}", gb))
        ]).set_index("Grupo")
        st.table(tabela)
        st.plotly_chart(grafico_medias([f"A: {nome_a}", f"B: {nome_b}"], [ga, gb], [mu_a, mu_b], cores),
                        width="stretch", config={"displayModeBar": False}, key=f"medias_{h.codigo}")
    with col_teste:
        st.markdown("**Teste t de Welch para a diferença de médias**")
        st.latex(r"EP = \sqrt{\frac{s_A^2}{n_A}\Big(1-\frac{n_A}{N_A}\Big) + \frac{s_B^2}{n_B}\Big(1-\frac{n_B}{N_B}\Big)}"
                 r"\qquad t = \frac{(\bar x_A - \bar x_B) - \delta_0}{EP}")
        st.latex(rf"t = \frac{{{tex(ga.media)} - {tex(gb.media)}}}{{{tex(t.se, 3)}}} = {tex(t.t)}"
                 rf"\qquad gl = {tex(t.gl, 1)}")
        prob = {"menor": rf"P(T \le {tex(t.t)})", "maior": rf"P(T \ge {tex(t.t)})",
                "diferente": rf"2\,P(T \ge |{tex(t.t)}|)"}[h.alternativa]
        st.latex(rf"\text{{valor-p}} = {prob} = {valor_p_tex(t.p_valor)}")
        st.latex(rf"\text{{IC de 95\%}}:\ {tex(t.diferenca)} \pm {tex(t.t_ic, 3)} \times {tex(t.se, 3)}"
                 rf" = [\,{tex(lo)};\ {tex(hi)}\,]")
        st.plotly_chart(grafico_t(t), width="stretch", config={"displayModeBar": False}, key=f"t_{h.codigo}")

    st.markdown("**Condições de aplicação**")
    col_cond, col_caixa = st.columns([3, 2], gap="large")
    with col_cond:
        st.table(pd.DataFrame([
            ("Amostra aleatória simples", "sorteio sem reposição, semente fixa (Painel 2)", "✓"),
            ("Grupos independentes", "escolas diferentes; cada escola está em um só grupo", "✓"),
            ("n ≥ 30 em cada grupo (teorema central do limite)", f"n_A = {br(ga.n)}, n_B = {br(gb.n)}",
             "✓" if min(ga.n, gb.n) >= 30 else "✗"),
            ("Assimetria na amostra", f"A: {br(am_a.skew(), 2)}; B: {br(am_b.skew(), 2)} (moderada; n grande)", "✓"),
            ("Variâncias diferentes: teste de Welch", f"s²_A / s²_B = {br(ga.dp**2 / gb.dp**2, 2)}", "✓"),
            ("Correção para população finita", f"n_A/N_A = {br(100 * ga.n / ga.N, 2)}%, n_B/N_B = {br(100 * gb.n / gb.N, 2)}%",
             "✓"),
        ], columns=["Condição", "Valor", "Atende"]).set_index("Condição"))
    with col_caixa:
        st.markdown("**Distribuição nos dois grupos da amostra**")
        st.plotly_chart(grafico_caixas([f"A: {nome_a}", f"B: {nome_b}"], [am_a, am_b], cores), width="stretch",
                        config={"displayModeBar": False}, key=f"caixas_{h.codigo}")
        st.caption("Caixa: quartis e mediana; linha tracejada interna: média; pontos: escolas atípicas.")

    st.subheader("Comparação com a população")
    h0_verdadeira = {"menor": dif_pop >= h.delta0, "maior": dif_pop <= h.delta0,
                     "diferente": abs(dif_pop - h.delta0) < 1e-12}[h.alternativa]
    classificacao = classificar_decisao(t.rejeita, h0_verdadeira)
    contem = lo <= dif_pop <= hi
    col_tab, col_txt = st.columns([2, 3], gap="large")
    with col_tab:
        st.table(pd.DataFrame([
            (f"Média de A na população (μ_A)", br(mu_a, 2)),
            (f"Média de A na amostra (x̄_A)", br(ga.media, 2)),
            (f"Média de B na população (μ_B)", br(mu_b, 2)),
            (f"Média de B na amostra (x̄_B)", br(gb.media, 2)),
            ("Diferença na população (μ_A − μ_B)", br(dif_pop, 2)),
            ("Diferença na amostra (x̄_A − x̄_B)", br(t.diferenca, 2)),
            ("O IC de 95% contém a diferença verdadeira?", "Sim" if contem else "Não"),
            ("H₀ na população", "Verdadeira" if h0_verdadeira else "Falsa"),
            ("Decisão do teste", ("Rejeita H₀" if t.rejeita else "Não rejeita H₀")
             + (" (decisão correta)" if classificacao == "correta" else f" ({classificacao.removeprefix('um ')})")),
        ], columns=["", "Valor"]).set_index(""))
    with col_txt:
        sentido = {"menor": "menor", "maior": "maior", "diferente": "diferente"}[h.alternativa]
        conclusao = (f"há evidência de que a média de A é {sentido} que a de B, ou seja, {h.h1}" if t.rejeita
                     else f"a amostra não traz evidência suficiente contra H₀ ({h.h0})")
        st.markdown(
            f"**Interpretação.** Com 95% de confiança, a diferença entre as médias populacionais "
            f"({nome_a.lower()} menos {nome_b.lower()}) está entre {br(lo, 1)} e {br(hi, 1)} pontos. O teste "
            f"{'rejeita' if t.rejeita else 'não rejeita'} H₀ ao nível de 5% (valor-p {valor_p_txt(t.p_valor)}): "
            f"{conclusao}.\n\n"
            f"Como a população inteira é conhecida, dá para conferir: a diferença verdadeira é {br(dif_pop, 1)} "
            f"pontos ({br(mu_a, 1)} contra {br(mu_b, 1)}), a estimativa errou por {br(abs(t.diferenca - dif_pop), 1)} "
            f"ponto{'s' if abs(t.diferenca - dif_pop) >= 2 else ''}, o intervalo {'contém' if contem else 'não contém'} "
            f"o valor verdadeiro, e a decisão do teste foi {classificacao}."
        )

    st.subheader("E se fosse outra amostra?")
    sim = simulacao(h.codigo)
    col_g, col_s = st.columns([3, 2], gap="large")
    with col_g:
        st.plotly_chart(grafico_simulacao(sim, t, h.delta0), width="stretch", config={"displayModeBar": False},
                        key=f"sim_{h.codigo}")
    with col_s:
        st.markdown(
            f"O sorteio da amostra inteira ({br(par['n'])} escolas) repetido **{br(sim['repeticoes'])} vezes**, "
            "refazendo o teste com os grupos que caem em cada amostra. A diferença estimada muda de uma amostra "
            "para outra: essa é a variabilidade amostral."
        )
        st.metric("Amostras em que o teste rejeita H₀", f"{br(100 * sim['taxa_rejeicao'], 1)}%", border=True,
                  help="Com H₀ falsa na população, é o poder do teste; com H₀ verdadeira, seria a taxa de erro tipo I.")
        st.metric("Intervalos de 95% que contêm a diferença verdadeira", f"{br(100 * sim['cobertura'], 1)}%",
                  border=True, help="Deve ficar perto de 95%: é o significado do nível de confiança.")
        if not (sim["diferencas"].min() <= h.delta0 <= sim["diferencas"].max()):
            st.caption(f"Nenhuma das {br(sim['repeticoes'])} amostras chegou perto de δ₀ = {br(h.delta0, 0)}: "
                       "a diferença entre os grupos é grande demais para a variabilidade amostral apagá-la.")

    st.subheader("Limitações")
    st.markdown("\n".join(f"- {l}" for l in h.limitacoes))


st.title("Painel 3b: inferência para médias")
st.caption(
    "Intervalos de confiança e testes para a diferença entre as médias de dois grupos de escolas, calculados só com "
    f"a amostra aleatória simples de {br(par['n'])} escolas (Painel 2). As médias verdadeiras, conhecidas porque "
    "temos a população inteira, entram só na comparação."
)
nomes_abas = [f"Hipótese {h.codigo}" for h in MEDIAS]
pedida = f"Hipótese {st.query_params.get('hipotese')}"
abas = st.tabs(nomes_abas, default=pedida if pedida in nomes_abas else None)
for aba, h in zip(abas, MEDIAS):
    with aba:
        mostrar(h)
