"""Medidas descritivas dos painéis. As mesmas funções servem à população (Painel 1) e à amostra (Painel 2)."""
import pandas as pd

from variaveis import QUALI_BINARIA, VARIAVEIS, rotulo

# Qualitativas nominais que entram na tabela-resumo (região e UF já estão no recorte geográfico)
NOMINAIS_RESUMO = ["REDE", "DEPENDENCIA", "LOCALIZACAO", "COMPOSICAO_RACIAL"]
ORDEM = {
    "REDE": ["Pública", "Privada"],
    "DEPENDENCIA": ["Federal", "Estadual", "Municipal", "Privada"],
    "LOCALIZACAO": ["Urbana", "Rural"],
    "NO_REGIAO": ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"],
    "COMPOSICAO_RACIAL": ["Maioria negra", "Maioria branca", "Sem maioria negra ou branca", "Declaração insuficiente"],
}


def qualitativa(coluna: str) -> bool:
    return VARIAVEIS[coluna][1].startswith("Qualitativa")


def binaria(coluna: str) -> bool:
    return VARIAVEIS[coluna][1] == QUALI_BINARIA


def frequencias(serie: pd.Series, coluna: str) -> pd.DataFrame:
    """Frequência absoluta e proporção de cada categoria, entre as escolas com a informação."""
    s = serie.dropna()
    if binaria(coluna):
        s, ordem = s.map({1: "Sim", 0: "Não"}), ["Sim", "Não"]
    else:
        ordem = ORDEM.get(coluna) or s.value_counts().index.tolist()
    contagem = s.value_counts().reindex(ordem, fill_value=0)
    total = contagem.sum()
    return pd.DataFrame({"Categoria": contagem.index, "Escolas": contagem.to_numpy(),
                         "Proporção": contagem.to_numpy() / total if total else float("nan")})


def resumo_qualitativas(df: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por categoria das nominais e uma linha ("Sim") por variável binária."""
    partes = []
    for col in NOMINAIS_RESUMO:
        partes.append(frequencias(df[col], col).assign(Variável=rotulo(col)))
    for col in (c for c in VARIAVEIS if binaria(c)):
        f = frequencias(df[col], col)
        partes.append(f[f["Categoria"] == "Sim"].assign(Variável=rotulo(col)))
    t = pd.concat(partes, ignore_index=True)
    return t[["Variável", "Categoria", "Escolas", "Proporção"]]


def medidas(serie: pd.Series) -> dict:
    s = serie.dropna()
    media = s.mean()
    return {
        "n": len(s), "Média": media, "Mediana": s.median(), "Desvio-padrão": s.std(),
        "Coef. de variação": s.std() / media if media else float("nan"), "Assimetria": s.skew(),
        "Mínimo": s.min(), "1º quartil": s.quantile(0.25), "3º quartil": s.quantile(0.75), "Máximo": s.max(),
    }


def resumo_quantitativas(df: pd.DataFrame) -> pd.DataFrame:
    linhas = [{"Variável": rotulo(c), **medidas(df[c])} for c in VARIAVEIS if not qualitativa(c)]
    return pd.DataFrame(linhas)
