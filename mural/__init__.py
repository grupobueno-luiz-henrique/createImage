"""Pacote do gerador de mural de aniversariantes.

Os módulos estão organizados em camadas (cada um faz UMA coisa):

- ``config``        → constantes editáveis (mês, fontes, cores, espaçamentos).
- ``utilitarios``   → conversões de unidade e parsing de cor.
- ``tipos``         → dataclasses compartilhadas (Aniversariante, LayoutMural...).
- ``planilha``      → leitura e validação do Excel.
- ``layout``        → calcula a posição absoluta (em px) de cada texto;
                      depende do Pillow apenas para *medir* o texto.
- ``render_pillow`` → recebe um ``LayoutMural`` e desenha o PNG.
- ``render_pptx``   → recebe o mesmo ``LayoutMural`` e gera o .pptx editável.

A separação entre layout (cálculo) e renderers (desenho) garante que o PNG
e o PPTX usam exatamente as mesmas coordenadas.
"""

__all__ = [
    "config",
    "layout",
    "planilha",
    "render_pillow",
    "render_pptx",
    "tipos",
    "utilitarios",
]
