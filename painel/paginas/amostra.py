"""Painel 2: dimensionamento e sorteio da amostra, e análise descritiva da amostra."""
import math
from statistics import NormalDist

import pandas as pd
import streamlit as st

from componentes import distribuicao, escolher_recorte, indicadores, mapa, tabela_resumo
from dados_painel import amostra, br, parametros_amostra, pct, populacao, resumo, tex
from variaveis import rotulo

pop = populacao()
am = amostra()
par = parametros_amostra()
info = resumo()
N, n, z, E, p = par["N"], par["n"], par["z"], par["margem"], par["p_planejamento"]


st.title("Painel 2: a amostra")
st.caption(
    f"Amostra aleatória simples de {br(n)} escolas, sorteada entre as {br(N)} da população. "
    "Primeiro o cálculo do tamanho da amostra e o sorteio; depois, a análise descritiva só com as escolas sorteadas."
)

# --- 1. tamanho da amostra -----------------------------------------------------------------------
st.header("1. Tamanho da amostra")
st.markdown(
    "O tamanho é calculado para estimar uma **proporção** com a precisão desejada. Como uma única amostra "
    "serve a todas as hipóteses do trabalho, usa-se o cenário mais exigente, e a precisão que resulta para "
    "as **médias** é conferida em seguida."
)
st.table(pd.DataFrame([
    ("Tamanho da população (N)", br(N), "As escolas da população (Painel 0)."),
    ("Nível de confiança (1 − α)", f"{pct(par['confianca'], 0)} (z = {br(z, 2)})",
     "Convenção usual: equilibra a confiança dos intervalos e o tamanho da amostra."),
    ("Margem de erro (E)", f"{br(100 * E, 0)} pontos percentuais",
     "Basta para separar diferenças de poucos pontos nas proporções, com uma amostra de cerca de 4% da população."),
    ("Proporção de planejamento (p)", br(p, 1),
     "Sem estimativa prévia, p = 0,5 maximiza p(1 − p) e dá o maior n: serve a qualquer proporção estudada."),
], columns=["Parâmetro", "Valor", "Justificativa"]).set_index("Parâmetro"))

st.markdown("**Passo 1: tamanho para uma população infinita**")
st.latex(rf"n_0 = \frac{{z_{{\alpha/2}}^2 \; p\,(1-p)}}{{E^2}} = \frac{{{tex(z)}^2 \times {tex(p, 1)} \times {tex(1 - p, 1)}}}"
         rf"{{{tex(E)}^2}} = {tex(par['n0'])}")
st.markdown("**Passo 2: correção para população finita**, porque N é conhecido e a amostra é sem reposição")
st.latex(rf"n = \frac{{n_0}}{{1 + \dfrac{{n_0 - 1}}{{N}}}} = \frac{{{tex(par['n0'])}}}{{1 + \dfrac{{{tex(par['n0'] - 1)}}}"
         rf"{{{br(N)}}}}} = {tex(par['n_corrigido'])} \;\Rightarrow\; n = {br(n)}")
st.markdown(f"Arredondando para cima: **n = {br(n)} escolas**, {pct(n / N, 2)} da população.")

col_cen, col_med = st.columns(2, gap="large")
with col_cen:
    st.markdown("**Outros cenários** (mesma população, p = 0,5)")
    linhas = []
    for conf in (0.95, 0.99):
        zc = NormalDist().inv_cdf(1 - (1 - conf) / 2)
        for marg in (0.02, 0.03, 0.04, 0.05):
            n0c = zc**2 * 0.25 / marg**2
            escolhido = conf == par["confianca"] and math.isclose(marg, E)
            linhas.append({"Confiança": pct(conf, 0), "Margem": f"{br(100 * marg, 0)} p.p.",
                           "n": br(math.ceil(n0c / (1 + (n0c - 1) / N))), "": "← adotado" if escolhido else ""})
    st.dataframe(pd.DataFrame(linhas), hide_index=True, width="stretch")
with col_med:
    st.markdown(f"**Precisão para as médias** com n = {br(n)}")
    fpc = math.sqrt((N - n) / (N - 1))
    linhas = []
    for col in ["ENEM_MEDIA_GERAL", "ENEM_MEDIA_MT", "ENEM_MEDIA_REDACAO", "PCT_PPI"]:
        s = am[col].std()
        e = z * s / math.sqrt(am[col].notna().sum()) * fpc
        linhas.append({"Variável": rotulo(col), "Desvio-padrão (amostra)": br(s, 1), "Margem de erro": f"± {br(e, 1)}",
                       "Margem relativa": pct(e / am[col].mean())})
    st.table(pd.DataFrame(linhas).set_index("Variável"))
    st.caption("Margem = z · s / √n · √((N − n)/(N − 1)), com o desvio-padrão s da própria amostra. "
               "As notas estão em pontos do ENEM; o % de pretos, pardos e indígenas, em pontos percentuais.")

# --- 2. sorteio ----------------------------------------------------------------------------------
st.header("2. Sorteio da amostra aleatória simples")
st.markdown(
    f"""
1. **Cadastro:** as {br(N)} escolas da população, em ordem crescente do código do INEP (`CO_ENTIDADE`),
   numeradas de 1 a {br(N)}.
2. **Sorteio:** um gerador de números pseudoaleatórios com **semente fixa ({par['semente']})** escolhe
   {br(n)} posições diferentes do cadastro, **sem reposição**.
3. **Mesma chance para todas:** cada escola tem a mesma probabilidade de entrar na amostra,
   n/N = {pct(n / N, 2)}, e todo conjunto de {br(n)} escolas tem a mesma chance de ser o sorteado.
4. **Reprodutível:** com a mesma semente e o mesmo cadastro, o sorteio dá sempre a mesma amostra. A lista
   sorteada fica gravada, e este painel só a lê.
"""
)
st.code(
    f"""cadastro = populacao.sort_values("CO_ENTIDADE").reset_index(drop=True)   # N = {N}
gerador = numpy.random.default_rng({par['semente']})
posicoes = gerador.choice(len(cadastro), size={n}, replace=False)       # sem reposição
amostra = cadastro.loc[posicoes]""",
    language="python",
)
st.caption(f"Gerador: {par['gerador']}. Sorteio feito em {par['data_sorteio']} (painel/sortear_amostra.py).")

lista = am[["ORDEM_SORTEIO", "POSICAO_CADASTRO", "CO_ENTIDADE", "NO_ENTIDADE", "NO_MUNICIPIO", "SG_UF", "DEPENDENCIA"]]
lista = lista.rename(columns={"ORDEM_SORTEIO": "Ordem do sorteio", "POSICAO_CADASTRO": "Posição no cadastro",
                              "CO_ENTIDADE": "Código INEP", "NO_ENTIDADE": "Escola", "NO_MUNICIPIO": "Município",
                              "SG_UF": "UF", "DEPENDENCIA": "Dependência"})
st.markdown("**As primeiras escolas sorteadas**")
st.dataframe(lista.head(10), hide_index=True, width="stretch",
             column_config={"Código INEP": st.column_config.NumberColumn(format="%d")})
st.download_button(f"Baixar a lista das {br(n)} escolas sorteadas (CSV)",
                   lista.to_csv(index=False, sep=";").encode("utf-8-sig"),
                   file_name="amostra_escolas_enem_2025.csv", mime="text/csv", icon=":material/download:")

# --- 3. análise descritiva da amostra ------------------------------------------------------------
st.header("3. Análise descritiva da amostra")
st.markdown(
    "As mesmas análises do Painel 1, calculadas **só com as escolas sorteadas**. A população, no mesmo recorte, "
    "aparece ao lado como referência, para ver onde a amostra se parece com ela e onde se afasta."
)
rec = escolher_recorte(am, "p2")
sel = rec.selecao(am)
ref = rec.selecao(pop)
indicadores(sel, ref)

col_mapa, col_tabela = st.columns([3, 2], gap="medium")
with col_mapa:
    mapa("amostra", rec, [m for m in info["municipios_sem_poligono"] if m["CO_MUNICIPIO"] in set(am["CO_MUNICIPIO"])])
with col_tabela:
    tabela_resumo(sel, ref, chave="p2")

st.subheader("Distribuição de cada variável: amostra e população")
distribuicao(sel, ref, chave="p2")
st.caption(
    f"Recorte: {rec.nome} ({br(len(sel))} escolas sorteadas; {br(len(ref))} na população). Em recortes pequenos "
    "a amostra tem poucas escolas, e as diferenças em relação à população tendem a ser maiores."
)
