QUERY_EMPLOYEES = """
SELECT INITCAP(f."nome") AS nome,
       (EXTRACT(DAY FROM f."nascimento"))::integer AS dia,
       f."codigo",
       d."nome" AS departamento,
       f."nomefuncao"
FROM econtador.funcionarios f
LEFT JOIN econtador.departamentos d
       ON d.id = f.departamento_id
WHERE f.demissao IS NULL
  AND EXTRACT(MONTH FROM f."nascimento") = EXTRACT(MONTH FROM CURRENT_DATE + INTERVAL ' 0 month')
ORDER BY f."nome";
"""