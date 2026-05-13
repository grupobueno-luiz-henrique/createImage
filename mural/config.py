"""
Configurações editáveis do mural.

Tudo que você costuma trocar (mês, fontes, tamanhos, espaçamentos, caminhos
de arquivo) está agrupado aqui. A lógica de desenho mora em outros módulos:

- ``mural.layout``        calcula posições.
- ``mural.render_pillow`` desenha o PNG.
- ``mural.render_pptx``   gera o .pptx editável.

Os valores estão como constantes de módulo (em vez de dataclass) para que
mexer seja simples: abre o arquivo, troca o número, salva e roda.
"""

from __future__ import annotations

import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

from .utilitarios import rgb


# ───────────────────────────────────────────────────────────────────────────
# 1) Mês de referência
#    O mural é sempre do MÊS SEGUINTE ao atual, para casar com a query
#    em ``core/query.py`` (EXTRACT(MONTH FROM CURRENT_DATE + INTERVAL '1 month')).
#    Ou seja: se hoje é maio, o mural — e o nome do arquivo — sai como JUNHO.
#    Detecta o mês em português sem depender de locale do sistema (que
#    muitas vezes não tem pt_BR instalado).
#    Para forçar um mês específico, troque MES por uma string, ex.:
#        MES = "FEVEREIRO"
# ───────────────────────────────────────────────────────────────────────────

_MESES_PT = (
    "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
    "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO",
)

_HOJE = datetime.now()
_MES_REFERENCIA = (_HOJE.month % 12) + 1            # mês seguinte (1..12)
MES = _MESES_PT[_MES_REFERENCIA - 1]
ANO = _HOJE.year + (1 if _HOJE.month == 12 else 0)  # vira o ano em dez → jan


def _slug(texto: str) -> str:
    """Versão sem acentos/cedilha e em minúsculas — boa para nome de arquivo."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower()


# ───────────────────────────────────────────────────────────────────────────
# 2) Caminhos (entrada em assets/, saída em saida/)
#    Os arquivos de saída seguem MES e ANO automaticamente.
# ───────────────────────────────────────────────────────────────────────────

PASTA_ASSETS = Path("assets")
PASTA_SAIDA = Path("saida")
PASTA_FONTES = PASTA_ASSETS / "fontes"

TEMPLATE = PASTA_ASSETS / "template.png"
PLANILHA = PASTA_ASSETS / "aniversariantes.xlsx"
PLANILHA_FALLBACK = PASTA_ASSETS / "aniversariantes_exemplo.xlsx"

_NOME_BASE_SAIDA = f"mural_{_slug(MES)}_{ANO}"
ARQUIVO_SAIDA_PNG = PASTA_SAIDA / f"{_NOME_BASE_SAIDA}.png"
ARQUIVO_SAIDA_PPTX = PASTA_SAIDA / f"{_NOME_BASE_SAIDA}.pptx"


def obter_referencia(
    mes: int, ano: Optional[int] = None
) -> tuple[str, int, Path, Path]:
    """Devolve ``(mes_nome, ano, arquivo_png, arquivo_pptx)`` para o ``mes``.

    Permite gerar um mural para qualquer mês escolhido na UI sem depender
    das constantes ``MES``/``ANO`` deste módulo (que ficam fixadas no
    momento do ``import``). Quando ``ano`` é ``None``, usa o ano atual.
    """
    if not 1 <= mes <= 12:
        raise ValueError(f"mes deve estar entre 1 e 12 (recebido: {mes})")
    if ano is None:
        ano = datetime.now().year
    mes_nome = _MESES_PT[mes - 1]
    base = f"mural_{_slug(mes_nome)}_{ano}"
    return (
        mes_nome,
        ano,
        PASTA_SAIDA / f"{base}.png",
        PASTA_SAIDA / f"{base}.pptx",
    )


# ───────────────────────────────────────────────────────────────────────────
# 3) Fontes
#    - Caminho dos arquivos .ttf/.otf usados pelo Pillow para desenhar e medir.
#    - Nome (família) gravado no .pptx — precisa coincidir com a fonte
#      instalada no Canva/PowerPoint, senão eles substituem por outra.
# ───────────────────────────────────────────────────────────────────────────

FONTE_MES = "Ailerons 400.otf"
FONTE_DIA = "itoya-bold.ttf"
FONTE_NOME = "itoya-bold.ttf"
FONTE_CARGO = "itoya-bold.ttf"

PPTX_NOME_FONTE_MES = "Ailerons"
PPTX_NOME_FONTE_DIA = "itoya-bold"
PPTX_NOME_FONTE_NOME = "itoya-bold"
PPTX_NOME_FONTE_CARGO = "itoya-bold"

# Tamanhos em pixels (96 dpi).
TAMANHO_MES = 125
TAMANHO_DIA = 21
TAMANHO_NOME = 21
TAMANHO_CARGO = 21


# ───────────────────────────────────────────────────────────────────────────
# 4) Cores
# ───────────────────────────────────────────────────────────────────────────

COR_TURQUESA = rgb("#00a5ac")  # dia e cargo
COR_PRETO = rgb("#191919")     # nome (cinza quase preto)


# ───────────────────────────────────────────────────────────────────────────
# 5) Posição do título do mês
#    No Pillow o título é desenhado com anchor="mt" (centro/topo). O
#    OFFSET_X_MES desloca o ponto central em relação ao centro da imagem.
# ───────────────────────────────────────────────────────────────────────────

Y_MES = 220
OFFSET_X_MES = -250  # + direita / − esquerda


# ───────────────────────────────────────────────────────────────────────────
# 6) Layout das colunas
# ───────────────────────────────────────────────────────────────────────────

LARGURA_COLUNA_PX = 410
ALTURA_COLUNA_PX: Optional[int] = None  # None = altura_img - Y_INICIAL - MARGEM_INFERIOR
MARGEM_INFERIOR = 80
POSICAO_X_PRIMEIRA_COLUNA: Optional[int] = None  # None = bloco centralizado
Y_INICIAL = 335
MAX_COLUNAS = 6  # só aviso se estourar


# ───────────────────────────────────────────────────────────────────────────
# 7) Espaçamentos
#    Cada par "valor / multiplicador" funciona assim: se o valor for None,
#    ele é calculado como ``max(piso, base_fonte * multiplicador)``. Isso
#    deixa o mural "responsivo" caso você troque o tamanho da fonte.
# ───────────────────────────────────────────────────────────────────────────

ESPACO_DIA_PARA_NOME: Optional[int] = None
MULT_ESPACO_DIA_NOME = 0.80

ESPACO_ENTRE_COLUNAS: Optional[int] = None
MULT_ESPACO_ENTRE_COLUNAS = 0.40

ESPACO_ENTRE_PESSOAS: Optional[int] = None
MULT_ESPACO_ENTRE_PESSOAS = 0.45

ESPACO_NOME_PARA_CARGO: Optional[int] = None
MULT_ESPACO_NOME_PARA_CARGO = 0.18

ESPACO_ENTRE_LINHAS: Optional[int] = None
MULT_ESPACO_ENTRE_LINHAS = 0.10


# ───────────────────────────────────────────────────────────────────────────
# 8) Saída e debug
# ───────────────────────────────────────────────────────────────────────────

EXPORTAR_PPTX = True
PPTX_GRUPO_POR_COLUNA = True   # cada coluna vira um grupo arrastável no Canva
MODO_DEBUG = False             # desenha guias verdes nas células do PNG
