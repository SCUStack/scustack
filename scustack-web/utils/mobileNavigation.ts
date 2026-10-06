const MOBILE_PAGE_TITLES: Array<[string, string]> = [
  ['/search', '资料搜索'],
  ['/course', '课程详情'],
  ['/material', '资料详情'],
  ['/upload', '贡献资料'],
  ['/user', '个人中心'],
  ['/colleges', '学院列表'],
]

export function getMobilePageTitle(path: string, routeTitle?: unknown): string {
  if (typeof routeTitle === 'string' && routeTitle.trim()) return routeTitle
  return MOBILE_PAGE_TITLES.find(([prefix]) => path.startsWith(prefix))?.[1] || '川流课栈'
}
