<template>
  <div>
    <Breadcrumb :items="[{ label: '首页', to: '/' }, { label: '关于' }]" />

    <!-- Hero -->
    <section class="relative overflow-hidden bg-gradient-to-br from-primary-900 via-primary-800 to-primary-950">
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(59,130,246,0.15),transparent_50%)]" />
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,rgba(245,158,11,0.08),transparent_50%)]" />
      <div class="relative max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-16 sm:py-20 text-center">
        <h1 class="text-3xl sm:text-4xl font-bold text-white mb-4 tracking-tight">川大课栈</h1>
        <p class="text-lg text-primary-200/80 max-w-xl mx-auto mb-10 leading-relaxed">
          四川大学课程资料共享平台<br />
          <span class="text-primary-200/60">由学生贡献 · 为学生服务 · 公益 · 开源</span>
        </p>

        <!-- Stats -->
        <div v-if="stats" class="grid grid-cols-2 sm:grid-cols-5 gap-3 max-w-3xl mx-auto">
          <div
            v-for="s in statCards"
            :key="s.label"
            class="bg-white/10 backdrop-blur-sm border border-white/15 rounded-xl p-4 sm:p-5"
          >
            <p class="text-2xl sm:text-3xl font-bold text-white">{{ s.value }}</p>
            <p class="text-xs sm:text-sm text-primary-200/70 mt-1">{{ s.label }}</p>
          </div>
        </div>
        <div v-else-if="loading" class="grid grid-cols-5 gap-3 max-w-3xl mx-auto">
          <div v-for="i in 5" :key="i" class="bg-white/10 rounded-xl p-5 animate-pulse">
            <div class="h-8 bg-white/10 rounded w-12 mx-auto mb-2" />
            <div class="h-3 bg-white/10 rounded w-10 mx-auto" />
          </div>
        </div>
      </div>
    </section>

    <!-- Mission + Story -->
    <section class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
      <div class="grid lg:grid-cols-2 gap-10">
        <!-- Mission -->
        <div>
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-700 text-xs font-medium mb-4">
            <AppIcon name="Lightbulb" :size="14" />
            我们的初心
          </div>
          <h2 class="text-xl font-semibold text-slate-900 mb-4">为什么做川大课栈</h2>
          <div class="space-y-3 text-sm text-slate-600 leading-relaxed">
            <p>
              每个学期末，朋友圈和课程群里都会出现同样的场景：求笔记、求真题、求复习提纲。
              这些宝贵的资料往往随着学长学姐的毕业而消失，学弟学妹们又得从零开始收集。
            </p>
            <p>
              川大课栈的初衷很简单 —— <strong class="text-slate-800">让知识传承下去</strong>。
              我们搭建一个公共的资料共享空间，让每一届学生的笔记、真题、复习资料都能
              被下一届同学看到和使用。
            </p>
            <p>
              我们相信，<strong class="text-slate-800">知识不应该被锁在个人的网盘里</strong>，
              特别是在大学这个本应以知识共享为核心的地方。
            </p>
          </div>
          <div class="mt-6 flex flex-wrap gap-3">
            <span class="inline-flex items-center gap-1.5 text-xs text-slate-500 bg-slate-100 rounded-full px-3 py-1.5">
              <AppIcon name="Heart" :size="12" class="text-rose-400" /> 非营利
            </span>
            <span class="inline-flex items-center gap-1.5 text-xs text-slate-500 bg-slate-100 rounded-full px-3 py-1.5">
              <AppIcon name="BadgeCheck" :size="12" class="text-emerald-400" /> 无广告
            </span>
            <span class="inline-flex items-center gap-1.5 text-xs text-slate-500 bg-slate-100 rounded-full px-3 py-1.5">
              <AppIcon name="Code" :size="12" class="text-primary-400" /> 开源
            </span>
            <span class="inline-flex items-center gap-1.5 text-xs text-slate-500 bg-slate-100 rounded-full px-3 py-1.5">
              <AppIcon name="Users" :size="12" class="text-amber-400" /> 学生维护
            </span>
          </div>
        </div>

        <!-- Disclaimer -->
        <div class="lg:border-l lg:border-slate-200 lg:pl-10">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-600 text-xs font-medium mb-4">
            <AppIcon name="Info" :size="14" />
            重要声明
          </div>
          <h2 class="text-xl font-semibold text-slate-900 mb-4">关于"川大"名称</h2>
          <div class="bg-amber-50 border border-amber-200 rounded-xl p-5">
            <div class="flex gap-3">
              <AppIcon name="AlertTriangle" :size="18" class="text-amber-500 shrink-0 mt-0.5" />
              <div class="text-sm text-amber-800 leading-relaxed space-y-2">
                <p>
                  川大课栈是由<strong>四川大学在校学生自发组织并维护的公益平台</strong>，
                  并非四川大学的官方网站或下属机构。
                </p>
                <p>
                  平台名称中的"川大"仅用于描述服务对象群体，<strong>不表示四川大学的认可或授权</strong>。
                  平台运营中使用的相关标识仅用于非营利性学术交流目的，其知识产权归四川大学所有。
                </p>
              </div>
            </div>
          </div>
          <div class="mt-4 text-xs text-slate-400 leading-relaxed space-y-1">
            <p>· 本平台对学生永久免费，不进行任何商业化运营</p>
            <p>· 所有资料由用户自愿上传，仅供学习参考</p>
            <p>· 如四川大学提出异议，本平台将立即停止使用相关标识</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Contribution heatmap -->
    <section class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
      <div class="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8">
        <div class="flex items-center justify-between mb-2">
          <div>
            <h2 class="text-lg font-semibold text-slate-800">贡献热力图</h2>
            <p class="text-xs text-slate-400 mt-0.5">过去一年每日上传资料数量</p>
          </div>
          <div class="hidden sm:flex items-center gap-1 text-[10px] text-slate-400">
            <span>少</span>
            <div class="w-3 h-3 rounded-sm bg-slate-100" />
            <div class="w-3 h-3 rounded-sm bg-primary-200" />
            <div class="w-3 h-3 rounded-sm bg-primary-400" />
            <div class="w-3 h-3 rounded-sm bg-primary-600" />
            <div class="w-3 h-3 rounded-sm bg-primary-800" />
            <span>多</span>
          </div>
        </div>
        <div v-if="loading" class="h-32 bg-slate-50 rounded-lg animate-pulse" />
        <div v-else class="overflow-x-auto pb-2 -mx-2 px-2">
          <div class="flex gap-[3px] min-w-[750px] flex-wrap" style="max-height: 124px">
            <div
              v-for="day in heatmap"
              :key="day.date"
              :title="day.date + ': ' + day.count + ' 份'"
              class="w-3 h-3 rounded-sm"
              :class="heatColor(day.count)"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- Contributors Hall of Fame -->
    <section class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
      <div class="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8">
        <div class="flex items-center justify-between mb-6">
          <div>
            <h2 class="text-lg font-semibold text-slate-800">贡献者墙</h2>
            <p class="text-xs text-slate-400 mt-0.5">感谢每一位为知识共享做出贡献的同学</p>
          </div>
        </div>

        <div v-if="loading" class="space-y-3">
          <div v-for="i in 5" :key="i" class="flex items-center gap-3 animate-pulse">
            <div class="w-6 h-4 bg-slate-100 rounded" />
            <div class="w-10 h-10 bg-slate-100 rounded-full" />
            <div class="flex-1 h-4 bg-slate-100 rounded" />
            <div class="w-16 h-4 bg-slate-100 rounded" />
          </div>
        </div>

        <div v-else-if="contributors.length === 0" class="text-center py-12">
          <AppIcon name="Users" :size="48" class="text-slate-300 mx-auto mb-4" />
          <p class="text-sm text-slate-400">还没有贡献者</p>
          <NuxtLink to="/upload" class="inline-flex items-center gap-1.5 mt-3 h-9 px-4 rounded-md text-sm font-medium bg-primary-700 text-white hover:bg-primary-800 no-underline transition-colors">
            <AppIcon name="Upload" :size="14" /> 成为第一位贡献者
          </NuxtLink>
        </div>

        <div v-else>
          <!-- Top 3 podium -->
          <div v-if="contributors.length >= 3" class="flex items-end justify-center gap-4 sm:gap-6 mb-10 pb-8 border-b border-slate-100">
            <!-- 2nd -->
            <div class="text-center">
              <div class="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-2 ring-2 ring-slate-300">
                <AppIcon name="User" :size="28" class="text-slate-400" />
              </div>
              <p class="text-xs font-medium text-slate-700 truncate max-w-[80px]">{{ contributors[1]?.display_name }}</p>
              <p class="text-[10px] text-slate-400">{{ contributors[1]?.material_count }} 份 · {{ fmtNum(contributors[1]?.total_downloads || 0) }} 下载</p>
              <div class="mt-2 w-14 h-1 bg-slate-300 rounded-full mx-auto" />
              <p class="text-[10px] text-slate-400 mt-1">🥈 第 2 名</p>
            </div>
            <!-- 1st -->
            <div class="text-center -mt-4">
              <div class="w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-amber-50 flex items-center justify-center mx-auto mb-2 ring-2 ring-amber-400">
                <AppIcon name="User" :size="32" class="text-amber-500" />
              </div>
              <p class="text-sm font-semibold text-slate-800 truncate max-w-[96px]">{{ contributors[0]?.display_name }}</p>
              <p class="text-xs text-slate-500">{{ contributors[0]?.material_count }} 份 · {{ fmtNum(contributors[0]?.total_downloads || 0) }} 下载</p>
              <div class="mt-2 w-16 h-1.5 bg-amber-400 rounded-full mx-auto" />
              <p class="text-[10px] text-amber-600 mt-1 font-medium">🥇 第 1 名</p>
            </div>
            <!-- 3rd -->
            <div class="text-center">
              <div class="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-slate-100 flex items-center justify-center mx-auto mb-2 ring-2 ring-amber-200">
                <AppIcon name="User" :size="24" class="text-slate-400" />
              </div>
              <p class="text-xs font-medium text-slate-700 truncate max-w-[70px]">{{ contributors[2]?.display_name }}</p>
              <p class="text-[10px] text-slate-400">{{ contributors[2]?.material_count }} 份 · {{ fmtNum(contributors[2]?.total_downloads || 0) }} 下载</p>
              <div class="mt-2 w-12 h-1 bg-amber-200 rounded-full mx-auto" />
              <p class="text-[10px] text-slate-400 mt-1">🥉 第 3 名</p>
            </div>
          </div>

          <!-- Rest of contributors -->
          <div class="space-y-1">
            <div
              v-for="c in contributors.slice(top3Count)"
              :key="c.user_id"
              class="flex items-center gap-3 py-2.5 px-3 rounded-lg hover:bg-slate-50 transition-colors"
            >
              <span class="w-8 text-center text-xs font-medium tabular-nums"
                :class="c.rank <= 5 ? 'text-amber-600' : 'text-slate-400'"
              >#{{ c.rank }}</span>
              <div class="w-9 h-9 rounded-full bg-primary-50 flex items-center justify-center shrink-0">
                <AppIcon name="User" :size="16" class="text-primary-500" />
              </div>
              <span class="flex-1 text-sm text-slate-700 truncate font-medium">{{ c.display_name }}</span>
              <span class="text-xs text-slate-500 shrink-0 tabular-nums">{{ c.material_count }} 份</span>
              <span class="text-xs text-slate-400 shrink-0 w-24 text-right tabular-nums hidden sm:block">{{ fmtNum(c.total_downloads) }} 次下载</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Sponsor -->
    <section class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-12">
      <div class="bg-gradient-to-br from-amber-50 via-white to-orange-50 border border-amber-200 rounded-2xl p-6 sm:p-8">
        <div class="text-center mb-8">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-100 border border-amber-200 text-amber-700 text-xs font-medium mb-3">
            <AppIcon name="Heart" :size="14" />
            支持我们
          </div>
          <h2 class="text-xl font-semibold text-slate-900 mb-2">赞助川大课栈</h2>
          <p class="text-sm text-slate-500 max-w-lg mx-auto leading-relaxed">
            川大课栈是完全公益的平台，服务器、存储、短信等费用全部由学生自费承担。
            每一份赞助都将直接用于维持平台运转，让知识共享持续下去。
          </p>
        </div>

        <!-- Cost breakdown -->
        <div class="grid sm:grid-cols-4 gap-3 mb-8 max-w-2xl mx-auto">
          <div class="text-center p-3 bg-white/70 rounded-lg border border-slate-100">
            <AppIcon name="Server" :size="18" class="text-slate-400 mx-auto mb-1" />
            <p class="text-xs font-medium text-slate-700">服务器</p>
            <p class="text-[10px] text-slate-400 mt-0.5">~¥200/月</p>
          </div>
          <div class="text-center p-3 bg-white/70 rounded-lg border border-slate-100">
            <AppIcon name="HardDrive" :size="18" class="text-slate-400 mx-auto mb-1" />
            <p class="text-xs font-medium text-slate-700">对象存储</p>
            <p class="text-[10px] text-slate-400 mt-0.5">~¥50/月</p>
          </div>
          <div class="text-center p-3 bg-white/70 rounded-lg border border-slate-100">
            <AppIcon name="Smartphone" :size="18" class="text-slate-400 mx-auto mb-1" />
            <p class="text-xs font-medium text-slate-700">短信服务</p>
            <p class="text-[10px] text-slate-400 mt-0.5">~¥30/月</p>
          </div>
          <div class="text-center p-3 bg-white/70 rounded-lg border border-slate-100">
            <AppIcon name="Globe" :size="18" class="text-slate-400 mx-auto mb-1" />
            <p class="text-xs font-medium text-slate-700">域名</p>
            <p class="text-[10px] text-slate-400 mt-0.5">~¥10/月</p>
          </div>
        </div>

        <!-- QR code area -->
        <div class="text-center">
          <p class="text-xs text-slate-400 mb-4">扫码赞赏，金额随意</p>
          <div class="inline-flex gap-6">
            <div class="text-center">
              <div class="w-40 h-40 rounded-xl bg-slate-100 flex items-center justify-center mb-2 border border-slate-200">
                <div class="text-center">
                  <AppIcon name="Wallet" :size="32" class="text-emerald-400 mx-auto mb-1" />
                  <p class="text-[10px] text-slate-400">微信赞赏码</p>
                  <p class="text-[10px] text-slate-300 mt-1">请替换为实际二维码</p>
                </div>
              </div>
              <p class="text-xs text-slate-500">微信支付</p>
            </div>
            <div class="text-center">
              <div class="w-40 h-40 rounded-xl bg-slate-100 flex items-center justify-center mb-2 border border-slate-200">
                <div class="text-center">
                  <AppIcon name="Wallet" :size="32" class="text-blue-400 mx-auto mb-1" />
                  <p class="text-[10px] text-slate-400">支付宝收款码</p>
                  <p class="text-[10px] text-slate-300 mt-1">请替换为实际二维码</p>
                </div>
              </div>
              <p class="text-xs text-slate-500">支付宝</p>
            </div>
          </div>
        </div>

        <p class="text-center text-[11px] text-slate-400 mt-6">
          赞助为自愿行为，不附带任何商业回报。感谢每一位支持者
          <AppIcon name="Heart" :size="11" class="inline text-rose-400 align-text-bottom" />
        </p>
      </div>
    </section>

    <!-- Footer links -->
    <section class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
      <div class="grid sm:grid-cols-3 gap-4">
        <NuxtLink to="/privacy" class="flex items-center gap-3 p-4 rounded-xl border border-slate-200 hover:border-primary-200 hover:bg-primary-50/50 no-underline transition-all group">
          <AppIcon name="Shield" :size="20" class="text-slate-400 group-hover:text-primary-500 transition-colors" />
          <div>
            <p class="text-sm font-medium text-slate-700">隐私政策</p>
            <p class="text-xs text-slate-400">我们如何保护你的数据</p>
          </div>
        </NuxtLink>
        <NuxtLink to="/terms" class="flex items-center gap-3 p-4 rounded-xl border border-slate-200 hover:border-primary-200 hover:bg-primary-50/50 no-underline transition-all group">
          <AppIcon name="FileText" :size="20" class="text-slate-400 group-hover:text-primary-500 transition-colors" />
          <div>
            <p class="text-sm font-medium text-slate-700">用户协议</p>
            <p class="text-xs text-slate-400">使用条款与行为规范</p>
          </div>
        </NuxtLink>
        <a href="https://github.com/yeyixiang2007/scustack" target="_blank" rel="noopener"
           class="flex items-center gap-3 p-4 rounded-xl border border-slate-200 hover:border-primary-200 hover:bg-primary-50/50 no-underline transition-all group">
          <AppIcon name="Code2" :size="20" class="text-slate-400 group-hover:text-primary-500 transition-colors" />
          <div>
            <p class="text-sm font-medium text-slate-700">开源代码</p>
            <p class="text-xs text-slate-400">MIT License · 欢迎贡献</p>
          </div>
        </a>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
const { apiBase } = useRuntimeConfig().public

interface Stats {
  college_count: number
  course_count: number
  material_count: number
  contributor_count: number
  total_downloads: number
}

interface HeatmapDay {
  date: string
  count: number
  day_of_week: number
}

interface Contributor {
  user_id: string
  display_name: string
  material_count: number
  total_downloads: number
  rank: number
}

const stats = ref<Stats | null>(null)
const heatmap = ref<HeatmapDay[]>([])
const contributors = ref<Contributor[]>([])
const loading = ref(true)

const statCards = computed(() => {
  if (!stats.value) return []
  const s = stats.value
  return [
    { label: '学院', value: s.college_count },
    { label: '课程', value: s.course_count },
    { label: '资料', value: s.material_count },
    { label: '贡献者', value: s.contributor_count },
    { label: '总下载', value: fmtNum(s.total_downloads) },
  ]
})

const top3Count = computed(() => contributors.value.length >= 3 ? 3 : 0)

function fmtNum(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

function heatColor(count: number): string {
  if (count === 0) return 'bg-slate-100'
  if (count <= 2) return 'bg-primary-200'
  if (count <= 5) return 'bg-primary-400'
  if (count <= 10) return 'bg-primary-600'
  return 'bg-primary-800'
}

onMounted(async () => {
  try {
    const resp = await $fetch<{ code: number; data: { stats: Stats; heatmap: HeatmapDay[]; contributors: Contributor[] } }>(
      `${apiBase}/api/v1/about`
    )
    if (resp.code === 0) {
      stats.value = resp.data.stats
      heatmap.value = resp.data.heatmap
      contributors.value = resp.data.contributors
    }
  } catch { /* noop */ }
  loading.value = false
})
</script>
