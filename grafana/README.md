# GRAFANA - ANÁLISE DE DADOS DO ARANDU

1.PAINÉIS

O Grafana lê o MySQL do sistema direto e cruza com a base externa de `dados-externos/gold`, ou seja nenhum dado é copiado pra outro banco. São 3 painéis, todos na pasta Arandu Digital.

PAINEL DO CLUBE (cliente) - A diretoria do Tamoios acompanhando nas mais diversas frentes a presença, progressão por classe, especialidades, documentos obrigatórios, consentimento LGPD e agenda. Aqui também entra o cruzamento da presença com chuva, feriado prolongado e eventos na cidade.

PAINEL DO ADMINISTRADOR - A equipe do ARANDU acompanhando dos detalhes mais técnicos ao mais simples o pipeline bronze, silver e gold, o tamanho de cada camada, o atraso de cada fonte, o volume do banco e as verificações de cadastro incompleto e integridade.

AUTO ATENDIMENTO - Quem usa escolhe o recorte(período, unidade, classe, gênero, desbravador), a medida e por onde quebrar, e os painéis se recalculam na hora. Não depende de ninguém montar relatório, o link da página já guarda os filtros escolhido.

2.SUBIR

Precisa do MySQL local do backend rodando com o banco `clube_tamoios` e do Docker. De dentro desta pasta é um comando só.

```bash
docker compose up -d --build
```

O `--build` refaz as duas imagens, sem ele uma mudança nos painéis ou no SQL não entra. Antes do Grafana sobe o container `arandu-grafana-dados`, que roda o `preparar_banco.py` e para. Ele cria o banco `arandu_analise` e o usuário `grafana_leitura`(só SELECT), carrega a gold e a lista de arquivos do pipeline e gera os dados de demonstração. O Grafana só sobe depois que ele termina sem erro, caso contrário o motivo aparece em `docker logs arandu-grafana-dados`.

Ele entra no MySQL como `root` com a senha `7425`, a mesma do `application.properties` do backend. Quem usa outra senha sobe com `ARANDU_DB_ROOT_PASSWORD=suasenha docker compose up -d`.

Depois é só abrir `http://localhost:3001` com `admin` / `admin`. A porta é 3001 e não 3000 pra não brigar com o Grafana da Aula 8, e os dois containers rodam com `network_mode: host` já que o MySQL do backend só escuta em `127.0.0.1`.

Tudo é refeito a cada `docker compose up`, então uma gold nova do notebook de `dados-externos` entra na próxima subida. Os painéis do sistema não precisam de carga porque leem o banco ao vivo.

3.DADOS DE DEMONSTRAÇÃO

O banco local tem pouquíssimas chamadas, então o `02_dados_demo.sql` cria as reuniões de sábado de 07/02/2026 até o dia em que roda e as presenças dos desbravadores ativos. Ele não duplica nada, a cada subida só entram os sábados que ainda não tem chamada, ou seja quem sobe o Grafana numa semana nova ganha a reunião daquela semana. A presença não é aleatória pura, ela cai com chuva forte e com feriado prolongado pra que o cruzamento com a base externa tenha o que mostrar. As chamadas ficam marcadas com `[demo]` no título e os eventos com `[demo-grafana]` na descrição.

Pra tirar tudo do banco local roda o `03_remover_demo.sql`, mas na próxima subida o demo volta. Quem não quer o demo sobe com `ARANDU_DEMO=0 docker compose up -d --build`.

```bash
mysql -uroot -p < sql/03_remover_demo.sql
```

4.AWS

Na AWS o Grafana sobe junto com o resto pelo `infra_arandu.sh`(ou pelo Terraform), não precisa fazer nada nesta pasta. A infra builda as duas imagens direto deste repo com o `docker build` apontando pra URL do git, por isso este repo precisa continuar público, igual ao do backend.

As duas imagens rodam na EC2 de backend. O `grafana-dados` roda uma vez depois que a API responde, cria o `arandu_analise` e o `grafana_leitura` no RDS com uma senha aleatória, carrega a gold e, no lugar das pastas locais, lista os objetos dos buckets bronze, silver e gold de verdade. Aqui o demo também roda, o RDS já recebe pessoas fictícias do `data.sql` do backend e sem o demo os gráficos de presença ficam vazios. Quando o clube começar a usar o sistema de verdade o demo tem que ser desligado com `GRAFANA_DEMO=0` no script ou `grafana_demo = false` no Terraform.

O acesso é pelo mesmo ALB do site, em `http://<alb>/grafana/`. O usuário é `admin` e a senha é gerada a cada provisionamento, o script mostra ela no final junto com a do RDS e no Terraform sai em `terraform output -raw grafana_admin_password`. Mudança nos painéis só chega na AWS depois do push na `main` e da opção 4 do script, que refaz as imagens.

5.LIMITES

A gold do clima termina em 31/07/2026 por causa da defasagem do INMET, então o painel do administrador mostra o clima em vermelho e as reuniões de agosto em diante caem em Sem dado de clima. Os dashboards ficam em `dashboards/` como JSON provisionado, uma mudança feita pela tela do Grafana precisa ser exportada pra esse arquivo, caso contrário ela some na próxima vez que o arquivo mudar e não chega no resto do grupo.
