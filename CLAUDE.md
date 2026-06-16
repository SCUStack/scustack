# CLAUDE.md

## Project context

川流课栈 (SCU Course Stack) — public-welfare course material sharing platform for Sichuan University students. Stack: Nuxt 3 + Element Plus + Tailwind (frontend), FastAPI + SQLAlchemy async + Celery (backend), PostgreSQL 16, Elasticsearch 8 + IK, Redis 7, Alibaba Cloud OSS.

## Issue-driven development

All work is driven by issues on GitHub. Each issue is a vertical slice across all layers (schema → API → UI → test). Before starting any work:

1. Read the target issue's full description, acceptance criteria, and `Blocked by` field
2. Verify all blocking issues are completed before starting
3. Implement the complete slice — do NOT implement only one layer and leave the rest for later
4. When done, verify every acceptance criterion passes before marking complete

## Directory structure

```
scustack-web/                 # Nuxt 3 frontend
  pages/                      # File-based routing
  components/                 # Vue components by domain
  composables/                # useAuth, useSearch, useUpload, etc.
  server/api/                 # Proxy to FastAPI
  stores/                     # Pinia (auth, course, upload)

scustack-api/                 # FastAPI backend
  app/
    api/v1/                   # Route handlers (thin — delegate to services)
    models/                   # SQLAlchemy ORM
    schemas/                  # Pydantic request/response
    services/                 # Business logic
    core/                     # DB, Redis, ES, OSS, Celery, security
    middleware/                # Auth, rate limit, CORS, audit
    tasks/                    # Celery async tasks
  alembic/                    # DB migrations
  tests/                      # pytest
```

## Coding conventions

### General
- No comments unless the WHY is non-obvious. Well-named identifiers document the WHAT.
- No dead code, no half-finished features, no `// TODO` without a linked issue.
- Don't add error handling for scenarios that can't happen. Validate only at system boundaries (user input, external APIs).
- Three similar lines is better than a premature abstraction.

### Frontend (Nuxt 3 + Vue 3 + TypeScript)
- Use `<script setup lang="ts">` exclusively
- Composables for reusable logic (`composables/`), Pinia stores for global state (`stores/`)
- Element Plus components for UI; override styles via Tailwind classes, not scoped CSS
- Icons: Lucide Icons via `<AppIcon name="..." size="20" />` — never emoji
- Responsive: Tailwind breakpoints `sm`(640) `md`(768) `lg`(1024) `xl`(1280). Mobile-first.
- Pages use Nuxt routeRules for rendering mode: `/` ISR 5min, `/search` `/course/:id` `/material/:id` SSR, `/upload` `/user/*` `/admin/*` CSR
- Design tokens: use `var(--color-*)` or Tailwind theme extensions; never hardcode hex colors

### Backend (Python 3.12 + FastAPI)
- Strict layered architecture: Router → Schema (Pydantic) → Service → Model (SQLAlchemy). Router never calls Model directly.
- Use `async/await` throughout. asyncpg for DB, elasticsearch-py async for ES.
- `dependencies.py` for FastAPI dependency injection (get_current_user, require_permission).
- Permission model: `app/core/permissions.py` — capability-based enum (`materials:create`, `materials:delete:own`, etc.), role-to-permission mapping.
- Pydantic v2 with `model_config = ConfigDict(from_attributes=True)` for ORM mode.
- Alembic for all schema changes. Never modify tables directly.
- Celery tasks for async work: virus scan, thumbnail generation, ES index sync, content pre-screening.

### Database
- PostgreSQL 16 with `zhparser` extension for Chinese full-text search on `materials.title`, `materials.description`, `courses.name`.
- All tables use UUID primary keys (`gen_random_uuid()`). Timestamps use `TIMESTAMPTZ`.
- PII fields (phone, university_id) are AES-256-GCM encrypted at application layer.
- JSONB for flexible fields (`courses.aliases`, `audit_logs.detail`). GIN index on queried JSONB paths.
- Use `selectinload`/`joinedload` to avoid N+1. Cursor-based pagination for infinite scroll lists.

### Git
- Branch: `issue-NNN-short-description` from `main`
- Commit: Conventional Commits — `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:` with English descriptions
- Never skip hooks. Never force-push to main.
- Create new commits rather than amending.
- Never pass a multi-line commit message as an inline PowerShell here-string (e.g. ``git commit -m @'...'@``). When used in a Bash-shell, each `@` will be interpreted as part of the commit message. Omit the `@` characters, e.g. ``git commit -m '...'``.

## Testing
- Backend: pytest + pytest-asyncio + pytest-cov. Test at service layer; mock external APIs (OSS, SMS, WeChat).
- Frontend: vitest for unit/composable tests, @playwright/test for E2E (critical user paths).
- Each issue must include tests covering its acceptance criteria. Target ≥80% coverage on new code.

## Design system quick reference

See `docs/UI-UX-DESIGN.md` for full specification.

- Primary: `#1E3A5F`–`#3B82F6` (academic blue). Accent: `#F59E0B` (amber, CTAs and trust badges).
- Font: Noto Sans SC (Google Fonts, weights 300/400/500/600/700).
- Spacing: 4px base unit. Tailwind scale (`p-1`=4px … `p-12`=48px).
- Trust badges: `maintainer_picked`(amber ShieldCheck), `community_verified`(green Users), `unverified`(gray Circle), `doubtful`(red AlertTriangle). Always color + icon + text triple encoding.
- Cards: `border border-slate-200 rounded-lg`, hover `shadow-sm`, transition 200ms ease-out.
- Empty states: icon (Lucide, slate-300, 40-48px) + title + subtitle + action button. Centered with 64px vertical padding.
- Loading: skeleton screens with `animate-pulse`, never blank pages.
- Touch targets: ≥44×44px on all interactive elements.

## Issue workflow example

When asked "implement ISSUE-025" (College-Course cascading selector):

1. Read ISSUE-025 in `docs/ISSUES.md` — note it's blocked by ISSUE-024 and needs the `/api/v1/courses?college_id=` endpoint
2. Check ISSUE-024 is complete (colleges + courses API exists)
3. Implement:
   - Backend: verify `GET /api/v1/colleges` and `GET /api/v1/courses?college_id=` return needed data
   - Frontend: `CollegeCourseSelect.vue` — two cascading `<el-select>` components, college selection triggers async course fetch, supports local text filtering
   - Tests: vitest for component logic (college change clears course, filtering works)
4. Verify acceptance criteria: select college → course dropdown loads; filter by typing; parent form reads selected values
5. Mark issue complete, commit with message `feat: add college-course cascading selector (ISSUE-025)`
