"""Painel 1: análise descritiva da população."""
import streamlit as st

from componentes import distribuicao, escolher_recorte, indicadores, mapa, tabela_resumo
from dados_painel import br, populacao, resumo

pop = populacao()
info = resumo()

st.title("Painel 1: análise descritiva da população")
st.caption(
    f"{br(len(pop))} escolas em atividade, com ensino médio presencial e pelo menos 10 participantes do ENEM 2025 "
    "com as cinco notas. Fontes: INEP, Censo Escolar 2025 e microdados do ENEM 2025."
)

rec = escolher_recorte(pop, "p1")
sel = rec.selecao(pop)
indicadores(sel)

col_mapa, col_tabela = st.columns([3, 2], gap="medium")
with col_mapa:
    mapa("populacao", rec, info["municipios_sem_poligono"])
with col_tabela:
    tabela_resumo(sel, chave="p1")

st.subheader("Distribuição de cada variável")
distribuicao(sel, chave="p1")
st.caption(f"Recorte: {rec.nome} ({br(len(sel))} escolas).")
