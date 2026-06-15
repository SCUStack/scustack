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

// ── Subject alias map — full course name → short subject key ─────────

import SUBJECT_ALIASES from '~/data/subjects'

// ── Category-specific keyword sets ───────────────────────────────────

const CAT_KW = new Set([
  '考试', '期末', '期中', '真题', '试卷', '答案', '解析', '试题', '答题',
  '模考', '补考', '样卷', '小题', '大题', '论述', '问答', '辨析', '判断',
  '单选', '多选', '名词解释', '完形', '阅读', '专项训练', '模拟题',
])

const REVIEW_KW = new Set([
  '复习', '提纲', '总结', '归纳', '重点', '考点', '高频', '思维导图',
  '易错', '错题', '框架', '概要', '速查', '背诵', '口诀', '对比表',
  '速记', '突击', '汇总', '整理', '专题',
])

const NOTES_KW = new Set([
  '笔记', '课堂', '手写', '扫描', '标注', '电子', '随堂', '听课',
  '心得', '记录', '彩色', '标注', '整理', 'iPad', '平板',
])

const TEXTBOOK_KW = new Set([
  '教材', '课本', '参考书', '经典', '原版', '影印', '译本', '合集',
  '电子版', '指定', '辅助', '推荐',
])

const PROBLEM_KW = new Set([
  '习题', '作业', '编程', '代码', '算法', '课后', '上机', '课程设计',
  '专项', '题库', '综合', '证明', '计算', '应用', '训练', '小题狂练',
  '练习', '解答', '参考答案',
])

const LAB_KW = new Set([
  '实验', '数据', '报告', '指导书', '操作', '规范', '模板', '现象',
  '处理', '步骤', '分析', '记录',
])

const PAST_KW = new Set([
  '历年', '考研', '汇编', '回忆', '真题', '十年', '合集',
])

const SLIDES_KW = new Set([
  '课件', '讲义', 'PPT', '黑板', '板书', '教学大纲', '幻灯片',
  '演示', '投影',
])

const ALL_CAT_KW = new Set([
  ...CAT_KW, ...REVIEW_KW, ...NOTES_KW, ...TEXTBOOK_KW,
  ...PROBLEM_KW, ...LAB_KW, ...PAST_KW, ...SLIDES_KW,
])

// ── Direct subject keywords (used in titles without full course name)

const SUB_KW = new Set([
  '数学', '代数', '几何', '概率', '统计', '物理', '力学', '电磁',
  '化学', '有机', '无机', '生物', '遗传', '细胞', '分子',
  '计算机', '编程', '代码', '算法', '程序', '软件', '网络',
  '数据库', '电子', '电路', '信号', '通信', '管理', '经济',
  '会计', '金融', '医学', '解剖', '病理', '药学', '诊断',
  '文学', '汉语', '语言', '英语', '历史',
])

// ── Format and vibe keywords ─────────────────────────────────────────

const FORMAT_KW = new Set([
  '手写', '扫描', '电子', '打印', '装订', '影印', '复印', '高清',
  '彩色', '黑白', '平板', 'iPad', '手机', '草稿', 'PDF',
  '扫描版', '电子版', '打印版', '影印本', '原卷', '套装',
  'A4', '活页', '装订成册',
])

const VIBE_KW = new Set([
  '泛黄', '旧', '整洁', '密集', '简约', '经典', '最新', '回忆',
  '完整', '整理', '详细', '简单', '精美', '清晰', '高清',
  '手绘', '原创', '自整理', '独家',
])

// ── Tokenizer ────────────────────────────────────────────────────────

function tokenize(text: string, category: string) {
  const cat = new Set<string>()
  const sub = new Set<string>()
  const fmt = new Set<string>()
  const vibe = new Set<string>()

  // Category tokens: match against all category keyword sets
  for (const kw of ALL_CAT_KW) {
    if (text.includes(kw)) cat.add(kw)
  }

  // Subject — course name aliases
  for (const [course, alias] of Object.entries(SUBJECT_ALIASES)) {
    if (text.includes(course)) sub.add(alias)
  }
  // Direct keyword match
  for (const kw of SUB_KW) {
    if (text.includes(kw)) sub.add(kw)
  }

  // Format
  for (const kw of FORMAT_KW) {
    if (text.includes(kw)) fmt.add(kw)
  }

  // Vibe
  for (const kw of VIBE_KW) {
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
  _tagsCache = (await import('~/data/covers')).default as TagsData
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
export function resolveCoverSync(
  item: { id?: string; title?: string; category?: string },
  tags: TagsData,
): string {
  const title = item.title || ''
  const category = item.category || ''
  const id = item.id || title

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
