import csv
import gzip
import sys
from datetime import datetime
from pathlib import Path

PADRAO = Path(__file__).resolve().parent.parent / "dados-externos"
FORMATO = "%Y-%m-%d %H:%M:%S"


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
        return []
    valores = ",\n".join("(" + ", ".join(sql(linha.get(c)) for c in colunas) + ")" for linha in linhas)
    return [f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES\n{valores};"]


def arquivos_locais(dados):
    arquivos = []
    for camada in ("bronze", "silver", "gold"):
        pasta = dados / camada
        if not pasta.is_dir():
            continue
        for caminho in sorted(pasta.iterdir()):
            if not caminho.is_file():
                continue
            info = caminho.stat()
            contavel = camada != "bronze" and caminho.suffix in (".gz", ".csv")
            arquivos.append({
                "camada": camada,
                "arquivo": caminho.name,
                "bytes": info.st_size,
                "linhas": len(ler_csv(caminho)) if contavel else None,
                "modificado_em": datetime.fromtimestamp(info.st_mtime).strftime(FORMATO),
            })
    return arquivos


def gerar_sql(dados=PADRAO, arquivos=None):
    agora = datetime.now().strftime(FORMATO)
    comandos = ["USE arandu_analise;", "START TRANSACTION;", "DELETE FROM fatores_dia;"]

    fatores = ler_csv(dados / "gold" / "fatores_presenca_dia.csv.gz")
    for linha in fatores:
        linha["dia"] = linha["data"]
    comandos += inserir(
        "fatores_dia",
        ["dia", "chuva_mm", "temp_media_c", "temp_max_c", "eventos_sp", "nome_feriado",
         "feriado", "feriado_prolongado", "fim_de_semana"],
        fatores,
    )

    comandos.append("DELETE FROM cobertura_fontes;")
    comandos += inserir(
        "cobertura_fontes",
        ["fonte", "primeiro_dia", "ultimo_dia", "dias_com_dado", "cobertura_pct"],
        ler_csv(dados / "gold" / "cobertura_fontes.csv"),
    )

    comandos.append("DELETE FROM arquivos_pipeline;")
    arquivos = arquivos_locais(dados) if arquivos is None else arquivos
    for arquivo in arquivos:
        arquivo["carregado_em"] = agora
    comandos += inserir("arquivos_pipeline",
                        ["camada", "arquivo", "bytes", "linhas", "modificado_em", "carregado_em"], arquivos)

    comandos.append("COMMIT;")
    return "\n".join(comandos)


if __name__ == "__main__":
    print(gerar_sql(Path(sys.argv[1]) if len(sys.argv) > 1 else PADRAO))
