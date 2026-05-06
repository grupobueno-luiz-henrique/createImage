# Mural de Aniversariantes - Grupo Bueno

Script Python que lê uma planilha Excel e gera automaticamente o mural
de aniversariantes do mês a partir de um template.

## 📦 Instalação

```bash
pip install pillow pandas openpyxl
```

## 📁 Estrutura de pastas necessária

```
mural_aniversariantes/
├── gerar_mural.py
├── template.png             ← seu template em branco
├── aniversariantes.xlsx     ← planilha do mês
└── fontes/
    ├── Ailerons 400.otf
    └── itoya-bold.ttf
```

## 🎨 Preparando o template

1. Abre o template original no Canva
2. Faz uma cópia (pra não perder o original)
3. **Apaga todos os textos placeholder**: FUNCIONARIO, CARGO e os números 00
4. Mantém: fundo, título "ANIVERSARIANTES", logo do Grupo Bueno
5. Exporta como **PNG em alta resolução** (ideal: 1920x1280px ou maior)
6. Salva como `template.png` na pasta do script

## 📋 Preparando a planilha

Cria um arquivo Excel chamado `aniversariantes.xlsx` com **exatamente** essas colunas:

| dia | nome           | cargo       |
|-----|----------------|-------------|
| 2   | João Silva     | Vendedor    |
| 5   | Maria Santos   | Gerente     |
| 8   | Pedro Costa    | Estoquista  |

⚠️ **Importante**: o script já ordena por dia automaticamente, então
você pode adicionar os nomes em qualquer ordem.

## 🔧 Calibração (passo mais importante)

Como cada template tem dimensões e proporções diferentes, você precisa
ajustar as posições dos textos. Faz assim:

### 1. Ativa o modo debug

No `gerar_mural.py`, mude:
```python
MODO_DEBUG = True
```

### 2. Roda o script

```bash
python gerar_mural.py
```

### 3. Abre a imagem gerada

Você vai ver linhas verdes mostrando onde os textos estão sendo desenhados.

### 4. Ajusta os valores

Mexe nessas variáveis pra alinhar com seu template:

- `Y_MES` e `OFFSET_X_MES` → posição vertical e nudge horizontal do nome do mês
- `LARGURA_COLUNA_PX` → largura horizontal fixa de cada coluna
- `ALTURA_COLUNA_PX` → altura útil de cada coluna; `None` usa `imagem - Y_INICIAL - MARGEM_INFERIOR`
- `MARGEM_INFERIOR` → folga até o pé da imagem (só usada quando `ALTURA_COLUNA_PX = None`)
- `POSICAO_X_PRIMEIRA_COLUNA` → `None` centraliza o bloco; número fixa o X da 1ª coluna
- `Y_INICIAL` → onde começa a primeira linha
- `ESPACO_ENTRE_COLUNAS` → distância horizontal entre uma coluna e a seguinte (`None` = proporcional à fonte)
- `ESPACO_DIA_PARA_NOME` → espaço **depois** do número do dia (`None` = proporcional à fonte)
- `ESPACO_ENTRE_PESSOAS` → espaço entre o **fim do cargo** e o **topo** da próxima entrada
- `ESPACO_NOME_PARA_CARGO` → espaço entre a **base** do nome e o **topo** do cargo
- `ESPACO_ENTRE_LINHAS` (`MULT_ESPACO_ENTRE_LINHAS`) → espaço quando o nome ou o cargo precisa quebrar em várias linhas (`None` = proporcional à fonte)
- `MAX_COLUNAS` → só aviso de segurança caso a planilha estoure

> Nomes que estourarem a `LARGURA_COLUNA_PX` são quebrados automaticamente em palavras; o cargo segue o mesmo critério. A altura para o cálculo das colunas leva em conta as linhas extras.

### 5. Quando estiver alinhado

Volta `MODO_DEBUG = False` e gera a versão final.

## 🚀 Uso mensal (depois de calibrado)

Toda vez que precisar gerar o mural de um novo mês:

1. Atualiza a planilha `aniversariantes.xlsx` com os nomes do mês
2. Muda no script:
   ```python
   MES = "FEVEREIRO"
   ARQUIVO_SAIDA = "mural_fevereiro_2026.png"
   ```
3. Roda: `python gerar_mural.py`
4. Pronto! O arquivo é gerado em segundos.

## 💡 Dicas

- **Nome muito longo cortando**: diminui `MAX_COLUNAS`, aumenta `META_LINHAS_POR_COLUNA` (menos colunas = faixas mais largas), afina margens ou diminui o `TAMANHO_NOME`
- **Texto fora do template**: provavelmente você exportou o template numa resolução diferente. Reajusta as posições proporcionalmente
- **Quero usar outras fontes**: só trocar os caminhos `FONTE_*` para os arquivos `.ttf` ou `.otf` desejados
- **Quero centralizar o nome**: posso te passar uma versão alternativa que centraliza, é só pedir

## ❓ Problemas comuns

**"Template não encontrado"** → confere se o arquivo `template.png` está
na mesma pasta do script.

**"Planilha precisa ter as colunas..."** → confere se sua planilha tem
exatamente as colunas `dia`, `nome` e `cargo` (em minúsculas).

**Fonte não carrega** → confere se o caminho do arquivo `.ttf`/`.otf`
está correto e se o arquivo existe.
