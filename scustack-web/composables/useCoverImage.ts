/**
 * Cover image matching composable.
 *
 * Four-dimensional weighted tag matching:
 *   Category ×3  |  Subject ×2  |  Format ×1  |  Vibe ×1
 *
 * Falls back through: tag match → category random (hash) → empty string
 */
// ── Types ────────────────────────────────────────────────────────────

interface CoverEntry {
  readonly file: string
  readonly cat: readonly string[]
  readonly sub: readonly string[]
  readonly fmt: readonly string[]
  readonly vibe: readonly string[]
}

interface TagsData {
  readonly [category: string]: readonly CoverEntry[]
}

// ── Weights ──────────────────────────────────────────────────────────

const W_CAT = 3
const W_SUB = 2
const W_FMT = 1
const W_VIBE = 1

import {
  allCategoryKeywords,
  coverCategoryInferenceOrder,
  coverTagsData,
  directSubjectKeywords,
  formatKeywords,
  subjectAliases,
  vibeKeywords,
} from '~/data/coverRules'

// ── Tokenizer ────────────────────────────────────────────────────────

function tokenize(text: string, category: string) {
  const cat = new Set<string>()
  const sub = new Set<string>()
  const fmt = new Set<string>()
  const vibe = new Set<string>()

  // Category tokens: match against all category keyword sets
  for (const kw of allCategoryKeywords) {
    if (text.includes(kw)) cat.add(kw)
  }

  // Subject — course name aliases
  for (const [course, alias] of Object.entries(subjectAliases)) {
    if (text.includes(course)) sub.add(alias)
  }
  // Direct keyword match
  for (const kw of directSubjectKeywords) {
    if (text.includes(kw)) sub.add(kw)
  }

  // Format
  for (const kw of formatKeywords) {
    if (text.includes(kw)) fmt.add(kw)
  }

  // Vibe
  for (const kw of vibeKeywords) {
    if (text.includes(kw)) vibe.add(kw)
  }

  return { cat, sub, fmt, vibe }
}

// ── Matching ─────────────────────────────────────────────────────────

function matchEntry(
  title: string,
  category: string,
  entry: CoverEntry,
): number {
  const tokens = tokenize(title, category)
  return (
    W_CAT * intersectCount(tokens.cat, new Set(entry.cat))
    + W_SUB * intersectCount(tokens.sub, new Set(entry.sub))
    + W_FMT * intersectCount(tokens.fmt, new Set(entry.fmt))
    + W_VIBE * intersectCount(tokens.vibe, new Set(entry.vibe))
  )
}

function intersectCount(a: Set<string>, b: Set<string>): number {
  let count = 0
  for (const item of a) {
    if (b.has(item)) count++
  }
  return count
}

function hashString(s: string): number {
  let h = 0
  for (let i = 0; i < s.length; i++) {
    h = ((h << 5) - h) + s.charCodeAt(i)
    h |= 0
  }
  return Math.abs(h)
}

// ── Public API ───────────────────────────────────────────────────────

let _tagsCache: TagsData | null = null

async function loadTags(): Promise<TagsData> {
  if (_tagsCache) return _tagsCache
  _tagsCache = coverTagsData as TagsData
  return _tagsCache!
}

/**
 * Resolve the cover image path for a material.
 *
 * @returns The relative path to the cover image, or empty string for fallback.
 */
export async function resolveCover(item: { id?: string; title?: string; category?: string }): Promise<string> {
  const title = item.title || ''
  const category = item.category || ''
  const id = item.id || title

  const tags = await loadTags()
  const pool = tags[category]
  if (!pool || pool.length === 0) return ''

  let bestFile = ''
  let bestScore = -1

  for (const entry of pool) {
    const score = matchEntry(title, category, entry)
    if (score > bestScore) {
      bestScore = score
      bestFile = entry.file
    } else if (score === bestScore && score > 0) {
      // Tie-break: deterministic hash of material id
      const hashA = hashString(`${id}:${bestFile}`)
      const hashB = hashString(`${id}:${entry.file}`)
      if (hashB > hashA) bestFile = entry.file
    }
  }

  // Fallback: hash-based random from category pool
  if (bestScore <= 0) {
    const idx = hashString(id) % pool.length
    bestFile = pool[idx].file
  }

  return `/covers/${category}/${bestFile}`
}

/**
 * Synchronous version that uses a pre-loaded tags object.
 * Useful for SSR/build-time where async import isn't needed.
 */
// ── Category inference (fallback when API category doesn't match cover keys)

function inferCategory(title: string): string | null {
  let best = ''
  let bestCount = 0
  for (const [cat, kwSet] of coverCategoryInferenceOrder) {
    let count = 0
    for (const kw of kwSet) {
      if (title.includes(kw)) count++
    }
    if (count > bestCount) {
      bestCount = count
      best = cat
    }
  }
  return bestCount > 0 ? best : null
}

export function resolveCoverSync(
  item: { id?: string; title?: string; category?: string },
  tags: TagsData,
): string {
  const title = item.title || ''
  const id = item.id || title
  let category = item.category || ''

  // Exact match first, then fallback to inference from title
  let pool = tags[category]
  if (!pool || pool.length === 0) {
    const inferred = inferCategory(title)
    if (inferred) {
      category = inferred
      pool = tags[category]
    }
  }
  if (!pool || pool.length === 0) return ''

  let bestFile = ''
  let bestScore = -1

  for (const entry of pool) {
    const score = matchEntry(title, category, entry)
    if (score > bestScore) {
      bestScore = score
      bestFile = entry.file
    } else if (score === bestScore && score > 0) {
      const hashA = hashString(`${id}:${bestFile}`)
      const hashB = hashString(`${id}:${entry.file}`)
      if (hashB > hashA) bestFile = entry.file
    }
  }

  if (bestScore <= 0) {
    const idx = hashString(id) % pool.length
    bestFile = pool[idx].file
  }

  return `/covers/${category}/${bestFile}`
}
