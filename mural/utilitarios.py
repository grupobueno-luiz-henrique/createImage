"""Helpers que NÃO dependem de Pillow nem de python-pptx.

Conversões de unidade (px → EMU, px → pt) e parsing de cor hex.
"""

from __future__ import annotations


def rgb(hex_color: str) -> tuple[int, int, int]:
    """Converte ``'#RRGGBB'`` (ou ``'RRGGBB'``) em tupla ``(R, G, B)``.

    O Pillow espera tuplas ``(r, g, b)`` em ``fill=``; o python-pptx
    aceita ``RGBColor(r, g, b)``. Esta função produz a tupla crua que
    serve para os dois.
    """
    h = hex_color.strip().lstrip("#")
    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
        raise ValueError(f"Cor hex inválida (use #RRGGBB): {hex_color!r}")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# OOXML mede comprimentos em EMU (English Metric Units): 914400 EMU = 1 polegada.
# Como o restante do código pensa em pixels (96 dpi padrão de tela), pré-calculamos
# o fator para evitar contas espalhadas pelo projeto.
DPI_PADRAO = 96
EMU_POR_PIXEL = 914400 / DPI_PADRAO


def px_para_emu(px: float) -> int:
    """Converte pixels (96 dpi) para EMU — unidade que o python-pptx usa."""
    return int(round(px * EMU_POR_PIXEL))


def px_fonte_para_pt(px: float) -> float:
    """Converte tamanho de fonte em pixels (96 dpi) para pontos tipográficos.

    1 pt = 1/72 polegada; 1 px (96 dpi) = 1/96 polegada → ``px * 72 / 96``.
    """
    return px * 72.0 / 96.0
