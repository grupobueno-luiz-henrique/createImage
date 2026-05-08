# Mural de Aniversariantes — Grupo Bueno

Gera o mural mensal a partir de uma planilha Excel + um template PNG. Saída
em **PNG** (Pillow) e **PowerPoint editável** (.pptx) — esse último abre no
Canva/PowerPoint com cada texto em uma caixa, e cada coluna em um grupo
arrastável.

## Estrutura do projeto

```
pillow_draft/
├── gerar_mural.py            # entrypoint da CLI (orquestra tudo)
├── mural/                    # pacote com a lógica
│   ├── config.py             # ⚙️ constantes editáveis (mês, fontes, ...)
│   ├── tipos.py              # dataclasses compartilhadas
│   ├── utilitarios.py        # rgb(), conversões px → EMU/pt
│   ├── planilha.py           # leitura do Excel
│   ├── layout.py             # cálculo de posições (Pillow só p/ medir)
│   ├── render_pillow.py      # geração do PNG
│   └── render_pptx.py        # geração do .pptx
├── assets/
│   ├── template.png          # template em branco (fundo do mural)
│   ├── aniversariantes.xlsx  # planilha do mês
│   └── fontes/               # arquivos .ttf/.otf
└── saida/                    # PNG e .pptx gerados
```

## Instalação

```bash
pip install -e .
# ou só as dependências:
pip install pillow pandas openpyxl python-pptx
```

## Preparando o template

1. Abra o template original no Canva e faça uma cópia.
2. Apague todos os textos (FUNCIONARIO, CARGO, números 00 etc.).
3. Mantenha fundo, título "ANIVERSARIANTES" e logo.
4. Exporte como PNG em alta resolução e salve em `assets/template.png`.

## Preparando a planilha

`assets/aniversariantes.xlsx` precisa ter exatamente estas colunas:

| dia | nome           | cargo       |
|-----|----------------|-------------|
| 2   | João Silva     | Vendedor    |
| 5   | Maria Santos   | Gerente     |
| 8   | Pedro Costa    | Estoquista  |

A ordem das linhas não importa: o script ordena por dia automaticamente.

## Rodar

```bash
python gerar_mural.py
```

Sai em `saida/`:

- `mural_<mes>_<ano>.png` — versão final.
- `mural_<mes>_<ano>.pptx` — versão editável para Canva/PowerPoint.

Antes de gerar, o script **remove** todos os `mural_*.png` e `mural_*.pptx`
já existentes em `saida/` — assim, ao mudar o mês (maio → junho), não ficam
arquivos antigos misturados.

## Onde mexer (`mural/config.py`)

Tudo que você normalmente quer trocar está em seções comentadas no topo do
arquivo:

| Seção                | O que controla                                   |
|----------------------|--------------------------------------------------|
| Mês de referência    | `MES = "JANEIRO"`                                |
| Caminhos             | template, planilha, fontes, arquivos de saída    |
| Fontes               | arquivos `.ttf/.otf`, tamanhos, nome no PPTX     |
| Cores                | `COR_TURQUESA`, `COR_PRETO`                      |
| Posição do mês       | `Y_MES`, `OFFSET_X_MES`                          |
| Layout das colunas   | largura, altura, posição da 1ª coluna, ...       |
| Espaçamentos         | absolutos OU proporcionais à fonte (None)        |
| Saída e debug        | `EXPORTAR_PPTX`, `PPTX_GRUPO_POR_COLUNA`, debug  |

## Calibração visual (modo debug)

1. Em `mural/config.py`, deixe `MODO_DEBUG = True`.
2. Rode `python gerar_mural.py`.
3. Abra o PNG: linhas verdes mostram as células de cada pessoa.
4. Ajuste `Y_INICIAL`, `LARGURA_COLUNA_PX`, espaçamentos.
5. Quando estiver alinhado, volte `MODO_DEBUG = False`.

## Como o código está dividido

- O **layout** calcula a posição absoluta (em pixels) de **cada texto**;
  o resultado é um `LayoutMural` (dataclass).
- O **renderer Pillow** recebe esse `LayoutMural` e desenha o PNG.
- O **renderer python-pptx** recebe o **mesmo** `LayoutMural` e gera o
  `.pptx`. Como ambos partem das mesmas coordenadas, PNG e PPTX batem
  visualmente.
- Os "ajustes finos" do PPTX (paddings da caixa de texto) ficam isolados
  no topo de `mural/render_pptx.py`, deixando claro que são calibragem.

## Trocando para outro mês

1. Atualize `assets/aniversariantes.xlsx`.
2. Em `mural/config.py`, mude:
   ```python
   MES = "FEVEREIRO"
   ARQUIVO_SAIDA_PNG  = PASTA_SAIDA / "mural_fevereiro_2026.png"
   ARQUIVO_SAIDA_PPTX = PASTA_SAIDA / "mural_fevereiro_2026.pptx"
   ```
3. Rode `python gerar_mural.py`.

## Problemas comuns

- **"Template não encontrado"** → confira `assets/template.png`.
- **"A planilha precisa ter as colunas..."** → as colunas devem ser
  `dia`, `nome`, `cargo` (em minúsculas).
- **Fonte não carrega** → verifique se o `.ttf/.otf` está em
  `assets/fontes/` e se o nome em `mural/config.py` bate.
- **No Canva a fonte saiu trocada** → o nome em `PPTX_NOME_FONTE_*`
  precisa coincidir com a fonte instalada no Canva (ou enviada ao Brand
  Kit). Se aparecer `Itoya Bold` na lista, ajuste para esse texto.
