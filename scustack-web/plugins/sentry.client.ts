export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig()
  const dsn = config.public.sentryDsn as string | undefined

  if (!dsn) {
    if (import.meta.dev) {
      console.info('[sentry] DSN not configured — client-side errors will be logged to console')
    }
    return
  }

  import('@sentry/vue').then((Sentry) => {
    Sentry.init({
      app: nuxtApp.vueApp,
      dsn,
      environment: config.public.appEnv || 'dev',
      tracesSampleRate: 0.1,
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1.0,
      integrations: [
        Sentry.browserTracingIntegration({ router: nuxtApp.$router as any }),
        Sentry.replayIntegration(),
      ],
    })

    nuxtApp.vueApp.config.errorHandler = (err, instance, info) => {
      Sentry.captureException(err, { extra: { info, component: instance?.$options?.name } })
      console.error('[sentry]', err)
    }

    if (import.meta.dev) {
      console.info('[sentry] Initialized for environment:', config.public.appEnv)
    }
  }).catch(() => {
    console.warn('[sentry] @sentry/vue not installed — client-side errors will be logged to console')
  })
})
