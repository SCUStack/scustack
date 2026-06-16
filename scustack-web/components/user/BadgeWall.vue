<template>
  <div v-if="allBadges.length > 0" class="bg-white border border-slate-200 rounded-lg p-6">
    <h3 class="text-base font-medium text-slate-800 mb-4">徽章</h3>
    <div class="flex flex-wrap gap-4">
      <el-tooltip
        v-for="badge in allBadges"
        :key="badge.type"
        :content="badge.tooltip"
        placement="top"
        :show-after="300"
      >
        <div class="flex flex-col items-center gap-1.5 cursor-default">
          <div
            class="w-12 h-12 rounded-full flex items-center justify-center border-2 transition-colors duration-200"
            :class="badge.earned ? 'border-current' : 'border-slate-200'"
            :style="badge.earned ? { color: badge.color, backgroundColor: badge.color + '15' } : {}"
          >
            <AppIcon :name="badge.icon" :size="22" :class="badge.earned ? '' : 'text-slate-300'" />
          </div>
          <span
            class="text-xs text-center leading-tight max-w-[64px]"
            :class="badge.earned ? 'text-slate-700 font-medium' : 'text-slate-400'"
          >
            {{ badge.label }}
          </span>
        </div>
      </el-tooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
interface BadgeDef {
  type: string
  label: string
  description: string
  color: string
  icon: string
  earned: boolean
  awardedAt: string | null
  tooltip: string
}

const { getBadges } = useAuth()

const allBadges = ref<BadgeDef[]>([])

const BADGE_TEMPLATES: Omit<BadgeDef, 'earned' | 'awardedAt' | 'tooltip'>[] = [
  { type: 'first_upload', label: '初次上传', description: '上传第一份通过审核的资料', color: '#3B82F6', icon: 'Upload' },
  { type: 'prolific_10', label: '高产作者', description: '累计上传 10 份资料', color: '#8B5CF6', icon: 'Layers' },
  { type: 'prolific_50', label: '资料达人', description: '累计上传 50 份资料', color: '#7C3AED', icon: 'Layers' },
  { type: 'prolific_100', label: '资料大师', description: '累计上传 100 份资料', color: '#5B21B6', icon: 'Layers' },
  { type: 'popular_100', label: '小有名气', description: '单份资料下载量突破 100', color: '#F59E0B', icon: 'TrendingUp' },
  { type: 'popular_1000', label: '万人迷', description: '单份资料下载量突破 1000', color: '#EA580C', icon: 'TrendingUp' },
  { type: 'popular_10000', label: '超级明星', description: '单份资料下载量突破 10000', color: '#DC2626', icon: 'TrendingUp' },
  { type: 'selfless', label: '活雷锋', description: '上传资料被收藏夹收录 10 次', color: '#10B981', icon: 'HeartHandshake' },
  { type: 'college_contributor', label: '学院贡献者', description: '所在学院上传量 Top 3', color: '#06B6D4', icon: 'GraduationCap' },
  { type: 'continuous_3', label: '连续贡献', description: '连续 3 个月有上传', color: '#F97316', icon: 'CalendarCheck' },
  { type: 'wish_fulfiller', label: '心愿达成者', description: '上传资料满足了心愿单需求', color: '#EC4899', icon: 'Sparkles' },
]

onMounted(async () => {
  try {
    const resp = await getBadges()
    if (resp.code !== 0) return
    const earnedSet = new Set(resp.data.badges.map(b => b.badge_type))
    allBadges.value = BADGE_TEMPLATES.map(t => ({
      ...t,
      earned: earnedSet.has(t.type),
      awardedAt: resp.data.badges.find(b => b.badge_type === t.type)?.awarded_at ?? null,
      tooltip: earnedSet.has(t.type) ? `${t.label} — ${t.description}` : `${t.label} — 尚未获得`,
    }))
  } catch { /* ignore */ }
})
</script>
