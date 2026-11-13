# Pipeline Modular de Coleta e Classificação de Licitações (PNCP)

Arquitetura puramente funcional, modularizada e orientada à interface de linha de comando (CLI) para extração de dados da API do Portal Nacional de Contratações Públicas (PNCP), pré-processamento NLP e classificação supervisionada (`TF-IDF` + `SGDClassifier`).

## Estrutura do Projeto

```text
pncp_pipeline/
├── main.py                        # Roteador CLI (Entrypoint)
├── config.py                      # Constantes e configurações globais
├── requirements.txt               # Dependências do projeto
├── Skills.md                      # Especificação determinística para Agentes de IA
└── modulos/
    ├── __init__.py
    ├── configurar_db.py           # Schema SQLite + colunas geradas JSON1
    ├── buscar_pagina.py           # Requisição HTTP resiliente (Retry/Backoff)
    ├── salvar_registros.py        # Persistência em lote no SQLite
    ├── coletar_pncp.py            # Orquestrador de paginação (ETL)
    ├── limpar_texto.py            # Função pura de NLP / Regex / Stopwords
    ├── montar_dataset.py          # ETL de montagem do gabarito supervisionado
    ├── treinar_classificador.py   # Treinamento e avaliação TF-IDF + SGD
    └── filtrar_relevantes.py      # Inferência em lotes (Batch) para produção
```

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

## Uso via CLI

```bash
# 1. Coleta demonstrativa (3 páginas de Pregão)
python main.py coletar --db pncp_demo.db --paginas 3

# 2. Montagem do dataset supervisionado
python main.py montar-dataset

# 3. Treinamento e avaliação do classificador
python main.py treinar

# 4. Filtragem em lotes no banco de produção
python main.py filtrar --db-origem pncp_data_19000.db --db-destino licitacoes_filtradas_19k.db
```
