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
