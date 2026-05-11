"""
App principal — página inicial.
As páginas das etapas aparecem automaticamente na sidebar
porque estão na pasta `pages/`.
"""

import streamlit as st

st.set_page_config(
    page_title="Gerador de Apresentações",
    layout="wide",
)

st.title("Gerador de Aniversariantes")

st.markdown(
    """
    Bem-vindo! Este app tem duas etapas, navegue pela **sidebar**:

    - **Etapa 1 — Geração e Validação**
      Gera o XLSX, permite edição e validação dos dados.

    - **Etapa 2 — Geração de PNG e PPTX**
      Após a Etapa 1 ser validada, gera os arquivos finais.
    """
)