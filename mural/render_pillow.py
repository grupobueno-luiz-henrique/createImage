"""
Renderização do mural em PNG via Pillow.

Recebe um :class:`LayoutMural` já calculado em :mod:`mural.layout` e desenha
sobre o template. Esta camada NÃO calcula posições — apenas pinta.

Pillow (resumo prático):
    - ``Image.open(path).convert("RGB")`` carrega a imagem de fundo.
    - ``ImageDraw.Draw(imagem)`` cria o "pincel" que desenha texto e formas.
    - ``draw.text((x, y), texto, font=..., fill=..., anchor="lt")`` escreve
      o texto a partir do canto superior esquerdo. Para o título usamos
      ``anchor="mt"`` (centro/topo) — porque a posição-alvo é o centro
      horizontal do mês, não a borda esquerda.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from PIL import Image, ImageDraw

from . import config as cfg
from .layout import FontesPillow
from .tipos import BlocoPessoa, LayoutMural, TextoPosicionado
from .utilitarios import rgb


# Cor da guia de debug (retângulo verde por pessoa).
COR_DEBUG = rgb("#30d413")


def renderizar_png(
    layout: LayoutMural,
    fontes: FontesPillow,
    caminho_template: Path,
    caminho_saida: Path,
) -> None:
    """Abre o template, desenha os textos do layout e salva o PNG final."""
    if not caminho_template.exists():
        raise FileNotFoundError(f"Template não encontrado: {caminho_template}")

    imagem = Image.open(caminho_template).convert("RGB")
    draw = ImageDraw.Draw(imagem)

    _desenhar_titulo(draw, layout.titulo_mes, fontes)

    for bloco in layout.blocos:
        for elemento in bloco.elementos:
            _desenhar_elemento(draw, elemento, fontes)
        if cfg.MODO_DEBUG:
            _desenhar_guia_debug(draw, bloco)

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    imagem.save(caminho_saida, quality=95)
    print(f"✅ Mural gerado: {caminho_saida}")
    print(f"📐 Tamanho da imagem: {imagem.size[0]}x{imagem.size[1]}px")


# ───────────────────────────────────────────────────────────────────────────
# Desenho de cada parte
# ───────────────────────────────────────────────────────────────────────────


def _desenhar_titulo(
    draw: ImageDraw.ImageDraw,
    titulo: TextoPosicionado,
    fontes: FontesPillow,
) -> None:
    # Voltamos para o ponto central horizontal e usamos anchor="mt" para que
    # o título fique simetricamente alinhado com OFFSET_X_MES, igual ao PPTX.
    centro_x = titulo.x + titulo.largura // 2
    draw.text(
        (centro_x, titulo.y),
        titulo.texto,
        font=fontes.mes,
        fill=cfg.COR_TURQUESA,
        anchor="mt",
    )


def _desenhar_elemento(
    draw: ImageDraw.ImageDraw,
    elemento: TextoPosicionado,
    fontes: FontesPillow,
) -> None:
    fonte, cor = _estilo_para_papel(elemento.papel, fontes)
    draw.text((elemento.x, elemento.y), elemento.texto, font=fonte, fill=cor)


def _estilo_para_papel(
    papel: str, fontes: FontesPillow
) -> Tuple[object, tuple[int, int, int]]:
    if papel == "dia":
        return fontes.dia, cfg.COR_TURQUESA
    if papel == "nome":
        return fontes.nome, cfg.COR_PRETO
    if papel == "cargo":
        return fontes.cargo, cfg.COR_TURQUESA
    raise ValueError(f"Papel inesperado para Pillow: {papel!r}")


def _desenhar_guia_debug(draw: ImageDraw.ImageDraw, bloco: BlocoPessoa) -> None:
    """Retângulo verde mostrando a célula efetiva de uma pessoa."""
    altura = max(20, bloco.y_base - bloco.y_topo)
    draw.rectangle(
        [
            (bloco.x_coluna, bloco.y_topo),
            (bloco.x_coluna + cfg.LARGURA_COLUNA_PX, bloco.y_topo + altura),
        ],
        outline=COR_DEBUG,
        width=1,
    )
