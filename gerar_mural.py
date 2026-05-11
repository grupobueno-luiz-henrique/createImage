"""
Gerador de Mural de Aniversariantes do Mês — Grupo Bueno
========================================================

Este arquivo é apenas o ponto de entrada da CLI. A lógica está dividida
em camadas no pacote ``mural/``:

- ``mural.config``        → constantes editáveis (mês, fontes, posições...).
- ``mural.planilha``      → leitura/validação do Excel.
- ``mural.layout``        → cálculo das posições (independente de renderer).
- ``mural.render_pillow`` → desenha o PNG.
- ``mural.render_pptx``   → exporta o ``.pptx`` editável (Canva/PowerPoint).

Para mudar o mês, fontes, espaçamentos ou caminhos: edite ``mural/config.py``.

Uso:
    python gerar_mural.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from mural import config as cfg
from mural.layout import calcular_layout, carregar_fontes_pillow
from mural.planilha import carregar_aniversariantes
from mural.render_pillow import renderizar_png
from mural.render_pptx import exportar_pptx
from core.service import Service

service = Service()


def _limpar_murais_antigos(pasta_saida: Path) -> None:
    """Apaga ``mural_*.png`` e ``mural_*.pptx`` da pasta de saída.

    Assim, ao mudar o mês (ex.: maio → junho), não ficam arquivos do mês
    anterior — só o par recém-gerado permanece.
    """
    if not pasta_saida.is_dir():
        return
    removidos: list[str] = []
    for padrao in ("mural_*.png", "mural_*.pptx"):
        for arq in pasta_saida.glob(padrao):
            arq.unlink()
            removidos.append(arq.name)
    if removidos:
        print(
            f"🗑️  Saídas antigas removidas ({len(removidos)}): "
            f"{', '.join(sorted(removidos))}"
        )


def main() -> None:
    _limpar_murais_antigos(cfg.PASTA_SAIDA)
    sucesso = service.run()
    if not sucesso:
        print("Erro ao executar o serviço")
        return

    aniversariantes = carregar_aniversariantes(cfg.PLANILHA, cfg.PLANILHA_FALLBACK)
    print(f"📋 {len(aniversariantes)} aniversariantes encontrados")

    if not cfg.TEMPLATE.exists():
        raise FileNotFoundError(f"Template não encontrado: {cfg.TEMPLATE}")
    with Image.open(cfg.TEMPLATE) as img:
        tamanho_imagem = img.size

    fontes = carregar_fontes_pillow(cfg.PASTA_FONTES)
    layout = calcular_layout(aniversariantes, tamanho_imagem, fontes)

    renderizar_png(layout, fontes, cfg.TEMPLATE, cfg.ARQUIVO_SAIDA_PNG)

    if cfg.EXPORTAR_PPTX:
        exportar_pptx(layout, cfg.TEMPLATE, cfg.ARQUIVO_SAIDA_PPTX)


if __name__ == "__main__":
    main()
