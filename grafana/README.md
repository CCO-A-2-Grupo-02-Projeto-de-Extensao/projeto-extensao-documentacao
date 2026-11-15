# GRAFANA - ANÁLISE DE DADOS DO ARANDU

1.PAINÉIS

O Grafana lê o MySQL do sistema direto e cruza com a base externa de `dados-externos/gold`, ou seja nenhum dado é copiado pra outro banco. São 3 painéis, todos na pasta Arandu Digital.

PAINEL DO CLUBE (cliente) - A diretoria do Tamoios acompanhando nas mais diversas frentes a presença, progressão por classe, especialidades, documentos obrigatórios, consentimento LGPD e agenda. Aqui também entra o cruzamento da presença com chuva, feriado prolongado e eventos na cidade.

PAINEL DO ADMINISTRADOR - A equipe do ARANDU acompanhando dos detalhes mais técnicos ao mais simples o pipeline bronze, silver e gold, o tamanho de cada camada, o atraso de cada fonte, o volume do banco e as verificações de cadastro incompleto e integridade.

AUTO ATENDIMENTO - Quem usa escolhe o recorte(período, unidade, classe, gênero, desbravador), a medida e por onde quebrar, e os painéis se recalculam na hora. Não depende de ninguém montar relatório, o link da página já guarda os filtros escolhido.

2.SUBIR

Precisa do MySQL local do backend rodando com o banco `clube_tamoios` e do Docker. Segue abaixo os comandos, na ordem, de dentro desta pasta.

```bash
mysql -uroot -p < sql/01_schema_analise.sql
python3 carga_analise.py | mysql -uroot -p
mysql -uroot -p < sql/02_dados_demo.sql
docker compose up -d
```

O primeiro cria o banco `arandu_analise` e o usuário `grafana_leitura`, que só tem SELECT. O segundo carrega a gold e a lista de arquivos do pipeline, ele usa só biblioteca padrão do Python sendo assim não precisa de venv. O terceiro é opcional e está explicado em 3.DADOS DE DEMONSTRAÇÃO.

Depois é só abrir `http://localhost:3001` com `admin` / `admin`. A porta é 3001 e não 3000 pra não brigar com o Grafana da Aula 8, e o container roda com `network_mode: host` já que o MySQL do backend só escuta em `127.0.0.1`.

Toda vez que o notebook de `dados-externos` gerar uma gold nova basta rodar o `carga_analise.py` de novo, os painéis do sistema não precisam de carga porque leem o banco ao vivo.

3.DADOS DE DEMONSTRAÇÃO

O banco local tem pouquíssimas chamadas, então o `02_dados_demo.sql` cria as reuniões de sábado de 07/02/2026 até 14/11/2026 e as presenças dos 49 desbravadores ativos. A presença não é aleatória pura, ela cai com chuva forte e com feriado prolongado pra que o cruzamento com a base externa tenha o que mostrar. As chamadas ficam marcadas com `[demo]` no título e os eventos com `[demo-grafana]` na descrição.

Nunca rode esse script no RDS. Pra tirar tudo do banco local é só rodar o `03_remover_demo.sql`.

```bash
mysql -uroot -p < sql/03_remover_demo.sql
```

4.LIMITES

A gold do clima termina em 31/07/2026 por causa da defasagem do INMET, então o painel do administrador mostra o clima em vermelho e as reuniões de agosto em diante caem em Sem dado de clima. Os dashboards ficam em `dashboards/` como JSON provisionado, uma mudança feita pela tela do Grafana precisa ser exportada pra esse arquivo, caso contrário ela some na próxima vez que o arquivo mudar e não chega no resto do grupo.
