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

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from core.service import Service


# =====================================================================
# Meses em português — usado pelo seletor de mês de referência.
# Mantido local para não acoplar a UI ao mural/config.py.
# =====================================================================
MESES_PT = (
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
)


# =====================================================================
# Caminhos — sempre relativos ao próprio arquivo, para funcionar mesmo
# se o Streamlit não for iniciado a partir da raiz do projeto.
# =====================================================================
_UI_DIR = Path(__file__).resolve().parent.parent
_ARQUIVOS = _UI_DIR / "arquivos"
_PROJECT_ROOT = _UI_DIR.parent

CAMINHO_TRABALHO = _ARQUIVOS / "dados.xlsx"               # rascunho
CAMINHO_VALIDADO = _ARQUIVOS / "dados_validado.xlsx"      # XLSX final p/ Etapa 2
META_VALIDADO = _ARQUIVOS / "dados_validado.json"         # metadados (mês/ano)
FLAG_VALIDADO = _ARQUIVOS / ".validado"                   # sinaliza p/ Etapa 2
PLANILHA_INICIAL = _PROJECT_ROOT / "assets" / "aniversariantes.xlsx"


# =====================================================================
# Helpers — lógica pura, sem widgets de Streamlit, mais fácil de testar.
# =====================================================================
@st.cache_resource(show_spinner=False)
def _service() -> Service:
    """Mantém uma única instância do Service entre reruns da página."""
    return Service()


def _gerar_planilha_inicial(mes: int) -> pd.DataFrame:
    """Roda o Service para o ``mes`` escolhido e devolve a planilha gerada."""
    _service().run(mes)
    return pd.read_excel(PLANILHA_INICIAL)


def _salvar_xlsx(df: pd.DataFrame, destino: Path) -> None:
    """Grava ``df`` em ``destino``, criando a pasta se necessário."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(destino, index=False)


# =====================================================================
# Cabeçalho — contexto do papel (equipe GG).
# =====================================================================
st.title("Etapa 1 — Validação (Equipe GG)")
st.caption(
    "Gere a lista do mês, confira nomes/dias/cargos e libere para o Marketing."
)
st.divider()


# =====================================================================
# Estado inicial da página
# =====================================================================
_mes_default = (datetime.now().month % 12) + 1  # mês seguinte, casa com a query atual

st.session_state.setdefault("df", None)
st.session_state.setdefault("validado", False)
st.session_state.setdefault("enviado", False)
st.session_state.setdefault("mes_selecionado", _mes_default)


# ---------------------------------------------------------------------
# Passo 1 — escolher o mês de referência e gerar a planilha do banco.
# O int 1..12 do mês escolhido fica em st.session_state["mes_selecionado"]
# para ser consumido pela lógica da query (a ser plugada depois).
# ---------------------------------------------------------------------
with st.container(border=True):
    st.subheader("1. Mês de referência")
    col_mes, col_btn, _ = st.columns([1, 1, 2], vertical_alignment="bottom")

    with col_mes:
        mes_nome = st.selectbox(
            "Mês",
            MESES_PT,
            index=st.session_state["mes_selecionado"] - 1,
            key="mes_nome",
        )
        st.session_state["mes_selecionado"] = MESES_PT.index(mes_nome) + 1

    with col_btn:
        if st.button("Gerar planilha", type="primary", use_container_width=True):
            with st.spinner("Consultando banco e gerando planilha..."):
                try:
                    st.session_state.df = _gerar_planilha_inicial(
                        st.session_state["mes_selecionado"]
                    )
                    st.session_state.validado = False
                    st.session_state.enviado = False
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao gerar planilha: {e}")


# ---------------------------------------------------------------------
# Empty state — antes de gerar a primeira planilha.
# ---------------------------------------------------------------------
if st.session_state.df is None:
    with st.container(border=True):
        st.markdown("#### Nenhuma planilha gerada ainda")
        st.caption(
            "Escolha o mês acima e clique em **Gerar planilha** para começar."
        )
    st.stop()


# ---------------------------------------------------------------------
# Passo 2 — conferir a lista (KPIs + editor de dados).
# O retorno de st.data_editor é o DataFrame já com as edições aplicadas.
# ---------------------------------------------------------------------
with st.container(border=True):
    st.subheader("2. Conferir lista")

    k1, k2, k3 = st.columns(3)
    k1.metric(
        "Mês de referência",
        MESES_PT[st.session_state["mes_selecionado"] - 1].title(),
    )
    k2.metric("Aniversariantes", len(st.session_state.df))

    st.session_state.df = st.data_editor(
        st.session_state.df,
        num_rows="dynamic",
        use_container_width=True,
        key="editor",
    )


# ---------------------------------------------------------------------
# Passo 3 — salvar rascunho, confirmar conferência e enviar p/ Marketing.
# ---------------------------------------------------------------------
with st.container(border=True):
    st.subheader("3. Liberar para a criação da arte")
    col_save, col_valid, col_send = st.columns(
        [1, 1, 2], vertical_alignment="center"
    )

    with col_save:
        if st.button("Salvar rascunho", use_container_width=True):
            _salvar_xlsx(st.session_state.df, CAMINHO_TRABALHO)
            st.toast("Rascunho salvo.", icon="💾")

    with col_valid:
        st.session_state.validado = st.checkbox(
            "Confirmo que conferi a lista",
            value=st.session_state.validado,
        )

    with col_send:
        if st.button(
            "Enviar para a criação da arte",
            disabled=not st.session_state.validado,
            type="primary",
            use_container_width=True,
        ):
            _salvar_xlsx(st.session_state.df, CAMINHO_VALIDADO)
            META_VALIDADO.write_text(
                json.dumps(
                    {
                        "mes": int(st.session_state["mes_selecionado"]),
                        "ano": datetime.now().year,
                    }
                ),
                encoding="utf-8",
            )
            FLAG_VALIDADO.touch()
            st.session_state.enviado = True
            st.rerun()

    if st.session_state.get("enviado"):
        st.success(
            "Planilha liberada para a ciração da arte. "
            "A equipe da Etapa 2 já pode gerar a arte."
        )
