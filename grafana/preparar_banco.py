import os
from pathlib import Path

import pymysql
from pymysql.constants import CLIENT

from carga_analise import FORMATO, gerar_sql

AQUI = Path(__file__).resolve().parent
BANCO = os.environ.get("ARANDU_DB_NAME", "clube_tamoios")
SENHA_LEITURA = os.environ.get("ARANDU_GRAFANA_DB_PASSWORD", "grafana_leitura")
DEMO = os.environ.get("ARANDU_DEMO", "1") == "1"
BUCKETS = os.environ.get("ARANDU_BUCKETS", "")


def ler_sql(nome):
    texto = (AQUI / "sql" / nome).read_text(encoding="utf-8")
    return texto.replace("{{banco_sistema}}", BANCO).replace("{{senha_leitura}}", SENHA_LEITURA)


def arquivos_s3():
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError

    s3 = boto3.client("s3")
    arquivos = []
    for par in BUCKETS.split(","):
        camada, bucket = par.split("=")
        try:
            for pagina in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket):
                for objeto in pagina.get("Contents", []):
                    arquivos.append({
                        "camada": camada,
                        "arquivo": objeto["Key"],
                        "bytes": objeto["Size"],
                        "linhas": None,
                        "modificado_em": objeto["LastModified"].strftime(FORMATO),
                    })
        except (BotoCoreError, ClientError) as erro:
            print(f"aviso: não deu para listar {bucket}: {erro}", flush=True)
    return arquivos


etapas = [
    ("schema de análise", ler_sql("01_schema_analise.sql")),
    ("carga da gold", gerar_sql(arquivos=arquivos_s3() if BUCKETS else None)),
]
if DEMO:
    etapas.append(("dados de demonstração", ler_sql("02_dados_demo.sql")))

conexao = pymysql.connect(
    host=os.environ.get("ARANDU_DB_HOST", "127.0.0.1"),
    port=int(os.environ.get("ARANDU_DB_PORT", "3306")),
    user=os.environ.get("ARANDU_DB_ROOT_USER", "root"),
    password=os.environ.get("ARANDU_DB_ROOT_PASSWORD", "7425"),
    charset="utf8mb4",
    autocommit=True,
    client_flag=CLIENT.MULTI_STATEMENTS,
)

with conexao:
    for nome, comandos in etapas:
        with conexao.cursor() as cursor:
            cursor.execute(comandos)
            while cursor.nextset():
                pass
        print(f"ok: {nome}", flush=True)
