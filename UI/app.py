import streamlit as st

st.set_page_config(
    page_title="Gerador de Aniversariantes",
    layout="wide",
)

pg = st.navigation(
    [
        st.Page(
            "pages/etapa1.py",
            title="Etapa 1 — Validação",
            icon="📝",
            default=True,
        ),
        st.Page(
            "pages/etapa2.py",
            title="Etapa 2 — PNG e PPTX",
            icon="🖼️",
        ),
    ]
)
pg.run()
