# Skills.md — Pipeline Modular PNCP

Especificação determinística das funções e subcomandos CLI do sistema de coleta, ETL e classificação de licitações do Portal Nacional de Contratações Públicas (PNCP).

---

## 1. Visão Geral da Arquitetura

O sistema segue o paradigma **puramente funcional**, onde cada arquivo em `modulos/` expõe uma função única, tipada e sem estado global mutável, orquestrada pelo roteador CLI `main.py`.

| Subcomando CLI | Módulo Responsável | Entrada Principal | Saída Determinística (JSON) |
| :--- | :--- | :--- | :--- |
| `coletar` | `modulos/coletar_pncp.py` | API PNCP (`HTTP GET`) | `{"paginas_processadas": int, "registros_coletados": int, "registros_novos": int}` |
| `montar-dataset` | `modulos/montar_dataset.py` | CSVs positivos + SQLite negativos | `{"total_registros": int, "irrelevantes_0": int, "relevantes_1": int}` |
| `treinar` | `modulos/treinar_classificador.py` | `dataset.csv` | `{"acuracia": float, "caminho_modelo": str}` + Relatório de Classificação |
| `filtrar` | `modulos/filtrar_relevantes.py` | SQLite bruto + `.joblib` | `{"total_processado": int, "total_relevante": int}` |

---

## 2. Especificação dos Comandos CLI (Few-Shot)

### 2.1 `coletar`
Coleta licitações paginadas da API do PNCP com *retry* e *backoff* exponencial e persiste no SQLite com extração automática via `JSON1`.

* **Assinatura da Função:** `coletar_pncp(caminho_db: str, url: str, params_base: dict[str, Any], limite_paginas: int | None = None, pausa_segundos: float = 0.5) -> dict[str, int]`
* **Parâmetros CLI:** `--db` (str), `--paginas` (int), `--modalidade` (int: `6`=Pregão, `8`=Dispensa).

**Exemplo Few-Shot 1 (Entrada):**
```bash
python main.py coletar --db pncp_demo.db --paginas 3 --modalidade 6
```
**Exemplo Few-Shot 1 (Saída):**
```json
{
  "paginas_processadas": 3,
  "registros_coletados": 150,
  "registros_novos": 150
}
```

---

### 2.2 `montar-dataset`
Consolida os arquivos CSV de exemplos positivos (`1`) e o banco SQLite de amostras negativas (`0`), aplica limpeza de `BLOB`/nulos, rotula IDs manuais e remove duplicatas.

* **Assinatura da Função:** `montar_dataset(csvs_positivos: list[str], db_negativos: str, ids_positivos: set[int], csv_saida: str) -> dict[str, int]`
* **Parâmetros CLI:** `--saida` (str).

**Exemplo Few-Shot 2 (Entrada):**
```bash
python main.py montar-dataset --saida dataset.csv
```
**Exemplo Few-Shot 2 (Saída):**
```json
{
  "total_registros": 672,
  "irrelevantes_0": 475,
  "relevantes_1": 197
}
```

---

### 2.3 `treinar`
Aplica pré-processamento NLP (`limpar_texto`), divide o dataset (80/20 estratificado), treina o pipeline `TfidfVectorizer` + `SGDClassifier(class_weight="balanced")` e serializa o modelo em `.joblib`.

* **Assinatura da Função:** `treinar_classificador(csv_dataset: str, caminho_saida_modelo: str) -> dict[str, float | str]`
* **Parâmetros CLI:** `--dataset` (str), `--modelo` (str).

**Exemplo Few-Shot 3 (Entrada):**
```bash
python main.py treinar --dataset dataset.csv --modelo modelo_relevancia.joblib
```
**Exemplo Few-Shot 3 (Saída):**
```json
{
  "acuracia": 0.9704,
  "caminho_modelo": "modelo_relevancia.joblib"
}
```

---

### 2.4 `filtrar`
Lê o banco SQLite de produção em lotes (`chunksize`) para evitar estouro de memória RAM, classifica cada registro e grava apenas os relevantes (`pred == 1`) em um novo banco SQLite.

* **Assinatura da Função:** `filtrar_relevantes(caminho_modelo: str, db_origem: str, db_destino: str, tamanho_lote: int = 2000) -> dict[str, int]`
* **Parâmetros CLI:** `--modelo` (str), `--db-origem` (str), `--db-destino` (str), `--lote` (int).

**Exemplo Few-Shot 4 (Entrada):**
```bash
python main.py filtrar --modelo modelo_relevancia.joblib --db-origem pncp_data_19000.db --db-destino licitacoes_filtradas_19k.db --lote 2000
```
**Exemplo Few-Shot 4 (Saída):**
```json
{
  "total_processado": 19947,
  "total_relevante": 965
}
```

---

## 3. Funções Utilitárias Internas (`modulos/`)

* `configurar_db(caminho_db: str) -> bool`: Cria a tabela `contratacoes` com colunas virtuais `STORED` (`pncp_id`, `orgao_nome`, `uf_sigla`, `objeto_compra`) e índices.
* `buscar_pagina(url: str, params: dict[str, Any], max_tentativas: int = 5, backoff_inicial: float = 1.0) -> tuple[list[dict[str, Any]], int | None] | None`: Realiza `GET` HTTP tratando códigos `200`, `204` e falhas de rede com espera exponencial.
* `salvar_registros(caminho_db: str, registros: list[dict[str, Any]], numero_pagina: int) -> int`: Executa `INSERT OR IGNORE` respeitando a restrição `UNIQUE(pncp_id)`.
* `limpar_texto(texto: str | None) -> str`: Normaliza para minúsculas, remove caracteres não alfabéticos, tokeniza e filtra *stopwords* em português e tokens com `len <= 2`.
