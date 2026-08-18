export default defineNuxtConfig({
  compatibilityDate: '2026-06-15',

  devtools: { enabled: false },

  experimental: {
    appManifest: false,
  },

  modules: ['@nuxtjs/tailwindcss', '@pinia/nuxt'],

  app: {
    head: {
      htmlAttrs: { lang: 'zh-CN' },
    },
    pageTransition: { name: 'page' },
    layoutTransition: { name: 'layout' },
  },

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
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8403',
      officePreviewBase: process.env.NUXT_PUBLIC_OFFICE_PREVIEW_BASE || '',
      sentryDsn: process.env.NUXT_PUBLIC_SENTRY_DSN || '',
      appEnv: process.env.NUXT_PUBLIC_APP_ENV || 'dev',
    },
  },

  typescript: {
    strict: true,
    typeCheck: true,
  },

  vite: {
    build: {
      chunkSizeWarningLimit: 1000,
      rollupOptions: {
        output: {
          manualChunks(id) {
            const normalized = id.replaceAll('\\', '/')
            if (normalized.includes('node_modules/element-plus') || normalized.includes('node_modules/@element-plus')) return 'vendor-element-plus'
            if (normalized.includes('node_modules/pdfjs-dist')) return 'vendor-pdf'
            if (normalized.includes('node_modules/shiki')) return 'vendor-shiki'
          },
        },
      },
    },
  },
});
