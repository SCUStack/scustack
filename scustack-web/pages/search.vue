<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <el-input
      v-model="query"
      placeholder="搜索课程、资料、关键词..."
      size="large"
      clearable
      @keyup.enter="onSearch"
    >
      <template #prefix>
        <AppIcon name="Search" :size="18" class="text-slate-400" />
      </template>
    </el-input>

    <div class="mt-8 text-center">
      <AppIcon name="Inbox" :size="48" class="text-slate-300 mb-3" />
      <p class="text-slate-500">输入关键词开始搜索</p>
      <p class="text-sm text-slate-400 mt-1">支持全文搜索，按学院、课程、学期筛选</p>
    </div>
  </div>
</template>

<script setup lang="ts">
definePageMeta({ title: '搜索' });

const query = ref('');

function onSearch() {
  if (query.value.trim()) {
    navigateTo(`/search?q=${encodeURIComponent(query.value)}`);
  }
}
</script>
