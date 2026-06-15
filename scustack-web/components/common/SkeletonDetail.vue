<template>
  <div class="animate-pulse max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
    <div class="lg:flex lg:gap-8">
      <div class="flex-1 space-y-4">
        <div class="bg-slate-200 rounded h-8 w-2/3" />
        <div class="flex gap-3">
          <div class="bg-slate-200 rounded h-4 w-20" />
          <div class="bg-slate-200 rounded h-4 w-16" />
          <div class="bg-slate-200 rounded h-4 w-12" />
        </div>
        <div class="space-y-2">
          <div class="bg-slate-200 rounded h-3 w-full" />
          <div class="bg-slate-200 rounded h-3 w-5/6" />
          <div class="bg-slate-200 rounded h-3 w-4/6" />
        </div>
        <div class="bg-slate-200 rounded h-64 w-full" />
        <div class="space-y-3 border border-slate-200 rounded-lg p-4">
          <div class="bg-slate-200 rounded h-4 w-24" />
          <div v-for="n in 3" :key="n" class="flex items-center gap-4 py-1">
            <div class="bg-slate-200 rounded-full w-3 h-3" />
            <div class="flex-1 bg-slate-200 rounded h-3 w-1/3" />
            <div class="bg-slate-200 rounded h-3 w-16" />
          </div>
        </div>
      </div>
      <div class="lg:w-72 shrink-0 mt-6 lg:mt-0 space-y-3">
        <div class="bg-slate-200 rounded-lg h-40" />
        <div class="bg-slate-200 rounded-lg h-32" />
      </div>
    </div>
  </div>
</template>
