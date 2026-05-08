"""Leitura e validação do Excel de aniversariantes.

Espera as colunas ``dia`` (int), ``nome`` (texto) e ``cargo`` (texto). A
saída é uma lista de :class:`Aniversariante` ordenada por dia.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from .tipos import Aniversariante


COLUNAS_OBRIGATORIAS = {"dia", "nome", "cargo"}


def carregar_aniversariantes(
    caminho: Path,
    caminho_fallback: Optional[Path] = None,
) -> list[Aniversariante]:
    """Lê a planilha, valida e devolve a lista ordenada por dia.

    ``caminho_fallback`` é usado quando o arquivo principal não existe —
    útil para rodar a calibração com uma planilha de exemplo.
    """
    arquivo = _resolver_caminho(caminho, caminho_fallback)
    df = pd.read_excel(arquivo)

    faltando = COLUNAS_OBRIGATORIAS - set(df.columns)
    if faltando:
        raise ValueError(
            f"A planilha precisa ter as colunas {sorted(COLUNAS_OBRIGATORIAS)}. "
            f"Faltando: {sorted(faltando)}. Encontradas: {list(df.columns)}"
        )

    df = df.sort_values(by="dia").reset_index(drop=True)
    return [
        Aniversariante(
            dia=str(int(linha["dia"])).zfill(2),
            nome=str(linha["nome"]).upper(),
            cargo=str(linha["cargo"]).upper(),
        )
        for _, linha in df.iterrows()
    ]


def _resolver_caminho(principal: Path, fallback: Optional[Path]) -> Path:
    if principal.exists():
        return principal
    if fallback is not None and fallback.exists():
        print(f"⚠️  {principal} não encontrado — usando {fallback}")
        return fallback
    msg = f"Planilha não encontrada: {principal}"
    if fallback is not None:
        msg += f" (também não há fallback em {fallback})"
    raise FileNotFoundError(msg)
