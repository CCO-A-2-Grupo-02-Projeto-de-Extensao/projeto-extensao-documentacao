# Correções de Segurança — Evidências

Registro das vulnerabilidades encontradas no Arandu Digital e das correções aplicadas,
com o código antes e depois de cada alteração.

As imagens em `evidencias/` foram geradas a partir do **histórico do git**, não de
capturas de tela: cada trecho é o conteúdo real que estava versionado no commit
indicado. Isso é verificável — `git show <commit>:<arquivo>` reproduz o mesmo texto.

## Achados

| # | Vulnerabilidade | Categoria OWASP Top 10:2025 | CWE | Repositório | Commit |
|---|---|---|---|---|---|
| 01 | Chave criptográfica fixa no código | A04 Cryptographic Failures | CWE-321 | backend | `3d5813b` |
| 02 | Credenciais fixas no código (aplicação) | A02 Security Misconfiguration | CWE-798 | backend | `3d5813b` |
| 03 | Credencial fixa no código (infraestrutura) | A02 Security Misconfiguration | CWE-798 | infraestrutura | `784e135` |
| 04 | Dado sensível gravado em log | A09 Security Logging & Alerting Failures | CWE-532 | backend | `e47e03c` |
| 05 | Encerramento de sessão incompleto | A07 Identification and Authentication Failures | CWE-613 | frontend | `0b4af83` |
| 06 | Sessão inválida sem tratamento | A07 Identification and Authentication Failures | CWE-613 | frontend | `e4cda2d` |

A referência usada é o [OWASP Top 10:2025](https://owasp.org/Top10/2025/0x00_2025-Introduction/),
publicado em novembro de 2025. Equivalências na versão de 2021, caso o material da
disciplina use a lista anterior: A04→A02, A02→A05, A09→A09, A07→A07.

## Detalhamento

**01 — Chave criptográfica fixa no código.** O segredo que assina os tokens JWT estava
escrito em `JwtUtil.java` e versionado em repositório público. Quem tivesse acesso ao
código conseguia forjar um token válido para qualquer usuário. Passou a ser lido da
variável de ambiente `JWT_SECRET`, gerada aleatoriamente a cada provisionamento.

**02 e 03 — Credenciais fixas no código.** Senha do banco local, do usuário
administrativo e do RDS gravadas em texto puro. As da aplicação passaram a aceitar
variável de ambiente, mantendo um valor padrão apenas para desenvolvimento local. A do
RDS passou a ser gerada com `openssl rand` a cada execução do script de infraestrutura.

**04 — Dado sensível gravado em log.** O filtro de autenticação imprimia o header
`Authorization` completo a cada requisição, o que expunha o token JWT nos logs do
container — um token em log é reutilizável por quem tiver acesso a ele.

**05 — Encerramento de sessão incompleto.** O botão "Sair" apenas navegava para a tela
de login, sem remover o token do `localStorage`. A sessão continuava válida: bastava
retornar a `/dashboard` para reentrar, já que a proteção de rota verificava apenas se o
token existia, não se era válido. Em máquina compartilhada, o usuário seguinte herdava
a sessão.

**06 — Sessão inválida sem tratamento.** Não havia tratamento para resposta HTTP 401.
Com o token expirado (validade de 1 dia) ou invalidado por rotação do segredo, a
aplicação mantinha o usuário na área autenticada exibindo tela vazia, sem mensagem e sem
redirecionamento.

## Pendências identificadas e não corrigidas

Registradas por afetarem categorias de maior severidade que as acima:

- **Senhas armazenadas em texto puro no banco** — A04:2025, CWE-256. O login compara a
  senha diretamente via `findByEmailAndSenha`, sem hash. Corrigir exige adotar BCrypt e
  regerar as senhas do `data.sql`.
- **Ausência de controle de autorização** — A01:2025, CWE-862. O `JwtFilter` autentica
  com lista de permissões vazia, então todo usuário autenticado tem o mesmo acesso. O
  campo `Cargo` existe no banco mas não é verificado em nenhum endpoint.

## Prevenção adotada

Os três repositórios de código passaram a rodar `gitleaks` no CI a cada push, com regras
próprias em `.gitleaks.toml` para os padrões que originaram os achados 01 a 03 — senha
literal em `.properties`, segredo literal em `.java` e senha literal em `.sh`. As regras
padrão da ferramenta não detectam esses casos, por serem voltadas a tokens de provedores
conhecidos.

## Regerar as imagens

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python gerar_evidencias.py
```

Os trechos de código ficam em `trechos/` e as imagens são escritas em `evidencias/`.
