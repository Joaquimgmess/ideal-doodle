# SOS-JF API

API centralizadora de pedidos de ajuda, voluntários, doações e outros dados de emergência de Juiz de Fora/MG, agregando 20+ portais externos.

## Stack

- **FastAPI** + **SQLModel** (async) + **PostgreSQL**
- **APScheduler** — scraping automático a cada hora
- **httpx** + **BeautifulSoup4** — scrapers
- **uv** — gerenciador de pacotes

---

## Rodando local

### Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- PostgreSQL rodando em `localhost:5432`

### 1. Configurar variáveis de ambiente

```bash
cp .env.example .env
# edite .env com suas credenciais do Postgres
```

### 2. Instalar dependências

```bash
cd backend
uv sync
```

### 3. Rodar migrations

```bash
cd backend
uv run alembic upgrade head
```

### 4. Criar superuser inicial

```bash
cd backend
uv run python app/initial_data.py
```

### 5. Subir a API

```bash
cd backend
uv run fastapi dev app/main.py
```

API disponível em **http://localhost:8000**
Docs em **http://localhost:8000/docs**

---

## Rodando com Docker

### Pré-requisitos

- Docker + Docker Compose

### 1. Configurar variáveis de ambiente

```bash
cp .env.example .env
# edite .env — mínimo obrigatório: POSTGRES_PASSWORD, SECRET_KEY, FIRST_SUPERUSER_PASSWORD
```

### 2. Subir

```bash
docker compose up --build
```

Isso irá:
1. Subir o PostgreSQL
2. Aguardar o banco ficar disponível
3. Rodar as migrations automaticamente
4. Criar o superuser inicial
5. Subir a API em **http://localhost:8000**

### Parar

```bash
docker compose down
```

### Parar e remover dados do banco

```bash
docker compose down -v
```

---

## Variáveis de ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `POSTGRES_SERVER` | Host do banco | `localhost` |
| `POSTGRES_PORT` | Porta do banco | `5432` |
| `POSTGRES_DB` | Nome do banco | `app` |
| `POSTGRES_USER` | Usuário | `postgres` |
| `POSTGRES_PASSWORD` | Senha | — |
| `SECRET_KEY` | Chave JWT | — |
| `FIRST_SUPERUSER` | Email do admin | — |
| `FIRST_SUPERUSER_PASSWORD` | Senha do admin | — |
| `SCRAPER_INTERVAL_HOURS` | Intervalo do scraping | `1` |
| `SCRAPER_RUN_ON_STARTUP` | Rodar scraping ao iniciar | `false` |

---

## Usando a API

### 1. Registrar uma API Key (para o seu app)

```bash
curl -X POST http://localhost:8000/api/v1/api-keys \
  -H "Content-Type: application/json" \
  -d '{"name": "meu-app", "description": "descrição opcional"}'
```

Guarde o campo `key` — ele é exibido **apenas uma vez**.

### 2. Consultar dados

```bash
curl http://localhost:8000/api/v1/pedidos \
  -H "X-API-Key: sos_..."
```

### Endpoints disponíveis

todo! vincular com https://doc-hub-emergencia-api.vercel.app/docs/endpoints

todo! incorporar estas rotas
todo! importar rotas `rust`

| Método | Rota | Auth | Descrição |
|--------|------|------|-----------|
| `GET` | `/api/v1/pedidos` | API Key | Lista pedidos de socorro |
| `POST` | `/api/v1/pedidos` | API Key | Cria pedido |
| `GET` | `/api/v1/voluntarios` | API Key | Lista voluntários |
| `POST` | `/api/v1/voluntarios` | API Key | Cadastra voluntário |
| `GET` | `/api/v1/pontos` | API Key | Lista pontos de ajuda |
| `POST` | `/api/v1/pontos` | API Key | Cria ponto de ajuda |
| `GET` | `/api/v1/pets` | API Key | Lista pets (perdidos/encontrados/adoção) |
| `POST` | `/api/v1/pets` | API Key | Cadastra pet |
| `GET` | `/api/v1/feed` | API Key | Lista alertas e notícias |
| `POST` | `/api/v1/feed` | API Key | Cria item no feed |
| `GET` | `/api/v1/outros` | API Key | Lista contatos, links, vaquinhas |
| `POST` | `/api/v1/outros` | API Key | Cria item |
| `POST` | `/api/v1/users/signup` | — | Cria conta de desenvolvedor |
| `POST` | `/api/v1/login/access-token` | — | Login (retorna JWT) |
| `POST` | `/api/v1/api-keys` | — | Registra API Key |

Todos os GETs aceitam `?skip=0&limit=100` e filtros específicos por endpoint (ex: `?cidade=juiz+de+fora&categoria=agua`).

Documentação interativa completa em `/docs`.
