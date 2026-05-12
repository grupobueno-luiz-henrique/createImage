"""
Etapa 1 — Geração, edição e validação do XLSX.

Fluxo da página (de cima para baixo):
    1. "Gerar XLSX"           → Service.run() consulta o banco, aplica o
                                 mapeamento de cargos e grava
                                 assets/aniversariantes.xlsx. O DataFrame
                                 resultante vai para o session_state.
    2. data_editor             → o usuário ajusta nomes/dias/cargos.
    3. "Salvar edições"        → escreve um rascunho em
                                 UI/arquivos/dados.xlsx (não dispara Etapa 2).
    4. checkbox "Validado"     → libera o botão de envio.
    5. "Enviar para Etapa 2"   → grava UI/arquivos/dados_validado.xlsx e
                                 toca a flag UI/arquivos/.validado, que é
                                 o sinal consumido pela Etapa 2.
"""

from pathlib import Path

import pandas as pd
import streamlit as st

from core.service import Service


# =====================================================================
# Caminhos — sempre relativos ao próprio arquivo, para funcionar mesmo
# se o Streamlit não for iniciado a partir da raiz do projeto.
# =====================================================================
_UI_DIR = Path(__file__).resolve().parent.parent
_ARQUIVOS = _UI_DIR / "arquivos"
_PROJECT_ROOT = _UI_DIR.parent

CAMINHO_TRABALHO = _ARQUIVOS / "dados.xlsx"               # rascunho
CAMINHO_VALIDADO = _ARQUIVOS / "dados_validado.xlsx"      # XLSX final p/ Etapa 2
FLAG_VALIDADO = _ARQUIVOS / ".validado"                   # sinaliza p/ Etapa 2
PLANILHA_INICIAL = _PROJECT_ROOT / "assets" / "aniversariantes.xlsx"


# =====================================================================
# Helpers — lógica pura, sem widgets de Streamlit, mais fácil de testar.
# =====================================================================
@st.cache_resource(show_spinner=False)
def _service() -> Service:
    """Mantém uma única instância do Service entre reruns da página."""
    return Service()


def _gerar_planilha_inicial() -> pd.DataFrame:
    """Roda o Service e devolve a planilha recém-gerada como DataFrame."""
    _service().run()
    return pd.read_excel(PLANILHA_INICIAL)


def _salvar_xlsx(df: pd.DataFrame, destino: Path) -> None:
    """Grava ``df`` em ``destino``, criando a pasta se necessário."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(destino, index=False)


# =====================================================================
# Estado inicial da página
# =====================================================================
st.title("📝 Gerar planilha de aniversariantes")

st.session_state.setdefault("df", None)
st.session_state.setdefault("validado", False)


# ---------------------------------------------------------------------
# Passo 1 — gerar a planilha inicial a partir do banco.
# ---------------------------------------------------------------------
col_btn, _ = st.columns([1, 3])
with col_btn:
    if st.button("Gerar planilha 🥳", type="primary"):
        with st.spinner("Consultando banco e gerando planilha..."):
            try:
                st.session_state.df = _gerar_planilha_inicial()
                st.session_state.validado = False
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao gerar planilha: {e}")


if st.session_state.df is None:
    st.info("Clique em **Gerar planilha 🥳** para começar.")
    st.stop()


# ---------------------------------------------------------------------
# Passo 2 — editor de dados em tela.
# O retorno de st.data_editor é o DataFrame já com as edições aplicadas.
# ---------------------------------------------------------------------
st.subheader("Edite os dados conforme necessário")
st.session_state.df = st.data_editor(
    st.session_state.df,
    num_rows="dynamic",
    use_container_width=True,
    key="editor",
)

st.divider()


# ---------------------------------------------------------------------
# Passos 3, 4 e 5 — salvar rascunho, marcar como validado e enviar.
# ---------------------------------------------------------------------
col_save, col_valid, col_send = st.columns(3, gap="xxlarge")

with col_save:
    if st.button("💾 Salvar edições"):
        _salvar_xlsx(st.session_state.df, CAMINHO_TRABALHO)
        st.success("Rascunho salvo.")

with col_valid:
    st.session_state.validado = st.checkbox(
        "Validado",
        value=st.session_state.validado,
    )

with col_send:
    if st.button(
        "✅ Enviar para Etapa 2",
        disabled=not st.session_state.validado,
        type="primary",
    ):
        _salvar_xlsx(st.session_state.df, CAMINHO_VALIDADO)
        FLAG_VALIDADO.touch()
        st.success(
            "Planilha validada enviada para a Etapa 2! "
            "A outra equipe já pode acessar."
        )
