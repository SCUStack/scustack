<template>
  <footer class="border-t border-slate-200 bg-slate-50 mt-12 pb-16 lg:pb-0">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <!-- Main grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8 mb-8">
        <!-- Brand -->
        <div>
          <h4 class="text-sm font-semibold text-slate-800 mb-3">川流课栈</h4>
          <p class="text-xs text-slate-500 leading-relaxed">
            四川大学公益课程资料共享平台<br />
            由学生社区维护，无广告、无收费
          </p>
        </div>

        <!-- Links -->
        <div>
          <h4 class="text-sm font-semibold text-slate-800 mb-3">导航</h4>
          <ul class="space-y-2">
            <li><NuxtLink to="/" class="text-xs text-slate-500 hover:text-slate-700 no-underline transition-colors">首页</NuxtLink></li>
            <li><NuxtLink to="/colleges" class="text-xs text-slate-500 hover:text-slate-700 no-underline transition-colors">学院目录</NuxtLink></li>
            <li><NuxtLink to="/search" class="text-xs text-slate-500 hover:text-slate-700 no-underline transition-colors">搜索资料</NuxtLink></li>
            <li><NuxtLink to="/upload" class="text-xs text-slate-500 hover:text-slate-700 no-underline transition-colors">贡献资料</NuxtLink></li>
          </ul>
        </div>

        <!-- Legal -->
        <div>
          <h4 class="text-sm font-semibold text-slate-800 mb-3">法律</h4>
          <ul class="space-y-2">
            <li><NuxtLink to="/about" class="text-xs text-slate-500 hover:text-slate-700 no-underline transition-colors">关于本站</NuxtLink></li>
            <li><NuxtLink to="/copyright" class="text-xs text-slate-500 hover:text-slate-700 no-underline transition-colors">版权投诉</NuxtLink></li>
            <li><NuxtLink to="/privacy" class="text-xs text-slate-500 hover:text-slate-700 no-underline transition-colors">隐私政策</NuxtLink></li>
            <li><NuxtLink to="/terms" class="text-xs text-slate-500 hover:text-slate-700 no-underline transition-colors">用户协议</NuxtLink></li>
          </ul>
        </div>

        <!-- Community -->
        <div>
          <h4 class="text-sm font-semibold text-slate-800 mb-3">社区</h4>
          <ul class="space-y-2">
            <li>
              <a href="https://github.com/yeyixiang2007/scustack" target="_blank" rel="noopener"
                 class="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 no-underline transition-colors">
                <AppIcon name="Code2" :size="12" /> GitHub
              </a>
            </li>
            <li>
              <a href="mailto:admin@scustack.com" class="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700 no-underline transition-colors">
                <AppIcon name="Mail" :size="12" /> 联系维护者
              </a>
            </li>
          </ul>
        </div>
      </div>

      <!-- Bottom bar -->
      <div class="pt-6 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div class="flex flex-wrap items-center justify-center gap-x-4 gap-y-1 text-xs text-slate-400">
          <span>&copy; {{ currentYear }} 川流课栈</span>
          <span class="hidden sm:inline">·</span>
          <span>公益 · 无广告 · 开源</span>
        </div>
        <div class="flex flex-wrap items-center justify-center gap-x-3 gap-y-1 text-xs text-slate-400">
          <a href="https://beian.miit.gov.cn/" target="_blank" rel="noopener" class="text-slate-400 hover:text-slate-600 no-underline transition-colors">蜀ICP备XXXXXXXX号</a>
          <span class="hidden sm:inline">·</span>
          <a href="http://www.beian.gov.cn/" target="_blank" rel="noopener" class="text-slate-400 hover:text-slate-600 no-underline transition-colors">川公网安备 XXXXXXXXXXXXXX号</a>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
const currentYear = new Date().getFullYear()
</script>
