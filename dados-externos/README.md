# Base externa: fatores da cidade e a presença no clube

Cruza o percentual de presença das chamadas do Arandu Digital com **três fatores externos do dia** —
clima, eventos na cidade e feriados. Recorte: **cidade de São Paulo**, 2023–2026.

O tratamento segue **bronze → silver → gold**:

| Camada | O que é | Vai para o Git? |
|---|---|---|
| 🥉 `bronze/` | o arquivo como a fonte publicou, sem uma linha alterada, + `manifesto.csv` | não (403 MB) |
| 🥈 `silver/` | uma tabela por fonte, limpa e tipada, no grão natural dela | sim (148 KB) |
| 🥇 `gold/` | a tabela de análise: uma linha por dia | sim (20 KB) |

- `fatores-presenca.ipynb` — o notebook, já executado (abre com as saídas prontas).
- `gold/fatores_presenca_dia.csv.gz` — 1.461 dias × 8 colunas.
- `gold/cobertura_fontes.csv` — a janela real de cada fonte.

## A tabela gold

| Coluna | O que é |
|---|---|
| `chuva_mm` | chuva acumulada no dia |
| `temp_media_c`, `temp_max_c` | temperatura do dia |
| `eventos_sp` | megaeventos culturais na cidade (shows, festivais e convenções) |
| `feriado`, `nome_feriado` | feriado nacional |
| `feriado_prolongado` | **derivada** — dia dentro de um bloco de 3+ dias seguidos sem expediente |
| `fim_de_semana` | sábado ou domingo |

## Rodar

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install pandas jupyter xlrd
jupyter lab fatores-presenca.ipynb
```

A camada bronze baixa ~403 MB e pula o que já estiver em `bronze/`.

## Fontes

| O quê | Onde | Atualização |
|---|---|---|
| Clima (horário, por estação) | INMET — `portal.inmet.gov.br/uploads/dadoshistoricos/{ANO}.zip` | mensal |
| Eventos na cidade | MusicBrainz — `data.metabrainz.org/pub/musicbrainz/data/json-dumps/LATEST/event.tar.xz` | 2×/semana |
| Feriados nacionais | ANBIMA — `anbima.com.br/feriados/arqs/feriados_nacionais.xls` | estático, cobre 2001–2099 |

Todas são arquivo para download, não API.

## Por que só três fatores

O escopo começou com cinco. **Trânsito** e **futebol** foram cortados por falta de janela:

- A base de lentidão da **CET-SP** foi descontinuada em 31/12/2023 — o próprio dataset traz o aviso.
- A base do **Brasileirão** na Base dos Dados declara atualização recorrente, mas o arquivo não é
  tocado desde **26/08/2024**, que é também a data do último jogo que ele contém.

As chamadas do clube são de 2026 em diante, então nenhuma das duas jamais cruzaria com elas. Um fator
que entra vazio é pior do que um fator ausente: sugere que foi testado.

## O que a camada silver corrige

- **Clima em UTC.** O INMET publica com a coluna `Hora UTC`. Agrupar por dia sem converter para
  `America/Sao_Paulo` joga 3 horas de cada dia para o dia errado — justamente a faixa do fim de tarde.
  `-9999` é falha de sensor e vira nulo (645 leituras de chuva e 212 de temperatura só em 2023).
- **Eventos de mais de um dia.** Os 15 eventos multi-dia viram uma linha por dia, o que leva a
  cobertura de 132 para 148 dias com evento. Os 14 cancelados e os 2 sem data completa saem.
- **Rodapé da planilha de feriados.** A ANBIMA fecha o arquivo com quatro linhas de nota dentro da
  coluna de data; são descartadas por não converterem para data.

## Limites conhecidos

- **Amostra pequena.** Reunião semanal dá ~50 pontos por ano. Para três fatores ainda é pouco: o
  resultado provável é chuva e feriadão aparecerem e evento ficar no ruído. "Não há evidência" é
  resultado legítimo.
- **`eventos_sp = 0` significa "ninguém cadastrou", não "não teve evento".** O MusicBrainz é
  colaborativo e a distribuição é irregular — em 2026 há 2 eventos em fevereiro, 1 em maio e 21 em
  julho, quase todos do Anime Friends. O erro é conservador: enfraquece correlação, não inventa uma.
- **A base de eventos é musical na origem.** Cataloga convenção e festival quando há música envolvida
  (118 Concert, 92 Festival, 22 Convention/Expo). Não tem futebol, F1, corrida de rua nem feira de
  negócios.
- **Feriados nacionais só.** A listagem da ANBIMA exclui feriados municipais — 25 de janeiro,
  aniversário da cidade, não está lá.
- **Clima com defasagem.** O INMET publica com cerca de um mês de atraso, então o fim do ano corrente
  fica vazio e preenche a cada atualização (cobertura de 89,5% hoje).
- **Clima de uma estação só.** A A701 fica no Mirante de Santana, zona norte; chuva em São Paulo é
  muito local. Trocar `ESTACAO` no notebook resolve.
