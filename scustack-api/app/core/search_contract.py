SEARCH_SORT_OPTIONS = [
    {'key': 'relevance', 'label': '相关度'},
    {'key': 'newest', 'label': '最新'},
    {'key': 'downloads', 'label': '最多下载'},
    {'key': 'rating', 'label': '最高评分'},
]

SEARCH_FILTER_GROUPS_META = [
    {'key': 'category', 'label': '资料分类'},
    {'key': 'semester', 'label': '学期'},
    {'key': 'trust_status', 'label': '信任状态'},
    {'key': 'source_type', 'label': '来源'},
]

SEARCH_FILTER_OPTIONS = {
    'category': [
        {'value': '课堂笔记', 'label': '课堂笔记'},
        {'value': '考试资料', 'label': '考试资料'},
        {'value': '复习提纲', 'label': '复习提纲'},
        {'value': '教材', 'label': '教材'},
        {'value': '习题集', 'label': '习题集'},
        {'value': '实验报告', 'label': '实验报告'},
        {'value': '历年真题', 'label': '历年真题'},
        {'value': '课件讲义', 'label': '课件讲义'},
        {'value': '考研专区', 'label': '考研专区'},
    ],
    'source_type': [
        {'value': 'hosted', 'label': '托管文件'},
        {'value': 'external', 'label': '外部链接'},
    ],
    'trust_status': [
        {'value': 'maintainer_picked', 'label': '维护者精选'},
        {'value': 'community_verified', 'label': '社区验证'},
        {'value': 'unverified', 'label': '未验证'},
        {'value': 'doubtful', 'label': '存疑'},
    ],
}
