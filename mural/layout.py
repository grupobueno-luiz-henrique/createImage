"""
Cálculo do layout do mural — não desenha nada, apenas computa coordenadas.

A partir da lista de :class:`Aniversariante` e das constantes em
:mod:`mural.config`, devolve um :class:`LayoutMural` com a posição absoluta
(em pixels) de cada texto. Os renderers (PNG e PPTX) recebem esse layout
pronto e só "pintam" — usando exatamente as mesmas coordenadas.

Pillow é usado aqui APENAS para *medir* texto (``ImageDraw.textbbox``),
nunca para desenhar. Manter este arquivo livre de python-pptx é proposital:
a separação garante que a geometria seja única para PNG e PPTX.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from . import config as cfg
from .tipos import Aniversariante, BlocoPessoa, LayoutMural, TextoPosicionado


# ───────────────────────────────────────────────────────────────────────────
# Espaçamentos: resolve "valor fixo OU proporcional à fonte" uma única vez.
# ───────────────────────────────────────────────────────────────────────────


def _font_px_base() -> int:
    return max(cfg.TAMANHO_DIA, cfg.TAMANHO_NOME, cfg.TAMANHO_CARGO)


def _resolver(fixo: Optional[int], multiplicador: float, base: int, piso: int) -> int:
    if fixo is not None:
        return int(fixo)
    return max(piso, int(base * multiplicador))


@dataclass(frozen=True)
class Espacamentos:
    """Espaçamentos em pixels, já resolvidos a partir de :mod:`config`."""

    dia_para_nome: int
    entre_colunas: int
    abaixo_pessoa: int
    nome_para_cargo: int
    entre_linhas: int

    @classmethod
    def a_partir_da_config(cls) -> "Espacamentos":
        base = _font_px_base()
        nc = max(cfg.TAMANHO_NOME, cfg.TAMANHO_CARGO)
        return cls(
            dia_para_nome=_resolver(
                cfg.ESPACO_DIA_PARA_NOME, cfg.MULT_ESPACO_DIA_NOME, base, piso=8
            ),
            entre_colunas=_resolver(
                cfg.ESPACO_ENTRE_COLUNAS, cfg.MULT_ESPACO_ENTRE_COLUNAS, base, piso=12
            ),
            abaixo_pessoa=_resolver(
                cfg.ESPACO_ENTRE_PESSOAS, cfg.MULT_ESPACO_ENTRE_PESSOAS, nc, piso=14
            ),
            nome_para_cargo=_resolver(
                cfg.ESPACO_NOME_PARA_CARGO, cfg.MULT_ESPACO_NOME_PARA_CARGO, nc, piso=6
            ),
            entre_linhas=_resolver(
                cfg.ESPACO_ENTRE_LINHAS, cfg.MULT_ESPACO_ENTRE_LINHAS, nc, piso=2
            ),
        )


# ───────────────────────────────────────────────────────────────────────────
# Carregamento das fontes (Pillow)
# ───────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FontesPillow:
    """Pacote das 4 fontes do Pillow já abertas no tamanho certo."""

    mes: ImageFont.FreeTypeFont
    dia: ImageFont.FreeTypeFont
    nome: ImageFont.FreeTypeFont
    cargo: ImageFont.FreeTypeFont


def carregar_fontes_pillow(pasta_fontes: Path) -> FontesPillow:
    """Abre os arquivos .ttf/.otf via ``ImageFont.truetype``.

    Falha cedo se algum arquivo não existir, evitando erro misterioso depois.
    """
    return FontesPillow(
        mes=ImageFont.truetype(str(pasta_fontes / cfg.FONTE_MES), cfg.TAMANHO_MES),
        dia=ImageFont.truetype(str(pasta_fontes / cfg.FONTE_DIA), cfg.TAMANHO_DIA),
        nome=ImageFont.truetype(str(pasta_fontes / cfg.FONTE_NOME), cfg.TAMANHO_NOME),
        cargo=ImageFont.truetype(str(pasta_fontes / cfg.FONTE_CARGO), cfg.TAMANHO_CARGO),
    )


# ───────────────────────────────────────────────────────────────────────────
# Quebra de texto em linhas (greedy por palavras)
# ───────────────────────────────────────────────────────────────────────────


def quebrar_em_linhas(
    texto: str,
    fonte: ImageFont.FreeTypeFont,
    largura_max: int,
    measure: ImageDraw.ImageDraw,
) -> list[str]:
    """Quebra ``texto`` em linhas que caibam em ``largura_max`` pixels.

    Estratégia gulosa: enche a linha até estourar e abre uma nova. Uma
    palavra maior que ``largura_max`` vai sozinha na sua linha (não tenta
    quebrar dentro da palavra).
    """
    if largura_max <= 0 or not texto:
        return [texto]

    def w(s: str) -> int:
        b = measure.textbbox((0, 0), s, font=fonte)
        return b[2] - b[0]

    if w(texto) <= largura_max:
        return [texto]

    palavras = texto.split()
    if not palavras:
        return [texto]

    linhas: list[str] = []
    atual = palavras[0]
    for palavra in palavras[1:]:
        candidato = atual + " " + palavra
        if w(candidato) <= largura_max:
            atual = candidato
        else:
            linhas.append(atual)
            atual = palavra
    linhas.append(atual)
    return linhas


# ───────────────────────────────────────────────────────────────────────────
# Posicionamento de uma pessoa (dia + nome + cargo, com possível quebra)
# ───────────────────────────────────────────────────────────────────────────


def _bloco_pessoa(
    pessoa: Aniversariante,
    *,
    x_col: int,
    y_topo: int,
    coluna_idx: int,
    largura_coluna: int,
    fontes: FontesPillow,
    esp: Espacamentos,
    measure: ImageDraw.ImageDraw,
) -> BlocoPessoa:
    """Retorna o ``BlocoPessoa`` com posições absolutas de cada texto."""
    elementos: list[TextoPosicionado] = []

    bd = measure.textbbox((x_col, y_topo), pessoa.dia, font=fontes.dia)
    largura_dia = max(1, bd[2] - bd[0])
    altura_dia = max(1, bd[3] - bd[1])
    elementos.append(
        TextoPosicionado(
            texto=pessoa.dia,
            x=x_col,
            y=y_topo,
            largura=largura_dia,
            altura=altura_dia,
            papel="dia",
            largura_max_disponivel=largura_coluna,
        )
    )

    nx = bd[2] + esp.dia_para_nome
    largura_disp_texto = max(1, x_col + largura_coluna - nx)

    nome_linhas = quebrar_em_linhas(pessoa.nome, fontes.nome, largura_disp_texto, measure)
    nome_bottom = y_topo
    for i, linha in enumerate(nome_linhas):
        ny = y_topo if i == 0 else nome_bottom + esp.entre_linhas
        bn = measure.textbbox((nx, ny), linha, font=fontes.nome)
        elementos.append(
            TextoPosicionado(
                texto=linha,
                x=nx,
                y=ny,
                largura=max(1, bn[2] - bn[0]),
                altura=max(1, bn[3] - bn[1]),
                papel="nome",
                largura_max_disponivel=largura_disp_texto,
            )
        )
        nome_bottom = bn[3]

    base_linha_superior = max(bd[3], nome_bottom)
    cargo_linhas = quebrar_em_linhas(pessoa.cargo, fontes.cargo, largura_disp_texto, measure)
    cargo_top_y = base_linha_superior + esp.nome_para_cargo
    cargo_bottom = cargo_top_y
    for i, linha in enumerate(cargo_linhas):
        cy = cargo_top_y if i == 0 else cargo_bottom + esp.entre_linhas
        bc = measure.textbbox((nx, cy), linha, font=fontes.cargo)
        elementos.append(
            TextoPosicionado(
                texto=linha,
                x=nx,
                y=cy,
                largura=max(1, bc[2] - bc[0]),
                altura=max(1, bc[3] - bc[1]),
                papel="cargo",
                largura_max_disponivel=largura_disp_texto,
            )
        )
        cargo_bottom = bc[3]

    return BlocoPessoa(
        aniversariante=pessoa,
        coluna_idx=coluna_idx,
        x_coluna=x_col,
        y_topo=y_topo,
        y_base=cargo_bottom,
        elementos=elementos,
    )


def _altura_pessoa(
    pessoa: Aniversariante,
    *,
    largura_coluna: int,
    fontes: FontesPillow,
    esp: Espacamentos,
    measure: ImageDraw.ImageDraw,
) -> int:
    """Mede a altura da entrada SEM desenhar — só para distribuir em colunas."""
    bloco = _bloco_pessoa(
        pessoa,
        x_col=0,
        y_topo=0,
        coluna_idx=0,
        largura_coluna=largura_coluna,
        fontes=fontes,
        esp=esp,
        measure=measure,
    )
    return bloco.y_base


# ───────────────────────────────────────────────────────────────────────────
# Distribuição em colunas e cálculo dos Xs
# ───────────────────────────────────────────────────────────────────────────


def _montar_colunas(
    pessoas: list[Aniversariante],
    alturas: list[int],
    altura_max: int,
    gap_abaixo: int,
) -> list[list[Aniversariante]]:
    """Enche a primeira coluna até ``altura_max``; quando estoura, abre outra.

    NÃO equaliza alturas — segue a ordem da planilha (já ordenada por dia).
    """
    colunas: list[list[Aniversariante]] = []
    atual: list[Aniversariante] = []
    usado = 0
    for pessoa, h in zip(pessoas, alturas):
        consumo = h if not atual else gap_abaixo + h
        if atual and usado + consumo > altura_max:
            colunas.append(atual)
            atual = [pessoa]
            usado = h
        else:
            atual.append(pessoa)
            usado += consumo
    if atual:
        colunas.append(atual)
    return colunas


def _xs_colunas(
    largura_imagem: int,
    n_cols: int,
    largura_coluna: int,
    gap_entre_cols: int,
) -> list[int]:
    """X inicial de cada coluna; centraliza o bloco se ``POSICAO_X_PRIMEIRA_COLUNA`` for ``None``."""
    if n_cols <= 0:
        return []
    largura_total = n_cols * largura_coluna + gap_entre_cols * max(0, n_cols - 1)
    if cfg.POSICAO_X_PRIMEIRA_COLUNA is None:
        x0 = (largura_imagem - largura_total) // 2
    else:
        x0 = int(cfg.POSICAO_X_PRIMEIRA_COLUNA)
    return [x0 + i * (largura_coluna + gap_entre_cols) for i in range(n_cols)]


# ───────────────────────────────────────────────────────────────────────────
# Título do mês
# ───────────────────────────────────────────────────────────────────────────


def _titulo_mes(
    largura_imagem: int,
    fonte_mes: ImageFont.FreeTypeFont,
    measure: ImageDraw.ImageDraw,
) -> TextoPosicionado:
    """Calcula o top-left do título a partir do centro desejado.

    O Pillow desenhará com ``anchor="mt"`` no centro, mas guardamos o
    top-left para que o renderer PPTX coloque a caixa na mesma posição.
    """
    centro_x = largura_imagem // 2 + cfg.OFFSET_X_MES
    bd = measure.textbbox((0, 0), cfg.MES, font=fonte_mes)
    w = max(1, bd[2] - bd[0])
    h = max(1, bd[3] - bd[1])
    esquerda = centro_x - w // 2
    return TextoPosicionado(
        texto=cfg.MES,
        x=esquerda,
        y=cfg.Y_MES,
        largura=w,
        altura=h,
        papel="mes",
        largura_max_disponivel=w,
    )


# ───────────────────────────────────────────────────────────────────────────
# API pública
# ───────────────────────────────────────────────────────────────────────────


def calcular_layout(
    aniversariantes: list[Aniversariante],
    tamanho_imagem: tuple[int, int],
    fontes: FontesPillow,
) -> LayoutMural:
    """Devolve o :class:`LayoutMural` com posição absoluta de cada texto."""
    largura_img, altura_img = tamanho_imagem
    esp = Espacamentos.a_partir_da_config()

    # ImageDraw exige uma imagem para existir; criamos uma 1x1 só para usar
    # o método ``textbbox`` (medição). Nada é desenhado nela.
    dummy = Image.new("RGB", (1, 1))
    measure = ImageDraw.Draw(dummy)

    altura_max = (
        int(cfg.ALTURA_COLUNA_PX)
        if cfg.ALTURA_COLUNA_PX is not None
        else max(0, altura_img - cfg.Y_INICIAL - cfg.MARGEM_INFERIOR)
    )
    if altura_max <= 0:
        raise ValueError(
            "Altura útil para colunas ≤ 0: aumente a imagem, suba Y_INICIAL "
            "ou diminua MARGEM_INFERIOR."
        )

    alturas = [
        _altura_pessoa(
            p,
            largura_coluna=cfg.LARGURA_COLUNA_PX,
            fontes=fontes,
            esp=esp,
            measure=measure,
        )
        for p in aniversariantes
    ]
    colunas = _montar_colunas(aniversariantes, alturas, altura_max, esp.abaixo_pessoa)
    if len(colunas) > cfg.MAX_COLUNAS:
        print(
            f"⚠️  {len(colunas)} colunas necessárias > MAX_COLUNAS={cfg.MAX_COLUNAS}; "
            "considere aumentar ALTURA_COLUNA_PX, reduzir fonte ou MAX_COLUNAS."
        )

    n_cols = len(colunas)
    xs = _xs_colunas(largura_img, n_cols, cfg.LARGURA_COLUNA_PX, esp.entre_colunas)

    blocos: list[BlocoPessoa] = []
    for idx_col, pessoas in enumerate(colunas):
        x_col = xs[idx_col]
        y = cfg.Y_INICIAL
        for pessoa in pessoas:
            bloco = _bloco_pessoa(
                pessoa,
                x_col=x_col,
                y_topo=y,
                coluna_idx=idx_col,
                largura_coluna=cfg.LARGURA_COLUNA_PX,
                fontes=fontes,
                esp=esp,
                measure=measure,
            )
            blocos.append(bloco)
            y = bloco.y_base + esp.abaixo_pessoa

    titulo = _titulo_mes(largura_img, fontes.mes, measure)

    posicionamento = (
        "centralizado"
        if cfg.POSICAO_X_PRIMEIRA_COLUNA is None
        else f"x0={cfg.POSICAO_X_PRIMEIRA_COLUNA}"
    )
    print(
        f"📐 {n_cols} coluna(s) ({posicionamento}) | "
        f"largura={cfg.LARGURA_COLUNA_PX}px altura_max={altura_max}px | X = {xs}"
    )

    return LayoutMural(
        largura_imagem=largura_img,
        altura_imagem=altura_img,
        titulo_mes=titulo,
        blocos=blocos,
        n_colunas=n_cols,
        xs_colunas=xs,
    )
