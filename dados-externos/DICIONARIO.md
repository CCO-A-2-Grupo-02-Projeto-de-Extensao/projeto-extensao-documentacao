# Dicionário de dados — fatores externos

Dicionário das camadas **bronze → silver → gold** da base de fatores externos (clima, eventos na
cidade e feriados) e das chamadas do Arandu Digital, que dão a presença do clube. Bronze e Silver são geradas pelas Lambdas de
`projeto-extensao-infraestrutura/Infra - Terraform` (`lambda.tf`, `lambda_src/`); a Gold é gerada
pelo notebook `fatores-presenca.ipynb`.

Faixas de valores, nulos e contagens vêm dos arquivos versionados em `silver/` e `gold/` (recorte
2023-01-01 a 2026-07-31 para clima). O esquema é o mesmo que as Lambdas produzem.

## Visão geral

| Camada | Conjunto | Onde fica | Grão | Gerado por |
|---|---|---|---|---|
| 🥉 Bronze | Clima INMET | `s3://<bronze>/clima/inmet_{ano}_{versao}.zip` | um arquivo por ano | Lambda `arandu-fatores-inmet` |
| 🥉 Bronze | Eventos MusicBrainz | `s3://<bronze>/eventos/{versao_dump}/event.tar.xz` | um arquivo por dump | Lambda `arandu-fatores-musicbrainz` |
| 🥉 Bronze | Feriados ANBIMA | `s3://<bronze>/feriados/feriados_nacionais_{versao}.xls` | um arquivo por versão | Lambda `arandu-fatores-anbima` |
| 🥉 Bronze | Chamadas Arandu Digital | `s3://<bronze>/chamadas/presencas_{versao}.csv` | um arquivo por versão | Lambda `arandu-fatores-chamadas` |
| 🥉 Bronze | Manifesto | `s3://<bronze>/manifesto.csv` | uma linha por arquivo ingerido | as quatro Lambdas de ingestão |
| 🥈 Silver | `clima_horario` | `s3://<silver>/clima_horario.csv.gz` | uma hora | Lambda `arandu-fatores-silver` |
| 🥈 Silver | `eventos_cidade` | `s3://<silver>/eventos_cidade.csv.gz` | um evento × um dia | Lambda `arandu-fatores-silver` |
| 🥈 Silver | `feriados_nacionais` | `s3://<silver>/feriados_nacionais.csv.gz` | um dia de feriado | Lambda `arandu-fatores-silver` |
| 🥈 Silver | `presenca_chamadas` | `s3://<silver>/presenca_chamadas.csv.gz` | uma chamada | Lambda `arandu-fatores-silver` |
| 🥇 Gold | `fatores_presenca_dia` | `gold/fatores_presenca_dia.csv.gz` | um dia | notebook |
| 🥇 Gold | `cobertura_fontes` | `gold/cobertura_fontes.csv` | uma fonte | notebook |
| ⚙️ Controle | Lock do manifesto | DynamoDB `arandu-fatores-manifest-lock-{conta}` | um lock ativo | as quatro Lambdas de ingestão |

Nomes dos buckets (`s3.tf`): `<bronze>` = `arandu-bronze-{s3_member_tag}-{conta}` e
`<silver>` = `arandu-silver-{s3_member_tag}-{conta}`, sobrescrevíveis por `bucket_bronze_name` e
`bucket_silver_name`. O bucket Gold (`arandu-gold-…`) é criado, mas nenhuma Lambda escreve nele.

### Fluxo e agenda

| Lambda | Disparo | O que faz |
|---|---|---|
| `arandu-fatores-inmet` | EventBridge `cron(0 6 1 * ? *)` — dia 1 de cada mês, 06:00 UTC | baixa um zip por ano, de `INMET_START_YEAR` (2023) até o ano corrente |
| `arandu-fatores-musicbrainz` | EventBridge `cron(0 7 ? * MON *)` — segundas, 07:00 UTC | lê `LATEST` e baixa o `event.tar.xz` daquele dump |
| `arandu-fatores-anbima` | EventBridge `cron(0 8 1 * ? *)` — dia 1 de cada mês, 08:00 UTC | baixa a planilha de feriados |
| `arandu-fatores-chamadas` | EventBridge `cron(0 9 ? * SUN *)` — domingos, 09:00 UTC | consulta `presenca` × `chamada` no RDS e grava o CSV |
| `arandu-fatores-silver` | `s3:ObjectCreated:*` nos prefixos `clima/`, `eventos/`, `feriados/`, `chamadas/` | reprocessa a fonte inteira e sobrescreve a tabela Silver dela |

A ingestão é idempotente: se o objeto já existe na Bronze, não baixa de novo, só registra no
manifesto (que ignora `arquivo_s3` repetido). O sufixo `{versao}` são os 16 primeiros caracteres
do SHA-256 do `ETag` (ou do `Last-Modified`) devolvido pelo servidor, então um arquivo republicado
pela fonte gera um objeto novo, e o anterior fica preservado. Nas chamadas, que vêm do banco e não
de um servidor HTTP, o `{versao}` é o SHA-256 do próprio CSV: semana sem chamada nova não gera objeto.

---

## 🥉 Bronze

Os arquivos ficam **exatamente como a fonte publicou**. As tabelas abaixo listam só os campos que a
Silver lê; o resto do arquivo é preservado, mas não é usado.

### `clima/inmet_{ano}_{versao}.zip`

| Item | Valor |
|---|---|
| Fonte | INMET — `https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip` |
| Formato | ZIP com um CSV por estação automática; ~55–107 MB por ano |
| Arquivo usado | o CSV cujo nome contém `A701` (São Paulo – Mirante de Santana) |
| Codificação | `latin-1`, separador `;`, decimal com vírgula |
| Estrutura | 8 linhas de cabeçalho da estação (região, UF, código WMO, coordenadas…), depois o CSV |

| Coluna na fonte | Tipo | Exemplo | Vai para |
|---|---|---|---|
| `Data` (1ª coluna) | texto `AAAA/MM/DD` | `2024/01/01` | `clima_horario.instante` |
| `Hora UTC` (2ª coluna) | texto `HHMM UTC` | `0000 UTC` | `clima_horario.instante` |
| `PRECIPITAÇÃO TOTAL, HORÁRIO (mm)` | decimal com vírgula | `0` | `clima_horario.chuva_mm` |
| `TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)` | decimal com vírgula | `19,5` | `clima_horario.temp_c` |

As colunas de precipitação e temperatura são localizadas por trecho do nome (`PRECIPITA` e
`TEMPERATURA DO AR`), não por posição. `-9999` indica falha de sensor.

### `eventos/{versao_dump}/event.tar.xz`

| Item | Valor |
|---|---|
| Fonte | MusicBrainz — `https://data.metabrainz.org/pub/musicbrainz/data/json-dumps/{LATEST}/event.tar.xz` |
| Formato | TAR comprimido com XZ, ~47 MB |
| Arquivo usado | `mbdump/event` — um objeto JSON por linha (JSON Lines), UTF-8 |
| Versão | `{versao_dump}` é o conteúdo de `LATEST`, ex. `20260926-001002` |

| Campo JSON | Tipo | Uso na Silver |
|---|---|---|
| `name` | texto | `eventos_cidade.evento` |
| `type` | texto ou nulo | `eventos_cidade.tipo` |
| `cancelled` | booleano | `true` → evento descartado |
| `life-span.begin` | texto `AAAA-MM-DD` (pode vir parcial: `AAAA` ou `AAAA-MM`) | primeiro dia; se não for data completa, o evento sai |
| `life-span.end` | texto `AAAA-MM-DD` ou vazio | último dia; vazio ou inválido assume `begin` |
| `relations[].type` | texto | só relações `held at` contam |
| `relations[].place.name` | texto | `eventos_cidade.local` |
| `relations[].place.area.name` | texto | precisa ser `São Paulo` |

### `feriados/feriados_nacionais_{versao}.xls`

| Item | Valor |
|---|---|
| Fonte | ANBIMA — `https://www.anbima.com.br/feriados/arqs/feriados_nacionais.xls` (exige `Referer` de `feriados.asp`) |
| Formato | Excel 97 (`.xls`), primeira aba, cabeçalho na linha 1; lido com `xlrd` (Lambda Layer `arandu-fatores-xlrd`) |
| Cobertura | 2001–2099 |

| Coluna na fonte | Tipo | Exemplo | Vai para |
|---|---|---|---|
| `Data` | célula de data do Excel (ou texto `DD/MM/AAAA`) | `01/01/2001` | `feriados_nacionais.dia` |
| `Feriado` | texto | `Confraternização Universal` | `feriados_nacionais.nome_feriado` |

As quatro linhas de nota no rodapé da planilha ficam na coluna `Data` e são descartadas por não
converterem para data.

### `chamadas/presencas_{versao}.csv`

| Item | Valor |
|---|---|
| Fonte | MySQL do Arandu Digital (RDS `bdClubeDesbravadores`), tabelas `presenca` e `chamada` |
| Acesso | Lambda dentro da VPC, subnet privada do backend, SG `arandu-sg-lambda-banco`; lido com `pymysql` |
| Formato | CSV UTF-8, separador `,`, com cabeçalho; uma linha por registro de presença |
| Dados pessoais | nenhum: não sai id, nome nem qualquer outro campo do desbravador |

| Coluna | Tipo | Origem no banco | Vai para |
|---|---|---|---|
| `id_chamada` | inteiro | `chamada.idChamada` | `presenca_chamadas.id_chamada` |
| `data_chamada` | data `AAAA-MM-DD` | `chamada.data_chamada` | `presenca_chamadas.dia` |
| `presenca` | `0` ou `1` | `presenca.presenca`; nulo vira `0` | `presenca_chamadas.registros` e `presentes` |

### `manifesto.csv`

Registro de toda ingestão na Bronze. CSV UTF-8, separador `,`, na raiz do bucket.

| Coluna | Tipo | Nulo | Descrição | Exemplo |
|---|---|---|---|---|
| `fonte` | texto | não | origem do arquivo: `INMET`, `MusicBrainz`, `ANBIMA` ou `Arandu Digital` | `INMET` |
| `data_coleta` | timestamp ISO 8601 com fuso UTC | não | momento em que a Lambda registrou o arquivo | `2026-10-01T06:00:12.345678+00:00` |
| `tamanho_bytes` | inteiro | não | tamanho do objeto no S3, em bytes | `49483012` |
| `url` | texto | não | URL de onde o arquivo foi baixado; nas chamadas, `mysql://{host}/{banco}`, sem credencial | `https://portal.inmet.gov.br/uploads/dadoshistoricos/2024.zip` |
| `arquivo_s3` | texto | não | chave do objeto no bucket Bronze; **chave única** do manifesto | `clima/inmet_2024_3f9a1c0b7d2e4a51.zip` |

---

## 🥈 Silver

Uma tabela por fonte, limpa e tipada, no grão natural dela. Todas são CSV UTF-8, separador `,`,
com cabeçalho, comprimidas com gzip (`Content-Encoding: gzip`). Valor nulo é **campo vazio**. A
cada novo objeto na Bronze, a tabela da fonte é **reescrita inteira** (não é incremental).

### `clima_horario.csv.gz`

Uma linha por hora de leitura da estação A701. 31.389 linhas (2023-01-01 a 2026-07-31).

| Coluna | Tipo | Unidade | Nulo | Descrição | Regra de transformação | Exemplo |
|---|---|---|---|---|---|---|
| `instante` | timestamp com fuso (`AAAA-MM-DD HH:MM:SS-03:00`) | — | não | início da hora da leitura, no horário de São Paulo; **chave** | `Data` + `Hora UTC` convertidos de UTC para `America/Sao_Paulo`; `2400 UTC` vira 00:00 do dia seguinte; linhas com data/hora ilegível saem; só anos de 2023 até o corrente | `2023-01-01 00:00:00-03:00` |
| `chuva_mm` | decimal | mm | sim (2,8%) | precipitação acumulada na hora | vírgula → ponto; `-9999` ou vazio → nulo | `0.0` (faixa 0,0–82,0) |
| `temp_c` | decimal | °C | sim (1,4%) | temperatura do ar (bulbo seco) na hora | vírgula → ponto; `-9999` ou vazio → nulo | `20.4` (faixa 5,8–37,2) |

Ordenada por `instante`. Quando há mais de um zip do mesmo ano na Bronze, só o mais recente
(`LastModified`) é usado.

### `eventos_cidade.csv.gz`

Uma linha por evento por dia em que ele acontece em São Paulo. 235 linhas, 165 eventos, 148 dias
distintos.

| Coluna | Tipo | Nulo | Descrição | Regra de transformação | Exemplo |
|---|---|---|---|---|---|
| `dia` | data `AAAA-MM-DD` | não | dia em que o evento acontece | evento de vários dias vira uma linha por dia, de `begin` a `end` inclusive; `end` anterior a `begin` descarta o evento | `2016-03-02` |
| `evento` | texto | não | nome do evento no MusicBrainz | `name`, sem alteração | `PIANO OPERA: music from FINAL FANTASY` |
| `local` | texto | não | local onde o evento foi realizado (40 distintos) | `place.name` da primeira relação `held at` cuja área é `São Paulo` | `Allianz Parque` |
| `tipo` | texto | sim (0,9%) | categoria do evento | `type`, sem alteração | `Concert` |

Domínio de `tipo`: `Concert` (118), `Festival` (92), `Convention/Expo` (22), `Launch event` (1),
vazio (2).

Chave: (`dia`, `evento`, `local`, `tipo`) — linhas idênticas são deduplicadas. Saem os eventos
cancelados, os sem relação `held at` em São Paulo e os sem `begin` completo. Não há filtro de ano:
a tabela traz o histórico inteiro (o mais antigo é de 1983); o recorte acontece na Gold.

### `feriados_nacionais.csv.gz`

Uma linha por dia de feriado nacional. 1.263 linhas, de 2001-01-01 a 2099-12-25.

| Coluna | Tipo | Nulo | Descrição | Regra de transformação | Exemplo |
|---|---|---|---|---|---|
| `dia` | data `AAAA-MM-DD` | não | data do feriado; **chave** | célula `Data` convertida; linhas que não convertem (rodapé) saem; se a data repete, fica a primeira ocorrência | `2001-01-01` |
| `nome_feriado` | texto | não | nome do feriado (13 distintos) | `Feriado`, sem espaços nas pontas; linhas com nome vazio saem | `Confraternização Universal` |

Ordenada por `dia`. Só feriados **nacionais** — municipais (ex.: 25 de janeiro) não constam.

### `presenca_chamadas.csv.gz`

Uma linha por chamada registrada no sistema.

| Coluna | Tipo | Nulo | Descrição | Regra de transformação | Exemplo |
|---|---|---|---|---|---|
| `id_chamada` | inteiro | não | chamada no Arandu Digital; **chave** | `id_chamada` da Bronze | `1` |
| `dia` | data `AAAA-MM-DD` | não | data da chamada | `data_chamada`; linhas com data inválida saem | `2026-05-20` |
| `registros` | inteiro | não | quantos desbravadores constam na chamada | contagem de linhas da chamada | `5` |
| `presentes` | inteiro | não | quantos estavam presentes | soma de `presenca` | `4` |

Ordenada por `dia` e `id_chamada`. Quando há mais de uma exportação na Bronze, só a mais recente
(`LastModified`) é usada — cada uma é uma foto completa do banco.

---

## 🥇 Gold

Gerada pelo notebook `fatores-presenca.ipynb` a partir das quatro tabelas Silver. Não é produzida
pelas Lambdas.

### `fatores_presenca_dia.csv.gz`

Uma linha por dia do calendário, de 2023-01-01 a 2026-12-31 (1.461 dias). CSV UTF-8 com gzip.
Booleanos são gravados como `True`/`False`.

| Coluna | Tipo | Unidade | Nulo | Descrição | Regra de cálculo | Exemplo |
|---|---|---|---|---|---|---|
| `data` | data `AAAA-MM-DD` | — | não | dia do calendário; **chave** | todos os dias de 2023 a 2026, tenham dado ou não | `2023-01-01` |
| `chuva_mm` | decimal (1 casa) | mm | sim (10,5%) | chuva acumulada no dia | soma de `clima_horario.chuva_mm` do dia (horas nulas são ignoradas); nulo se o dia não tem nenhuma leitura | `1.0` (faixa 0,0–125,6) |
| `temp_media_c` | decimal (1 casa) | °C | sim (10,5%) | temperatura média do dia | média de `clima_horario.temp_c` do dia | `22.7` (faixa 10,7–30,4) |
| `temp_max_c` | decimal (1 casa) | °C | sim (10,5%) | temperatura máxima do dia | máximo de `clima_horario.temp_c` do dia | `27.6` (faixa 12,7–37,2) |
| `eventos_sp` | inteiro | eventos | não | quantidade de eventos na cidade no dia | contagem de linhas de `eventos_cidade` com aquele `dia`; 0 quando não há | `0` (faixa 0–5) |
| `nome_feriado` | texto | — | sim (96,5%) | nome do feriado nacional | `feriados_nacionais.nome_feriado` do dia; nulo se não é feriado | `Confraternização Universal` |
| `feriado` | booleano | — | não | o dia é feriado nacional | `nome_feriado` não nulo | `True` |
| `fim_de_semana` | booleano | — | não | o dia é sábado ou domingo | dia da semana ≥ sábado | `True` |
| `registros_chamada` | inteiro | registros | não | registros de presença das chamadas do dia | soma de `presenca_chamadas.registros` do dia; 0 quando não houve chamada | `5` |
| `percentual_presenca` | decimal (1 casa) | % | sim | presença do clube no dia | `presentes / registros × 100` somando as chamadas do dia; nulo quando não houve chamada | `80.0` |
| `feriado_prolongado` | booleano | — | não | o dia faz parte de um bloco sem expediente | `feriado` ou `fim_de_semana`, dentro de uma sequência de **3 ou mais** dias seguidos nessa condição | `False` |

Os 153 dias sem `chuva_mm` são exatamente 2026-08-01 a 2026-12-31, ainda não publicados pelo INMET
(defasagem de cerca de um mês). As colunas de temperatura têm um nulo a mais: 2023-11-27, dia com
leitura de chuva mas sem nenhuma de temperatura.

### `cobertura_fontes.csv`

Uma linha por fonte, com a janela real em que ela tem dado dentro da Gold. CSV UTF-8 sem
compressão.

| Coluna | Tipo | Nulo | Descrição | Regra de cálculo | Exemplo |
|---|---|---|---|---|---|
| `fonte` | texto | não | `clima`, `eventos`, `feriados` ou `chamadas`; **chave** | — | `clima` |
| `primeiro_dia` | data `AAAA-MM-DD` | não | primeiro dia com dado | menor `data` em que a fonte tem dado | `2023-01-01` |
| `ultimo_dia` | data `AAAA-MM-DD` | não | último dia com dado | maior `data` em que a fonte tem dado | `2026-07-31` |
| `dias_com_dado` | inteiro | não | quantidade de dias com dado | clima: `temp_media_c` não nulo; eventos: `eventos_sp > 0`; feriados: `feriado` verdadeiro; chamadas: `percentual_presenca` não nulo | `1307` |
| `cobertura_pct` | decimal (1 casa) | não | percentual dos 1.461 dias com dado | `dias_com_dado / 1461 × 100` | `89.5` |

---

## ⚙️ Controle — lock do manifesto (DynamoDB)

Tabela `arandu-fatores-manifest-lock-{conta}`, cobrança sob demanda. Garante que duas Lambdas de
ingestão não reescrevam o `manifesto.csv` ao mesmo tempo. Fica vazia fora das execuções.

| Atributo | Tipo DynamoDB | Papel | Descrição | Exemplo |
|---|---|---|---|---|
| `lock_id` | `S` | chave de partição | nome do recurso travado; hoje sempre `manifesto.csv` | `manifesto.csv` |
| `owner` | `S` | — | UUID da execução que detém o lock; só ela pode removê-lo | `8b1e6c2a-…` |
| `expires_at` | `N` | TTL | epoch em segundos; o lock vale por 120 s e, vencido, pode ser tomado por outra execução | `1791262812` |

Quem não consegue o lock tenta de novo a cada 0,25 s, até 120 vezes, e então falha com
`TimeoutError`.

---

## Divergências entre o notebook e as Lambdas

| Ponto | Notebook | Lambda |
|---|---|---|
| Colunas do `manifesto.csv` | `arquivo`, `mb`, `origem` | `fonte`, `data_coleta`, `tamanho_bytes`, `url`, `arquivo_s3` |
| Nome dos arquivos Bronze | `inmet_2024.zip`, `event.tar.xz`, `feriados_nacionais.xls`, `chamadas.csv` | com prefixo de fonte e sufixo de versão (ver acima) |
| Histórico na Bronze | sobrescreve; um arquivo por fonte/ano | preserva cada versão publicada |
| Banco das chamadas | MySQL local (`clube_tamoios`) ou o apontado por `ARANDU_DB_*` | RDS `bdClubeDesbravadores` |
| Gold | gera | não gera; o bucket Gold existe vazio |

O `manifesto.csv` versionado em `bronze/` segue o formato do notebook. Na AWS vale o formato da
Lambda.
