import coverTagsData from '~/data/covers'
import subjectAliases from '~/data/subjects'

export const coverCategoryKeywordSets = {
  category: new Set([
    '考试', '期末', '期中', '真题', '试卷', '答案', '解析', '试题', '答题',
    '模考', '补考', '样卷', '小题', '大题', '论述', '问答', '辨析', '判断',
    '单选', '多选', '名词解释', '完形', '阅读', '专项训练', '模拟题',
  ]),
  review: new Set([
    '复习', '提纲', '总结', '归纳', '重点', '考点', '高频', '思维导图',
    '易错', '错题', '框架', '概要', '速查', '背诵', '口诀', '对比表',
    '速记', '突击', '汇总', '整理', '专题',
  ]),
  notes: new Set([
    '笔记', '课堂', '手写', '扫描', '标注', '电子', '随堂', '听课',
    '心得', '记录', '彩色', '标注', '整理', 'iPad', '平板',
  ]),
  textbook: new Set([
    '教材', '课本', '参考书', '经典', '原版', '影印', '译本', '合集',
    '电子版', '指定', '辅助', '推荐',
  ]),
  problem: new Set([
    '习题', '作业', '编程', '代码', '算法', '课后', '上机', '课程设计',
    '专项', '题库', '综合', '证明', '计算', '应用', '训练', '小题狂练',
    '练习', '解答', '参考答案',
  ]),
  lab: new Set([
    '实验', '数据', '报告', '指导书', '操作', '规范', '模板', '现象',
    '处理', '步骤', '分析', '记录',
  ]),
  past: new Set([
    '历年', '考研', '汇编', '回忆', '真题', '十年', '合集',
  ]),
  slides: new Set([
    '课件', '讲义', 'PPT', '黑板', '板书', '教学大纲', '幻灯片',
    '演示', '投影',
  ]),
} as const

export const coverCategoryInferenceOrder: [string, ReadonlySet<string>][] = [
  ['考试资料', coverCategoryKeywordSets.category],
  ['复习提纲', coverCategoryKeywordSets.review],
  ['课堂笔记', coverCategoryKeywordSets.notes],
  ['教材', coverCategoryKeywordSets.textbook],
  ['习题集', coverCategoryKeywordSets.problem],
  ['实验报告', coverCategoryKeywordSets.lab],
  ['历年真题', coverCategoryKeywordSets.past],
  ['课件讲义', coverCategoryKeywordSets.slides],
]

export const directSubjectKeywords = new Set([
  '数学', '代数', '几何', '概率', '统计', '物理', '力学', '电磁',
  '化学', '有机', '无机', '生物', '遗传', '细胞', '分子',
  '计算机', '编程', '代码', '算法', '程序', '软件', '网络',
  '数据库', '电子', '电路', '信号', '通信', '管理', '经济',
  '会计', '金融', '医学', '解剖', '病理', '药学', '诊断',
  '文学', '汉语', '语言', '英语', '历史',
])

export const formatKeywords = new Set([
  '手写', '扫描', '电子', '打印', '装订', '影印', '复印', '高清',
  '彩色', '黑白', '平板', 'iPad', '手机', '草稿', 'PDF',
  '扫描版', '电子版', '打印版', '影印本', '原卷', '套装',
  'A4', '活页', '装订成册',
])

export const vibeKeywords = new Set([
  '泛黄', '旧', '整洁', '密集', '简约', '经典', '最新', '回忆',
  '完整', '整理', '详细', '简单', '精美', '清晰', '高清',
  '手绘', '原创', '自整理', '独家',
])

export const allCategoryKeywords = new Set([
  ...coverCategoryKeywordSets.category,
  ...coverCategoryKeywordSets.review,
  ...coverCategoryKeywordSets.notes,
  ...coverCategoryKeywordSets.textbook,
  ...coverCategoryKeywordSets.problem,
  ...coverCategoryKeywordSets.lab,
  ...coverCategoryKeywordSets.past,
  ...coverCategoryKeywordSets.slides,
])

export { coverTagsData, subjectAliases }
