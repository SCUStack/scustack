export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()
  const requiredRole = to.meta.requiredRole as string | undefined
  if (requiredRole) {
    const roles = ['student', 'contributor', 'maintainer', 'admin']
    const userIdx = roles.indexOf(auth.user?.role || 'student')
    const requiredIdx = roles.indexOf(requiredRole)
    if (userIdx < requiredIdx) {
      return navigateTo('/')
    }
  }
})
