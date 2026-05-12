"""
Etapa 2 — Geração de PNG e PPTX a partir da planilha validada.

Fluxo da página (de cima para baixo):
    1. Guarda de entrada    → exige UI/arquivos/dados_validado.xlsx e a
                              flag .validado. Sem isso a página para com
                              um aviso ("aguarde a Etapa 1").
    2. Preview da planilha  → carrega o XLSX validado e exibe num expander.
    3. "Gerar PNG e PPTX"   → roda a pipeline do pacote ``mural``:
                              planilha → layout → render_pillow (PNG)
                                                → render_pptx (PPTX).
                              Os bytes resultantes ficam no session_state.
    4. Pré-visualização     → mostra o PNG e oferece o download do PPTX.
"""

from pathlib import Path
import os

import mural.config as cfg
import pandas as pd
import streamlit as st
from PIL import Image

from mural.layout import calcular_layout, carregar_fontes_pillow
from mural.planilha import carregar_aniversariantes
from mural.render_pillow import renderizar_png
from mural.render_pptx import exportar_pptx


# =====================================================================
# Caminhos — relativos ao próprio arquivo. ``mural.config`` usa caminhos
# relativos à raiz do projeto; _resolve_projeto cuida disso.
# =====================================================================
_UI_DIR = Path(__file__).resolve().parent.parent
_ARQUIVOS = _UI_DIR / "arquivos"
_PROJECT_ROOT = _UI_DIR.parent

CAMINHO_VALIDADO = _ARQUIVOS / "dados_validado.xlsx"
FLAG_VALIDADO = _ARQUIVOS / ".validado"


def _resolve_projeto(caminho: Path) -> Path:
    """Resolve caminhos relativos contra a raiz do projeto."""
    return caminho if caminho.is_absolute() else (_PROJECT_ROOT / caminho).resolve()


# =====================================================================
# Helpers — lógica pura, fora dos blocos de widget.
# =====================================================================
@st.cache_data(show_spinner=False)
def _carregar_preview(caminho_xlsx: Path, mtime: float) -> pd.DataFrame:
    """Lê o XLSX validado para exibir o preview.

    ``mtime`` faz parte da chave do cache: se a Etapa 1 reenviar uma
    planilha nova, o cache é invalidado automaticamente.
    """
    return pd.read_excel(caminho_xlsx)


def _limpar_saidas_antigas(pasta: Path) -> None:
    """Remove murais de meses anteriores para não confundir o usuário."""
    if not pasta.is_dir():
        return
    for padrao in ("mural_*.png", "mural_*.pptx"):
        for arq in pasta.glob(padrao):
            arq.unlink()


def _gerar_mural() -> tuple[bytes, bytes]:
    """Executa a pipeline do pacote ``mural`` e devolve (png, pptx).

    Levanta exceção se faltar template/fontes/planilha — a página
    captura e exibe via st.error.
    """
    template = _resolve_projeto(cfg.TEMPLATE)
    if not template.exists():
        raise FileNotFoundError(f"Template não encontrado: {template}")

    aniversariantes = carregar_aniversariantes(
        CAMINHO_VALIDADO.resolve(),
        _resolve_projeto(cfg.PLANILHA_FALLBACK),
    )

    pasta_saida = _resolve_projeto(cfg.PASTA_SAIDA)
    _limpar_saidas_antigas(pasta_saida)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    arquivo_png = _resolve_projeto(cfg.ARQUIVO_SAIDA_PNG)
    arquivo_pptx = _resolve_projeto(cfg.ARQUIVO_SAIDA_PPTX)

    with Image.open(template) as img:
        tamanho_imagem = img.size

    fontes = carregar_fontes_pillow(_resolve_projeto(cfg.PASTA_FONTES))
    layout = calcular_layout(aniversariantes, tamanho_imagem, fontes)

    renderizar_png(layout, fontes, template, arquivo_png)
    png_bytes = arquivo_png.read_bytes()

    if cfg.EXPORTAR_PPTX:
        exportar_pptx(layout, template, arquivo_pptx)
        pptx_bytes = arquivo_pptx.read_bytes()
    else:
        pptx_bytes = b""

    return png_bytes, pptx_bytes


# =====================================================================
# Configuração da página
# =====================================================================
st.title("🖼️ Etapa 2 — Geração de PNG e PPTX")


# ---------------------------------------------------------------------
# Guarda — precisa existir o XLSX validado E a flag .validado.
# ---------------------------------------------------------------------
if not FLAG_VALIDADO.exists() or not CAMINHO_VALIDADO.exists():
    st.warning(
        "⏳ Nenhuma planilha validada disponível ainda. "
        "Aguarde a equipe da Etapa 1 finalizar a validação."
    )
    if st.button("🔄 Verificar novamente"):
        st.rerun()
    st.stop()


# ---------------------------------------------------------------------
# Preview da planilha validada (somente leitura).
# ---------------------------------------------------------------------
df = _carregar_preview(CAMINHO_VALIDADO, CAMINHO_VALIDADO.stat().st_mtime)

st.success("✅ Planilha validada recebida da Etapa 1.")
with st.expander("Ver dados validados"):
    st.dataframe(df, use_container_width=True)

st.divider()


# ---------------------------------------------------------------------
# Geração do PNG e PPTX.
# ---------------------------------------------------------------------
if st.button("🎨 Gerar PNG e PPTX", type="primary"):
    with st.spinner("Renderizando mural..."):
        try:
            png_bytes, pptx_bytes = _gerar_mural()
            st.session_state.png_bytes = png_bytes
            st.session_state.pptx_bytes = pptx_bytes
        except Exception as e:
            st.error(f"Erro ao gerar mural: {e}")


# ---------------------------------------------------------------------
# Pré-visualização + download (só aparece após a geração).
# ---------------------------------------------------------------------
png_bytes = st.session_state.get("png_bytes")
pptx_bytes = st.session_state.get("pptx_bytes")

if png_bytes:
    st.subheader("Pré-visualização (PNG)")
    st.image(png_bytes, use_container_width=True)

    if pptx_bytes:
        st.download_button(
            "⬇️ Baixar PPTX",
            data=pptx_bytes,
            file_name=Path(cfg.ARQUIVO_SAIDA_PPTX).name,
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            type="primary",
        )
