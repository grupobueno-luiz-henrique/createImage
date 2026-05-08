from datetime import datetime

import pandas as pd

from config import SCRIPT_DIR, MAPEAMENTO_PATH
from core.database import DatabaseManager
from core.mapeamento import aplicar_resultado, carregar_mapeamento
from core.query import QUERY, QUERY_EMPLOYEES

# Ordem e cabeçalhos no Excel (coluna no DataFrame, título na planilha).
EXCEL_COLUMNS: list[tuple[str, str]] = [
    ("nome", "nome"),
    ("dia", "dia"),
    ("resultado", "cargo"),
]


PREPOSICOES = frozenset({"de", "da", "do", "das", "dos", "e"})


def encurtar_nome(nome: object, limite: int = 25) -> str:
    texto = str(nome).strip()
    if not texto:
        return texto
    if len(texto) <= limite:
        return texto.title()

    partes = texto.split()
    while len(partes) > 2 and (
        len(" ".join(partes)) > limite or partes[-1].lower() in PREPOSICOES
    ):
        partes.pop()

    return " ".join(partes).title()


def _nome_encurtado_para_excel(val: object) -> object:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return val
    return encurtar_nome(val)


def _datetime_naive_for_excel(df: pd.DataFrame) -> pd.DataFrame:
    """Remove timezone das datas: openpyxl não aceita datetimes com tz."""

    def cell_naive(x):
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return x
        if isinstance(x, pd.Timestamp):
            return x.tz_localize(None) if x.tzinfo is not None else x
        if isinstance(x, datetime) and x.tzinfo is not None:
            return x.replace(tzinfo=None)
        return x

    out = df.copy()
    for col in out.columns:
        s = out[col]
        if pd.api.types.is_datetime64tz_dtype(s):
            out[col] = s.dt.tz_localize(None)
        elif s.dtype == object:
            sample = s.dropna().head(200)
            if any(
                isinstance(v, (datetime, pd.Timestamp)) and getattr(v, "tzinfo", None)
                for v in sample
            ):
                out[col] = s.map(cell_naive)
    return out

def _dataframe_para_excel(df: pd.DataFrame) -> pd.DataFrame:
    """Reordena e renomeia colunas conforme EXCEL_COLUMNS; ignora chaves ausentes."""
    keys_labels = [(k, lbl) for k, lbl in EXCEL_COLUMNS if k in df.columns]
    if not keys_labels:
        return df
    keys = [k for k, _ in keys_labels]
    out = df[keys].copy()
    rename = {k: lbl for k, lbl in keys_labels if lbl != k}
    if rename:
        out = out.rename(columns=rename)
    return out


class Service:
    def __init__(self):
        self.database = DatabaseManager()

    def exibir_terminal(self, df):
        """Exibe os dados formatados no terminal."""
        print("\n" + "=" * 150)
        print("LISTAGEM ANIVERSARIOS DO MES")
        print("=" * 150)

        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 200)
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_colwidth", 30)

        print(df.to_string(index=False))
        print(f"\nTotal: {len(df)} aniversariantes")

    def exportar_excel(self, df):
        """Exporta o DataFrame para um arquivo Excel (.xlsx)."""
        out = _datetime_naive_for_excel(df)
        if "nome" in out.columns:
            out = out.copy()
            out["nome"] = out["nome"].map(_nome_encurtado_para_excel)
        out = _dataframe_para_excel(out)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_arquivo = SCRIPT_DIR / f"aniversariantes.xlsx"

        if nome_arquivo.is_file():
            nome_arquivo.unlink()

        with pd.ExcelWriter(nome_arquivo, engine="openpyxl") as writer:
            out.to_excel(writer, sheet_name="Funcionarios", index=False)

            ws = writer.sheets["Funcionarios"]
            for col_idx, col_name in enumerate(out.columns, 1):
                max_len = max(
                    int(out[col_name].map(lambda v: 0 if pd.isna(v) else len(str(v))).max()),
                    len(col_name),
                ) + 2
                ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = min(max_len, 40)

        print(f"\nArquivo Excel gerado: {nome_arquivo}")
        return str(nome_arquivo)

    def run(self) -> bool:
        """Executa o programa principal."""
        try:
            self.database.connect()
            df = self.database.consultar_funcionarios(QUERY_EMPLOYEES)

            if df.empty:
                print("Nenhum aniversariante encontrado")
                return True

            mapa = carregar_mapeamento(MAPEAMENTO_PATH)
            df = aplicar_resultado(df, mapa)

            print(df)
            #self.exibir_terminal(df)
            self.exportar_excel(df)
            return True
        except Exception as e:
            print(f"ERRO ao executar o serviço: {e}")
            return False
        finally:
            self.database.close()
