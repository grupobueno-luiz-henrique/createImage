import sys
import os
import pandas as pd
import requests

from datetime import datetime
from sqlalchemy import create_engine
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, SCRIPT_DIR


class DatabaseManager:
    """Gerencia conexão e consultas ao banco de dados PostgreSQL."""

    def __init__(self, host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                 user=DB_USER, password=DB_PASS):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.engine = None

    def _validar_credenciais(self):
        """Valida se as credenciais necessárias estão definidas."""
        faltando = []
        if not self.user:
            print(self.user)
            faltando.append("DB_USER")
        if not self.password:
            faltando.append("DB_PASSWORD")
        if faltando:
            print(f"ERRO: Variaveis de ambiente nao definidas: {', '.join(faltando)}")
            sys.exit(1)

    def connect(self):
        """Estabelece conexão com o banco de dados."""
        self._validar_credenciais()

        try:
            url = (
                f"postgresql+psycopg2://{self.user}:{self.password}"
                f"@{self.host}:{self.port}/{self.dbname}"
            )
            self.engine = create_engine(url)
            print("Conexao com o banco estabelecida com sucesso.")
            return self.engine
        except Exception as e:
            print(f"ERRO ao conectar no banco: {e}")
            sys.exit(1)

    def consultar_funcionarios(self, QUERY):
        """Executa a query e retorna um DataFrame."""
        if self.engine is None:
            self.connect()

        print("Executando consulta...")
        df = pd.read_sql_query(QUERY, self.engine)
        print(f"Total de funcionarios encontrados: {len(df)}")
        return df

    def close(self):
        """Fecha a conexão com o banco."""
        if self.engine is not None:
            self.engine.dispose()
            print("Conexao encerrada.")