# Contribuindo com o SOS-JF

## Setup do ambiente

### Pré-requisitos

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- PostgreSQL rodando em `localhost:5432`

### Instalação

```bash
cd backend
uv sync
```

### Hooks de pre-commit

O projeto usa [pre-commit](https://pre-commit.com/) para rodar lint e formatação automaticamente a cada commit.

```bash
uv run pre-commit install
```

Depois disso, a cada `git commit`, o pre-commit vai:

1. Corrigir espaços e newlines
2. Rodar o **Ruff** (lint + format)

Se o hook falhar, ele corrige os arquivos automaticamente — basta re-adicionar e commitar de novo.

---

## Comandos úteis

Todos os comandos abaixo devem ser rodados dentro de `backend/`.

### Lint

```bash
uv run ruff check app/
```

Com auto-fix:

```bash
uv run ruff check app/ --fix
```

### Formatação

```bash
uv run ruff format app/
```

Verificar sem alterar:

```bash
uv run ruff format app/ --check
```

### Testes

```bash
uv run pytest tests/ -v
```

Os testes usam um banco PostgreSQL separado (`app_test`). Certifique-se de que o PostgreSQL está rodando.

### Migrations

Criar uma nova migration após alterar modelos:

```bash
uv run alembic revision --autogenerate -m "descricao da mudanca"
```

Aplicar migrations pendentes:

```bash
uv run alembic upgrade head
```

### Rodar a API em modo dev

```bash
uv run fastapi dev app/main.py
```

---

## CI

O projeto roda lint e testes automaticamente via GitHub Actions em todo push e PR para `main`. O workflow está em `.github/workflows/ci.yml`.

---

## Convenções

- **Mensagens de erro da API** em português
- **Commits** em inglês, seguindo [Conventional Commits](https://www.conventionalcommits.org/) (ex: `feat:`, `fix:`, `test:`, `ci:`, `chore:`)
- **Branches** com prefixo descritivo (ex: `feat/nova-rota`, `fix/correcao-login`, `chore/ruff-setup`)
- **Modelos de resposta** sempre tipados — sem retornar `dict` puro nas rotas
- **Linter/Formatter** — Ruff com as regras definidas em `pyproject.toml`
