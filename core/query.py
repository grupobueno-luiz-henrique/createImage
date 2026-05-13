"""SQL principal — query parametrizada por mês (1..12).

O placeholder ``:mes`` é resolvido pelo SQLAlchemy quando passamos
``params={"mes": <int>}`` em ``pd.read_sql_query`` (ver ``DatabaseManager``).
"""

from sqlalchemy import text


QUERY_EMPLOYEES = text("""
SELECT INITCAP(f."nome") AS nome,
       (EXTRACT(DAY FROM f."data_nascimento"))::integer AS dia,
       f."codigo",
       d."nome" AS departamento,
       f."nomefuncao"
FROM econtador.funcionarios f
LEFT JOIN econtador.departamentos d
       ON d.id = f.departamento_id
WHERE f.demissao IS NULL
  AND EXTRACT(MONTH FROM f."data_nascimento") = :mes
ORDER BY dia;
""")
