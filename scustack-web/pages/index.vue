<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="text-center mb-10">
      <h1 class="text-4xl font-bold text-primary-800 mb-2">川大课栈</h1>
      <p class="text-lg text-slate-500">SCU Course Stack — 四川大学课程资料共享平台</p>
      <p class="mt-2 text-sm text-slate-400">公益 · 无广告 · 开源</p>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
      <el-card v-for="stat in stats" :key="stat.label" shadow="hover">
        <div class="text-center py-4">
          <AppIcon :name="stat.icon" :size="32" class="text-primary-500 mb-2" />
          <p class="text-2xl font-semibold text-slate-800">{{ stat.value }}</p>
          <p class="text-sm text-slate-500">{{ stat.label }}</p>
        </div>
      </el-card>
    </div>

    <div class="text-center">
      <el-button type="primary" size="large" @click="onSearch">
        <AppIcon name="Search" :size="18" class="mr-1" />
        搜索课程资料
      </el-button>
      <el-button size="large" class="ml-3" @click="onUpload">
        <AppIcon name="Upload" :size="18" class="mr-1" />
        贡献资料
      </el-button>
    </div>

    <p class="text-center mt-6 text-xs text-slate-400">
      Nuxt 3 + Element Plus + Tailwind CSS — ISSUE-002
    </p>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ title: '首页' });

const stats = [
  { label: '覆盖学院', value: '30+', icon: 'Building2' },
  { label: '收录课程', value: '500+', icon: 'BookOpen' },
  { label: '课程资料', value: '2,000+', icon: 'Files' },
];

function onSearch() {
  navigateTo('/search');
}

function onUpload() {
  navigateTo('/upload');
}
</script>
