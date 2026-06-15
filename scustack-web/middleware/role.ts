export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()
  const requiredRole = to.meta.requiredRole as string | undefined
  if (requiredRole) {
    const roles = ['student', 'contributor', 'maintainer', 'admin']
    const userIdx = roles.indexOf(auth.user?.role || 'student')
    const requiredIdx = roles.indexOf(requiredRole)
    if (userIdx < requiredIdx) {
      throw createError({ statusCode: 403, message: '需要更高权限才能访问此页面' })
    }
  }
})
