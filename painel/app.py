"""Painéis do trabalho de IA003: ENEM 2025 por escola, com o Censo Escolar 2025.

    streamlit run app.py

Cada painel é uma página com endereço próprio (para entregar um link por painel).
"""
import streamlit as st

st.set_page_config(page_title="ENEM por escola · IA003", page_icon=":material/school:", layout="wide")

paginas = [
    st.Page("paginas/base_de_dados.py", title="Painel 0: base de dados", icon=":material/database:",
            url_path="base-de-dados", default=True),
    st.Page("paginas/populacao.py", title="Painel 1: população", icon=":material/public:",
            url_path="populacao"),
    st.Page("paginas/amostra.py", title="Painel 2: amostra", icon=":material/casino:", url_path="amostra"),
    st.Page("paginas/inferencia_proporcoes.py", title="Painel 3a: proporções", icon=":material/percent:",
            url_path="inferencia-proporcoes"),
    st.Page("paginas/inferencia_medias.py", title="Painel 3b: médias", icon=":material/functions:",
            url_path="inferencia-medias"),
]
st.navigation(paginas).run()
