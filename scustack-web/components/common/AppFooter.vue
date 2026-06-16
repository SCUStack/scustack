<template>
  <footer class="border-t border-slate-200 bg-white mt-12">
    <div class="max-w-7xl mx-auto px-2 sm:px-3 lg:px-4 py-8">
      <div class="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div class="text-sm text-slate-400">
          <span class="font-medium text-slate-500">川大课栈</span>
          <span class="mx-2">·</span>
          <span>公益 · 无广告 · 开源</span>
        </div>
        <nav class="flex items-center gap-4 text-sm">
          <a href="https://github.com/yeyixiang2007/scustack" target="_blank" rel="noopener"
             class="text-slate-400 hover:text-slate-600 no-underline transition-colors duration-150">GitHub</a>
          <NuxtLink to="/colleges" class="text-slate-400 hover:text-slate-600 no-underline transition-colors duration-150">学院目录</NuxtLink>
          <NuxtLink to="/about" class="text-slate-400 hover:text-slate-600 no-underline transition-colors duration-150">关于</NuxtLink>
        </nav>
      </div>
    </div>
  </footer>
</template>
