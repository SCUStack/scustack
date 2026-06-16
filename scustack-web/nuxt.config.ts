export default defineNuxtConfig({
  compatibilityDate: '2026-06-15',

  devtools: { enabled: true },

  modules: ['@nuxtjs/tailwindcss', '@pinia/nuxt'],

  // Disable directory prefix so components/auth/LoginModal.vue → <LoginModal>
  components: {
    dirs: [{ path: '~/components', pathPrefix: false }],
  },

  css: ['element-plus/dist/index.css', '~/assets/css/main.css'],

  tailwindcss: {
    configPath: './tailwind.config.ts',
  },

  routeRules: {
    '/': { swr: 300 },
    '/search': { ssr: true },
    '/course': { ssr: true },
    '/course/**': { ssr: true },
    '/material/**': { ssr: true },
    '/upload/**': { ssr: false },
    '/user/**': { ssr: false },
    '/about': { swr: 300 },
    '/admin/**': { ssr: false },
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
    },
  },

  typescript: {
    strict: true,
    typeCheck: true,
  },
});
