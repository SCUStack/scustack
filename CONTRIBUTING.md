# Contributing to 川流课栈

## Prerequisites

| Dependency | Version | Purpose |
|---|---|---|
| Node.js | >= 18 | Nuxt 3 frontend runtime |
| pnpm | >= 8 | Frontend package manager |
| Python | >= 3.12 | FastAPI backend runtime |
| Docker Compose | >= 2 | PostgreSQL, Redis, Elasticsearch, OnlyOffice services |
| Git | >= 2.40 | Version control |

## Local development setup

### 1. Clone and install

```bash
git clone https://github.com/yeyixiang2007/scustack.git
cd scustack
```

### 2. Start infrastructure services

```bash
cd scustack-api
cp .env.example .env    # fill in required values
docker compose up -d postgres redis elasticsearch
```

### 3. Backend setup

```bash
cd scustack-api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8403
```

Swagger UI is available at <http://localhost:8403/docs>.

### 4. Frontend setup

```bash
cd scustack-web
pnpm install
cp .env.example .env       # set API_BASE=http://localhost:8403
pnpm dev                   # starts at http://localhost:3000
```

## Running tests

### Backend (pytest)

```bash
cd scustack-api
pytest                          # run all tests
pytest --cov=app --cov-report=term-missing   # with coverage
```

### Frontend (vitest + Playwright)

```bash
cd scustack-web
pnpm test                       # unit tests (vitest)
pnpm test:coverage              # with coverage
pnpm test:e2e                   # E2E tests (Playwright)
```

## Pull request process

1. **Branch naming**: Create from `main` using the pattern `issue-NNN-short-description` (e.g. `issue-132-batch-upload`).
2. **Commits**: Use [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:` with English descriptions.
3. **Scope**: Each PR implements a complete vertical slice across all layers (schema → API → UI → test), driven by its issue.
4. **Testing**: New code must include tests covering the issue's acceptance criteria. Target >= 80% coverage on new code.
5. **Review**: At least one maintainer approval required before merge. Never skip pre-commit hooks.
6. **Coding standards**: See [CLAUDE.md](CLAUDE.md) for language-specific conventions (Nuxt 3 + TypeScript for frontend, FastAPI + SQLAlchemy async for backend).

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full technical architecture document, and [docs/UI-UX-DESIGN.md](docs/UI-UX-DESIGN.md) for the design system specification.
