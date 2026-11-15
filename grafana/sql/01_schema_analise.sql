CREATE DATABASE IF NOT EXISTS arandu_analise CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

USE arandu_analise;

CREATE TABLE IF NOT EXISTS fatores_dia (
    dia DATE PRIMARY KEY,
    chuva_mm DECIMAL(6,1),
    temp_media_c DECIMAL(4,1),
    temp_max_c DECIMAL(4,1),
    eventos_sp INT NOT NULL,
    nome_feriado VARCHAR(80),
    feriado BOOLEAN NOT NULL,
    feriado_prolongado BOOLEAN NOT NULL,
    fim_de_semana BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS cobertura_fontes (
    fonte VARCHAR(20) PRIMARY KEY,
    primeiro_dia DATE,
    ultimo_dia DATE,
    dias_com_dado INT NOT NULL,
    cobertura_pct DECIMAL(5,1) NOT NULL
);

CREATE TABLE IF NOT EXISTS arquivos_pipeline (
    camada VARCHAR(10) NOT NULL,
    arquivo VARCHAR(120) NOT NULL,
    bytes BIGINT NOT NULL,
    linhas INT,
    modificado_em DATETIME NOT NULL,
    carregado_em DATETIME NOT NULL,
    PRIMARY KEY (camada, arquivo)
);

CREATE USER IF NOT EXISTS 'grafana_leitura'@'localhost' IDENTIFIED BY 'grafana_leitura';
GRANT SELECT ON clube_tamoios.* TO 'grafana_leitura'@'localhost';
GRANT SELECT ON arandu_analise.* TO 'grafana_leitura'@'localhost';
