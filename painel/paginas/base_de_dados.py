"""Painel 0: escolha e descrição da base de dados (item 2 do enunciado)."""
import pandas as pd
import streamlit as st

from dados_painel import br, populacao, resumo
from variaveis import VARIAVEIS

pop = populacao()
info = resumo()
fontes = info["fontes"]
N = len(pop)

st.title("Painel 0: a base de dados")
st.markdown(
    "Desempenho das escolas de ensino médio no **ENEM 2025**, ligado às características das escolas no "
    "**Censo Escolar 2025**. A unidade de análise é a escola."
)

# --- 1. Fonte e acesso -------------------------------------------------------------------------
st.header("Fonte e acesso")
st.markdown(
    """
| Base | Fonte | Acesso |
|---|---|---|
| Censo Escolar da Educação Básica 2025 (microdados, versão 2, julho de 2026) | INEP, Ministério da Educação | [gov.br/inep: microdados do Censo Escolar](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar) |
| ENEM 2025 (microdados) | INEP, Ministério da Educação | [gov.br/inep: microdados do ENEM](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem) |
"""
)

# --- 2. Contexto e objetivo --------------------------------------------------------------------
st.header("Contexto e objetivo")
col1, col2 = st.columns(2, gap="large")
with col1:
    st.markdown(
        """
**Censo Escolar.** Levantamento anual do INEP, feito com as secretarias estaduais e municipais de
educação, que cobre todas as escolas públicas e privadas de educação básica do país: infraestrutura,
matrículas, turmas, docentes e gestores. É a principal fonte de estatísticas da educação básica e
orienta a distribuição de recursos, como o Fundeb, e programas como os de alimentação escolar e livro
didático. Desde a adequação à LGPD, os microdados são publicados por escola, sem registros de alunos.
"""
    )
with col2:
    st.markdown(
        """
**ENEM.** Exame Nacional do Ensino Médio, aplicado pelo INEP a quem conclui ou já concluiu o ensino
médio, com participação voluntária. Tem quatro provas objetivas (ciências da natureza, ciências
humanas, linguagens e matemática) e uma redação. As notas dão acesso ao ensino superior (Sisu, Prouni,
Fies). O arquivo de resultados traz o código da escola de conclusão do ensino médio de cada
participante.
"""
    )
st.markdown(
    """
**Objetivo deste trabalho.** Descrever as escolas de ensino médio pelo desempenho médio dos seus
alunos no ENEM e pelas suas características no Censo (rede, localização, infraestrutura, composição
por cor/raça), e comparar os parâmetros calculados com a população inteira com as estimativas obtidas
de uma amostra aleatória simples.

**Ligação entre as bases.** O código da escola no ENEM (`CO_ESCOLA`) é o código da escola no Censo
(`CO_ENTIDADE`). Nas escolas ligadas, a dependência administrativa informada pelas duas bases coincide
em todos os casos. Escolas com menos de 10 participantes têm o código mascarado no ENEM e não se
ligam. O questionário socioeconômico do ENEM não tem o código da escola, por isso o perfil por
cor/raça vem do Censo.
"""
)

# --- 3. Observações e variáveis ----------------------------------------------------------------
st.header("Observações e variáveis")
tamanhos = pd.DataFrame([
    ("Censo Escolar 2025", fontes["censo_escola"]["arquivo"], "escola (cadastro e infraestrutura)",
     fontes["censo_escola"]["linhas"], fontes["censo_escola"]["colunas"]),
    ("Censo Escolar 2025", fontes["censo_matricula"]["arquivo"], "escola (matrículas por etapa, cor/raça, sexo…)",
     fontes["censo_matricula"]["linhas"], fontes["censo_matricula"]["colunas"]),
    ("Censo Escolar 2025", fontes["censo_docente"]["arquivo"], "escola (docentes por formação, vínculo…)",
     fontes["censo_docente"]["linhas"], fontes["censo_docente"]["colunas"]),
    ("ENEM 2025", fontes["enem_resultados"]["arquivo"], "participante (notas e escola)",
     fontes["enem_resultados"]["linhas"], fontes["enem_resultados"]["colunas"]),
    ("Base de análise", "escolas_populacao.parquet", "escola da população", N, len(VARIAVEIS)),
], columns=["Base", "Arquivo", "Uma linha por", "Observações", "Variáveis"])
for c in ["Observações", "Variáveis"]:
    tamanhos[c] = tamanhos[c].map(br)
st.dataframe(tamanhos, hide_index=True, width="stretch")
st.caption(
    "A base de análise junta as três tabelas do Censo (pelo código da escola) às médias do ENEM calculadas "
    "por escola. Nela, \"variáveis\" conta só as variáveis de análise listadas abaixo."
)

# --- 4. População e unidade amostral -----------------------------------------------------------
st.header("População e unidade amostral")
st.markdown(
    f"""
- **População de interesse:** as **{br(N)} escolas** brasileiras em atividade em 2025, com matrícula
  presencial no ensino médio regular e pelo menos 10 participantes do ENEM 2025 com as cinco notas.
- **Unidade amostral:** a escola, identificada pelo código do INEP (`CO_ENTIDADE`). A lista dessas
  {br(N)} escolas é o cadastro de onde sai a amostra aleatória simples.
"""
)
funil = pd.DataFrame(list(info["funil"].items()), columns=["Etapa", "Escolas"])
funil["Escolas"] = funil["Escolas"].map(br)
st.dataframe(funil, hide_index=True, width="content")
st.caption(
    "Ensino médio presencial: ao menos uma matrícula no ensino médio regular fora da educação a distância. "
    "Cinco notas: ciências da natureza, ciências humanas, linguagens, matemática e redação "
    "(participante presente nos dois dias)."
)

# --- 5. Variáveis selecionadas -----------------------------------------------------------------
st.header("Variáveis selecionadas")


def tabela_variaveis(qualitativas: bool) -> pd.DataFrame:
    linhas = []
    for col, (rot, tipo, fonte, desc) in VARIAVEIS.items():
        if tipo.startswith("Qualitativa") != qualitativas:
            continue
        linhas.append({"Variável": rot, "Descrição": desc, "Tipo": tipo, "Fonte": fonte, "Coluna": col,
                       "Faltantes": br(pop[col].isna().sum())})
    return pd.DataFrame(linhas).set_index("Variável")


aba_quali, aba_quanti = st.tabs(["Qualitativas (proporções)", "Quantitativas (médias)"])
with aba_quali:
    st.table(tabela_variaveis(True))
with aba_quanti:
    st.table(tabela_variaveis(False))
st.caption("Definições completas e justificativas em DECISOES_METODOLOGICAS.md, no repositório do trabalho.")
