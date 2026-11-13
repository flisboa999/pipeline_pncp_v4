from typing import Any

URL_BASE: str = "https://pncp.gov.br/api/consulta"
ENDPOINT: str = "/v1/contratacoes/proposta"
URL_FINAL: str = f"{URL_BASE}{ENDPOINT}"

PARAMS_API_PADRAO: dict[str, Any] = {
    "dataFinal": 20251216,
    "codigoModalidadeContratacao": 6,
    "pagina": 1,
    "tamanhoPagina": 50,
}

CAMINHO_DB_PADRAO: str = "pncp_data_19000.db"
DB_TREINO_NEGATIVOS: str = "pncp_data_500.db"
IDS_RELEVANTES_CADERNO: set[int] = {5, 85, 164, 199, 319, 327, 463}
ARQUIVOS_CSV_POSITIVOS: list[str] = ["dataset_2024.csv", "dataset_2025.csv"]

CAMINHO_SAIDA_DATASET: str = "dataset.csv"
CAMINHO_SAIDA_MODELO: str = "modelo_relevancia.joblib"
CAMINHO_DB_FILTRADO: str = "licitacoes_filtradas_19k.db"
TAMANHO_LOTE: int = 2000
