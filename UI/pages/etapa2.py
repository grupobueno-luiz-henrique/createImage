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

import json
from datetime import datetime
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
META_VALIDADO = _ARQUIVOS / "dados_validado.json"
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


def _carregar_meta() -> dict:
    """Lê os metadados (mês/ano) gravados pela Etapa 1 no envio.

    Faz fallback gracioso para o "mês seguinte / ano atual" se o JSON
    não existir ou estiver corrompido — preserva o comportamento antigo
    quando a Etapa 1 ainda não foi atualizada.
    """
    if META_VALIDADO.exists():
        try:
            data = json.loads(META_VALIDADO.read_text(encoding="utf-8"))
            return {
                "mes": int(data.get("mes")),
                "ano": int(data.get("ano", datetime.now().year)),
            }
        except Exception:
            pass
    return {
        "mes": (datetime.now().month % 12) + 1,
        "ano": datetime.now().year,
    }


def _gerar_mural(mes: int, ano: int) -> tuple[bytes, bytes]:
    """Executa a pipeline do pacote ``mural`` para o ``mes``/``ano`` informado.

    Sobrescreve ``cfg.MES``/``cfg.ANO`` em tempo de execução para que o
    título desenhado pelo ``mural.layout`` reflita o mês escolhido na UI,
    e usa caminhos de saída calculados via ``cfg.obter_referencia``.
    """
    mes_nome, ano_ref, arquivo_png_rel, arquivo_pptx_rel = cfg.obter_referencia(
        mes, ano
    )

    cfg.MES = mes_nome
    cfg.ANO = ano_ref

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

    arquivo_png = _resolve_projeto(arquivo_png_rel)
    arquivo_pptx = _resolve_projeto(arquivo_pptx_rel)

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
# Cabeçalho — contexto do papel (equipe Marketing).
# =====================================================================
st.title("Etapa 2 — Geração da arte (Equipe Marketing)")
st.caption(
    "Receba a lista validada pelo GG, confira e gere o mural em PNG e PPTX."
)
st.divider()


# ---------------------------------------------------------------------
# Guarda — precisa existir o XLSX validado E a flag .validado.
# ---------------------------------------------------------------------
if not FLAG_VALIDADO.exists() or not CAMINHO_VALIDADO.exists():
    with st.container(border=True):
        st.markdown("#### Aguardando o GG")
        st.caption(
            "Nenhuma lista validada disponível ainda. "
            "Quando o GG liberar, ela aparece aqui automaticamente."
        )
        if st.button("Verificar novamente"):
            st.rerun()
    st.stop()


# ---------------------------------------------------------------------
# Metadados gravados pela Etapa 1: mês/ano escolhidos no envio.
# Tudo nesta página passa a usar esses valores em vez de cfg.MES (que
# é congelado no import time).
# ---------------------------------------------------------------------
meta = _carregar_meta()
mes_ref = int(meta["mes"])
ano_ref = int(meta["ano"])
mes_nome_ref, _, _, arquivo_pptx_ref = cfg.obter_referencia(mes_ref, ano_ref)


# ---------------------------------------------------------------------
# Painel "Recebido do GG" — KPIs + preview da planilha validada.
# ---------------------------------------------------------------------
df = _carregar_preview(CAMINHO_VALIDADO, CAMINHO_VALIDADO.stat().st_mtime)
recebido_em = datetime.fromtimestamp(CAMINHO_VALIDADO.stat().st_mtime)

with st.container(border=True):
    st.subheader("1. Planilha Revisada")
    k1, k2, k3 = st.columns(3)
    k1.metric("Mês do mural", mes_nome_ref.title())
    k2.metric("Aniversariantes", len(df))
    k3.metric("Recebido em", recebido_em.strftime("%d/%m as %H:%M"))

    with st.expander("Ver dados validados"):
        st.dataframe(df, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------
# Geração do PNG e PPTX (com feedback via st.status).
# ---------------------------------------------------------------------
with st.container(border=True):
    st.subheader("2. Gerar a arte")
    if st.button("Gerar PNG e PPTX", type="primary"):
        with st.status("Renderizando mural...", expanded=True) as status:
            try:
                st.write("Calculando layout...")
                png_bytes, pptx_bytes = _gerar_mural(mes_ref, ano_ref)
                st.session_state.png_bytes = png_bytes
                st.session_state.pptx_bytes = pptx_bytes
                status.update(
                    label="Mural pronto.", state="complete", expanded=False
                )
                st.balloons()
            except Exception as e:
                status.update(label="Falhou.", state="error")
                st.error(f"Erro ao gerar mural: {e}")


# ---------------------------------------------------------------------
# Resultado: download do PPTX + pré-visualização.
# ---------------------------------------------------------------------
png_bytes = st.session_state.get("png_bytes")
pptx_bytes = st.session_state.get("pptx_bytes")

if png_bytes:
    with st.container(border=True):
        st.subheader("3. Resultado")

        if pptx_bytes:
            st.download_button(
                "Baixar PPTX",
                data=pptx_bytes,
                file_name=Path(arquivo_pptx_ref).name,
                mime=(
                    "application/vnd.openxmlformats-officedocument"
                    ".presentationml.presentation"
                ),
                type="primary",
                use_container_width=True,
            )

    st.image(png_bytes, use_container_width=True, caption="Pré-visualização")
