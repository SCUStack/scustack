<template>
  <NuxtLayout>
    <NuxtPage keepalive />
  </NuxtLayout>
</template>

<script setup lang="ts">
useHead({
  titleTemplate: '川流课栈 >( ⁰▿⁰)< 好好学习天天向上 ~ SCUStack',
  meta: [
    { charset: 'utf-8' },
    { name: 'viewport', content: 'width=device-width, initial-scale=1, viewport-fit=cover' },
    { name: 'description', content: '四川大学课程资料共享平台' },
  ],
  link: [
    { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
    { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
    {
      rel: 'stylesheet',
      href: 'https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;600;700&display=swap',
    },
  ],
});
</script>
