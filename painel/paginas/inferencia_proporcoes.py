"""Painel 3a: inferência para proporções (intervalo de confiança e teste de hipótese, comparados à população)."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dados_painel import (AZUL, LARANJA, NEUTRO, amostra, br, parametros_amostra, pct, populacao, tex, valor_p_tex,
                          valor_p_txt)
from hipoteses import DOMINIOS, PROPORCOES, HipoteseProporcao
from inferencia import ALTERNATIVAS, NULAS, Z, TesteProporcao, simular_proporcao, teste_proporcao
from variaveis import rotulo

pop = populacao()
am = amostra()
par = parametros_amostra()
REGIAO_REJEICAO = "rgba(235, 104, 52, 0.30)"


def grafico_normal(t: TesteProporcao) -> go.Figure:
    lim = max(4.0, abs(t.z) + 0.8)
    xs = np.linspace(-lim, lim, 600)
    ys = np.array([Z.pdf(x) for x in xs])
    fig = go.Figure(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=NEUTRO, width=2), name="N(0, 1) se H₀ for verdadeira",
                               hoverinfo="skip"))
    zc = t.z_critico
    regioes = {"menor": [xs <= zc], "maior": [xs >= zc], "diferente": [xs <= -zc, xs >= zc]}[t.alternativa]
    for i, m in enumerate(regioes):
        fig.add_trace(go.Scatter(x=xs[m], y=ys[m], fill="tozeroy", fillcolor=REGIAO_REJEICAO, mode="lines",
                                 line=dict(width=0), name=f"região de rejeição (α = {pct(t.alpha, 0)})",
                                 showlegend=i == 0, hoverinfo="skip"))
    for zc_i in ([zc] if t.alternativa != "diferente" else [-zc, zc]):
        fig.add_vline(x=zc_i, line_color=LARANJA, line_width=1.5, annotation_text=f"z crítico {br(zc_i, 3)}",
                      annotation_position="top right" if zc_i > t.z else "top left", annotation_font_color=LARANJA)
    fig.add_vline(x=t.z, line_color=AZUL, line_width=3, annotation_text=f"z observado {br(t.z, 2)}",
                  annotation_position="top left" if t.z < zc else "top right", annotation_font_color=AZUL)
    fig.update_layout(height=320, margin=dict(l=0, r=0, t=40, b=0), separators=",.", yaxis_title="densidade",
                      xaxis_title="estatística z", legend=dict(orientation="h", y=1.12, yanchor="bottom", x=0))
    return fig


def grafico_intervalo(t: TesteProporcao, p_pop: float) -> go.Figure:
    lo, hi = t.ic
    fig = go.Figure([
        go.Scatter(x=[lo, hi], y=["Amostra"] * 2, mode="lines", line=dict(color=AZUL, width=8), name="IC de 95%",
                   hovertemplate="%{x:.2%}<extra>IC de 95%</extra>"),
        go.Scatter(x=[t.p_hat], y=["Amostra"], mode="markers", name="p̂ (estimativa da amostra)",
                   marker=dict(color=AZUL, size=15, line=dict(color="white", width=2)),
                   hovertemplate="p̂ = %{x:.2%}<extra></extra>"),
        go.Scatter(x=[p_pop], y=["População"], mode="markers", name="p (valor verdadeiro na população)",
                   marker=dict(color=LARANJA, size=15, symbol="diamond", line=dict(color="white", width=2)),
                   hovertemplate="p = %{x:.2%}<extra></extra>"),
    ])
    fig.add_vline(x=t.p0, line_color=NEUTRO, line_width=2, annotation_text=f"p₀ = {pct(t.p0, 0)}",
                  annotation_position="top", annotation_font_color=NEUTRO)
    xmin, xmax = min(lo, t.p0, p_pop), max(hi, t.p0, p_pop)
    folga = (xmax - xmin) * 0.25 + 0.005
    fig.update_layout(height=260, margin=dict(l=0, r=0, t=50, b=0), separators=",.",
                      xaxis=dict(tickformat=".0%", range=[xmin - folga, xmax + folga], title="proporção"),
                      yaxis=dict(title=None, categoryorder="array", categoryarray=["População", "Amostra"]),
                      legend=dict(orientation="h", y=1.18, yanchor="bottom", x=0))
    return fig


@st.cache_data(show_spinner=False)
def simulacao(K: int, N: int, n: int, p0: float, alternativa: str, alpha: float) -> dict:
    return simular_proporcao(K, N, n, p0, alternativa, alpha)


def grafico_simulacao(sim: dict, t: TesteProporcao) -> go.Figure:
    bordas = np.arange(sim["p_hat"].min() - 0.5 / t.n, sim["p_hat"].max() + 1 / t.n, 1 / t.n)
    altura = 100 * np.histogram(sim["p_hat"], bins=bordas)[0].max() / len(sim["p_hat"]) * 1.08
    fig = go.Figure(go.Histogram(x=sim["p_hat"], histnorm="percent", marker_color=AZUL, opacity=0.85,
                                 xbins=dict(start=bordas[0], end=bordas[-1], size=1 / t.n), name="p̂ das amostras simuladas",
                                 hovertemplate="p̂ = %{x:.1%}<br>%{y:.1f}% das amostras<extra></extra>"))
    # linhas de referência como séries com legenda: os rótulos não colidem quando as linhas ficam próximas
    for x, nome, cor in ((t.p_hat, f"nossa amostra: {pct(t.p_hat, 1)}", "#0d366b"),
                         (sim["p_populacao"], f"p da população: {pct(sim['p_populacao'], 2)}", LARANJA),
                         (t.p0, f"p₀ = {pct(t.p0, 0)}", NEUTRO)):
        fig.add_trace(go.Scatter(x=[x, x], y=[0, altura], mode="lines", line=dict(color=cor, width=2.5), name=nome,
                                 hoverinfo="skip"))
    fig.update_layout(height=340, margin=dict(l=0, r=0, t=10, b=0), separators=",.", bargap=0.05,
                      xaxis=dict(tickformat=".0%", title="proporção estimada (p̂)"),
                      yaxis=dict(title="% das amostras", range=[0, altura]),
                      legend=dict(orientation="h", y=-0.28, yanchor="top", x=0))
    return fig


def decisao_vs_verdade(h: HipoteseProporcao, t: TesteProporcao, p_pop: float) -> tuple[bool, str]:
    h0_verdadeira = {"menor": p_pop >= h.p0, "maior": p_pop <= h.p0, "diferente": abs(p_pop - h.p0) < 1e-12}[h.alternativa]
    if t.rejeita:
        return h0_verdadeira, "um erro tipo I (rejeitou uma H₀ verdadeira)" if h0_verdadeira else "correta"
    return h0_verdadeira, "correta" if h0_verdadeira else "um erro tipo II (não rejeitou uma H₀ falsa)"


def mostrar(h: HipoteseProporcao) -> None:
    nome_dom, filtro = DOMINIOS[h.dominio]
    pop_d, am_d = filtro(pop), filtro(am)
    t = teste_proporcao(am_d[h.variavel], N=int(pop_d[h.variavel].notna().sum()), p0=h.p0,
                        alternativa=h.alternativa, alpha=h.alpha)
    p_pop = float(pop_d[h.variavel].mean())
    K = int(pop_d[h.variavel].sum())
    lo, hi = t.ic
    sinal, nula = ALTERNATIVAS[h.alternativa], NULAS[h.alternativa]
    lado = {"menor": "unilateral à esquerda", "maior": "unilateral à direita", "diferente": "bilateral"}[h.alternativa]

    st.header(f"Hipótese {h.codigo}: {h.titulo}")
    col_ctx, col_def = st.columns([3, 2], gap="large")
    with col_ctx:
        st.markdown(h.contexto)
        st.markdown(f"**Por que p₀ = {br(h.p0, 2)}.** {h.porque_p0}")
    with col_def:
        st.markdown("**Parâmetro**")
        st.markdown(
            f"p = proporção de escolas em que {h.evento}, entre as {nome_dom}.\n\n"
            f"- Variável: {rotulo(h.variavel)} (`{h.variavel}`)\n"
            f"- População do teste: N = {br(t.N)} escolas\n"
            f"- Amostra: n = {br(t.n)} dessas escolas, entre as {br(par['n'])} sorteadas"
        )
        st.markdown("**Hipóteses**")
        st.latex(rf"H_0:\; p {nula} {tex(h.p0)} \qquad\qquad H_1:\; p {sinal} {tex(h.p0)}")
        st.markdown(f"- H₀: {h.h0}.\n- H₁: {h.h1}.\n- Nível de significância α = {pct(h.alpha, 0)}; teste z {lado}.")

    st.subheader("Resultado")
    m1, m2, m3, m4, m5 = st.columns([1, 1.4, 0.9, 1, 1.5])
    m1.metric("Estimativa p̂", pct(t.p_hat, 1), help=f"{br(t.x)} de {br(t.n)} escolas da amostra.", border=True)
    m2.metric("IC de 95%", f"{br(100 * lo, 1)}–{pct(hi, 1)}", border=True)
    m3.metric("Estatística z", br(t.z, 2), border=True)
    m4.metric("Valor-p", valor_p_txt(t.p_valor), border=True)
    m5.metric("Decisão (α = 5%)", "Rejeita H₀" if t.rejeita else "Não rejeita H₀", border=True)

    col_ic, col_teste = st.columns(2, gap="large")
    with col_ic:
        st.markdown("**Intervalo de confiança de 95%**")
        st.latex(r"\hat p \pm z_{\alpha/2}\sqrt{\frac{\hat p(1-\hat p)}{n}}\sqrt{\frac{N-n}{N-1}}")
        st.latex(rf"{tex(t.p_hat, 4)} \pm {tex(t.z_ic)} \times {tex(t.se, 4)} = [\,{tex(lo, 4)};\ {tex(hi, 4)}\,]")
        st.plotly_chart(grafico_intervalo(t, p_pop), width="stretch", config={"displayModeBar": False}, key=f"ic_{h.codigo}")
    with col_teste:
        st.markdown("**Teste z para uma proporção**")
        st.latex(r"z = \frac{\hat p - p_0}{\sqrt{\dfrac{p_0(1-p_0)}{n}}\sqrt{\dfrac{N-n}{N-1}}}")
        prob = {"menor": rf"P(Z \le {tex(t.z)})", "maior": rf"P(Z \ge {tex(t.z)})",
                "diferente": rf"2\,P(Z \ge |{tex(t.z)}|)"}[h.alternativa]
        st.latex(rf"z = \frac{{{tex(t.p_hat, 4)} - {tex(h.p0)}}}{{{tex(t.se0, 4)}}} = {tex(t.z)}")
        st.latex(rf"\text{{valor-p}} = {prob} = {valor_p_tex(t.p_valor)}")
        st.plotly_chart(grafico_normal(t), width="stretch", config={"displayModeBar": False}, key=f"normal_{h.codigo}")

    st.markdown("**Condições de aplicação**")
    cond = [("Amostra aleatória simples", "sorteio sem reposição, semente fixa (Painel 2)", True),
            ("Fração amostral n/N", f"{pct(t.n / t.N, 2)}: correção para população finita aplicada "
                                    f"(fator {br(t.fpc, 4)})", True)]
    cond += [(f"{nome} ≥ 10", br(v, 0), ok) for nome, v, ok in t.condicoes()]
    st.table(pd.DataFrame([(c, v, "✓" if ok else "✗") for c, v, ok in cond],
                          columns=["Condição", "Valor", "Atende"]).set_index("Condição"))

    st.subheader("Comparação com a população")
    h0_verdadeira, classificacao = decisao_vs_verdade(h, t, p_pop)
    contem = lo <= p_pop <= hi
    col_tab, col_txt = st.columns([2, 3], gap="large")
    with col_tab:
        st.table(pd.DataFrame([
            ("Proporção na população (p)", pct(p_pop, 2)),
            ("Estimativa da amostra (p̂)", pct(t.p_hat, 2)),
            ("Diferença (p̂ − p)", f"{br(100 * (t.p_hat - p_pop), 2)} p.p."),
            ("O IC de 95% contém p?", "Sim" if contem else "Não"),
            ("H₀ na população", ("Verdadeira" if h0_verdadeira else "Falsa") + f": p = {pct(p_pop, 2)}"),
            ("Decisão do teste", ("Rejeita H₀" if t.rejeita else "Não rejeita H₀")
             + (" (decisão correta)" if classificacao == "correta" else f" ({classificacao.removeprefix('um ')})")),
        ], columns=["", "Valor"]).set_index(""))
    with col_txt:
        conclusao = (f"há evidência de que a proporção é {'menor' if h.alternativa == 'menor' else 'maior' if h.alternativa == 'maior' else 'diferente'} "
                     f"que {pct(h.p0, 0)}, ou seja, {h.h1}" if t.rejeita else
                     f"a amostra não traz evidência suficiente contra H₀ ({h.h0})")
        contrario = (h.alternativa == "maior" and hi < h.p0) or (h.alternativa == "menor" and lo > h.p0)
        if contrario:
            conclusao += (f". O intervalo inteiro fica {'abaixo' if h.alternativa == 'maior' else 'acima'} de "
                          f"{pct(h.p0, 0)}: a amostra aponta na direção contrária à de H₁")
        st.markdown(
            f"**Interpretação.** Com 95% de confiança, a proporção verdadeira de {nome_dom} com o evento está entre "
            f"{pct(lo, 1)} e {pct(hi, 1)}. O teste {'rejeita' if t.rejeita else 'não rejeita'} H₀ ao nível de 5% "
            f"(valor-p {valor_p_txt(t.p_valor)}): {conclusao}.\n\n"
            f"Como a população inteira é conhecida, dá para conferir: a proporção verdadeira é {pct(p_pop, 2)}, "
            f"a estimativa errou por {br(abs(100 * (t.p_hat - p_pop)), 2)} ponto percentual, o intervalo "
            f"{'contém' if contem else 'não contém'} o valor verdadeiro, e a decisão do teste foi {classificacao}."
        )

    st.subheader("E se fosse outra amostra?")
    sim = simulacao(K, t.N, t.n, h.p0, h.alternativa, h.alpha)
    col_g, col_s = st.columns([3, 2], gap="large")
    with col_g:
        st.plotly_chart(grafico_simulacao(sim, t), width="stretch", config={"displayModeBar": False}, key=f"sim_{h.codigo}")
    with col_s:
        st.markdown(
            f"A mesma análise repetida em **{br(sim['repeticoes'])} amostras aleatórias simples** de {br(t.n)} escolas, "
            f"sorteadas da população do teste. Cada amostra dá uma estimativa diferente: essa é a variabilidade amostral."
        )
        st.metric("Amostras em que o teste rejeita H₀", pct(sim["taxa_rejeicao"], 1), border=True,
                  help="Com H₀ falsa na população, é o poder do teste; com H₀ verdadeira, seria a taxa de erro tipo I (≈ α).")
        st.metric("Intervalos de 95% que contêm p", pct(sim["cobertura"], 1), border=True,
                  help="Deve ficar perto de 95%: é o significado do nível de confiança.")
        st.caption("O número de escolas com o evento numa AAS sem reposição segue a distribuição hipergeométrica; "
                   "cada repetição é um sorteio exato, não uma aproximação.")

    st.subheader("Limitações")
    st.markdown("\n".join(f"- {l}" for l in h.limitacoes))


st.title("Painel 3a: inferência para proporções")
st.caption(
    "Intervalo de confiança e teste de hipótese para proporções, calculados só com a amostra aleatória simples "
    f"de {br(par['n'])} escolas (Painel 2). A proporção verdadeira, conhecida porque temos a população inteira, "
    "entra só na comparação final."
)
nomes_abas = [f"Hipótese {h.codigo}" for h in PROPORCOES]
pedida = f"Hipótese {st.query_params.get('hipotese')}"  # ?hipotese=2 abre direto a aba
abas = st.tabs(nomes_abas, default=pedida if pedida in nomes_abas else None)
for aba, h in zip(abas, PROPORCOES):
    with aba:
        mostrar(h)
