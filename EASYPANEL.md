# Deploy no EasyPanel - Copy Trade Dashboard

## Requisitos

- **Servidor Linux** (Ubuntu 22.04+ recomendado)
- **Minimo 2GB RAM** (4GB recomendado)
- **Portas 80 e 443** abertas no firewall
- **Dominio** apontando para o IP do servidor (opcional, mas recomendado para SSL)

---

## 1. Instalar EasyPanel no Servidor

Conecte via SSH no servidor e execute:

```bash
# 1. Instalar Docker (se ainda nao tiver)
curl -sSL https://get.docker.com | sh

# 2. Instalar EasyPanel
docker run --rm -it \
  -v /etc/easypanel:/etc/easypanel \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  easypanel/easypanel setup
```

Apos a instalacao, acesse o painel em `http://SEU_IP:3000` e crie sua conta de admin.

---

## 2. Configurar Dominio (Recomendado)

No seu provedor de DNS, crie os seguintes registros **A** apontando para o IP do servidor:

| Tipo | Nome | Valor |
|------|------|-------|
| A | `copytrade.seudominio.com` | IP do servidor |
| A | `api.copytrade.seudominio.com` | IP do servidor |

Aguarde a propagacao do DNS (pode levar ate 24h, geralmente minutos).

---

## 3. Criar Projeto no EasyPanel

1. No painel, clique em **"New Project"**
2. Nome: `copytrade`

---

## 4. Adicionar Servico: PostgreSQL

1. Dentro do projeto, clique em **"+ New Service"** > **"Postgres"**
2. Configure:
   - **Version**: 15
   - **Password**: defina uma senha forte
3. Salve e anote as informacoes de conexao:
   - Host interno: `copytrade-postgres` (nome do servico dentro do EasyPanel)
   - Porta: `5432`
   - Database: `postgres` (default)
   - Username: `postgres` (default)

A **connection string** interna sera algo como:
```
postgresql://postgres:SUA_SENHA@copytrade-postgres:5432/postgres
```

---

## 5. Adicionar Servico: Backend (API)

1. Clique em **"+ New Service"** > **"App"**
2. Nome: `backend`
3. Em **Source**, selecione **GitHub** e conecte seu repositorio (veja secao abaixo sobre como configurar o GitHub)
4. Configure o build:
   - **Dockerfile path**: `backend/Dockerfile`
   - **Build context**: `backend`
5. Em **Domains**, adicione:
   - Dominio: `api.copytrade.seudominio.com`
   - **Proxy port**: `8000`
   - Ative **HTTPS** (Let's Encrypt automatico)
6. Em **Environment**, adicione as variaveis:

```
DATABASE_URL=postgresql://postgres:SUA_SENHA@copytrade-postgres:5432/postgres
JWT_SECRET_KEY=<gerar abaixo>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENCRYPTION_KEY=<gerar abaixo>
CORS_ORIGINS=https://copytrade.seudominio.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<sua senha admin>
ADMIN_EMAIL=seu@email.com
```

7. Clique em **Deploy**

---

## 6. Adicionar Servico: Frontend

1. Clique em **"+ New Service"** > **"App"**
2. Nome: `frontend`
3. Em **Source**, selecione **GitHub** e conecte o mesmo repositorio
4. Configure o build:
   - **Dockerfile path**: `frontend/Dockerfile`
   - **Build context**: `frontend`
5. Em **Domains**, adicione:
   - Dominio: `copytrade.seudominio.com`
   - **Proxy port**: `80`
   - Ative **HTTPS**
6. Em **Environment**, adicione:

```
VITE_API_URL=https://api.copytrade.seudominio.com
```

7. Clique em **Deploy**

---

## 7. Gerar Chaves Seguras

Execute estes comandos no seu terminal para gerar as chaves:

**JWT Secret Key:**
```bash
openssl rand -base64 32
```

**Encryption Key (Fernet):**
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Se nao tiver Python com cryptography instalado:
```bash
pip3 install cryptography && python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Senha Admin (aleatoria):**
```bash
openssl rand -base64 16
```

---

## 8. Configurar GitHub no EasyPanel

O EasyPanel usa **Personal Access Token** para integrar com GitHub (tambem suporta GitLab, Bitbucket e Gitea).

1. No GitHub, va em **Settings** > **Developer settings** > **Personal access tokens**
2. Crie um token (Classic ou Fine-grained) com as permissoes:
   - `repo` - acesso a repositorios privados
   - `admin:repo_hook` - para auto-deploy via webhook
3. No EasyPanel, va em **Settings** > **Github** e cole o token
4. Agora voce pode selecionar seus repositorios ao configurar o Source dos servicos

---

## 9. Verificacao

Apos o deploy, verifique:

1. **Health check da API**: acesse `https://api.copytrade.seudominio.com/api/health`
   - Deve retornar `{"status": "ok"}`
2. **Frontend**: acesse `https://copytrade.seudominio.com`
   - O dashboard deve carregar normalmente
3. **Login admin**: acesse `https://copytrade.seudominio.com/login`
   - Use as credenciais configuradas em `ADMIN_USERNAME` e `ADMIN_PASSWORD`
4. **API Docs**: acesse `https://api.copytrade.seudominio.com/docs`
   - Swagger UI deve estar disponivel

---

## Como Funciona o VITE_API_URL (Runtime Config)

O frontend usa um mecanismo de **runtime config** para que a URL da API possa ser alterada sem rebuild:

1. O `docker-entrypoint.sh` roda antes do nginx e gera o arquivo `/usr/share/nginx/html/env-config.js` com o valor da env var `VITE_API_URL`
2. O `index.html` carrega esse script antes do app React
3. O `client.ts` usa `window.__ENV__.VITE_API_URL` com fallback para o valor de build time

Isso significa que basta alterar a env var `VITE_API_URL` no EasyPanel e re-deploy (sem rebuild) para mudar o endpoint da API.

---

## Portas Dinamicas (docker-compose local)

Para desenvolvimento local com `docker-compose`, todas as portas sao configuraveis via `.env`:

| Variavel | Default | Descricao |
|----------|---------|-----------|
| `DB_PORT` | 5432 | Porta exposta do PostgreSQL |
| `BACKEND_PORT` | 8000 | Porta exposta do backend |
| `FRONTEND_PORT` | 3000 | Porta exposta do frontend |

Se alguma porta estiver em uso, altere no `.env`:
```
DB_PORT=5433
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

> **Nota:** No EasyPanel as portas internas nao conflitam, pois cada servico roda em container isolado. A configuracao de "Proxy port" no EasyPanel e o que mapeia o dominio para a porta interna do container.

---

## Troubleshooting

### Frontend nao conecta na API
- Verifique se `VITE_API_URL` no servico frontend aponta para o dominio correto da API (com `https://`)
- Verifique se `CORS_ORIGINS` no backend inclui o dominio do frontend (com `https://`)
- No DevTools do browser (F12 > Network), verifique para onde as requests estao indo

### Erro de banco de dados
- Verifique se a `DATABASE_URL` no backend usa o hostname interno correto do servico Postgres no EasyPanel
- O formato e: `postgresql://postgres:SENHA@NOME_DO_SERVICO_POSTGRES:5432/postgres`
- Verifique nos logs do backend se as migrations rodaram com sucesso

### Erro 502 Bad Gateway
- O servico pode estar iniciando. Aguarde 30-60 segundos
- Verifique se a **Proxy port** esta configurada corretamente (8000 para backend, 80 para frontend)
- Verifique os logs do servico no EasyPanel

### Admin nao consegue logar
- Verifique se `ADMIN_USERNAME` e `ADMIN_PASSWORD` estao configurados nas env vars do backend
- O admin e criado apenas no primeiro startup. Se mudar a senha na env var, precisa alterar diretamente no banco ou recriar o banco

### Frontend aponta para API antiga apos mudanca de VITE_API_URL
- Limpe o cache do browser (Ctrl+Shift+R / hard refresh)
- Verifique se `https://copytrade.seudominio.com/env-config.js` retorna a URL correta
- O nginx esta configurado para nao cachear env-config.js, mas CDNs ou proxies intermediarios podem cachear

### SSL nao funciona
- Verifique se o dominio esta apontando para o IP do servidor (use `dig seudominio.com`)
- Verifique se as portas 80 e 443 estao abertas no firewall do servidor
- No EasyPanel, verifique se HTTPS esta ativado para o dominio

---

## Atualizando o Sistema

Para atualizar apos mudancas no codigo:

1. Faca push das mudancas para o GitHub
2. No EasyPanel, va ate o servico que deseja atualizar
3. Clique em **"Deploy"** (ou ative auto-deploy para deploys automaticos no push)

Os dois servicos (backend e frontend) precisam ser deployados separadamente se ambos mudaram.

---

## Backup do Banco de Dados

Para fazer backup do PostgreSQL via EasyPanel:

```bash
# Conecte no servidor via SSH
# Descubra o nome do container Postgres
docker ps | grep postgres

# Faca o dump
docker exec NOME_DO_CONTAINER pg_dump -U postgres postgres > backup_$(date +%Y%m%d).sql
```

Para restaurar:
```bash
docker exec -i NOME_DO_CONTAINER psql -U postgres postgres < backup_20240101.sql
```
