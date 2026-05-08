import os

from pathlib import Path
from dotenv import load_dotenv


# Raiz do repositório (config/ → sobe dois níveis).
SCRIPT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = SCRIPT_DIR / ".env"
MAPEAMENTO_PATH = SCRIPT_DIR / "assets" / "regras" / "Departamentos Grupo Bueno VF 1.xls"

for enc in ("utf-8", "latin-1", "cp1252"):
    try:
        load_dotenv(ENV_PATH, encoding=enc, override=True)
        test_val = os.getenv("DB_HOST", "")
        test_val.encode("utf-8")
        print(f".env carregado com encoding: {enc}")
        break
    except (UnicodeDecodeError, UnicodeEncodeError):
        continue

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASSWORD")

print(f"Host: {DB_HOST}")
print(f"Port: {DB_PORT}")
print(f"DB:   {DB_NAME}")
print(f"User: {DB_USER}")