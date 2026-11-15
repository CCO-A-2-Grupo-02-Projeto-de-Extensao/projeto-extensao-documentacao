import csv
import gzip
import sys
from datetime import datetime
from pathlib import Path

DADOS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "dados-externos"
AGORA = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ler_csv(caminho):
    abrir = gzip.open if caminho.suffix == ".gz" else open
    with abrir(caminho, "rt", encoding="utf-8", newline="") as arquivo:
        return list(csv.DictReader(arquivo))


def sql(valor):
    if valor is None or valor == "":
        return "NULL"
    if valor in ("True", "False"):
        return "TRUE" if valor == "True" else "FALSE"
    return "'" + str(valor).replace("\\", "\\\\").replace("'", "''") + "'"


def inserir(tabela, colunas, linhas):
    if not linhas:
        return
    print(f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES")
    print(",\n".join("(" + ", ".join(sql(linha.get(c)) for c in colunas) + ")" for linha in linhas) + ";")


def contar_linhas(caminho):
    if caminho.suffix == ".gz" or caminho.suffix == ".csv":
        return len(ler_csv(caminho))
    return None


print("USE arandu_analise;")
print("START TRANSACTION;")

print("DELETE FROM fatores_dia;")
fatores = ler_csv(DADOS / "gold" / "fatores_presenca_dia.csv.gz")
for linha in fatores:
    linha["dia"] = linha["data"]
inserir(
    "fatores_dia",
    ["dia", "chuva_mm", "temp_media_c", "temp_max_c", "eventos_sp", "nome_feriado",
     "feriado", "feriado_prolongado", "fim_de_semana"],
    fatores,
)

print("DELETE FROM cobertura_fontes;")
inserir(
    "cobertura_fontes",
    ["fonte", "primeiro_dia", "ultimo_dia", "dias_com_dado", "cobertura_pct"],
    ler_csv(DADOS / "gold" / "cobertura_fontes.csv"),
)

print("DELETE FROM arquivos_pipeline;")
arquivos = []
for camada in ("bronze", "silver", "gold"):
    pasta = DADOS / camada
    if not pasta.is_dir():
        continue
    for caminho in sorted(pasta.iterdir()):
        if not caminho.is_file():
            continue
        info = caminho.stat()
        arquivos.append({
            "camada": camada,
            "arquivo": caminho.name,
            "bytes": info.st_size,
            "linhas": contar_linhas(caminho) if camada != "bronze" else None,
            "modificado_em": datetime.fromtimestamp(info.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "carregado_em": AGORA,
        })
inserir("arquivos_pipeline", ["camada", "arquivo", "bytes", "linhas", "modificado_em", "carregado_em"], arquivos)

print("COMMIT;")
