# Deploy em Producao no EasyPanel - Copy Trade Dashboard

## Objetivo

Este documento deixa o deploy em EasyPanel **decision-complete** para o estado atual do sistema:

- API v2 com sessao por cookie HttpOnly + CSRF
- Redis obrigatorio em producao (rate limit + estado de sessao)
- Postgres para persistencia
- Frontend React servido por Nginx
- Hardening ativo (docs/openapi desativados em producao, CORS explicito, fail-fast de secrets)
- Dependencias de auth/hardening atualizadas (FastAPI `0.128.2`, Starlette `0.49.3`, PyJWT `2.11.0`)

### Licoes aprendidas nesta implantacao

- O frontend pode estar 100% OK e ainda assim falhar em dados se `GET /api/public/stats` retornar `500`.
- `GET /api/health` pode retornar `200` mesmo com credencial de Postgres errada (endpoint nao consulta banco).
- Em EasyPanel, `404 Not Found` com tela padrao no dominio da API normalmente indica dominio/proxy mapeado errado.
- Em `Source = Github`, o campo `Caminho de Build` aceita **pasta**, nao arquivo (`backend/Dockerfile` ali gera `Invalid`).
- `VITE_API_URL` vazio em `/env-config.js` quebra o frontend mesmo com build correto.
- Senha de banco com caracteres especiais pode complicar URL (`@`, `%`) e causar erro de interpolation no Alembic.

---

## Arquitetura de servicos

### Servicos obrigatorios

1. `copytrade-postgres` (PostgreSQL 15)
2. `copytrade-redis` (Redis 7)
3. `backend` (FastAPI em `backend/Dockerfile`)
4. `frontend` (React + Nginx em `frontend/Dockerfile`)

### Servicos adicionais recomendados

1. Job de backup de banco (diario)
2. Monitoramento de uptime (ex.: Uptime Kuma)
3. Centralizacao de logs (ex.: Loki + Grafana, ELK, ou equivalente)

---

## Requisitos minimos

- Servidor Linux com Docker (Ubuntu 22.04+ recomendado)
- 2 vCPU / 4 GB RAM (minimo operacional)
- Portas 80 e 443 liberadas
- Dominio configurado (fortemente recomendado para cookies `Secure`)

---

## Topologia de dominio recomendada

Use subdominios no mesmo dominio raiz (same-site):

- Frontend: `https://copytrade.seudominio.com`
- Backend: `https://api.copytrade.seudominio.com`

Registros DNS tipo `A`:

| Tipo | Nome | Valor |
|------|------|-------|
| A | `copytrade.seudominio.com` | IP do servidor |
| A | `api.copytrade.seudominio.com` | IP do servidor |

---

## 1. Criar projeto no EasyPanel

1. Abra o painel EasyPanel.
2. Clique em `New Project`.
3. Nome sugerido: `copytrade`.

---

## 2. Criar servico PostgreSQL (obrigatorio)

1. `+ New Service` -> `Postgres`.
2. Nome sugerido: `copytrade-postgres`.
3. Versao: `15`.
4. Defina usuario, senha e database (sugestao abaixo):
   - User: `copytrade`
   - Database: `copytrade-postgres`

Connection string interna esperada (backend):

```bash
postgresql://copytrade:SENHA_FORTE@copytrade-postgres:5432/copytrade-postgres
```

Valide os dados reais do Postgres (nao assuma nomes):

```bash
echo "POSTGRES_USER=$POSTGRES_USER"
echo "POSTGRES_DB=$POSTGRES_DB"
echo "POSTGRES_PORT=${POSTGRES_PORT:-5432}"
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select current_user, current_database();"
```

---

## 3. Criar servico Redis (obrigatorio em producao)

1. `+ New Service` -> `Redis`.
2. Nome sugerido: `copytrade-redis`.
3. Versao: `7` (ou estavel equivalente).

Connection string interna esperada:

```bash
redis://copytrade-redis:6379/0
```

Sem Redis acessivel o backend em `APP_ENV=production` **nao sobe**.

---

## 4. Criar servico Backend (FastAPI)

1. `+ New Service` -> `App`.
2. Nome: `backend`.
3. Source: repositorio Git.
4. Build (muito importante):
   - Se a tela tiver apenas `Caminho de Build`, informe **somente** a pasta: `backend`.
   - Se a tela tiver `Dockerfile path` e `Build context`, use:
     - Dockerfile path: `backend/Dockerfile`
     - Build context: `backend`
   - Em `Source = Github`, nao coloque `backend/Dockerfile` no campo de caminho de build (gera `Invalid`).
5. Domain:
   - Dominio: `api.copytrade.seudominio.com`
   - Proxy port: `8000`
   - HTTPS: habilitado

### Variaveis de ambiente do backend (copiar e ajustar)

```bash
APP_ENV=production
DATABASE_URL=postgresql://copytrade:SENHA_FORTE@copytrade-postgres:5432/copytrade-postgres
REDIS_URL=redis://:SENHA_REDIS@copytrade-redis:6379/0
TRUST_X_FORWARDED_FOR=true

JWT_SECRET_KEY=GERAR_VALOR_FORTE
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

ENCRYPTION_KEY=GERAR_CHAVE_FERNET_VALIDA
PASSWORD_REVEAL_TTL_SECONDS=30

CORS_ORIGINS=https://copytrade.seudominio.com

ADMIN_USERNAME=admin
ADMIN_PASSWORD=GERAR_SENHA_FORTE_MIN_12
ADMIN_EMAIL=admin@seudominio.com

# Opcional (controle de transicao v1)
V1_DEPRECATION_START=2026-02-06T00:00:00+00:00
V1_DEPRECATION_WINDOW_DAYS=14
```

Notas importantes:

- `APP_ENV=production` e obrigatorio para comportamento seguro de cookies.
- `CORS_ORIGINS` nao pode ter `*` em producao.
- `TRUST_X_FORWARDED_FOR=true` somente atras de proxy confiavel (EasyPanel/Nginx/Cloudflare).
- `ADMIN_PASSWORD` com menos de 12 caracteres bloqueia startup.
- `ENCRYPTION_KEY` precisa ser Fernet valida.
- O container ja roda `alembic upgrade head` no startup.
- `DATABASE_URL` deve usar **os valores reais** do servico Postgres (`POSTGRES_USER` e `POSTGRES_DB`).
- Se Redis nao tiver senha, use `REDIS_URL=redis://copytrade-redis:6379/0`.
- Evite caracteres especiais na senha do Postgres (ex.: `@`, `%`, `:`) para reduzir erro de parsing de URL em startup/migrations.

Comando para gerar `ENCRYPTION_KEY` valida:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## 5. Criar servico Frontend (React + Nginx)

1. `+ New Service` -> `App`.
2. Nome: `frontend`.
3. Source: mesmo repositorio.
4. Build:
   - Dockerfile path: `frontend/Dockerfile`
   - Build context: `frontend`
5. Domain:
   - Dominio: `copytrade.seudominio.com`
   - Proxy port: `80`
   - HTTPS: habilitado
6. Environment:

```bash
VITE_API_URL=https://api.copytrade.seudominio.com
```

O frontend usa runtime config (`/env-config.js`), entao mudar `VITE_API_URL` nao exige rebuild da imagem.

Importante:

- Configure `VITE_API_URL` no servico `frontend` (aba `Ambiente` do frontend).
- Nao coloque `VITE_API_URL` no servico `backend`.
- O valor deve ser o dominio publico da API (com `https`).

Bloco pronto para copiar no `frontend`:

```bash
VITE_API_URL=https://api.copytrade.seudominio.com
```

Validacao obrigatoria apos implantar frontend:

```bash
curl -s https://copytrade.seudominio.com/env-config.js
```

Esperado conter:

```txt
VITE_API_URL: "https://api.copytrade.seudominio.com"
```

---

## 6. Gerar secrets com seguranca

JWT secret:

```bash
openssl rand -base64 48
```

Fernet key:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Senha admin:

```bash
openssl rand -base64 24
```

---

## 7. Integracao GitHub no EasyPanel

1. Gere um Personal Access Token no GitHub.
2. Permissoes recomendadas:
   - `repo`
   - `admin:repo_hook` (se usar webhook para auto-deploy)
3. EasyPanel -> `Settings` -> `Github` -> cole o token.

---

## 8. Ordem de deploy recomendada

1. Deploy `copytrade-postgres`
2. Deploy `copytrade-redis`
3. Deploy `backend`
4. Deploy `frontend`
5. Revalidar frontend apos backend responder `/api/public/stats`

### Processo operacional recomendado (release)

1. Antes do deploy, validar localmente:

```bash
python3 -m pytest -q
npm --prefix frontend run test
npm --prefix frontend run build
python3 -m pip_audit -r backend/requirements.txt
python3 -m bandit -q -r backend/app
```

2. Fazer deploy na ordem acima.
3. Antes do frontend, validar backend:

```bash
curl -i https://api.copytrade.seudominio.com/api/health
curl -i https://api.copytrade.seudominio.com/api/public/stats
```

4. Executar checklist de validacao pos-deploy.

---

## 9. Checklist de validacao pos-deploy

1. Health da API:

```bash
curl -i https://api.copytrade.seudominio.com/api/health
```

Esperado: HTTP `200` e payload com `status: healthy`.

2. Stats publicas da API (consulta banco):

```bash
curl -i https://api.copytrade.seudominio.com/api/public/stats
```

Esperado: HTTP `200`.
Se retornar `500`, verifique `DATABASE_URL`/senha do Postgres no backend.

3. Docs bloqueadas em producao:

```bash
curl -I https://api.copytrade.seudominio.com/docs
curl -I https://api.copytrade.seudominio.com/openapi.json
```

Esperado: `404` (ou endpoint indisponivel).

4. Frontend acessivel:

```bash
curl -I https://copytrade.seudominio.com
```

Esperado: `200`.

5. Runtime config do frontend:

```bash
curl -s https://copytrade.seudominio.com/env-config.js
```

Esperado conter `VITE_API_URL` com o dominio da API.
Se vier vazio (`""`), ajustar variavel de ambiente no servico `frontend` e implantar novamente.

6. Login v2 define cookies de sessao:
   - `ct_access` (HttpOnly, SameSite=Lax)
   - `ct_refresh` (HttpOnly, SameSite=Strict)
   - `ct_csrf` (leitura cliente para header CSRF)

7. Operacoes mutaveis com CSRF:
   - Sem header `X-CSRF-Token` deve falhar com `403`.

8. Headers de seguranca da API:

```bash
curl -I https://api.copytrade.seudominio.com/api/health
```

Esperado conter:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy` com `geolocation=()`
- `Strict-Transport-Security` (em HTTPS/producao)

---

## 10. Servicos adicionais (podem/devem subir junto)

### A) Backup diario de Postgres (recomendado forte)

Opcao simples:

1. Criar um servico adicional de job/cron.
2. Rodar `pg_dump` diario.
3. Enviar dump para armazenamento externo (S3, bucket compatvel, ou storage remoto).

Exemplo de comando:

```bash
pg_dump "postgresql://copytrade:SENHA_FORTE@copytrade-postgres:5432/copytrade-postgres" > /backup/copytrade_$(date +%Y%m%d_%H%M).sql
```

### B) Monitoramento de uptime (recomendado)

Suba um servico de monitoramento apontando para:

- `https://copytrade.seudominio.com`
- `https://api.copytrade.seudominio.com/api/health`

### C) Centralizacao de logs (opcional, recomendado em escala)

Se houver mais de um ambiente/instancia, adicione stack de logs centralizados para investigacao de incidentes.

---

## 11. Troubleshooting rapido

### Backend nao sobe

- Verifique logs de startup.
- Causas comuns em producao:
  - `REDIS_URL` ausente/inacessivel
  - `JWT_SECRET_KEY` muito curta
  - `ENCRYPTION_KEY` invalida
  - `ADMIN_PASSWORD` fraca

### Frontend carrega, mas mostra "Erro ao carregar estatisticas"

- Verifique no navegador:
  - `https://copytrade.seudominio.com/env-config.js`
  - `https://api.copytrade.seudominio.com/api/health`
  - `https://api.copytrade.seudominio.com/api/public/stats`
- Se `health=200` e `stats=500`, o problema e banco (`DATABASE_URL`/senha).
- Se `env-config.js` vier com `VITE_API_URL: ""`, variavel do frontend nao foi aplicada.

### Erro CSRF (`403`)

- Header `X-CSRF-Token` ausente ou diferente do cookie `ct_csrf`.
- Refaça login para renovar sessao/cookies.

### Erro de conexao com banco

- Sintoma comum nos logs:

```txt
password authentication failed for user "copytrade"
```

- Outro sintoma relacionado:

```txt
Error creating admin user: (psycopg2.OperationalError) ...
```

- A API pode subir mesmo com esse erro, mas endpoints que consultam banco (ex.: `/api/public/stats`) retornam `500`.

- Confirme `DATABASE_URL` com hostname interno correto do servico Postgres e banco real.
- Alinhe senha do usuario no Postgres e no `DATABASE_URL`.

Comandos uteis no container do Postgres:

```bash
echo "POSTGRES_USER=$POSTGRES_USER"
echo "POSTGRES_DB=$POSTGRES_DB"
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select current_user, current_database();"
```

Reset de senha (exemplo):

```bash
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "ALTER USER copytrade WITH PASSWORD 'Copytrade2026Safe';"
```

Depois ajuste no backend:

```bash
DATABASE_URL=postgresql://copytrade:Copytrade2026Safe@copytrade-postgres:5432/copytrade-postgres
```

### Erro Alembic `invalid interpolation syntax`

- Sintoma comum:

```txt
ValueError: invalid interpolation syntax in 'postgresql://...%40...'
```

- Causa: `DATABASE_URL` com `%` (ex.: senha URL-encoded com `%40`) passada para o parser do Alembic.
- Solucao recomendada: usar senha sem caracteres especiais no Postgres.
- Alternativa tecnica: escapar `%` como `%%` apenas se realmente precisar manter a senha atual.

### Dominio da API retorna tela 404 do EasyPanel

- Isso indica roteamento de dominio/proxy no painel, nao bug da API.
- Verifique no servico `backend`:
  - Dominio: `api.copytrade.seudominio.com`
  - `Proxy port`: `8000`
  - HTTPS habilitado
- Garanta que o mesmo dominio nao esta anexado ao `frontend`.

### Requests para `/.env` ou `/.env.*` nos logs

- Isso costuma ser scanner automatizado da internet.
- Se estiver retornando `404`, o comportamento esta correto.

---

## 12. Atualizacao e rollback

### Atualizar

1. Push no repositorio.
2. Rodar validacoes locais (testes + build + auditorias) conforme secao 8.
3. Deploy de `backend`.
4. Deploy de `frontend` (se houve mudanca no frontend).
5. Executar smoke test rapido:

```bash
curl -i https://api.copytrade.seudominio.com/api/health
curl -i https://api.copytrade.seudominio.com/api/public/stats
curl -I https://copytrade.seudominio.com
```

### Rollback

1. Re-deploy do ultimo commit/tag estavel no EasyPanel.
2. Se houver migracao irreversivel, restaurar backup do banco.

---

## 13. Observacoes de seguranca

- Nao exponha porta de Postgres/Redis para internet publica.
- Restrinja acesso administrativo do EasyPanel.
- Rotacione `JWT_SECRET_KEY`, `ENCRYPTION_KEY` e senhas periodicamente.
- Mantenha backups testados (restore validado).
- Revisar dependencias com `pip-audit` e `npm audit` antes de cada release.
- A API foi padronizada para JWT via `PyJWT`; manter `python-jose` fora da stack.

---

## 14. Deploy local (desenvolvimento)

Esta opcao sobe todo o ambiente local com Docker Compose, sem EasyPanel.

### Pre-requisitos

- Docker Desktop (ou Docker Engine + Compose) ativo
- Arquivo `.env` preenchido (pode copiar de `.env.example`)

### Passo a passo

1. Na raiz do projeto, subir/recriar com build:

```bash
docker compose up -d --build
```

2. Verificar status:

```bash
docker compose ps
```

3. Verificar health da API:

```bash
curl -i http://localhost:8000/api/health
```

4. Acessar localmente:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Health: `http://localhost:8000/api/health`

5. Validar headers de seguranca localmente:

```bash
curl -I http://localhost:8000/api/health
```

Nota:
- `TRUST_X_FORWARDED_FOR=false` por padrao em ambiente local (`docker-compose.yml`).
- Em EasyPanel/producao, manter `TRUST_X_FORWARDED_FOR=true` apenas atras de proxy confiavel.

### Logs uteis

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
docker compose logs -f redis
```

### Parar ambiente

```bash
docker compose down
```

### Limpeza completa (inclui volumes)

```bash
docker compose down -v
```
