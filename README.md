# CopyTrade Dashboard

![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178C6?logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-7-646CFF?logo=vite&logoColor=white)
![License](https://img.shields.io/badge/License-Private-red)

Painel administrativo para gerenciamento de contas de copy trade. Permite cadastrar, monitorar e administrar contas de traders com controle de fases de avaliacao (prop trading), gerenciamento seguro de senhas e dashboard publico de estatisticas.

---

## Funcionalidades

- **Gerenciamento de Contas** - CRUD completo de contas de copy trade com dados do comprador, servidor, datas de compra/expiracao e preco
- **Controle de Status** - Fluxo de status: `pending` → `approved` → `in_copy` → `expired` / `suspended`
- **Prop Trading (Fases 1 e 2)** - Acompanhamento de metas de avaliacao com margem, targets e status por fase
- **Senhas Criptografadas** - Senhas de contas armazenadas com criptografia Fernet; revelacao temporaria com autenticacao do admin e rate limiting
- **Rotacao de Senhas** - Troca de senha de contas pelo painel sem necessidade da senha anterior
- **Dashboard Publico** - Estatisticas agregadas acessiveis sem autenticacao (total de contas por status)
- **Dashboard Admin** - Painel completo com filtros por status, busca por nome do comprador e estatisticas de receita
- **Autenticacao Segura** - Cookies HTTP-only com protecao CSRF (double-submit cookie pattern)
- **Audit Trail** - Log de eventos de seguranca (login, logout, reveal de senha) com IP e user-agent
- **Rate Limiting** - Limites por IP e por usuario em login, refresh e reveal de senha
- **API Versionada** - v2 (atual) com deprecacao gradual da v1 via headers HTTP Sunset

---

## Tecnologias

| Camada | Tecnologia | Versao |
|--------|-----------|--------|
| Frontend | React + TypeScript | 18.2 / 5.3 |
| Build Tool | Vite | 7.3 |
| Estilizacao | Tailwind CSS | 3.4 |
| State (server) | TanStack React Query | 5.17 |
| Formularios | React Hook Form | 7.49 |
| HTTP Client | Axios | 1.6 |
| Backend | FastAPI | 0.128 |
| ORM | SQLAlchemy | 2.0 |
| Migracoes | Alembic | 1.14 |
| Banco de Dados | PostgreSQL | 15 |
| Cache/Sessoes | Redis | 7 |
| Autenticacao | PyJWT + bcrypt | 2.11 / 4.2 |
| Criptografia | cryptography (Fernet) | 44.0 |
| Web Server | Nginx (frontend) | Alpine |
| Containerizacao | Docker Compose | - |
| Testes Backend | pytest + pytest-cov | 8.3 |
| Testes Frontend | Vitest + Testing Library | 4.0 |

---

## Arquitetura

```
                         Internet
                            |
              +-------------+-------------+
              |                           |
   copytrade.dominio.com      api.copytrade.dominio.com
              |                           |
     +--------+--------+       +---------+---------+
     |  Frontend (Nginx)|       |  Backend (Uvicorn)|
     |  React SPA       |       |  FastAPI           |
     |  Port 80         |       |  Port 8000         |
     +------------------+       +---------+---------+
                                          |
                              +-----------+-----------+
                              |                       |
                    +---------+-------+     +---------+-------+
                    | PostgreSQL 15   |     | Redis 7         |
                    | Dados + Sessoes |     | Rate Limit      |
                    | Audit Logs      |     | Revogacao JWT   |
                    +-----------------+     +-----------------+
```

**Fluxo de autenticacao (v2):**

```
1. POST /api/v2/auth/login
   → Valida credenciais (bcrypt)
   → Cria RefreshToken no banco (hash SHA256)
   → Seta cookies: ct_access (15min), ct_refresh (7d), ct_csrf (7d)

2. Requisicoes autenticadas
   → Cookie ct_access enviado automaticamente
   → Header X-CSRF-Token injetado pelo Axios (lido do cookie ct_csrf)
   → Backend valida JWT + CSRF em mutacoes (POST/PUT/PATCH/DELETE)

3. POST /api/v2/auth/refresh
   → Rotaciona token (revoga antigo, cria novo)
   → Frontend faz retry automatico em 401

4. POST /api/v2/auth/logout
   → Revoga sessao no banco + Redis
   → Limpa cookies
```

---

## Pre-requisitos

- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/install/)
- [Git](https://git-scm.com/)

> Para desenvolvimento local sem Docker: Python 3.11+, Node.js 20+, PostgreSQL 15+, Redis 7+

---

## Instalacao e Configuracao

### Opcao 1: Setup automatizado

```bash
git clone <url-do-repositorio> copytrade-dashboard
cd copytrade-dashboard

# Script interativo que instala Docker, gera secrets e sobe os containers
chmod +x setup.sh
./setup.sh
```

O script `setup.sh` automaticamente:
- Detecta o SO e instala Docker se necessario
- Gera chaves seguras (JWT secret, Fernet key, senha admin)
- Cria o arquivo `.env`
- Sobe todos os servicos via Docker Compose
- Aguarda health checks e exibe credenciais do admin

### Opcao 2: Setup manual

```bash
git clone <url-do-repositorio> copytrade-dashboard
cd copytrade-dashboard

# 1. Criar .env a partir do template
cp .env.example .env

# 2. Gerar e preencher os secrets no .env:
#    JWT_SECRET_KEY  → openssl rand -base64 32
#    ENCRYPTION_KEY  → python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
#    DB_PASSWORD     → senha forte
#    ADMIN_PASSWORD  → minimo 12 caracteres

# 3. Subir os containers
docker compose up -d --build

# 4. Verificar saude dos servicos
docker compose ps
curl http://localhost:8000/api/health
```

Apos o startup, o backend automaticamente:
1. Executa migracoes do Alembic (`alembic upgrade head`)
2. Cria o usuario admin inicial (`python -m app.init_admin`)
3. Inicia o Uvicorn na porta 8000

**Acessos:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs (dev): http://localhost:8000/docs

---

## Variaveis de Ambiente

| Variavel | Padrao | Descricao |
|----------|--------|-----------|
| `APP_ENV` | `development` | Ambiente: `development`, `test` ou `production` |
| `DATABASE_URL` | SQLite local | Connection string PostgreSQL |
| `REDIS_URL` | - | URL do Redis. **Obrigatorio em producao** |
| `JWT_SECRET_KEY` | Aleatorio | Chave de assinatura JWT. Min 32 chars em producao |
| `JWT_ALGORITHM` | `HS256` | Algoritmo JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Tempo de vida do access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Tempo de vida do refresh token |
| `ENCRYPTION_KEY` | Aleatorio | Chave Fernet para criptografia de senhas |
| `PASSWORD_REVEAL_TTL_SECONDS` | `30` | Tempo de exibicao da senha revelada |
| `CORS_ORIGINS` | `localhost` | Origens permitidas (separadas por virgula). Sem `*` em producao |
| `VITE_API_URL` | `http://localhost:8000` | URL do backend para o frontend |
| `ADMIN_USERNAME` | `admin` | Username do admin inicial |
| `ADMIN_PASSWORD` | Aleatorio | Senha do admin. Min 12 chars em producao |
| `ADMIN_EMAIL` | `admin@copytrade.app` | Email do admin |
| `TRUST_X_FORWARDED_FOR` | `false` | Habilitar apenas atras de proxy reverso confiavel |
| `DB_USER` | `copytrade` | Usuario do PostgreSQL |
| `DB_PASSWORD` | - | Senha do PostgreSQL |

Consulte `.env.example` para a lista completa com comentarios.

---

## Estrutura do Projeto

```
copytrade-dashboard/
├── docker-compose.yml          # Orquestracao dos 4 servicos
├── .env.example                # Template de variaveis de ambiente
├── setup.sh                    # Script de setup automatizado
├── pytest.ini                  # Configuracao de testes backend
├── EASYPANEL.md                # Guia de deploy em producao
│
├── backend/
│   ├── app/
│   │   ├── api/                # Rotas da API
│   │   │   ├── auth_v2.py      #   Login, refresh, logout (cookies)
│   │   │   ├── accounts_v2.py  #   CRUD de contas, stats, senhas
│   │   │   └── public.py       #   Estatisticas publicas
│   │   ├── core/               # Seguranca e dependencias
│   │   │   ├── security.py     #   JWT, bcrypt, Fernet
│   │   │   └── dependencies.py #   Auth guards, CSRF validation
│   │   ├── crud/               # Operacoes de banco
│   │   ├── db/
│   │   │   ├── models.py       #   User, CopyTradeAccount, RefreshToken, SecurityAuditLog
│   │   │   └── database.py     #   Engine e session
│   │   ├── schemas/            # Pydantic models (request/response)
│   │   ├── services/           # Rate limit, audit, session management
│   │   ├── config.py           # Settings com validacao
│   │   ├── main.py             # App FastAPI + middlewares
│   │   └── init_admin.py       # Criacao do admin inicial
│   ├── alembic/                # Migracoes de banco
│   │   └── versions/           #   001: schema inicial
│   │                           #   002: campos prop trading
│   │                           #   003: sessoes e audit log
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements-dev.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts       # Axios com CSRF e refresh automatico
│   │   ├── components/
│   │   │   ├── admin/          # AccountTable, AccountForm
│   │   │   └── common/         # Header, Loading, StatusBadge
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx  # Estado de autenticacao
│   │   ├── pages/              # PublicDashboard, LoginPage, AdminDashboard
│   │   ├── types/              # Interfaces TypeScript
│   │   └── styles/             # Tailwind globals
│   ├── Dockerfile              # Build multi-stage (Node → Nginx)
│   ├── nginx.conf              # SPA routing, cache, security headers
│   ├── docker-entrypoint.sh    # Injeta VITE_API_URL em runtime
│   ├── vite.config.ts          # Build + obfuscacao + testes
│   └── package.json
│
└── tests/                      # Testes do backend (pytest)
    ├── conftest.py             # Fixtures
    ├── test_auth_v2_api.py     # Testes de autenticacao
    ├── test_accounts_v2_api.py # Testes de contas
    ├── test_security_hardening.py # Testes de seguranca
    └── ...                     # 12 arquivos de teste
```

---

## API Endpoints

### Autenticacao (`/api/v2/auth`)

| Metodo | Endpoint | Descricao | CSRF |
|--------|----------|-----------|------|
| POST | `/api/v2/auth/login` | Login (seta cookies HTTP-only) | Nao |
| POST | `/api/v2/auth/refresh` | Renova access token | Sim |
| GET | `/api/v2/auth/me` | Dados do usuario autenticado | Nao |
| POST | `/api/v2/auth/logout` | Logout (revoga sessao) | Sim |

### Administracao (`/api/v2/admin`)

| Metodo | Endpoint | Descricao | CSRF |
|--------|----------|-----------|------|
| GET | `/accounts` | Listar contas (paginacao, filtros) | Nao |
| GET | `/accounts/{id}` | Detalhes de uma conta | Nao |
| POST | `/accounts` | Criar nova conta | Sim |
| PUT | `/accounts/{id}` | Atualizar conta | Sim |
| PATCH | `/accounts/{id}/status` | Alterar status | Sim |
| DELETE | `/accounts/{id}` | Excluir conta | Sim |
| POST | `/accounts/{id}/password/reveal` | Revelar senha (requer senha admin) | Sim |
| POST | `/accounts/{id}/password/rotate` | Rotacionar senha da conta | Sim |
| GET | `/stats` | Estatisticas admin (receita, contas/mes) | Nao |

### Publico (`/api/public`)

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/stats` | Estatisticas agregadas (total por status) |

### Sistema

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/api/health` | Health check |
| GET | `/docs` | Documentacao OpenAPI (apenas em desenvolvimento) |

---

## Seguranca

### Autenticacao e Sessoes
- **Cookies HTTP-only** com flags `Secure` e `SameSite=None` para cross-origin
- **Rotacao de refresh tokens** a cada renovacao (token antigo revogado)
- **Revogacao imediata** via Redis (logout invalida sessao em todas as abas)
- **Hashing bcrypt** para senhas de usuarios

### Protecao CSRF
- Padrao **double-submit cookie**: cookie `ct_csrf` (legivel por JS) deve ser enviado no header `X-CSRF-Token`
- Validado em todas as mutacoes (POST, PUT, PATCH, DELETE)

### Criptografia de Dados
- Senhas de contas de trading criptografadas com **Fernet** (AES-128-CBC)
- Revelacao temporaria com TTL configuravel e autenticacao adicional do admin

### Rate Limiting
| Recurso | Limite | Janela |
|---------|--------|--------|
| Login (por IP) | 5 tentativas | 60 segundos |
| Login (por username) | 20 tentativas | 1 hora |
| Token refresh | 10 tentativas | 60 segundos |
| Password reveal | 3 tentativas | 10 minutos |

### Audit Log
Todos os eventos de seguranca sao registrados na tabela `SecurityAuditLog` com:
- Usuario, acao, alvo, sucesso/falha, motivo
- IP de origem e User-Agent
- Timestamp

### Headers de Seguranca
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy: geolocation=(), microphone=(), camera=()`
- `Strict-Transport-Security` (em producao)

---

## Testes

O projeto exige **100% de cobertura de codigo** tanto no backend quanto no frontend.

### Backend (pytest)

```bash
# Rodar testes com cobertura
cd backend
python -m pytest

# Ou via Docker
docker compose exec backend python -m pytest
```

Configuracao em `pytest.ini`:
- Coverage minima: 100% em `backend/app/`
- 12 arquivos de teste cobrindo auth, CRUD, seguranca, dependencias

### Frontend (Vitest)

```bash
# Rodar testes
cd frontend
npm test

# Com cobertura
npm run test:coverage
```

Configuracao em `vite.config.ts`:
- Coverage minima: 100% (lines + statements)
- Ambiente: jsdom
- Libraries: @testing-library/react, @testing-library/jest-dom

---

## Deploy em Producao

O deploy recomendado e via **EasyPanel** com 4 servicos separados.

Consulte o guia completo em [`EASYPANEL.md`](./EASYPANEL.md) que cobre:

- Configuracao de cada servico (PostgreSQL, Redis, Backend, Frontend)
- Variaveis de ambiente de producao
- Troubleshooting de cookies cross-origin
- Validacao pos-deploy (health checks, CSRF, headers)
- Licoes aprendidas em producao

**Topologia de producao:**
```
Frontend: https://copytrade.seudominio.com     → Nginx (port 80)
Backend:  https://api.copytrade.seudominio.com → FastAPI (port 8000)
```

**Checklist pos-deploy:**
- [ ] `GET /api/health` retorna 200
- [ ] `GET /api/public/stats` retorna dados (valida conexao com banco)
- [ ] `/docs` e `/openapi.json` retornam 404 (bloqueados em producao)
- [ ] Login seta cookies `ct_access`, `ct_refresh`, `ct_csrf`
- [ ] Mutacoes sem header `X-CSRF-Token` retornam 403
- [ ] Headers de seguranca presentes nas respostas

---

## Modelos de Dados

### CopyTradeAccount

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `account_number` | String | Numero da conta (unico) |
| `account_password` | String | Senha criptografada (Fernet) |
| `server` | String | Servidor de trading (ex: Exness-MT5) |
| `buyer_name` | String | Nome do comprador |
| `buyer_email` | String? | Email do comprador |
| `buyer_phone` | String? | Telefone do comprador |
| `purchase_date` | Date | Data da compra |
| `expiry_date` | Date? | Data de expiracao |
| `purchase_price` | Decimal? | Valor da compra |
| `status` | Enum | `pending`, `approved`, `in_copy`, `expired`, `suspended` |
| `copy_count` | Integer | Copias ativas |
| `max_copies` | Integer | Limite de copias |
| `margin_size` | Decimal? | Tamanho da margem (prop trading) |
| `phase1_target` | Decimal? | Meta da fase 1 |
| `phase1_status` | Enum? | `not_started`, `in_progress`, `passed`, `failed` |
| `phase2_target` | Decimal? | Meta da fase 2 |
| `phase2_status` | Enum? | Status da fase 2 |

---

## Licenca

Projeto privado. Todos os direitos reservados.
