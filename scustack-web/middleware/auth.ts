export default defineNuxtRouteMiddleware(async () => {
  const auth = useAuthStore()
  if (!auth.isLoggedIn) {
    await auth.fetchUser()
  }
  if (!auth.isLoggedIn) {
    auth.openLogin()
    return navigateTo('/')
  }
})
