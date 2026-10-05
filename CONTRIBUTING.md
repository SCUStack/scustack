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

本仓库支持的本地前端开发路径是根目录 pnpm workspace：在仓库根目录运行 `pnpm install`，再使用 workspace 命令。CI 前端任务目前使用 `scustack-web/package-lock.json` 执行 `npm ci`；这是 CI 的独立安装流程，不应与本地 workspace 锁文件混用。

```bash
git clone https://github.com/SCUStack/scustack.git
cd scustack
pnpm install
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
```

Playwright E2E is currently not part of the PR CI gate. The repository does not
contain a `playwright.config.*` file or a maintained API/frontend startup
orchestration for E2E, so the workflow omits the job rather than reporting a
check that cannot run. Re-enable it only after adding the configuration and
startup steps, and document the command here.

## Pull request process

1. **Branch naming**: Create from `main` using the pattern `issue-NNN-short-description` (e.g. `issue-132-batch-upload`).
2. **Commits**: Use [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:` with English descriptions.
3. **Scope**: Each PR implements a complete vertical slice across all layers (schema → API → UI → test), driven by its issue.
4. **Testing**: New code must include tests covering the issue's acceptance criteria. Target >= 80% coverage on new code.
5. **Review**: At least one maintainer approval required before merge. Never skip pre-commit hooks.
6. **Coding standards**: See [CLAUDE.md](CLAUDE.md) for language-specific conventions (Nuxt 3 + TypeScript for frontend, FastAPI + SQLAlchemy async for backend).

## Architecture

See [docs/ARCHITECTURE-技术架构.md](docs/ARCHITECTURE-技术架构.md) for the full technical architecture document, and [docs/DESIGN-UI-UX.md](docs/DESIGN-UI-UX.md) for the design system specification.
