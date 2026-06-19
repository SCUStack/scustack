# Anti-Scraping Protection Matrix

This matrix inventories the highest-value public data-discovery and download paths in the current product and assigns an explicit protection baseline for each one.

It is the policy input for follow-up implementation issues:

- `#240` unified request identity
- `#241` discovery-path rate limiting
- `#245` Redis failure strategy
- `#246` anti-scraping regression coverage

The source of truth for the machine-readable matrix lives in `scustack-api/app/core/anti_scraping.py`.

## Protection levels

| Level | Meaning |
| --- | --- |
| `baseline` | Minimal visibility path, generic protection is sufficient. |
| `guarded` | Public browsing path that must remain usable, but bulk enumeration should be slowed and observable. |
| `strict` | High-value discovery path where repeated scripted access should hit meaningful limits and escalation. |
| `critical` | Highest-value extraction path where silent loss of protection is unacceptable. |

## Matrix

| Route | Surface | Level | Current protection | Intended behavior | Redis failure strategy |
| --- | --- | --- | --- | --- | --- |
| `GET /api/v1/homepage` | Homepage discovery feed | `guarded` | No dedicated route limiter | Treat as a list-discovery path; add cursor-sensitive discovery limits and observability. | Degrade to per-process in-memory limiting. |
| `GET /api/v1/homepage/recent-updates` | Homepage recent feed pagination | `guarded` | No dedicated route limiter before endpoint split | Protect repeated cursor-driven feed pulls without recomputing homepage aggregate sections. | Degrade to per-process in-memory limiting. |
| `GET /api/v1/search` | Search results | `strict` | Per-IP limiter + rapid-scroll throttling | Preserve current search throttles and upgrade to identity-aware counters and escalation. | Degrade to per-process in-memory limiting. |
| `GET /api/v1/search/suggest` | Search suggestions | `strict` | Per-IP limiter | Share limiter identity with search and cap suggestion harvesting more aggressively. | Degrade to per-process in-memory limiting. |
| `GET /api/v1/colleges` | Top-level catalog | `guarded` | No dedicated route limiter | Bring into shared discovery-path limiting so enumeration cannot start here for free. | Degrade to per-process in-memory limiting. |
| `GET /api/v1/courses` | Course catalog | `guarded` | No dedicated route limiter | Protect both global and college-scoped list flows under the same discovery policy. | Degrade to per-process in-memory limiting. |
| `GET /api/v1/materials` | Materials list | `strict` | No dedicated route limiter | Apply discovery limits comparable to search so empty-query enumeration is harder. | Degrade to per-process in-memory limiting. |
| `GET /api/v1/materials/{material_id}` | Material detail | `guarded` | No dedicated route limiter | Allow ordinary reading while making deep scripted crawling measurable. | Degrade to per-process in-memory limiting. |
| `GET /api/v1/materials/{material_id}/related` | Related-material traversal | `strict` | No dedicated route limiter | Treat graph expansion as an enumeration vector and limit bursts more tightly than normal detail reads. | Degrade to per-process in-memory limiting. |
| `GET /api/v1/materials/{material_id}/download` | Hosted file download | `critical` | Per-user daily limit + per-IP hourly limiter | Keep strict quotas and introduce identity-aware fallback behavior. | Explicit deny-on-uncertain. |

## Notes

- This matrix covers public data exposure paths, not account-auth flows such as login, SMS verification, or password refresh.
- The matrix distinguishes policy from implementation. A route may already have partial protections today while still carrying stricter intended behavior for follow-up issues.
- Any new public list/detail/download endpoint should be added to the matrix before anti-scraping work is considered complete.
| 字段 | 内容 |
|---|---|
| Type | `matrix` |
| Status | `active` |
| Owner | `team` |
| Last Updated | `2026-06-19` |
| Source of Truth | `yes` |
| Scope | 反爬策略矩阵、不同路由的保护等级及其策略边界。 |

> 本文是反爬策略的主文档，定义不同能力等级下的保护要求，不负责具体代码实现细节。
