"""Monta a base do painel: uma linha por escola da população, com Censo Escolar 2025 + ENEM 2025.

População (ver DECISOES_METODOLOGICAS.md): escolas em atividade, com matrícula presencial no
ensino médio regular e pelo menos 10 participantes do ENEM 2025 com as cinco notas.

Entrada: os microdados extraídos em ../dados (fora do git); as malhas do IBGE são baixadas na
         primeira execução para ../dados/ibge.
Saída:   em dados/ (pequenos, vão para o git): escolas_populacao.parquet, municipios.parquet,
         funil_populacao.json e as malhas processadas em malha_ibge/.

    python preparar_dados.py
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
BRUTOS = AQUI.parent / "dados"
CENSO = BRUTOS / "microdados_censo_escolar_2025_v2" / "dados"
ENEM = BRUTOS / "microdados_enem_2025" / "DADOS" / "RESULTADOS_2025.csv"
IBGE = BRUTOS / "ibge"
SAIDA = AQUI / "dados"
URL_MALHA = ("https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo%2Bjson"
             "&qualidade={qualidade}&intrarregiao={nivel}")
MALHAS = {"uf": ("UF", "intermediaria"), "municipios": ("municipio", "minima")}  # saída: (nível, qualidade)

MIN_PARTICIPANTES = 10
LIMITE_NAO_DECLARADA = 50  # % máximo de matrículas sem cor/raça para classificar a composição racial
NOTAS = {"NU_NOTA_CN": "CN", "NU_NOTA_CH": "CH", "NU_NOTA_LC": "LC", "NU_NOTA_MT": "MT", "NU_NOTA_REDACAO": "REDACAO"}

COLS_ESCOLA = [
    "CO_ENTIDADE", "NO_ENTIDADE", "NO_REGIAO", "SG_UF", "NO_MUNICIPIO", "CO_MUNICIPIO",
    "TP_SITUACAO_FUNCIONAMENTO", "TP_DEPENDENCIA", "CO_REDE", "TP_LOCALIZACAO",
    "IN_INTERNET_ALUNOS", "IN_BIBLIOTECA_SALA_LEITURA", "IN_LABORATORIO_CIENCIAS", "IN_LABORATORIO_INFORMATICA",
    "IN_QUADRA_ESPORTES", "IN_ESGOTO_REDE_PUBLICA", "IN_BANHEIRO_PNE", "IN_ACESSIBILIDADE_INEXISTENTE",
    "IN_ORGAO_GREMIO_ESTUDANTIL", "IN_EXAME_SELECAO", "QT_PROF_PSICOLOGO", "QT_SALAS_UTILIZADAS",
]
COLS_MATRICULA = [
    "CO_ENTIDADE", "QT_MAT_BAS", "QT_MAT_MED", "QT_MAT_MED_3", "QT_MAT_MED_EAD", "QT_MAT_MED_INT",
    "QT_MAT_BAS_FEM", "QT_MAT_BAS_MASC",
    "QT_MAT_BAS_BRANCA", "QT_MAT_BAS_PRETA", "QT_MAT_BAS_PARDA", "QT_MAT_BAS_AMARELA", "QT_MAT_BAS_INDIGENA", "QT_MAT_BAS_ND",
]
COLS_DOCENTE = ["CO_ENTIDADE", "QT_DOC_BAS", "QT_DOC_BAS_ESCO_SUP_GRAD"]


def ler_censo(arquivo: str, colunas: list[str]) -> pd.DataFrame:
    return pd.read_csv(CENSO / arquivo, sep=";", encoding="latin-1", usecols=colunas, low_memory=False)


def dimensoes(caminho: Path, linhas: int) -> dict:
    colunas = len(pd.read_csv(caminho, sep=";", encoding="latin-1", nrows=0).columns)
    return {"arquivo": caminho.name, "linhas": int(linhas), "colunas": colunas}


def enem_por_escola() -> tuple[pd.DataFrame, dict]:
    r = pd.read_csv(ENEM, sep=";", encoding="latin-1", usecols=["CO_ESCOLA", *NOTAS])
    dim = dimensoes(ENEM, len(r))
    r = r[r["CO_ESCOLA"].notna()].rename(columns=NOTAS)
    completo = r[list(NOTAS.values())].notna().all(axis=1)
    r["GERAL"] = r[list(NOTAS.values())].mean(axis=1)
    validos = r[completo]
    agg = validos.groupby("CO_ESCOLA").agg(
        ENEM_COM_NOTAS=("GERAL", "size"),
        **{f"ENEM_MEDIA_{k}": (k, "mean") for k in ["GERAL", *NOTAS.values()]},
    )
    agg["ENEM_PARTICIPANTES"] = r.groupby("CO_ESCOLA").size()
    agg.index = agg.index.astype("int64")
    agg.index.name = "CO_ENTIDADE"
    return agg.reset_index(), dim


def _area(anel: list) -> float:
    return sum(x0 * y1 - x1 * y0 for (x0, y0, *_), (x1, y1, *_) in zip(anel, anel[1:])) / 2


def _anel(anel: list, externo: bool, casas: int = 3) -> list:
    r = [[round(x, casas), round(y, casas)] for x, y, *_ in anel]  # ~100 m: basta para o mapa
    r = [pt for i, pt in enumerate(r) if i == 0 or pt != r[i - 1]]
    if len(r) < 4:  # anel pequeno demais para arredondar
        r = [[x, y] for x, y, *_ in anel]
    # O IBGE segue o GeoJSON (anel externo anti-horário). O mapa do Plotly (d3-geo) quer o externo
    # horário e, se não for, pinta o complemento do polígono.
    return r[::-1] if (_area(r) > 0) == externo else r


def preparar_malha(nome: str) -> set[str]:
    nivel, qualidade = MALHAS[nome]
    bruta = IBGE / f"malha_{nivel.lower()}_{qualidade}.geojson"
    if not bruta.exists():
        IBGE.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(URL_MALHA.format(qualidade=qualidade, nivel=nivel), bruta)
    malha = json.loads(bruta.read_text(encoding="utf-8"))
    for f in malha["features"]:
        g = f["geometry"]
        poligonos = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        poligonos = [[_anel(a, i == 0) for i, a in enumerate(p)] for p in poligonos]
        g["coordinates"] = poligonos[0] if g["type"] == "Polygon" else poligonos
    (SAIDA / "malha_ibge").mkdir(parents=True, exist_ok=True)
    (SAIDA / "malha_ibge" / f"{nome}.geojson").write_text(json.dumps(malha, separators=(",", ":")))
    return {f["properties"]["codarea"] for f in malha["features"]}


def main() -> None:
    escola = ler_censo("Tabela_Escola_2025_V2.csv", COLS_ESCOLA)
    matricula = ler_censo("Tabela_Matricula_2025_V2.csv", COLS_MATRICULA)
    docente = ler_censo("Tabela_Docente_2025_V2.csv", COLS_DOCENTE)
    enem, dim_enem = enem_por_escola()
    fontes = {
        "censo_escola": dimensoes(CENSO / "Tabela_Escola_2025_V2.csv", len(escola)),
        "censo_matricula": dimensoes(CENSO / "Tabela_Matricula_2025_V2.csv", len(matricula)),
        "censo_docente": dimensoes(CENSO / "Tabela_Docente_2025_V2.csv", len(docente)),
        "enem_resultados": dim_enem,
    }

    base = escola.merge(matricula, on="CO_ENTIDADE", how="left").merge(docente, on="CO_ENTIDADE", how="left")
    base = base.merge(enem, on="CO_ENTIDADE", how="left")

    ativa = base["TP_SITUACAO_FUNCIONAMENTO"] == 1
    com_em = ativa & (base["QT_MAT_MED"] > 0)
    em_presencial = com_em & ((base["QT_MAT_MED"] - base["QT_MAT_MED_EAD"].fillna(0)) > 0)
    no_enem = em_presencial & (base["ENEM_COM_NOTAS"].fillna(0) >= MIN_PARTICIPANTES)
    funil = {
        "Escolas no cadastro do Censo 2025": int(len(base)),
        "Em atividade": int(ativa.sum()),
        "Com matrícula no ensino médio regular": int(com_em.sum()),
        "Com matrícula presencial no ensino médio": int(em_presencial.sum()),
        f"Com pelo menos {MIN_PARTICIPANTES} participantes do ENEM 2025 com as cinco notas (população)": int(no_enem.sum()),
    }
    pop = base[no_enem].copy()

    # códigos especiais do Censo: 9 = não informado nos indicadores, 88888 = valor extremo (viram faltantes)
    indicadores = [c for c in pop.columns if c.startswith("IN_")]
    pop[indicadores] = pop[indicadores].mask(pop[indicadores] == 9)
    pop["QT_PROF_PSICOLOGO"] = pop["QT_PROF_PSICOLOGO"].mask(pop["QT_PROF_PSICOLOGO"] == 88888)
    pop["TEM_PSICOLOGO"] = (pop["QT_PROF_PSICOLOGO"] > 0).astype(float).where(pop["QT_PROF_PSICOLOGO"].notna())

    # composição por cor/raça das matrículas da escola (entre quem declarou)
    racas = ["BRANCA", "PRETA", "PARDA", "AMARELA", "INDIGENA"]
    declarados = pop[[f"QT_MAT_BAS_{r}" for r in racas]].sum(axis=1)
    for r in racas:
        pop[f"PCT_{r}"] = 100 * pop[f"QT_MAT_BAS_{r}"] / declarados.where(declarados > 0)
    pop["PCT_PPI"] = pop[["PCT_PRETA", "PCT_PARDA", "PCT_INDIGENA"]].sum(axis=1, min_count=1)
    pop["PCT_NEGRA"] = pop[["PCT_PRETA", "PCT_PARDA"]].sum(axis=1, min_count=1)  # pretos + pardos (IBGE)
    pop["PCT_COR_NAO_DECLARADA"] = 100 * pop["QT_MAT_BAS_ND"] / pop["QT_MAT_BAS"]
    # composição racial: só com ao menos metade das matrículas com cor/raça declarada (D12)
    declarada = pop["PCT_COR_NAO_DECLARADA"] <= LIMITE_NAO_DECLARADA
    pop["COMPOSICAO_RACIAL"] = np.select(
        [~declarada, pop["PCT_NEGRA"] > 50, pop["PCT_BRANCA"] > 50],
        ["Declaração insuficiente", "Maioria negra", "Maioria branca"], default="Sem maioria negra ou branca")
    pop["PCT_FEMININO"] = 100 * pop["QT_MAT_BAS_FEM"] / pop["QT_MAT_BAS"]
    pop["PCT_DOC_SUPERIOR"] = 100 * pop["QT_DOC_BAS_ESCO_SUP_GRAD"] / pop["QT_DOC_BAS"].where(pop["QT_DOC_BAS"] > 0)
    pop["TAXA_PARTICIPACAO_ENEM"] = pop["ENEM_PARTICIPANTES"] / pop["QT_MAT_MED_3"].where(pop["QT_MAT_MED_3"] > 0)

    pop["DEPENDENCIA"] = pop["TP_DEPENDENCIA"].map({1: "Federal", 2: "Estadual", 3: "Municipal", 4: "Privada"})
    pop["REDE"] = pop["CO_REDE"].map({1: "Pública", 2: "Privada"})
    pop["LOCALIZACAO"] = pop["TP_LOCALIZACAO"].map({1: "Urbana", 2: "Rural"})

    # mapa: território dos municípios (malha do IBGE); o Censo 2025 não traz as coordenadas das escolas
    SAIDA.mkdir(parents=True, exist_ok=True)
    preparar_malha("uf")
    com_poligono = preparar_malha("municipios")
    municipios = (escola[["CO_MUNICIPIO", "NO_MUNICIPIO", "SG_UF", "NO_REGIAO"]]
                  .drop_duplicates("CO_MUNICIPIO").sort_values("CO_MUNICIPIO").reset_index(drop=True))
    municipios.to_parquet(SAIDA / "municipios.parquet", index=False)
    sem_poligono = (pop[~pop["CO_MUNICIPIO"].astype(str).isin(com_poligono)]
                    .groupby(["CO_MUNICIPIO", "NO_MUNICIPIO", "SG_UF"]).size().rename("escolas").reset_index())

    pop = pop.drop(columns=["TP_SITUACAO_FUNCIONAMENTO"]).sort_values("CO_ENTIDADE").reset_index(drop=True)
    for c in pop.columns:  # inteiros com faltantes ficam como float; os completos voltam a int
        if pop[c].dtype == float and pop[c].notna().all() and np.allclose(pop[c], pop[c].round()) and c.startswith(("QT_", "IN_", "ENEM_COM", "ENEM_PART")):
            pop[c] = pop[c].astype("int64")

    pop.to_parquet(SAIDA / "escolas_populacao.parquet", index=False)
    resumo = {"fontes": fontes, "funil": funil, "municipios": int(pop["CO_MUNICIPIO"].nunique()),
              "municipios_sem_poligono": sem_poligono.to_dict("records"),
              "participantes_enem_com_notas_na_populacao": int(pop["ENEM_COM_NOTAS"].sum())}
    (SAIDA / "funil_populacao.json").write_text(json.dumps(resumo, indent=1, ensure_ascii=False))
    print(json.dumps(resumo, indent=1, ensure_ascii=False))
    print(f"{len(pop):,} escolas x {pop.shape[1]} colunas -> {SAIDA / 'escolas_populacao.parquet'}")


if __name__ == "__main__":
    main()
