# Local Experience State Boundary

This project distinguishes backend-backed business truth from browser-only convenience state.

## Rule

- Backend-backed business data must come from API contracts, not `localStorage`.
- `localStorage` is allowed only for local experience state that improves convenience for the current browser and can be safely lost without changing product truth.

## Allowed local-only state

| State | Storage key | Why it may stay local |
| --- | --- | --- |
| Recent browsing history | `scustack_recent` | Convenience-only history for quickly returning to recently viewed courses and materials. |
| Search history | `scustack_search_history` | Personal browser shortcut history, not shared product truth. |
| Upload draft | `uploadDraft` | Recovery for an unfinished form before submission. |
| Dismissed announcements | `scustack_dismissed:{id}` | Per-browser dismissal preference for already seen announcements. |

## Not allowed in local-only state

- Authenticated user profile truth
- Bookmarks, follows, ratings, reports, review decisions
- Search filter capabilities, enum values, trust states, categories, source types
- Any state that affects what the backend accepts, stores, or returns

## Code contract

All approved local-only state access should go through `scustack-web/composables/useLocalExperienceState.ts`.
Direct new `localStorage` usage outside that boundary should be treated as a regression unless it is added to this document and the registry first.
| 字段 | 内容 |
|---|---|
| Type | `state` |
| Status | `active` |
| Owner | `team` |
| Last Updated | `2026-06-19` |
| Source of Truth | `yes` |
| Scope | 当前本地开发体验的状态边界、规则和已知约束。 |

> 本文记录的是当前状态快照，帮助团队快速了解本地开发体验，不替代长期架构和部署文档。
