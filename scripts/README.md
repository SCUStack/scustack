# Scripts

All scripts run from repo root: `python scripts/<name>.py`

## Recommendation algorithm

| Script | Purpose | Run when |
|---|---|---|
| `recommend_simulation.py` | Slot-based recommendation algorithm simulation. Generates synthetic contributor profiles, validates fairness metrics (Gini, unique contributors, newcomer exposure), and sweeps decay rate / exploration boost parameters. | Before changing recommendation logic |
| `personalize_simulation.py` | Personalized recommendation simulation. Models users with college, bookmarks, and download history. Validates college + course affinity recall paths against baseline. | Before adding personalization features |

## Cover image system

| Script | Purpose | Run when |
|---|---|---|
| `build_subject_aliases.py` | Generates `subject_aliases.py` and `scustack-web/data/subjects.ts` from the MOE 2024 undergraduate major catalog plus 30+ university curricula. Currently 1,265 course name → subject mappings. Outputs are committed to the repo. | When adding new majors or courses |
| `subject_aliases.py` | Generated file — 1,265 course name aliases. Imported by `cover_match_simulation.py`. Do not edit directly. | Auto-generated |
| `cover_match_simulation.py` | Validates the four-dimension tag matching algorithm (Category×3 Subject×2 Format×1 Vibe×1). Measures match rate, subject differentiation, per-category coverage, and weight sensitivity. | After changing the algorithm or expanding the cover pool |
| `export_tags.py` | Exports the cover pool to both `tags.json` and `scustack-web/data/covers.ts` (kept in sync). Use `--ext webp` after downloading real photos. | After changing the cover pool in the simulation |
| `download_covers.py` | Downloads real cover images from Pexels API (free tier: 200 req/hr) or LoremFlickr (free, no key needed but Chinese search unreliable). Set `PEXELS_API_KEY` env var before running. Images save to `scustack-web/public/covers/{category}/`. | Once, to replace placeholder SVGs with real photos |

### Cover image workflow

```
1. Edit cover pool   →  cover_match_simulation.py (add entries to COVER_POOL)
2. Validate          →  python scripts/cover_match_simulation.py
3. Export tags       →  python scripts/export_tags.py
4. Generate aliases  →  python scripts/build_subject_aliases.py  (if new courses added)
5. Download images   →  $env:PEXELS_API_KEY="your-key"; python scripts/download_covers.py
6. Done — covers are auto-matched in production by useCoverImage.ts
```

## Other

| Script | Purpose |
|---|---|
| `seed_data.py` | Seeds the database with sample colleges, courses, and materials |
