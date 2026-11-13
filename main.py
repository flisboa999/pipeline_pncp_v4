import argparse
import json
import config
from modulos.coletar_pncp import coletar_pncp
from modulos.montar_dataset import montar_dataset
from modulos.treinar_classificador import treinar_classificador
from modulos.filtrar_relevantes import filtrar_relevantes


def criar_parser_cli() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pipeline Modular de Coleta e Classificação de Licitações (PNCP)"
    )
    subparsers = parser.add_subparsers(dest="comando", required=True)

    # Comando 1: coletar
    cmd_coletar = subparsers.add_parser("coletar", help="Coleta licitações da API do PNCP")
    cmd_coletar.add_argument("--db", default=config.CAMINHO_DB_PADRAO, help="Caminho do SQLite de saída")
    cmd_coletar.add_argument("--paginas", type=int, default=3, help="Limite de páginas a coletar")
    cmd_coletar.add_argument("--modalidade", type=int, default=6, help="Código da modalidade (6=Pregão, 8=Dispensa)")

    # Comando 2: montar-dataset
    cmd_etl = subparsers.add_parser("montar-dataset", help="Gera o CSV supervisionado de treino")
    cmd_etl.add_argument("--saida", default=config.CAMINHO_SAIDA_DATASET, help="Caminho do CSV final")

    # Comando 3: treinar
    cmd_treinar = subparsers.add_parser("treinar", help="Treina e serializa o modelo TF-IDF + SGD")
    cmd_treinar.add_argument("--dataset", default=config.CAMINHO_SAIDA_DATASET, help="CSV de treino")
    cmd_treinar.add_argument("--modelo", default=config.CAMINHO_SAIDA_MODELO, help="Arquivo .joblib de saída")

    # Comando 4: filtrar
    cmd_filtrar = subparsers.add_parser("filtrar", help="Filtra banco de produção em lotes")
    cmd_filtrar.add_argument("--modelo", default=config.CAMINHO_SAIDA_MODELO, help="Modelo .joblib")
    cmd_filtrar.add_argument("--db-origem", default=config.CAMINHO_DB_PADRAO, help="Banco bruto de entrada")
    cmd_filtrar.add_argument("--db-destino", default=config.CAMINHO_DB_FILTRADO, help="Banco filtrado de saída")
    cmd_filtrar.add_argument("--lote", type=int, default=config.TAMANHO_LOTE, help="Tamanho do lote")

    return parser


def main() -> None:
    parser = criar_parser_cli()
    args = parser.parse_args()

    if args.comando == "coletar":
        params = {**config.PARAMS_API_PADRAO, "codigoModalidadeContratacao": args.modalidade}
        resultado = coletar_pncp(
            caminho_db=args.db,
            url=config.URL_FINAL,
            params_base=params,
            limite_paginas=args.paginas,
        )
        print(json.dumps(resultado, indent=2, ensure_ascii=False))

    elif args.comando == "montar-dataset":
        resultado = montar_dataset(
            csvs_positivos=config.ARQUIVOS_CSV_POSITIVOS,
            db_negativos=config.DB_TREINO_NEGATIVOS,
            ids_positivos=config.IDS_RELEVANTES_CADERNO,
            csv_saida=args.saida,
        )
        print(json.dumps(resultado, indent=2, ensure_ascii=False))

    elif args.comando == "treinar":
        resultado = treinar_classificador(
            csv_dataset=args.dataset,
            caminho_saida_modelo=args.modelo,
        )
        relatorio = resultado.pop("relatorio")
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        print("\nRelatório de Classificação:\n", relatorio)

    elif args.comando == "filtrar":
        resultado = filtrar_relevantes(
            caminho_modelo=args.modelo,
            db_origem=args.db_origem,
            db_destino=args.db_destino,
            tamanho_lote=args.lote,
        )
        print(json.dumps(resultado, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
