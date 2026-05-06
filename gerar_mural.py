"""
Gerador de Mural de Aniversariantes do Mês - Grupo Bueno
========================================================

Lê uma planilha Excel com os aniversariantes do mês e desenha sobre o template.

Lógica das colunas
------------------
Cada coluna tem **largura** e **altura** predefinidas (LARGURA_COLUNA_PX,
ALTURA_COLUNA_PX). O preenchimento é sequencial: enche a primeira coluna até
a altura máxima e, quando estoura, abre uma nova coluna à direita e continua.
O bloco fica centralizado horizontalmente por padrão; pode-se forçar a posição
em POSICAO_X_PRIMEIRA_COLUNA.

REQUISITOS:
    pip install pillow pandas openpyxl

ARQUIVOS NECESSÁRIOS NA MESMA PASTA:
    - template.png             (template em branco, sem nomes)
    - aniversariantes.xlsx     (planilha com colunas: dia, nome, cargo)
    - fontes/                  (pasta com os arquivos .ttf/.otf)

USO:
    python gerar_mural.py
"""

import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


def rgb(hex_color: str) -> tuple[int, int, int]:
    """Converte '#RRGGBB' ou 'RRGGBB' para tupla (R, G, B) usada pelo Pillow."""
    h = hex_color.strip().lstrip("#")
    if len(h) != 6 or any(c not in "0123456789abcdefABCDEF" for c in h):
        raise ValueError(f"Cor hex inválida (use #RRGGBB): {hex_color!r}")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


# ╔═══════════════════════════════════════════════════════════╗
# ║  CONFIGURAÇÕES — ajuste aqui                              ║
# ╚═══════════════════════════════════════════════════════════╝

# --- Arquivos ---
TEMPLATE_PATH = "template.png"
PLANILHA_PATH = "aniversariantes.xlsx"
PLANILHA_FALLBACK = "aniversariantes_exemplo.xlsx"
ARQUIVO_SAIDA = "mural_janeiro_2026.png"

# --- Mês de referência ---
MES = "JANEIRO"

# --- Fontes (caminhos dos arquivos .ttf/.otf) ---
FONTE_MES = "fontes/Ailerons 400.otf"
FONTE_DIA = "fontes/itoya-bold.ttf"
FONTE_NOME = "fontes/itoya-bold.ttf"
FONTE_CARGO = "fontes/itoya-bold.ttf"

# --- Tamanhos das fontes (em pixels) ---
TAMANHO_MES = 125
TAMANHO_DIA = 21
TAMANHO_NOME = 21
TAMANHO_CARGO = 21

# --- Cores em hexadecimal (#RRGGBB) ---
COR_TURQUESA = rgb("#00a5ac")  # dia, cargo (e ano, se usar)
COR_PRETO = rgb("#191919")     # nome (cinza quase preto; ≈ 25,25,25)

# --- Posição do nome do mês (ex.: JANEIRO) ---
# anchor="mt" → o ponto (centro_x, Y_MES) é o meio do topo da palavra.
Y_MES = 220
OFFSET_X_MES = -250  # empurra o mês para a direita (+) ou esquerda (−), em pixels

# --- Layout das colunas ---
# Cada coluna tem largura e altura predefinidas; quando enche, abre outra à direita.
LARGURA_COLUNA_PX = 410           # largura horizontal de cada coluna
ALTURA_COLUNA_PX = None           # altura útil; None = (altura_da_imagem − Y_INICIAL − MARGEM_INFERIOR)
MARGEM_INFERIOR = 80              # usada só quando ALTURA_COLUNA_PX é None

# X do início da PRIMEIRA coluna; None = bloco centralizado horizontalmente na imagem.
POSICAO_X_PRIMEIRA_COLUNA = None
# Y onde começa a primeira linha (precisa ficar abaixo do nome do mês)
Y_INICIAL = 335

# Espaço horizontal entre uma coluna e a seguinte (None = proporcional à fonte).
ESPACO_ENTRE_COLUNAS = None
MULT_ESPACO_ENTRE_COLUNAS = 0.40

# Pixels entre o fim do número do dia e o início do nome (None = proporcional à fonte).
ESPACO_DIA_PARA_NOME = None
MULT_ESPACO_DIA_NOME = 0.80

# Espaço vertical entre o fim do cargo e o topo da próxima entrada (None = proporcional à fonte).
ESPACO_ENTRE_PESSOAS = None
MULT_ESPACO_ENTRE_PESSOAS = 0.45

# Espaço entre a base do nome e o topo do cargo (None = proporcional à fonte).
ESPACO_NOME_PARA_CARGO = None
MULT_ESPACO_NOME_PARA_CARGO = 0.18

# Espaço entre linhas quando o nome (ou cargo) precisa quebrar (None = proporcional à fonte).
ESPACO_ENTRE_LINHAS = None
MULT_ESPACO_ENTRE_LINHAS = 0.10

# Limite duro só para evitar surpresas se a planilha vier enorme.
MAX_COLUNAS = 6

# --- Modo debug ---
# True desenha guias verdes mostrando a célula efetiva de cada pessoa.
MODO_DEBUG = False


# ╔═══════════════════════════════════════════════════════════╗
# ║  CÓDIGO — não precisa mexer daqui pra baixo               ║
# ╚═══════════════════════════════════════════════════════════╝

def _font_px_base() -> int:
    return max(TAMANHO_DIA, TAMANHO_NOME, TAMANHO_CARGO)


def espaco_dia_para_nome_px() -> int:
    if ESPACO_DIA_PARA_NOME is not None:
        return int(ESPACO_DIA_PARA_NOME)
    return max(8, int(_font_px_base() * MULT_ESPACO_DIA_NOME))


def espaco_entre_colunas_px() -> int:
    if ESPACO_ENTRE_COLUNAS is not None:
        return int(ESPACO_ENTRE_COLUNAS)
    return max(12, int(_font_px_base() * MULT_ESPACO_ENTRE_COLUNAS))


def espaco_entre_pessoas_px() -> int:
    """Pixels entre o fim do cargo e o topo da próxima linha (dia/nome)."""
    if ESPACO_ENTRE_PESSOAS is not None:
        return int(ESPACO_ENTRE_PESSOAS)
    return max(14, int(max(TAMANHO_NOME, TAMANHO_CARGO) * MULT_ESPACO_ENTRE_PESSOAS))


def espaco_nome_para_cargo_px() -> int:
    """Pixels entre a base da linha do nome e o topo da linha do cargo."""
    if ESPACO_NOME_PARA_CARGO is not None:
        return int(ESPACO_NOME_PARA_CARGO)
    return max(6, int(max(TAMANHO_NOME, TAMANHO_CARGO) * MULT_ESPACO_NOME_PARA_CARGO))


def espaco_entre_linhas_px() -> int:
    """Pixels entre linhas de um mesmo bloco (quando nome/cargo quebram)."""
    if ESPACO_ENTRE_LINHAS is not None:
        return int(ESPACO_ENTRE_LINHAS)
    return max(2, int(max(TAMANHO_NOME, TAMANHO_CARGO) * MULT_ESPACO_ENTRE_LINHAS))


def quebrar_em_linhas(
    texto: str,
    fonte: ImageFont.FreeTypeFont,
    largura_max: int,
    measure_draw: ImageDraw.ImageDraw,
) -> list[str]:
    """Quebra `texto` em linhas que cabem em `largura_max` px (greedy por palavras)."""
    if largura_max <= 0 or not texto:
        return [texto]

    def w(s: str) -> int:
        b = measure_draw.textbbox((0, 0), s, font=fonte)
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


def desenhar_entrada(
    draw: ImageDraw.ImageDraw,
    x_col: int,
    y: int,
    dia: str,
    nome: str,
    cargo: str,
    fonte_dia: ImageFont.FreeTypeFont,
    fonte_nome: ImageFont.FreeTypeFont,
    fonte_cargo: ImageFont.FreeTypeFont,
    gap_dia_nome: int,
    gap_nome_cargo: int,
    gap_entre_linhas: int,
    largura_coluna: int,
    desenhar: bool = True,
) -> int:
    """
    Desenha (ou apenas mede, se ``desenhar=False``) a entrada e retorna o Y do
    bottom da última linha (cargo). Quebra nome/cargo quando estouram a coluna.
    """
    bd = draw.textbbox((x_col, y), dia, font=fonte_dia)
    if desenhar:
        draw.text((x_col, y), dia, font=fonte_dia, fill=COR_TURQUESA)
    nx = bd[2] + gap_dia_nome
    largura_max_texto = max(1, x_col + largura_coluna - nx)

    nome_linhas = quebrar_em_linhas(nome, fonte_nome, largura_max_texto, draw)
    nome_bottom = y
    for i, linha in enumerate(nome_linhas):
        ny = y if i == 0 else nome_bottom + gap_entre_linhas
        if desenhar:
            draw.text((nx, ny), linha, font=fonte_nome, fill=COR_PRETO)
        bn = draw.textbbox((nx, ny), linha, font=fonte_nome)
        nome_bottom = bn[3]

    base_linha_superior = max(bd[3], nome_bottom)

    cargo_linhas = quebrar_em_linhas(cargo, fonte_cargo, largura_max_texto, draw)
    cargo_top_y = base_linha_superior + gap_nome_cargo
    cargo_bottom = cargo_top_y
    for i, linha in enumerate(cargo_linhas):
        cy = cargo_top_y if i == 0 else cargo_bottom + gap_entre_linhas
        if desenhar:
            draw.text((nx, cy), linha, font=fonte_cargo, fill=COR_TURQUESA)
        bc = draw.textbbox((nx, cy), linha, font=fonte_cargo)
        cargo_bottom = bc[3]

    return cargo_bottom


def altura_pessoa(
    measure_draw: ImageDraw.ImageDraw,
    dia: str,
    nome: str,
    cargo: str,
    fonte_dia: ImageFont.FreeTypeFont,
    fonte_nome: ImageFont.FreeTypeFont,
    fonte_cargo: ImageFont.FreeTypeFont,
    gap_dia_nome: int,
    gap_nome_cargo: int,
    gap_entre_linhas: int,
    largura_coluna: int,
) -> int:
    """Altura total em px da entrada (com possível quebra de linha)."""
    return desenhar_entrada(
        measure_draw,
        0,
        0,
        dia,
        nome,
        cargo,
        fonte_dia,
        fonte_nome,
        fonte_cargo,
        gap_dia_nome,
        gap_nome_cargo,
        gap_entre_linhas,
        largura_coluna,
        desenhar=False,
    )


def montar_colunas_por_altura(
    pessoas: list[tuple[str, str, str]],
    alturas: list[int],
    altura_max: int,
    gap_abaixo: int,
) -> list[list[tuple[str, str, str]]]:
    """
    Distribui pessoas em colunas: enche a coluna até altura_max, transborda
    para a próxima. NÃO equaliza — segue a ordem da planilha.
    """
    colunas: list[list[tuple[str, str, str]]] = []
    atual: list[tuple[str, str, str]] = []
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


def calcular_xs_colunas(
    largura_imagem: int,
    n_cols: int,
    largura_coluna: int,
    gap_entre_cols: int,
) -> list[int]:
    """
    Retorna o X inicial de cada coluna. Se POSICAO_X_PRIMEIRA_COLUNA é None,
    o bloco é centralizado horizontalmente na imagem.
    """
    if n_cols <= 0:
        return []
    largura_total = n_cols * largura_coluna + gap_entre_cols * max(0, n_cols - 1)
    if POSICAO_X_PRIMEIRA_COLUNA is None:
        x0 = (largura_imagem - largura_total) // 2
    else:
        x0 = int(POSICAO_X_PRIMEIRA_COLUNA)
    return [x0 + i * (largura_coluna + gap_entre_cols) for i in range(n_cols)]


def desenhar_guia_debug(draw, x, y, largura: int, altura: int):
    """Retângulo verde que mostra a célula da pessoa."""
    cor = rgb("#30d413")
    draw.rectangle([(x, y), (x + largura, y + altura)], outline=cor, width=1)


def _caminho_planilha():
    if os.path.exists(PLANILHA_PATH):
        return PLANILHA_PATH
    if os.path.exists(PLANILHA_FALLBACK):
        print(f"⚠️  {PLANILHA_PATH} não encontrado — usando {PLANILHA_FALLBACK}")
        return PLANILHA_FALLBACK
    raise FileNotFoundError(
        f"Planilha não encontrada. Coloque {PLANILHA_PATH} ou {PLANILHA_FALLBACK} "
        "na pasta do script."
    )


def gerar_mural():
    # ----- 1. Carrega a planilha -----
    caminho_planilha = _caminho_planilha()
    df = pd.read_excel(caminho_planilha)

    colunas_obrigatorias = {"dia", "nome", "cargo"}
    if not colunas_obrigatorias.issubset(df.columns):
        raise ValueError(
            f"A planilha precisa ter as colunas: {colunas_obrigatorias}.\n"
            f"Colunas encontradas: {list(df.columns)}"
        )

    df = df.sort_values(by="dia").reset_index(drop=True)
    aniversariantes = [
        (
            str(int(linha["dia"])).zfill(2),
            str(linha["nome"]).upper(),
            str(linha["cargo"]).upper(),
        )
        for _, linha in df.iterrows()
    ]

    print(f"📋 {len(aniversariantes)} aniversariantes encontrados")

    # ----- 2. Abre o template e prepara o desenho -----
    if not os.path.exists(TEMPLATE_PATH):
        raise FileNotFoundError(f"Template não encontrado: {TEMPLATE_PATH}")

    imagem = Image.open(TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(imagem)

    fonte_mes = ImageFont.truetype(FONTE_MES, TAMANHO_MES)
    fonte_dia = ImageFont.truetype(FONTE_DIA, TAMANHO_DIA)
    fonte_nome = ImageFont.truetype(FONTE_NOME, TAMANHO_NOME)
    fonte_cargo = ImageFont.truetype(FONTE_CARGO, TAMANHO_CARGO)

    # ----- 3. Desenha o título (MES) -----
    centro_x = imagem.size[0] // 2 + OFFSET_X_MES
    draw.text(
        (centro_x, Y_MES),
        MES,
        font=fonte_mes,
        fill=COR_TURQUESA,
        anchor="mt",
    )

    # ----- 4. Distribuição em colunas (por altura) -----
    espaco_dia_nome = espaco_dia_para_nome_px()
    gap_entre_cols = espaco_entre_colunas_px()
    gap_abaixo_bloco = espaco_entre_pessoas_px()
    gap_nome_para_cargo = espaco_nome_para_cargo_px()
    gap_entre_linhas = espaco_entre_linhas_px()

    altura_max = (
        int(ALTURA_COLUNA_PX)
        if ALTURA_COLUNA_PX is not None
        else max(0, imagem.size[1] - Y_INICIAL - MARGEM_INFERIOR)
    )
    if altura_max <= 0:
        raise ValueError(
            "Altura útil para colunas ≤ 0: aumente a imagem, suba Y_INICIAL "
            "ou diminua MARGEM_INFERIOR."
        )

    dummy = Image.new("RGB", (1, 1))
    measure_draw = ImageDraw.Draw(dummy)
    alturas = [
        altura_pessoa(
            measure_draw,
            d,
            n,
            c,
            fonte_dia,
            fonte_nome,
            fonte_cargo,
            espaco_dia_nome,
            gap_nome_para_cargo,
            gap_entre_linhas,
            int(LARGURA_COLUNA_PX),
        )
        for d, n, c in aniversariantes
    ]

    colunas = montar_colunas_por_altura(
        aniversariantes, alturas, altura_max, gap_abaixo_bloco
    )
    if len(colunas) > MAX_COLUNAS:
        print(
            f"⚠️  {len(colunas)} colunas necessárias > MAX_COLUNAS={MAX_COLUNAS}; "
            "considere aumentar ALTURA_COLUNA_PX, reduzir fonte ou aumentar MAX_COLUNAS."
        )

    n_cols = len(colunas)
    colunas_x = calcular_xs_colunas(
        imagem.size[0], n_cols, int(LARGURA_COLUNA_PX), gap_entre_cols
    )

    posicionamento = (
        "centralizado"
        if POSICAO_X_PRIMEIRA_COLUNA is None
        else f"x0={POSICAO_X_PRIMEIRA_COLUNA}"
    )
    print(
        f"📐 {n_cols} coluna(s) ({posicionamento}) | largura={LARGURA_COLUNA_PX}px "
        f"altura_max={altura_max}px | X = {colunas_x}"
    )

    # ----- 5. Desenha cada coluna -----
    for idx_coluna, pessoas in enumerate(colunas):
        x_coluna = colunas_x[idx_coluna]
        y = Y_INICIAL

        for dia, nome, cargo in pessoas:
            bottom = desenhar_entrada(
                draw,
                x_coluna,
                y,
                dia,
                nome,
                cargo,
                fonte_dia,
                fonte_nome,
                fonte_cargo,
                espaco_dia_nome,
                gap_nome_para_cargo,
                gap_entre_linhas,
                int(LARGURA_COLUNA_PX),
                desenhar=True,
            )

            if MODO_DEBUG:
                desenhar_guia_debug(
                    draw,
                    x_coluna,
                    y,
                    largura=int(LARGURA_COLUNA_PX),
                    altura=max(20, bottom - y),
                )

            y = bottom + gap_abaixo_bloco

    # ----- 6. Salva o resultado -----
    imagem.save(ARQUIVO_SAIDA, quality=95)
    print(f"✅ Mural gerado: {ARQUIVO_SAIDA}")
    print(f"📐 Tamanho da imagem: {imagem.size[0]}x{imagem.size[1]}px")


if __name__ == "__main__":
    gerar_mural()
