"""Mapeamento (departamento, função) -> 'Nome que deve aparecer'.

Lê a planilha de referência (Departamentos Grupo Bueno) e adiciona uma coluna
no DataFrame com o nome de exibição esperado.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Optional

import pandas as pd

ROMAN_RE = re.compile(r"\s+(?:[IVX]{1,4}|\d+)\s*$", flags=re.IGNORECASE)


def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def _norm(s: object) -> str:
    """Normaliza string para comparação: sem acento, minúsculo, espaços simples."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return ""
    txt = _strip_accents(str(s)).lower()
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def _limpar_funcao(funcao: object) -> str:
    """Remove prefixo de código ('000004 - X' -> 'X') e sufixo I/II/III/1/2."""
    if funcao is None or (isinstance(funcao, float) and pd.isna(funcao)):
        return ""
    txt = str(funcao).strip()
    # Remove prefixo numérico: "000004 - Auxiliar..." -> "Auxiliar..."
    if " - " in txt:
        head, _, rest = txt.partition(" - ")
        if head.strip().isdigit() or re.fullmatch(r"\d+", head.strip()):
            txt = rest.strip()
    # Remove sufixo de nivel (I, II, III, IV, 1, 2 ...) no fim
    txt = ROMAN_RE.sub("", txt).strip()
    return txt


class MapeamentoDepartamento:
    """Resolve o 'Nome que deve aparecer' a partir de (departamento, funcao)."""

    def __init__(
        self,
        por_funcao_dept: dict[tuple[str, str], str],
        por_dept: dict[str, str],
    ) -> None:
        self._por_funcao_dept = por_funcao_dept
        self._por_dept = por_dept

    def resolver(self, departamento: object, funcao: object) -> Optional[str]:
        dept_n = _norm(departamento)
        if not dept_n:
            return None
        func_n = _norm(_limpar_funcao(funcao))
        if func_n:
            v = self._por_funcao_dept.get((func_n, dept_n))
            if v:
                return v
        return self._por_dept.get(dept_n)


def carregar_mapeamento(path: str | Path) -> MapeamentoDepartamento:
    """Lê a planilha e constrói os índices de mapeamento."""
    df = pd.read_excel(path, header=0).dropna(how="all")
    df.columns = [c.strip() for c in df.columns]
    col_func = "Função"
    col_dept = "Departamento"
    col_alvo = "Nome que deve aparecer"
    faltando = [c for c in (col_func, col_dept, col_alvo) if c not in df.columns]
    if faltando:
        raise ValueError(
            f"Planilha de mapeamento sem colunas esperadas: {faltando}. "
            f"Encontradas: {df.columns.tolist()}"
        )

    por_funcao_dept: dict[tuple[str, str], str] = {}
    por_dept_counter: dict[str, Counter] = {}

    for _, row in df.iterrows():
        funcao = _norm(_limpar_funcao(row[col_func]))
        dept = _norm(row[col_dept])
        alvo = str(row[col_alvo]).strip()
        if not dept or not alvo:
            continue
        if funcao:
            por_funcao_dept.setdefault((funcao, dept), alvo)
        por_dept_counter.setdefault(dept, Counter())[alvo] += 1

    por_dept = {d: counter.most_common(1)[0][0] for d, counter in por_dept_counter.items()}
    return MapeamentoDepartamento(por_funcao_dept, por_dept)


def aplicar_resultado(
    df: pd.DataFrame,
    mapa: MapeamentoDepartamento,
    *,
    col_departamento: str = "departamento",
    col_funcao: str = "nomefuncao",
    col_destino: str = "resultado",
    fallback_para_departamento: bool = True,
) -> pd.DataFrame:
    """Adiciona ao DataFrame a coluna `col_destino` com o nome de exibição.

    Se não houver match e ``fallback_para_departamento`` for True, usa o valor
    da coluna ``col_departamento``; caso contrário deixa vazio.
    """
    if col_departamento not in df.columns:
        raise KeyError(f"Coluna ausente: {col_departamento!r}")

    funcoes = df[col_funcao] if col_funcao in df.columns else [None] * len(df)

    resultados = []
    for dept, func in zip(df[col_departamento], funcoes):
        valor = mapa.resolver(dept, func)
        if not valor and fallback_para_departamento:
            valor = "" if pd.isna(dept) else str(dept)
        resultados.append(valor or "")

    out = df.copy()
    out[col_destino] = resultados
    return out
