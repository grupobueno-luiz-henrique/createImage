import streamlit as st

st.set_page_config(
    page_title="Mural de Aniversariantes",
    page_icon="🎂",
    layout="wide",
)

with st.sidebar:
    st.markdown("### Mural de Aniversariantes")
    st.caption("Fluxo do processo")
    st.markdown(
        "**1. GG (Etapa 1)** — gera e valida a planilha do mês.\n\n"
        "**2. Marketing (Etapa 2)** — recebe a planilha validada e gera a arte."
    )
    st.divider()
    st.caption("Dica: use o menu acima para alternar entre as etapas.")

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
