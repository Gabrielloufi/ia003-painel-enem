"""Leitura da base do painel (gerada por preparar_dados.py) e constantes visuais compartilhadas."""
import json
import math
from pathlib import Path

import pandas as pd
import streamlit as st

DADOS = Path(__file__).resolve().parent / "dados"

# Cores que funcionam nos temas claro e escuro do Streamlit (o tema não chega com segurança ao script)
AZUL = "#2a78d6"  # série única
LARANJA = "#eb6834"  # destaque (município escolhido, linha da média)
VERDE_AGUA = "#1baf7a"  # segundo grupo nas comparações (o laranja fica para "população")
NEUTRO = "rgba(128, 128, 128, 0.95)"  # linha da mediana
UF_CONTORNO = "rgba(128, 128, 128, 0.85)"
MUN_CONTORNO = "rgba(128, 128, 128, 0.30)"
SEM_ESCOLA = "rgba(128, 128, 128, 0.12)"
# Rampa sequencial de um matiz, do claro ao escuro, para faixas ordinais
RAMPA_AZUL = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"]


@st.cache_data
def populacao() -> pd.DataFrame:
    return pd.read_parquet(DADOS / "escolas_populacao.parquet")


@st.cache_data
def amostra() -> pd.DataFrame:
    """As escolas sorteadas (sortear_amostra.py), com as mesmas colunas da população, na ordem do sorteio."""
    sorteio = pd.read_csv(DADOS / "amostra.csv")
    return sorteio.merge(populacao(), on="CO_ENTIDADE", how="left", validate="one_to_one")


@st.cache_data
def parametros_amostra() -> dict:
    return json.loads((DADOS / "amostra.json").read_text(encoding="utf-8"))


@st.cache_data
def municipios() -> pd.DataFrame:
    """Todos os municípios do Censo 2025: código IBGE, nome, UF e região."""
    return pd.read_parquet(DADOS / "municipios.parquet")


@st.cache_data
def malha(nome: str) -> dict:
    """Malha do IBGE já preparada para o Plotly (`uf` ou `municipios`); `codarea` = código IBGE."""
    return json.loads((DADOS / "malha_ibge" / f"{nome}.geojson").read_text(encoding="utf-8"))


@st.cache_data
def resumo() -> dict:
    return json.loads((DADOS / "funil_populacao.json").read_text(encoding="utf-8"))


def br(x: float, casas: int = 0) -> str:
    """Número no formato brasileiro: 1.234,5 (traço quando não há valor)."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(p: float, casas: int = 1) -> str:
    """Proporção (0 a 1) como percentual brasileiro: 0,435 -> 43,5%."""
    return "–" if p is None or math.isnan(p) else f"{br(100 * p, casas)}%"


def tex(x: float, casas: int = 2) -> str:
    """Número brasileiro dentro do LaTeX (a vírgula decimal vai entre chaves para não ganhar espaço)."""
    return br(x, casas).replace(",", "{,}")


def valor_p_txt(p: float) -> str:
    return "< 0,0001" if p < 0.0001 else br(p, 4)


def valor_p_tex(p: float) -> str:
    if p >= 0.0001:
        return tex(p, 4)
    mantissa, expoente = f"{p:.1e}".split("e")
    return rf"{mantissa.replace('.', '{,}')} \times 10^{{{int(expoente)}}}"
