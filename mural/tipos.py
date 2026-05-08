"""Dataclasses compartilhadas entre planilha, layout e renderers.

A ideia é: a leitura da planilha produz ``Aniversariante``; o cálculo de
layout produz ``LayoutMural``; e os renderers só consomem esses tipos. Nada
aqui depende de Pillow ou de python-pptx.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


PapelTexto = Literal["mes", "dia", "nome", "cargo"]


@dataclass(frozen=True)
class Aniversariante:
    """Linha da planilha já normalizada.

    ``dia`` vem com 2 dígitos zero-prefixados ('07'); ``nome`` e ``cargo``
    em UPPERCASE — tudo prontinho para desenhar.
    """

    dia: str
    nome: str
    cargo: str


@dataclass(frozen=True)
class TextoPosicionado:
    """Trecho de texto com posição final em pixels (top-left).

    ``largura`` / ``altura``  → bbox renderizado pelo Pillow (apertado).
    ``largura_max_disponivel`` → quanto espaço horizontal sobra na coluna a
    partir de ``x``; o renderer PPTX usa esse valor para criar a caixa de
    texto larga o suficiente, garantindo que o texto não quebre diferente
    do PNG por causa de uma diferença mínima de métrica entre Pillow e
    PowerPoint.
    """

    texto: str
    x: int
    y: int
    largura: int
    altura: int
    papel: PapelTexto
    largura_max_disponivel: int


@dataclass(frozen=True)
class BlocoPessoa:
    """Conjunto de elementos visuais de UMA pessoa, já posicionados."""

    aniversariante: Aniversariante
    coluna_idx: int
    x_coluna: int
    y_topo: int
    y_base: int
    elementos: list[TextoPosicionado]


@dataclass(frozen=True)
class LayoutMural:
    """Resultado completo do cálculo geométrico — basta renderizar."""

    largura_imagem: int
    altura_imagem: int
    titulo_mes: TextoPosicionado
    blocos: list[BlocoPessoa]
    n_colunas: int
    xs_colunas: list[int]
