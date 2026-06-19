# Website Launch Checklist

This checklist is the release gate for the **main website**.

It separates:

- work already completed in-repo
- manual verification still required before go-live
- unresolved external / HITL blockers that still prevent a true production launch

Use this document together with:

- [DEPLOYMENT-部署手册.md](./DEPLOYMENT-部署手册.md)
- [ARCHITECTURE-技术架构.md](./ARCHITECTURE-技术架构.md)

## 1. In-Repo Launch Work Completed

These items already have repository evidence and should not require more product code before a website launch decision.

### Search and business contract stability

- `#227` Frontend business enums are centralized.
- `#228` Cover mapping and subject alias rules are centralized.
- `#229` Homepage banner presentation is backend-configurable.
- `#230` Local-only browser convenience state is explicitly bounded.
- `#231` Search filters are backend-driven.
- `#232` Frontend/backend business contract consistency tests exist.

### Anti-scraping baseline

- `#239` High-value endpoint anti-scraping matrix exists.
- `#240` Unified anonymous/authenticated request identity exists.
- `#241` Discovery-path rate limiting covers colleges, courses, materials, homepage, and related traversal.
- `#242` Search pressure escalation exists.
- `#243` High-risk anonymous search challenge exists.
- `#244` Anti-scraping observability and admin security surface exist.
- `#245` Redis failure strategies are explicit.
- `#246` System-level anti-scraping regression coverage exists.

### Documentation alignment

- `#250` Architecture docs reflect the implemented homepage presentation config path and related API/service/model changes.

## 2. Required Automated Verification

Run these before calling the website release candidate ready:

### Frontend

```bash
pnpm --filter scustack-web typecheck
pnpm --filter scustack-web test
```

### Backend

```bash
pytest scustack-api/tests
```

### Critical focused suites

```bash
pytest scustack-api/tests/test_anti_scraping_regression.py
pytest scustack-api/tests/test_homepage_presentation.py
pytest scustack-api/tests/test_search.py
```

## 3. Manual Website Smoke Checklist

These are required because repo-only evidence cannot prove real production behavior.

- Home page renders with configured banners and loads recent updates.
- Search works for ordinary traffic.
- High-risk anonymous search returns a challenge response instead of silently failing open.
- Login succeeds and authenticated write actions still work.
- Hosted upload stays `pending` until review.
- Admin review can approve a material.
- Hosted download still works under normal conditions.
- Admin security page shows anti-scraping events after a triggered protection path.
- Office preview is reachable from the real frontend deployment.
- `/api/v1/health`, `/api/v1/health/live`, and `/api/v1/health/ready` all pass in the target environment.

## 4. External Blockers Still Preventing True Go-Live

These are **not solved by more repository-only code changes** and should be treated as launch blockers until explicitly cleared.

### Infrastructure / operations

- `#106` PgBouncer connection pooling deployment
  Why it blocks launch:
  Phase-1 audit identifies this as a P0 production stability requirement for peak traffic.

- `#107` Elastic scaling / ESS configuration
  Why it blocks launch:
  Peak traffic handling is still operationally incomplete.

- `#112` Performance load testing in a real environment
  Why it blocks launch:
  There is still no real production-like load evidence.

- `#223` Staging rollback rehearsal
  Why it blocks launch:
  The rollback runbook is documented but not proven in staging.

### Compliance / manual review

- `#120` Accessibility review and remediation
  Why it blocks launch:
  No real A11y audit evidence is present yet.

### Intentionally excluded

- `#139` Dark mode
  Not part of the current launch gate.

## 5. Multi-End Work That Does Not Block Main Website Launch

These remain open, but they are not required to launch the **website** itself:

- `#233` Multi-end technical route
- `#234` Shared API/type layer for multi-end clients
- `#235` Android/iOS shell packaging
- `#236` Mini program MVP
- `#237` Mobile upload/file capability convergence
- `#238` Multi-end regression coverage

## 6. Launch Decision Rule

The website should be considered ready for go-live only when:

1. Section 2 automated verification is green.
2. Section 3 manual smoke checks are completed in the target environment.
3. Every blocker in Section 4 is explicitly cleared or consciously waived by the people responsible for launch.

If any item in Section 4 remains unresolved and unwaived, the website is **not yet truly launch-ready**, even if the repository itself is in good shape.
| 字段 | 内容 |
|---|---|
| Type | `checklist` |
| Status | `active` |
| Owner | `team` |
| Last Updated | `2026-06-19` |
| Source of Truth | `yes` |
| Scope | MVP 上线前需要逐项确认的准备项、验证项与风险项。 |

> 本文用于上线前逐项核对，不替代部署步骤文档，也不承载架构决策。
