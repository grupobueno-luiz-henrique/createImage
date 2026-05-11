"""
Etapa 1 — Geração, edição e validação do XLSX
"""

from pathlib import Path
from core.service import Service

import streamlit as st
import pandas as pd

# =====================================================================
# IMPORTE AQUI SUAS FUNÇÕES JÁ EXISTENTES
# =====================================================================
# from suas_funcoes import gerar_xlsx
# =====================================================================

service = Service()

# ---------------------------------------------------------------------
# Configuração da página e caminho do arquivo em disco
# ---------------------------------------------------------------------
st.set_page_config(page_title="Etapa 1 — Geração e Validação", layout="wide")
st.title("Etapa 1 — Geração e validação do XLSX")

CAMINHO_XLSX = Path("assets/aniversariantes.xlsx")


# ---------------------------------------------------------------------
# Inicialização do session_state
# ---------------------------------------------------------------------
if "df" not in st.session_state:
    st.session_state.df = None
if "validado" not in st.session_state:
    st.session_state.validado = False


# ---------------------------------------------------------------------
# Botão para gerar o XLSX inicial
# ---------------------------------------------------------------------
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("Gerar XLSX", type="primary"):
        # =============================================================
        # >>> AQUI ENTRA SUA FUNÇÃO DE GERAR O XLSX <<<
        #
        service.run()
        caminho = Path("assets/aniversariantes.xlsx")
        df = pd.read_excel(caminho)

        # =============================================================
        # df = pd.DataFrame({
        #     "ID": [1, 2, 3],
        #     "Produto": ["A", "B", "C"],
        #     "Quantidade": [10, 20, 30],
        #     "Preço": [9.90, 19.90, 29.90],
        # })
        # =============================================================

        st.session_state.df = df
        st.session_state.validado = False
        st.rerun()


# ---------------------------------------------------------------------
# Editor + ações (só aparecem se já há um DF gerado)
# ---------------------------------------------------------------------
if st.session_state.df is not None:
    st.subheader("Edite os dados conforme necessário")

    df_editado = st.data_editor(
        st.session_state.df,
        num_rows="dynamic",
        use_container_width=True,
        key="editor",
    )
    st.session_state.df = df_editado

    st.divider()

    # -----------------------------------------------------------------
    # Linha de ações: salvar edições, validar, avançar
    # -----------------------------------------------------------------
    col_save, col_valid, col_next = st.columns([1, 1, 1])

    with col_save:
        if st.button("💾 Salvar edições"):
            CAMINHO_XLSX.parent.mkdir(parents=True, exist_ok=True)
            st.session_state.df.to_excel(CAMINHO_XLSX, index=False)
            st.success(f"Salvo em {CAMINHO_XLSX}")

    with col_valid:
        st.session_state.validado = st.checkbox(
            "Validado",
            value=st.session_state.validado,
        )

    with col_next:
        if st.button(
            "Avançar para Etapa 2",
            disabled=not st.session_state.validado,
            type="primary",
        ):
            # Garante que o arquivo em disco está atualizado antes de avançar
            CAMINHO_XLSX.parent.mkdir(parents=True, exist_ok=True)
            st.session_state.df.to_excel(CAMINHO_XLSX, index=False)
            st.session_state.df_validado = st.session_state.df.copy()
            st.success("Dados validados! Pronto para a Etapa 2.")
            # st.switch_page("pages/2_etapa2.py")  # quando criar a etapa 2

else:
    st.info("Clique em **Gerar XLSX** para começar.")

        