"""Partes compartilhadas dos painéis descritivos: recorte geográfico, indicadores, mapa, tabela-resumo e
distribuição de cada variável.

O Painel 1 as usa com a população. O Painel 2 as usa com a amostra e passa a população (no mesmo
recorte) como referência: as tabelas ganham as colunas da população e da diferença, e os gráficos
mostram as duas distribuições juntas.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dados_painel import (AZUL, LARANJA, MUN_CONTORNO, NEUTRO, RAMPA_AZUL, SEM_ESCOLA, UF_CONTORNO, amostra, br,
                          malha, municipios, pct, populacao)
from descritiva import frequencias, medidas, qualitativa, resumo_qualitativas, resumo_quantitativas
from variaveis import VARIAVEIS, rotulo

BRASIL, TODAS, TODOS = "Brasil", "Todas", "Todos"
REGIOES = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
TRANSPARENTE = [[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]]
CONJUNTOS = {"populacao": populacao, "amostra": amostra}
FAIXAS = {  # faixas de escolas por município no mapa (rótulo, limite superior)
    "populacao": [("Nenhuma", 0), ("1", 1), ("2–3", 3), ("4–9", 9), ("10–49", 49), ("50 ou mais", np.inf)],
    "amostra": [("Nenhuma", 0), ("1", 1), ("2–3", 3), ("4 ou mais", np.inf)],
}
CORES_FAIXAS = {"populacao": RAMPA_AZUL, "amostra": [RAMPA_AZUL[0], RAMPA_AZUL[2], RAMPA_AZUL[4]]}
CASAS = {"n": 0, "Coef. de variação": 2, "Assimetria": 2}


# --- recorte geográfico (drill-down) -------------------------------------------------------------
@dataclass(frozen=True)
class Recorte:
    regiao: str = BRASIL
    uf: str = TODAS
    municipio: str = TODOS

    @property
    def nome(self) -> str:
        if self.municipio != TODOS:
            return f"{self.municipio} ({self.uf})"
        if self.uf != TODAS:
            return self.uf
        return f"Região {self.regiao}" if self.regiao != BRASIL else BRASIL

    def area(self, df: pd.DataFrame) -> pd.DataFrame:
        """O que o mapa mostra: Brasil, região ou UF."""
        if self.regiao != BRASIL:
            df = df[df["NO_REGIAO"] == self.regiao]
        if self.uf != TODAS:
            df = df[df["SG_UF"] == self.uf]
        return df

    def selecao(self, df: pd.DataFrame) -> pd.DataFrame:
        """O que as tabelas resumem: a área ou, se houver, o município."""
        df = self.area(df)
        return df[df["NO_MUNICIPIO"] == self.municipio] if self.municipio != TODOS else df


def escolher_recorte(base: pd.DataFrame, prefixo: str) -> Recorte:
    """Título da seção e o botão de recorte (acima do mapa, à direita). Aceita ?regiao=, ?uf= e
    ?municipio= na URL na primeira carga."""
    ss = st.session_state
    k = lambda nome: f"{prefixo}_{nome}"
    if k("regiao") not in ss:
        qp = st.query_params
        uf = qp.get("uf") if qp.get("uf") in set(base["SG_UF"]) else TODAS
        ss[k("regiao")] = qp.get("regiao") if qp.get("regiao") in REGIOES and uf == TODAS else BRASIL
        ss[k("uf")] = uf
        ss[k("municipio")] = qp.get("municipio") if qp.get("municipio") in set(base.loc[base["SG_UF"] == uf, "NO_MUNICIPIO"]) else TODOS

    def mudou_regiao():
        ss[k("uf")], ss[k("municipio")] = TODAS, TODOS

    def mudou_uf():
        ss[k("municipio")] = TODOS

    def voltar():
        ss[k("regiao")], ss[k("uf")], ss[k("municipio")] = BRASIL, TODAS, TODOS

    rec = Recorte(ss[k("regiao")], ss[k("uf")], ss[k("municipio")])
    esq, dir_ = st.columns([3, 2], vertical_alignment="bottom")
    esq.subheader(f"Escolas e variáveis: {rec.nome}")
    with dir_.popover(f"Recorte: {rec.nome}", icon=":material/travel_explore:", width="stretch"):
        st.selectbox("Região", [BRASIL, *REGIOES], key=k("regiao"), on_change=mudou_regiao)
        ufs = base["SG_UF"] if rec.regiao == BRASIL else base.loc[base["NO_REGIAO"] == rec.regiao, "SG_UF"]
        st.selectbox("UF", [TODAS, *sorted(ufs.unique())], key=k("uf"), on_change=mudou_uf)
        nomes = sorted(base.loc[base["SG_UF"] == rec.uf, "NO_MUNICIPIO"].unique()) if rec.uf != TODAS else []
        st.selectbox("Município", [TODOS, *nomes], key=k("municipio"), disabled=rec.uf == TODAS,
                     help="Escolha uma UF para listar os municípios.")
        st.button("Voltar ao Brasil", on_click=voltar, icon=":material/public:", width="stretch", key=k("voltar"))
    return rec


# --- indicadores ---------------------------------------------------------------------------------
def indicadores(sel: pd.DataFrame, ref: pd.DataFrame | None = None) -> None:
    itens = [
        ("Escolas", lambda d: len(d), 0, None),
        ("Municípios", lambda d: d["CO_MUNICIPIO"].nunique(), 0, None),
        ("Participantes no ENEM", lambda d: d["ENEM_COM_NOTAS"].sum(), 0,
         "Participantes das escolas do recorte com as cinco notas."),
        ("Média geral no ENEM", lambda d: d["ENEM_MEDIA_GERAL"].mean(), 1,
         "Média, entre as escolas do recorte, da média geral de cada escola."),
    ]
    for col, (rot, f, casas, ajuda) in zip(st.columns(len(itens)), itens):
        delta = None if ref is None else f"população: {br(f(ref), casas)}"
        col.metric(rot, br(f(sel), casas), delta=delta, delta_color="off", delta_arrow="off", border=True, help=ajuda)


# --- mapa: território dos municípios -------------------------------------------------------------
def _qtd_escolas(n: int, conjunto: str) -> str:
    if conjunto == "populacao":
        return "nenhuma escola da população" if n == 0 else f"{br(n)} escola{'s' if n > 1 else ''} da população"
    return "nenhuma escola sorteada" if n == 0 else f"{br(n)} escola{'s' if n > 1 else ''} sorteada{'s' if n > 1 else ''}"


@st.cache_data(show_spinner=False)
def _figura_mapa(conjunto: str, regiao: str, uf: str, municipio: str) -> go.Figure:
    rec = Recorte(regiao, uf, municipio)
    mun = municipios()
    area = rec.area(CONJUNTOS[conjunto]())
    cod_uf = (mun.assign(CO_UF=mun["CO_MUNICIPIO"] // 100000).drop_duplicates("SG_UF")
              .set_index("SG_UF")["CO_UF"].astype(str))
    if rec.uf != TODAS:
        ufs_mapa = {cod_uf[rec.uf]}
    elif rec.regiao != BRASIL:
        ufs_mapa = set(cod_uf[mun.loc[mun["NO_REGIAO"] == rec.regiao, "SG_UF"].unique()])
    else:
        ufs_mapa = None
    no_mapa = lambda f: ufs_mapa is None or f["properties"]["codarea"][:2] in ufs_mapa
    malha_mun = {"type": "FeatureCollection", "features": [f for f in malha("municipios")["features"] if no_mapa(f)]}
    malha_uf = {"type": "FeatureCollection", "features": [f for f in malha("uf")["features"] if no_mapa(f)]}

    faixas = FAIXAS[conjunto]
    d = pd.DataFrame({"codarea": [f["properties"]["codarea"] for f in malha_mun["features"]]})
    d["CO_MUNICIPIO"] = d["codarea"].astype(int)
    d = d.merge(mun, on="CO_MUNICIPIO", how="left")
    d["escolas"] = d["CO_MUNICIPIO"].map(area.groupby("CO_MUNICIPIO").size()).fillna(0).astype(int)
    d["faixa"] = pd.cut(d["escolas"], [-1] + [lim for _, lim in faixas], labels=False)
    d["texto"] = d["escolas"].map(lambda n: _qtd_escolas(n, conjunto))

    cores = [SEM_ESCOLA, *CORES_FAIXAS[conjunto]]
    escala = [par for i, c in enumerate(cores) for par in ([i / len(cores), c], [(i + 1) / len(cores), c])]
    fig = go.Figure(go.Choropleth(
        geojson=malha_mun, featureidkey="properties.codarea", locations=d["codarea"], z=d["faixa"],
        zmin=-0.5, zmax=len(cores) - 0.5, colorscale=escala,
        marker_line_color=MUN_CONTORNO, marker_line_width=0.15 if ufs_mapa is None else 0.4,
        customdata=d[["NO_MUNICIPIO", "SG_UF", "texto"]].fillna(""),
        hovertemplate="<b>%{customdata[0]}</b> (%{customdata[1]})<br>%{customdata[2]}<extra></extra>",
        colorbar=dict(title=dict(text="Escolas no município" + (" (amostra)" if conjunto == "amostra" else ""),
                                 side="top"), orientation="h",
                      tickvals=list(range(len(cores))), ticktext=[n for n, _ in faixas],
                      x=0.5, xanchor="center", y=-0.02, yanchor="top", len=0.9, thickness=12, outlinewidth=0),
    ))
    fig.add_trace(go.Choropleth(
        geojson=malha_uf, featureidkey="properties.codarea",
        locations=[f["properties"]["codarea"] for f in malha_uf["features"]], z=[0] * len(malha_uf["features"]),
        colorscale=TRANSPARENTE, showscale=False, marker_line_color=UF_CONTORNO, marker_line_width=0.8,
        hoverinfo="skip",
    ))
    if rec.municipio != TODOS:
        cod = str(int(area.loc[area["NO_MUNICIPIO"] == rec.municipio, "CO_MUNICIPIO"].iloc[0]))
        fig.add_trace(go.Choropleth(
            geojson=malha_mun, featureidkey="properties.codarea", locations=[cod], z=[0],
            colorscale=TRANSPARENTE, showscale=False, marker_line_color=LARANJA, marker_line_width=3,
            hoverinfo="skip",
        ))
    fig.update_geos(visible=False, projection_type="mercator", fitbounds="locations", bgcolor="rgba(0,0,0,0)")
    fig.update_layout(height=640, margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)",
                      dragmode="pan", separators=",.")
    return fig


def mapa(conjunto: str, rec: Recorte, sem_poligono: list[dict]) -> None:
    st.plotly_chart(_figura_mapa(conjunto, rec.regiao, rec.uf, rec.municipio), width="stretch", config={"scrollZoom": True, "displaylogo": False},
                    key=f"mapa_{conjunto}")
    fora = [f"{m['NO_MUNICIPIO']} ({m['SG_UF']})" for m in sem_poligono]
    quem = "da população" if conjunto == "populacao" else "sorteadas"
    st.caption(
        f"Território de cada município (malha do IBGE), colorido pelo número de escolas {quem}. "
        "O Censo Escolar 2025 não traz a localização exata das escolas. "
        + (f"Sem polígono na malha do IBGE, fica fora do mapa: {', '.join(fora)}." if fora else "")
    )


# --- tabela-resumo das variáveis -----------------------------------------------------------------
def tabela_resumo(sel: pd.DataFrame, ref: pd.DataFrame | None = None, chave: str = "resumo") -> None:
    tipo = st.segmented_control("Variáveis", ["Qualitativas", "Quantitativas"], default="Qualitativas",
                                required=True, key=f"{chave}_tipo", label_visibility="collapsed")
    fixa = {"Variável": st.column_config.TextColumn(pinned=True)}
    if tipo == "Qualitativas":
        t = resumo_qualitativas(sel)
        if ref is not None:
            r = resumo_qualitativas(ref)[["Variável", "Categoria", "Proporção"]].rename(columns={"Proporção": "População"})
            t = t.merge(r, on=["Variável", "Categoria"], how="left")
            t["Diferença (p.p.)"] = (100 * (t["Proporção"] - t["População"])).map(lambda x: br(x, 1))
            t["População"] = t["População"].map(pct)
            t = t.rename(columns={"Proporção": "Amostra"}).drop(columns="Escolas")  # contagens: na seção de distribuição
            t["Amostra"] = t["Amostra"].map(pct)
        else:
            t["Proporção"] = t["Proporção"].map(pct)
            t["Escolas"] = t["Escolas"].map(br)
        st.dataframe(t, hide_index=True, height=600, width="stretch", column_config=fixa)
        st.caption("Proporção entre as escolas do recorte com a informação. Nas variáveis de sim ou não, a linha "
                   "mostra as escolas com \"sim\"." + (" Diferença: amostra menos população, em pontos percentuais."
                                                        if ref is not None else ""))
    else:
        t = resumo_quantitativas(sel)
        if ref is not None:
            r = resumo_quantitativas(ref).set_index("Variável")
            t = t[["Variável", "n", "Média", "Mediana", "Desvio-padrão"]].copy()
            t["Média da população"] = t["Variável"].map(r["Média"])
            t["Diferença"] = t["Média"] - t["Média da população"]
            t["Mediana da população"] = t["Variável"].map(r["Mediana"])
            t["DP da população"] = t["Variável"].map(r["Desvio-padrão"])
            t = t[["Variável", "n", "Média", "Média da população", "Diferença", "Mediana", "Mediana da população",
                   "Desvio-padrão", "DP da população"]]
        for c in t.columns[1:]:
            t[c] = t[c].map(lambda x, c=c: br(x, CASAS.get(c, 1)))
        st.dataframe(t, hide_index=True, height=600, width="stretch", column_config=fixa)
        st.caption("n: escolas do recorte com a informação. Percentuais na escala de 0 a 100; a taxa de participação "
                   "é uma razão (1 = tantos participantes quanto matrículas na 3ª série)."
                   + (" Diferença: média da amostra menos média da população." if ref is not None else ""))


# --- distribuição de uma variável ----------------------------------------------------------------
def _barras(f: pd.DataFrame, fr: pd.DataFrame | None) -> go.Figure:
    fig = go.Figure()
    series = [("Amostra" if fr is not None else "Escolas", f, AZUL)] + ([("População", fr, LARANJA)] if fr is not None else [])
    for nome, d, cor in series:
        fig.add_trace(go.Bar(
            x=d["Proporção"], y=d["Categoria"], orientation="h", name=nome, marker_color=cor,
            text=d["Proporção"].map(pct), textposition="outside", cliponaxis=False,
            customdata=d["Escolas"].map(lambda n: f"{br(n)} escolas"),
            hovertemplate=f"<b>%{{y}}</b> ({nome.lower()})<br>%{{customdata}} (%{{text}})<extra></extra>",
        ))
    maximo = max(f["Proporção"].max(), fr["Proporção"].max() if fr is not None else 0)
    fig.update_layout(
        barmode="group", bargap=0.3, bargroupgap=0.08, separators=",.", showlegend=fr is not None,
        height=120 + (52 if fr is not None else 34) * len(f), margin=dict(l=0, r=40, t=10, b=0),
        xaxis=dict(tickformat=".0%", range=[0, min(1.0, maximo * 1.2 + 0.03)], title="Proporção das escolas"),
        yaxis=dict(title=None, autorange="reversed"), legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0),
    )
    return fig


def _histograma(v: pd.Series, ref: pd.Series | None, var: str) -> go.Figure:
    if ref is None:
        m = medidas(v)
        fig = px.histogram(x=v, nbins=40, marginal="box")
        fig.update_traces(marker_color=AZUL, selector=dict(type="histogram"),
                          hovertemplate="%{x}<br>%{y} escolas<extra></extra>")
        fig.update_traces(marker_color=AZUL, line_color=AZUL, selector=dict(type="box"))
        linhas = [(m["Média"], "média", LARANJA, "right"), (m["Mediana"], "mediana", NEUTRO, "left")]
        eixo_y = "Escolas"
    else:
        # mesmas classes nas duas; em % das escolas, para comparar formas de tamanhos diferentes
        bordas = np.histogram_bin_edges(ref, bins=40)
        centros, largura = (bordas[:-1] + bordas[1:]) / 2, bordas[1] - bordas[0]
        pa = 100 * np.histogram(v.clip(bordas[0], bordas[-1]), bins=bordas)[0] / len(v)
        pp = 100 * np.histogram(ref, bins=bordas)[0] / len(ref)
        fig = go.Figure([
            go.Bar(x=centros, y=pa, width=largura * 0.95, name="Amostra", marker_color=AZUL,
                   hovertemplate="%{x:.1f}<br>%{y:.1f}% das escolas da amostra<extra></extra>"),
            go.Scatter(x=centros, y=pp, mode="lines", line=dict(color=LARANJA, width=2, shape="hvh"), name="População",
                       hovertemplate="%{x:.1f}<br>%{y:.1f}% das escolas da população<extra></extra>"),
        ])
        linhas = [(v.mean(), "média da amostra", AZUL, "left"), (ref.mean(), "média da população", LARANJA, "right")]
        eixo_y = "% das escolas"
    for valor, nome, cor, lado in linhas:
        fig.add_vline(x=valor, line_color=cor, line_width=2, **({"row": 1, "col": 1} if ref is None else {}),
                      annotation_text=f"{nome} {br(valor, 1)}", annotation_position=f"top {lado}",
                      annotation_font_color=cor)
    fig.update_layout(height=460, margin=dict(l=0, r=0, t=30 if ref is not None else 10, b=0), bargap=0.05,
                      showlegend=ref is not None, separators=",.", xaxis_title=rotulo(var), yaxis_title=eixo_y,
                      legend=dict(orientation="h", y=1.08, yanchor="bottom", x=0))
    return fig


def distribuicao(sel: pd.DataFrame, ref: pd.DataFrame | None = None, chave: str = "dist") -> None:
    escolha, _ = st.columns([2, 3])
    var = escolha.selectbox("Variável", list(VARIAVEIS), format_func=rotulo, key=f"{chave}_var",
                            index=list(VARIAVEIS).index("ENEM_MEDIA_GERAL"))
    col_graf, col_tab = st.columns([3, 2], gap="medium")
    if qualitativa(var):
        f = frequencias(sel[var], var)
        fr = frequencias(ref[var], var) if ref is not None else None
        col_graf.plotly_chart(_barras(f, fr), width="stretch", config={"displaylogo": False}, key=f"{chave}_graf")
        tabela = f[["Categoria", "Escolas"]].assign(Escolas=f["Escolas"].map(br))
        tabela["Amostra" if fr is not None else "Proporção"] = f["Proporção"].map(pct)
        if fr is not None:
            tabela["População"] = fr["Proporção"].map(pct)
        col_tab.markdown(f"**Frequências: {rotulo(var)}**")
        col_tab.dataframe(tabela, hide_index=True, width="stretch")
        col_tab.caption(f"{br(f['Escolas'].sum())} escolas com a informação; {br(sel[var].isna().sum())} sem a informação.")
    else:
        v = sel[var].dropna()
        r = ref[var].dropna() if ref is not None else None
        col_graf.plotly_chart(_histograma(v, r, var), width="stretch", config={"displaylogo": False}, key=f"{chave}_graf")
        m = medidas(v)
        tabela = pd.DataFrame({"Medida": list(m), ("Amostra" if r is not None else "Valor"):
                               [br(x, CASAS.get(k, 1)) for k, x in m.items()]})
        if r is not None:
            tabela["População"] = [br(x, CASAS.get(k, 1)) for k, x in medidas(r).items()]
        col_tab.markdown(f"**Medidas: {rotulo(var)}**")
        col_tab.dataframe(tabela, hide_index=True, width="stretch")
        col_tab.caption(f"{br(sel[var].isna().sum())} escolas do recorte sem a informação.")
