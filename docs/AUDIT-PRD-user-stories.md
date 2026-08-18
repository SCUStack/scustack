# PRD 用户故事代码审计

| 字段 | 内容 |
|---|---|
| Type | `audit` |
| Status | `completed` |
| Source PRD | `docs/PRD-产品需求文档.md` |
| Audit Date | `2026-07-06` |
| Scope Rule | 每轮最多对照 5 个用户故事 |

## 审计方法

本审计逐条对照 PRD「用户故事」与当前代码实现，按以下证据判断完成度：

- **产品闭环**：用户能否在前端自然完成该故事，不只看后端是否有接口。
- **后端能力**：API、服务、模型、索引是否支撑对应查询或展示。
- **前端呈现**：页面、组件、状态管理是否暴露对应能力。
- **测试证据**：单元测试、契约测试或 E2E 是否验证关键行为，而不是仅验证页面可加载。

状态定义：

- **通过**：前后端闭环实现，且有直接测试覆盖。
- **部分通过**：核心能力存在，但产品闭环、语义完整性或测试覆盖存在缺口。
- **未通过**：当前实现无法满足该用户故事。

## 第 1 轮：用户故事 1-5

### 总览

| 编号 | 用户故事摘要 | 审计状态 | 主要结论 |
|---|---|---|---|
| US-01 | 通过课程名称搜索课程资料 | 部分通过 | 后端搜索覆盖课程名称，搜索页可输入关键词；但测试主要 mock 服务，缺少真实 ES/降级查询与前端结果断言。 |
| US-02 | 按学院、课程、学期、分类浏览资料 | 部分通过 | 后端和部分页面支持这些维度，但搜索页没有学院/课程筛选入口，课程列表也缺少学院/分类浏览控件。 |
| US-03 | 按学期筛选资料 | 部分通过 | 搜索/课程页均有学期筛选能力；但前端多选与后端单值参数语义不一致，且 E2E 未验证结果正确性。 |
| US-04 | 展示适配教师或教学场景 | 部分通过 | 模型有 `teacher` 字段，详情修正表单也提到教师；但主详情页/卡片不展示教师，且没有教学场景字段。 |
| US-05 | 展示资料分类 | 部分通过 | 卡片、详情页、课程页均展示分类；测试覆盖偏契约和后端，缺少 UI 行为断言。 |

### US-01：通过课程名称搜索课程资料

PRD：作为一名四川大学学生，我希望能通过课程名称搜索课程资料，以便快速找到我所修课程的相关资源。

**证据**

- 搜索 API 接收关键词 `q`，并转交搜索服务：`scustack-api/app/api/v1/search.py:20`。
- 搜索服务将 `q` 传给 Elasticsearch；开发环境降级查询包含 `Course.name.ilike(...)`，可通过课程名命中资料：`scustack-api/app/services/search_service.py:111`、`scustack-api/app/services/search_service.py:187`。
- 前端搜索页从 URL 同步 `q` 并调用 `/api/v1/search`：`scustack-web/pages/search.vue:98`、`scustack-web/composables/useSearch.ts:102`。
- 后端测试包含关键词搜索用例：`scustack-api/tests/test_search.py:26`。

**缺口**

- `test_search_with_keyword` mock 了 `app.api.v1.search.search`，只证明路由能返回 mock 数据，不能证明课程名进入 ES 查询或降级 SQL 后能正确匹配。
- E2E `search functionality works` 只断言页面可见，没有断言搜索结果包含所属课程或相关资料：`scustack-web/e2e/path1-browse-search.spec.ts:29`。

**结论**

部分通过。用户入口和后端能力存在，但缺少真实查询路径与前端结果语义的回归测试。

### US-02：按学院、课程、学期、分类浏览资料

PRD：作为一名四川大学学生，我希望能按学院、课程、学期、分类浏览资料，以便在不知道确切文件名的情况下也能定位到资源。

**证据**

- 后端搜索接口支持 `college_id`、`course_id`、`category`、`semester`：`scustack-api/app/api/v1/search.py:22`-`scustack-api/app/api/v1/search.py:25`。
- 资料列表接口支持 `course_id`、`category`、`semester`：`scustack-api/app/api/v1/materials.py:30`。
- 学院详情页通过 `/api/v1/courses?college_id=` 展示学院下课程：`scustack-web/pages/colleges/[id].vue:65`。
- 课程详情页提供课程内搜索、分类、学期筛选：`scustack-web/pages/course/[id].vue:45`、`scustack-web/pages/course/[id].vue:49`、`scustack-web/pages/course/[id].vue:195`。
- 后端课程列表测试覆盖 `college_id` 过滤：`scustack-api/tests/test_courses.py:27`。

**缺口**

- 搜索页筛选配置只渲染 `category`、`semester`、`trust_status`、`source_type`，没有学院或课程筛选组；虽然 `useSearch` 状态里有 `college_id`，但没有用户可见入口：`scustack-web/pages/search.vue:26`、`scustack-web/composables/useSearch.ts:30`。
- 全部课程页只分页展示课程，缺少按学院或课程分类浏览控件：`scustack-web/pages/course/index.vue:151`。
- 学院详情页是「学院 -> 课程」路径，不是直接按学院浏览资料；用户还需进入单个课程才能看到资料。

**结论**

部分通过。系统具备部分导航路径，但 PRD 要求的四维浏览没有形成统一、可发现、可组合的产品闭环。

### US-03：按学期筛选资料

PRD：作为一名四川大学学生，我希望能按学期筛选资料，以便避免使用过时的资源。

**证据**

- 搜索接口和搜索服务都支持 `semester` 参数：`scustack-api/app/api/v1/search.py:25`、`scustack-api/app/services/search_service.py:75`。
- 搜索筛选配置从已审核资料中动态读取学期选项：`scustack-api/app/services/search_service.py:59`。
- 课程详情页提供「全部学期」下拉筛选：`scustack-web/pages/course/[id].vue:49`。
- 后端测试覆盖动态学期筛选配置：`scustack-api/tests/test_search.py:226`。

**缺口**

- 搜索页的 `FilterGroup` 是多选组件，`useSearch` 会对同一 key 多次 `params.append(...)`；但后端 `semester` 是单值 `str | None`，多选请求的真实语义不明确：`scustack-web/components/common/FilterGroup.vue:29`、`scustack-web/composables/useSearch.ts:100`、`scustack-api/app/api/v1/search.py:25`。
- 目前没有前端测试或 E2E 断言选择某一学期后，列表只出现该学期资料。

**结论**

部分通过。单学期筛选能力存在，但多选 UI 与单值 API 不一致，存在用户看到的筛选状态和实际查询语义不一致的风险。

### US-04：展示适配教师或教学场景

PRD：作为一名四川大学学生，我希望在资料信息可查时，能看到其适配的教师或教学场景，以便判断是否与我所上的课程匹配。

**证据**

- 资料表有 `teacher` 字段：`scustack-api/app/models/material.py:28`，迁移也创建了该列：`scustack-api/alembic/versions/004_create_materials.py:32`。
- 资料创建/更新 schema 支持 `teacher`：`scustack-api/app/schemas/material.py:10`、`scustack-api/app/schemas/material.py:20`。
- 前端类型包含 `teacher?: string`：`scustack-web/types/api.ts:76`。
- 资料详情页的修正字段包含「教师」：`scustack-web/pages/material/[id].vue:50`。

**缺口**

- `MaterialCard` 不展示教师：当前只展示分类、来源、信任状态、格式、评分、下载数和时间：`scustack-web/components/material/MaterialCard.vue:25`、`scustack-web/components/material/MaterialCard.vue:85`。
- `MaterialDetail` 顶部元信息展示课程、学期、分类、格式、来源，但没有展示 `material.teacher`：`scustack-web/components/material/MaterialDetail.vue:12`-`scustack-web/components/material/MaterialDetail.vue:21`。
- 代码中未发现独立的「教学场景」字段或模型语义；只有 `teacher`，无法表达实验班、荣誉课程、考研复习、通识课场景等 PRD 提到的判断依据。

**结论**

部分通过偏低。数据层支持教师，但用户主要查看界面没有展示；教学场景没有结构化建模。

### US-05：展示资料分类

PRD：作为一名四川大学学生，我希望能看到资料分类（如课堂笔记、考试资料、作业、实验报告、代码、教材、复习提纲等），以便找到我需要的资料类型。

**证据**

- 资料模型和 schema 都要求 `category`：`scustack-api/app/models/material.py:26`、`scustack-api/app/schemas/material.py:9`。
- 搜索筛选配置包含资料分类：`scustack-api/app/services/search_service.py:17`、`scustack-api/app/services/search_service.py:23`。
- 资料卡片顶部展示 `item.category`：`scustack-web/components/material/MaterialCard.vue:25`。
- 资料详情页展示 `material.category`：`scustack-web/components/material/MaterialDetail.vue:18`。
- 课程详情页支持按分类筛选：`scustack-web/pages/course/[id].vue:45`。
- 前后端契约测试覆盖分类枚举一致性：`scustack-web/tests/backendContractConsistency.test.ts:30`。

**缺口**

- PRD 举例包含「作业、代码」，当前业务枚举没有这两类，实际枚举为课堂笔记、考试资料、复习提纲、教材、习题集、实验报告、历年真题、课件讲义、考研专区：`scustack-web/data/business.ts:1`。
- UI 测试没有断言卡片/详情页一定渲染分类，也没有覆盖分类筛选后的结果正确性。

**结论**

部分通过。核心分类展示已实现，但分类体系与 PRD 示例存在偏差，测试没有覆盖用户可见展示。

## 第 2 轮：用户故事 6-10

### 总览

| 编号 | 用户故事摘要 | 审计状态 | 主要结论 |
|---|---|---|---|
| US-06 | 在线预览常见文档类型 | 部分通过 | 预览组件覆盖 PDF、Office、代码、Markdown、图片、文本；但预览 URL 复用登录下载接口，Office 固定依赖 localhost OnlyOffice，缺少预览专项测试。 |
| US-07 | 直接下载平台托管资料 | 部分通过 | 托管资料下载链路存在并有防刷和测试；但下载要求登录，是否符合“直接下载”需产品确认，且预览也被该登录门槛影响。 |
| US-08 | 外部链接与托管文件同课程页展示 | 通过偏弱 | 课程页统一调用资料列表，卡片标识外链，详情页区分托管预览与外链打开；测试缺少同页混合展示断言。 |
| US-09 | 看到评分与反馈 | 部分通过 | 评分、评分分布和评论区已实现；但卡片只展示评分不展示评论/反馈摘要，前端评分测试未验证登录成功后的 POST 行为。 |
| US-10 | 举报错误、过时、重复或不合规资料 | 通过偏弱 | 举报弹窗、后端提交、管理员处理队列均存在且有测试；但缺少前端举报流程测试和反滥用限制。 |

### US-06：在线预览常见文档类型

PRD：作为一名四川大学学生，我希望能在线预览常见文档类型，以便在下载前判断资料是否有用。

**证据**

- 资料详情页对托管文件显示「在线预览」并挂载 `FilePreview`：`scustack-web/components/material/MaterialDetail.vue:30`-`scustack-web/components/material/MaterialDetail.vue:32`。
- `FilePreview` 按格式分发到 PDF、Office、代码、Markdown、图片、文本预览，并对不支持或大 PDF 提供下载兜底：`scustack-web/components/preview/FilePreview.vue:12`、`scustack-web/components/preview/FilePreview.vue:15`、`scustack-web/components/preview/FilePreview.vue:34`、`scustack-web/components/preview/FilePreview.vue:65`。
- PDF 预览使用 `pdfjs-dist` 渲染 canvas，并带下载入口：`scustack-web/components/preview/PdfPreview.vue:21`、`scustack-web/components/preview/PdfPreview.vue:55`。
- 代码和文本预览支持全屏、复制、截断展示等基础体验：`scustack-web/components/preview/CodePreview.vue:13`、`scustack-web/components/preview/TextPreview.vue:13`。

**缺口**

- `useMaterial` 将 `previewUrl` 和 `downloadUrl` 都指向 `/api/v1/materials/{id}/download`：`scustack-web/composables/useMaterial.ts:31`-`scustack-web/composables/useMaterial.ts:32`。该接口要求 `get_current_user`，未登录用户无法预览，且 PDF/文本 fetch 会走 302 到 OSS，存在鉴权、跨域与跳转兼容风险。
- Office 预览固定依赖 `http://localhost:8088` 的 OnlyOffice 地址：`scustack-web/components/preview/OfficePreview.vue:35`。生产环境或非本机环境未配置时，Office 预览不可用。
- 未发现 `FilePreview`、`PdfPreview`、`OfficePreview` 的组件测试或 E2E 预览断言；现有 Path 1 只覆盖资料不存在页面和搜索页面可见。

**结论**

部分通过。预览组件体系较完整，但预览资源获取和 Office 服务配置不稳定，缺少真实预览路径测试。

### US-07：直接下载平台托管资料

PRD：作为一名四川大学学生，我希望能直接下载平台托管的资料，以便不再依赖不稳定的群文件或易失效的网盘链接。

**证据**

- 详情页对 `hosted` 资料显示下载按钮，并包含文件大小：`scustack-web/components/material/MaterialDetail.vue:78`。
- 下载 URL 指向 `/api/v1/materials/{id}/download`：`scustack-web/composables/useMaterial.ts:31`。
- 后端下载接口只允许托管文件，读取最新版本，生成 OSS 签名下载 URL，并记录下载计数：`scustack-api/app/api/v1/materials.py:167`、`scustack-api/app/api/v1/materials.py:223`、`scustack-api/app/api/v1/materials.py:230`。
- 下载接口有用户级和身份级限流保护，Redis 失效时拒绝高价值下载路径：`scustack-api/app/api/v1/materials.py:172`、`scustack-api/app/api/v1/materials.py:199`。
- 后端测试覆盖未登录下载、找不到文件、成功 302、Redis 保护不可用时拒绝：`scustack-api/tests/test_materials.py:269`、`scustack-api/tests/test_materials.py:273`、`scustack-api/tests/test_materials.py:308`。

**缺口**

- 下载接口依赖 `get_current_user`，未登录访问返回 401：`scustack-api/tests/test_materials.py:269`。若 PRD 的“直接下载”包含免登录访问，当前实现不满足；若仅面向登录学生，需要在 PRD 或权限规则中明确。
- 下载链接是普通 `<a>`，没有前端错误态处理；429/503/404 会直接跳转到 JSON 响应或错误页，体验不够闭环。

**结论**

部分通过。登录用户下载托管文件的核心链路和后端测试充分；“直接下载”的访问门槛和错误体验仍需收口。

### US-08：外部链接与托管文件展示在同一个课程页面

PRD：作为一名四川大学学生，我希望外部链接与托管文件能展示在同一个课程页面中，以便通过一个入口获取全部课程资源。

**证据**

- 课程详情页通过 `/api/v1/materials?course_id=...` 拉取课程资料，未按来源拆分列表：`scustack-web/pages/course/[id].vue:195`。
- 资料列表接口支持 `source_type` 但默认不传时返回同一课程下全部已审核资料：`scustack-api/app/api/v1/materials.py:32`、`scustack-api/app/services/material_service.py:23`。
- 资料卡片对外部链接显示「外链」标识：`scustack-web/components/material/MaterialCard.vue:32`。
- 资料详情页对托管文件显示在线预览，对外部链接显示外链入口并弹出离站确认：`scustack-web/components/material/MaterialDetail.vue:30`、`scustack-web/components/material/MaterialDetail.vue:21`、`scustack-web/pages/material/[id].vue:79`。
- 外部 URL 上传校验覆盖协议、黑名单域名、日限制和合法 URL：`scustack-api/tests/test_external_links.py:54`。

**缺口**

- 没有测试明确构造同一课程下一个 `hosted` 和一个 `external` 资料，并断言课程页同时展示二者。
- `MaterialCard` 只标识外链，不标识托管文件；用户能区分外链，但无法同等清晰地识别托管文件来源。

**结论**

通过偏弱。产品路径基本闭环，但缺少混合来源展示的回归测试和托管来源显式标识。

### US-09：看到资料评分与反馈

PRD：作为一名四川大学学生，我希望能看到资料的评分与反馈，以便优先选择高质量资源。

**证据**

- 资料卡片展示评分和下载数：`scustack-web/components/material/MaterialCard.vue:75`。
- 详情页侧栏挂载 `RatingWidget`，并传入平均分、评分数和评分分布：`scustack-web/components/material/MaterialDetail.vue:101`。
- `RatingWidget` 支持星级评分、评分分布浮层和登录校验：`scustack-web/components/material/RatingWidget.vue:3`、`scustack-web/components/material/RatingWidget.vue:17`、`scustack-web/components/material/RatingWidget.vue:58`。
- 后端评分接口写入或更新评分，并重算平均分和数量：`scustack-api/app/api/v1/materials.py:240`、`scustack-api/app/services/material_service.py:198`、`scustack-api/app/services/material_service.py:229`。
- 详情页包含评论区，评论接口支持列表、发布、回复和删除：`scustack-web/pages/material/[id].vue:23`、`scustack-api/app/api/v1/comments.py:14`、`scustack-api/app/api/v1/comments.py:27`、`scustack-api/app/services/comment_service.py:21`。
- 后端服务在详情数据中计算评分分布：`scustack-api/app/services/material_service.py:103`。

**缺口**

- 卡片只展示评分，不展示评论数或反馈摘要；用户在列表页无法直接看到“反馈”的质量信号。
- `RatingWidget` 的本地 `localRating` 用 `Math.round` 存储，显示为整数小数，如 3.5 初始值显示 4.0，存在评分展示失真：`scustack-web/components/material/RatingWidget.vue:47`。
- 前端评分测试覆盖挂载、星按钮和未登录状态，但没有模拟登录成功后断言 POST `/ratings` 与 UI 更新；评论测试也只覆盖游客登录和失败 toast。

**结论**

部分通过。评分和评论能力存在，但反馈展示不够前置，评分显示存在取整失真，测试没有覆盖成功交互。

### US-10：举报错误、过时、重复或不合规资料

PRD：作为一名四川大学学生，我希望能举报错误、过时、重复或不合规的资料，以便保障平台的可信度。

**证据**

- 详情页提供「举报」入口，未登录时打开登录弹窗：`scustack-web/components/material/MaterialDetail.vue:139`、`scustack-web/pages/material/[id].vue:250`。
- 举报弹窗包含版权问题、资料已过时、内容不当、重复资料、信息错误、其他：`scustack-web/pages/material/[id].vue:79`。
- 前端通过 `useMaterial.submitReport` 提交到 `/api/v1/materials/{id}/reports`：`scustack-web/composables/useMaterial.ts:162`。
- 后端 `ReportCreate` 对举报原因做枚举校验：`scustack-api/app/schemas/report.py:7`。
- 举报提交接口校验资料存在后创建举报记录：`scustack-api/app/api/v1/materials.py:320`、`scustack-api/app/services/report_service.py:11`。
- 管理后台支持举报列表和处理，接受举报时下架资料：`scustack-api/app/api/v1/admin.py:128`、`scustack-api/app/api/v1/admin.py:140`、`scustack-api/app/services/report_service.py:65`。
- 后端测试覆盖举报需登录、提交成功、非法原因、管理员处理和服务创建：`scustack-api/tests/test_admin.py:146`、`scustack-api/tests/test_admin.py:155`、`scustack-api/tests/test_admin.py:339`。

**缺口**

- 未发现前端举报弹窗和提交成功/失败的组件或 E2E 测试。
- 举报接口没有去重、频率限制或同一用户重复举报限制；恶意用户可反复创建举报记录，治理队列可能被噪声淹没。
- `handle_report` 接收 `comment` 但当前 `Report` 模型没有处理备注字段，处理意见只进入 audit log，不进入举报记录本身。

**结论**

通过偏弱。举报闭环从学生提交到维护者处理已存在，后端测试较充分；缺少前端流程测试和反滥用治理。

## 第 3 轮：用户故事 11-15

### 总览

| 编号 | 用户故事摘要 | 审计状态 | 主要结论 |
|---|---|---|---|
| US-11 | 看到资料是否被用户或维护者验证 | 部分通过 | 信任状态字段、徽章和维护者设置接口完整；但“其他用户验证”的来源不清晰，移动徽章隐藏文字削弱三重编码。 |
| US-12 | 关注或收藏课程并在新资料更新时收到通知 | 部分通过 | 关注课程、收藏资料、通知创建和通知铃铛均存在；但缺少独立通知中心页面，通知触发时机和“新提交/审核通过”语义需明确。 |
| US-13 | 首页推荐与当前校历节点相关资料 | 部分通过 | 首页有“为你推荐”和校历标签，后端推荐按月份映射考试/复习/选课分类；但没有使用真实 `academic_calendar` 事件。 |
| US-14 | 移动端无需安装软件也能正常使用 | 部分通过 | 有移动导航、首页、搜索、课程、学院、详情 Sheet；但移动端部分功能弱于桌面，缺少移动 viewport E2E。 |
| US-15 | 对标题、描述、标签、文档正文全文搜索 | 部分通过 | ES 支持标题/描述/正文/课程名/别名搜索和正文抽取；但未发现标签字段，降级搜索不覆盖正文，真实 ES 集成测试不足。 |

### US-11：看到资料是否经过其他用户或维护者验证

PRD：作为一名四川大学学生，我希望能看到资料是否经过其他用户或维护者验证，以便判断对资料的信任程度。

**证据**

- 资料模型持久化 `trust_status`，默认 `unverified`：`scustack-api/app/models/material.py:34`。
- 业务枚举包含维护者精选、社区验证、未验证、存疑，且定义图标和颜色：`scustack-web/data/business.ts:15`。
- `TrustBadge` 通过图标、颜色、文字展示信任状态：`scustack-web/components/common/TrustBadge.vue:2`。
- 资料卡片、详情页、移动详情 Sheet 均展示信任徽章：`scustack-web/components/material/MaterialCard.vue:45`、`scustack-web/components/material/MaterialDetail.vue:8`、`scustack-web/components/mobile/MaterialDetailSheet.vue:36`。
- 管理后台可设置资料信任状态，并写入审核日志：`scustack-api/app/api/v1/admin.py:105`、`scustack-api/app/services/review_service.py:111`。
- 内容预筛可将可疑内容标记为 `doubtful`：`scustack-api/app/tasks/material_tasks.py:39`。

**缺口**

- PRD 提到“其他用户或维护者验证”。当前 `community_verified` 只是状态值和维护者可设置的枚举，未发现由普通用户投票、多人确认或社区验证规则自动产生的机制。
- `TrustBadge` 的文字在小屏隐藏：`<span class="hidden sm:inline">`，移动端主要只剩颜色和图标，不完全满足设计规范中的“颜色 + 图标 + 文本三重编码”。
- 前端没有针对 `TrustBadge` 四种状态渲染的组件测试。

**结论**

部分通过。用户能看到信任状态，但“社区验证”的治理来源不完整，移动端可读性和测试覆盖不足。

### US-12：关注或收藏课程并收到新资料通知

PRD：作为一名四川大学学生，我希望能关注或收藏课程，以便有新资料更新时收到通知。

**证据**

- 课程详情页和移动课程页均有「关注课程」按钮：`scustack-web/pages/course/[id].vue:19`、`scustack-web/components/mobile/MobileCourseView.vue:18`。
- 关注课程复用 bookmark 接口，支持 `course_id` 与 `material_id`：`scustack-api/app/api/v1/bookmarks.py:16`、`scustack-api/app/models/bookmark.py:14`。
- 用户中心提供「收藏与关注」页面，可查看关注课程和收藏资料：`scustack-web/pages/user/bookmarks.vue:3`、`scustack-web/pages/user/bookmarks.vue:26`。
- 后端在资料创建和审核通过时调用 `notify_course_followers`：`scustack-api/app/api/v1/materials.py:114`、`scustack-api/app/api/v1/admin.py:88`。
- `notify_course_followers` 查找关注该课程的用户并创建 `course_update` 通知：`scustack-api/app/services/user_service.py:164`。
- 通知 API 支持列表、未读数、单条已读和全部已读：`scustack-api/app/api/v1/users.py:60`。
- 默认布局桌面和移动端都有通知铃铛、未读红点和通知下拉：`scustack-web/layouts/default.vue:46`、`scustack-web/layouts/default.vue:158`、`scustack-web/layouts/default.vue:322`。

**缺口**

- `create_material` 提交后即调用 `notify_course_followers`，但托管资料会进入 `pending`；随后审核通过又通知一次，可能产生“未公开资料通知”或重复通知：`scustack-api/app/api/v1/materials.py:103`、`scustack-api/app/api/v1/materials.py:114`。
- 没有独立通知中心页面，通知主要在导航下拉中展示，历史查看和批量管理能力较弱。
- 后端通知测试主要 mock API，未验证“关注课程 -> 审核通过新资料 -> 关注者收到通知”的真实服务链路。

**结论**

部分通过。关注、收藏和站内通知能力已具备，但通知触发语义有重复/提前风险，通知产品闭环仍偏轻。

### US-13：首页推荐与当前校历节点相关资料

PRD：作为一名四川大学学生，我希望首页能推荐与当前校历节点相关的资料，以便在考试、项目截止或选课阶段提前发现有用的资源。

**证据**

- 首页接口返回 `calendar_label` 和 `calendar_recommendations`：`scustack-api/app/api/v1/homepage.py:39`、`scustack-api/app/api/v1/homepage.py:48`。
- 首页桌面端展示带日历图标的「为你推荐」区域：`scustack-web/pages/index.vue:57`。
- 推荐算法将月份映射到考试资料、复习提纲、教材、课堂笔记等目标分类：`scustack-api/app/services/homepage_service.py:74`。
- 推荐服务综合质量、热度、新鲜度、校历分类匹配、信任状态和曝光衰减：`scustack-api/app/services/homepage_service.py:81`、`scustack-api/app/services/homepage_service.py:114`。
- 登录用户可基于关注课程/偏好分类获得个性化推荐：`scustack-api/app/services/homepage_service.py:367`。
- 后端测试覆盖推荐算法、分类多样性、冷启动、个性化、缓存和内容抽取相关路径：`scustack-api/tests/test_homepage.py:1`。

**缺口**

- 项目有 `academic_calendar` 模型和管理接口，但首页推荐没有读取真实校历事件表，而是按当前月份硬编码映射：`scustack-api/app/models/calendar.py:10`、`scustack-api/app/services/homepage_service.py:74`。
- PRD 提到考试、项目截止、选课阶段；当前映射没有项目截止或具体校历事件标签参与。
- 移动首页 `MobileHomeView` 的 recommend tab 实际先拉 `/homepage/recent-updates`，没有使用 `/homepage` 的 `calendar_recommendations`：`scustack-web/components/mobile/MobileHomeView.vue:130`。

**结论**

部分通过。桌面首页具备“校历感知推荐”的表象和算法基础，但推荐依据是月份分类映射，不是真实校历节点；移动端推荐与桌面语义不一致。

### US-14：移动端无需安装专门软件也能正常使用

PRD：作为一名四川大学学生，我希望移动端无需安装专门软件也能正常使用，以便在课堂、通勤或复习时随时访问资料。

**证据**

- 默认布局提供移动顶部栏、底部导航、安全区 padding 和移动通知下拉：`scustack-web/layouts/default.vue:132`、`scustack-web/layouts/default.vue:218`。
- 首页在小屏使用 `MobileHomeView`，搜索页使用 `MobileSearchView`，课程详情使用 `MobileCourseView`：`scustack-web/pages/index.vue:103`、`scustack-web/pages/search.vue:84`、`scustack-web/pages/course/[id].vue:114`。
- 移动端资料卡片展示分类、信任状态、评分、下载数和更新时间：`scustack-web/components/mobile/MaterialWaterfallCard.vue:29`。
- 移动资料详情 Sheet 支持下载、评分、收藏、分享、课程跳转和版本历史：`scustack-web/components/mobile/MaterialDetailSheet.vue:36`、`scustack-web/components/mobile/MaterialDetailSheet.vue:50`。
- 移动搜索页有搜索框、筛选 chips、筛选 Sheet、瀑布流和无限滚动：`scustack-web/components/mobile/MobileSearchView.vue:8`、`scustack-web/components/mobile/MobileSearchView.vue:47`、`scustack-web/components/mobile/MobileSearchView.vue:98`。

**缺口**

- 移动课程页只有课程内搜索，没有桌面课程页的分类、学期、排序筛选：`scustack-web/components/mobile/MobileCourseView.vue:29`。
- 移动详情 Sheet 没有在线预览、评论、举报、建议修正、外链离站确认等完整详情功能，需要跳转完整详情才能访问部分能力。
- E2E 没有设置移动 viewport 验证关键路径；现有 Path 1 只断言页面 body 可见。

**结论**

部分通过。移动端基础浏览、搜索、下载、收藏可用，但与桌面能力不完全等价，移动端真实用户路径缺少自动化验证。

### US-15：标题、描述、标签和文档正文全文搜索

PRD：作为一名四川大学学生，我希望能对标题、描述、标签以及可提取的文档正文进行全文搜索，以便仅通过部分关键词也能找到资料。

**证据**

- ES mapping 为 `title`、`description`、`content_text`、`course_name` 配置 IK 分词：`scustack-api/app/core/elasticsearch.py:15`、`scustack-api/app/core/elasticsearch.py:20`。
- 搜索使用 multi_match 覆盖 `title^3`、`description^2`、`content_text^2`、`course_name^2`、`course_aliases^2`：`scustack-api/app/core/elasticsearch.py:116`。
- 内容抽取任务支持文本和 PDF，限制大小、页数、字符数，并写入 `content_text`：`scustack-api/app/tasks/content_extract.py:33`、`scustack-api/app/tasks/content_extract.py:60`、`scustack-api/app/tasks/content_extract.py:106`。
- 审核通过托管资料后触发 `extract_material_content_to_es`：`scustack-api/app/api/v1/admin.py:79`。
- 搜索测试覆盖 ES 委派、中文 tokenizer 不报错；内容抽取测试覆盖文本抽取、大文件跳过和搜索字段包含 `content_text^2`：`scustack-api/tests/test_search.py:169`、`scustack-api/tests/test_content_extract.py:10`、`scustack-api/tests/test_content_extract.py:62`。

**缺口**

- 未发现资料 `tags` 字段、标签模型、上传表单标签输入或 ES `tags` mapping；PRD 中“标签”全文搜索未实现。
- 开发环境降级搜索只查标题、描述和课程名，不查正文或标签：`scustack-api/app/services/search_service.py:187`。
- 内容正文抽取只覆盖托管文件；外部链接没有正文抽取。Office 文档在预览上支持，但正文抽取只支持文本和 PDF。
- 测试没有启动真实 Elasticsearch/IK，无法证明中文分词、部分关键词和正文命中在集成环境中真实可用。

**结论**

部分通过。标题、描述、课程名和部分正文搜索具备后端设计；标签搜索缺失，正文抽取范围有限，真实 ES 搜索缺少集成验证。

## 第 4 轮：用户故事 16-20

| 用户故事 | 审计结论 | 主要判断 |
| --- | --- | --- |
| US-16 | 部分通过 | 桌面卡片展示分类、评分、格式、来源等字段，但缺少课程和学期；移动卡片字段更少。 |
| US-17 | 部分通过 | 支持相关度、最新、下载量、评分排序，但缺少学期排序，“最新”使用创建时间而非更新时间。 |
| US-18 | 部分通过 | 上传表单与后端支持课程、分类、学期、教师、描述、格式等结构化元数据，但缺少标签/教学场景，批量元数据较弱。 |
| US-19 | 通过偏弱 | 外部链接提交链路存在，并有 URL 安全校验和测试；但前端外链上传路径缺少专门测试，审核语义仍需更清晰。 |
| US-20 | 通过偏弱 | 新版本支持填写并展示更新说明；但说明为选填，端到端和前端测试不足。 |

### US-16：搜索结果展示所属课程、学期、分类、评分、格式与来源

PRD：作为一名四川大学学生，我希望搜索结果能展示所属课程、学期、分类、评分、格式与来源，以便快速对比不同结果。

**证据**

- 后端降级搜索结果包含 `course_name`、`college_name`、`category`、`semester`、`teacher`、`source_type`、`format`、`rating_avg`、`download_count`：`scustack-api/app/services/search_service.py:223`。
- ES mapping 也包含 `semester`、`category`、`format`、`source_type`、`rating_avg` 等可展示字段：`scustack-api/app/core/elasticsearch.py:65`。
- 桌面资料卡片展示分类、外链来源标识、信任状态、格式、评分、下载量和创建时间：`scustack-web/components/material/MaterialCard.vue:25`、`scustack-web/components/material/MaterialCard.vue:32`、`scustack-web/components/material/MaterialCard.vue:55`、`scustack-web/components/material/MaterialCard.vue:56`。
- 移动瀑布流卡片展示分类、信任状态、评分、下载量和时间：`scustack-web/components/mobile/MaterialWaterfallCard.vue:26`、`scustack-web/components/mobile/MaterialWaterfallCard.vue:37`。

**缺口**

- 桌面搜索结果卡片未展示 `course_name` 和 `semester`，用户无法直接按“所属课程、学期”对比结果。
- 移动搜索卡片未展示课程、学期、格式和外链来源标识，字段覆盖明显弱于 PRD。
- 当前测试更偏向接口与枚举一致性，没有验证搜索结果卡片必须渲染课程、学期、来源等字段。

**结论**

部分通过。后端数据基本准备好了，桌面 UI 覆盖了部分对比字段，但课程和学期这两个核心目录字段未进入搜索结果卡片，移动端缺口更明显。

### US-17：按相关度、更新时间、下载量、评分与学期排序

PRD：作为一名四川大学学生，我希望能按相关度、更新时间、下载量、评分与学期对资料排序，以便匹配不同的搜索需求。

**证据**

- 前端搜索排序选项为 `relevance`、`newest`、`downloads`、`rating`：`scustack-web/data/business.ts:33`。
- 后端搜索排序元数据同样只暴露相关度、最新、最多下载、最高评分：`scustack-api/app/services/search_service.py:9`。
- ES 排序支持 `newest`、`downloads`、`rating`，默认按 `_score` 和 `created_at`：`scustack-api/app/core/elasticsearch.py:189`。
- 前后端契约测试确认当前排序枚举一致：`scustack-web/tests/backendContractConsistency.test.ts` 本轮通过。

**缺口**

- PRD 要求“学期”排序，但前端枚举、后端元数据和 ES 排序实现均没有 `semester` 排序。
- PRD 要求“更新时间”，当前 `newest` 在 ES 中按 `created_at` 排序，并非 `updated_at`：`scustack-api/app/core/elasticsearch.py:190`。
- 资料列表服务 `_material_sort` 只支持下载量、评分和默认最新，同样没有学期排序，也没有明确的更新时间语义：`scustack-api/app/services/material_service.py:24`。

**结论**

部分通过。排序框架可用，且相关度/下载量/评分路径存在；但“更新时间”和“学期”两个 PRD 明确维度没有被准确实现。

### US-18：上传课程资料时填写结构化元数据

PRD：作为一名贡献者，我希望上传课程资料时可填写结构化元数据，以便其他用户能找到并理解这份资料。

**证据**

- 上传页包含标题、学院课程级联选择、分类、适用学期、授课教师、来源类型、外链/文件、描述和满足心愿入口：`scustack-web/pages/upload.vue:17`、`scustack-web/pages/upload.vue:23`、`scustack-web/pages/upload.vue:38`、`scustack-web/pages/upload.vue:48`、`scustack-web/pages/upload.vue:56`、`scustack-web/pages/upload.vue:63`。
- 前端创建托管资料时提交 `title`、`course_id`、`category`、`semester`、`teacher`、`source_type`、`description`、`storage_key`、`file_hash`、`file_size`、`format`：`scustack-web/pages/upload.vue:338`。
- 后端 `MaterialCreate` schema 对应支持标题、课程、分类、学期、教师、来源、外链、描述、文件哈希、大小、格式和分卷：`scustack-api/app/schemas/material.py:7`。
- 托管上传会先查重、拿上传凭证，再创建资料并排队审核/扫描：`scustack-web/pages/upload.vue:317`、`scustack-web/pages/upload.vue:327`、`scustack-api/app/api/v1/materials.py:100`。
- 本轮上传页和拖拽上传测试通过：`tests/UploadPage.test.ts`、`tests/DropZone.test.ts`。

**缺口**

- PRD 和前序用户故事提到标签、教学场景等检索/理解维度；上传表单、schema 和搜索 mapping 均未体现标签，教学场景也未建模。
- 批量上传只提供共享课程/学期/教师以及单文件标题/分类，不支持逐文件描述、标签或更细的元数据：`scustack-web/pages/upload.vue:220`。
- 上传页测试覆盖较轻，未断言结构化字段最终请求体完整、外链/托管分支差异、批量上传元数据继承规则。

**结论**

部分通过。核心目录元数据已经贯通前后端，但“让其他用户能找到并理解”的元数据面仍偏窄，批量上传的结构化能力也弱于单份上传。

### US-19：提交外部资源链接

PRD：作为一名贡献者，我希望能提交外部资源链接，以便当链接形式更合适时，无需重新上传已有优质资源。

**证据**

- 上传页提供来源类型单选，选择外部资源后显示外部链接输入框：`scustack-web/pages/upload.vue:63`、`scustack-web/pages/upload.vue:76`。
- 前端外链提交流程直接创建 `source_type: 'external'` 的资料，并传入 `external_url`：`scustack-web/pages/upload.vue:350`。
- 后端创建资料时对外链调用 `validate_external_url`，并对新用户外链进入审核：`scustack-api/app/api/v1/materials.py:86`。
- URL 校验限制协议为 http/https，阻止不可解析域名、黑名单域名，并做域名日提交上限：`scustack-api/app/services/upload_service.py:181`、`scustack-api/app/services/upload_service.py:194`。
- 外链资料详情页包含离站确认弹窗，继续访问使用 `noopener noreferrer nofollow`：`scustack-web/pages/material/[id].vue:118`。
- 本轮 `tests/test_external_links.py` 随后端测试组通过，覆盖危险协议、异常 URL、域名限额等路径。

**缺口**

- 外链上传前端没有专门测试覆盖“切换为外链 -> 填 URL -> 创建 external material”的完整请求。
- 外链资料的可用性/存活性没有异步健康检查；优质外链的“持续有效”仍依赖人工治理。
- 新用户外链会 pending，但非新用户外链可能直接进入后续流程，审核策略与“外部资源可信度”之间的产品规则需要更明确。

**结论**

通过偏弱。外链提交主链路、基础安全校验和离站提醒都已实现；质量风险主要在前端流程测试、链接健康和审核策略细化。

### US-20：替换或修订资料时添加更新说明

PRD：作为一名贡献者，我希望替换或修订资料时能添加更新说明，以便用户了解改动内容。

**证据**

- 资料详情页有上传新版本弹窗，包含“更新说明（选填）”文本框：`scustack-web/pages/material/[id].vue:134`、`scustack-web/pages/material/[id].vue:141`。
- `useMaterial.submitNewVersion` 上传文件后调用 `/materials/{id}/versions`，请求体包含 `change_note`：`scustack-web/composables/useMaterial.ts:216`、`scustack-web/composables/useMaterial.ts:233`。
- 后端 `VersionCreate` 支持 `change_note`：`scustack-api/app/schemas/material.py:106`。
- 服务层 `add_version` 将 `change_note` 写入 `MaterialVersion`，并重置资料信任状态：`scustack-api/app/services/material_service.py:167`。
- 版本时间线展示每个版本的 `change_note`：`scustack-web/components/material/VersionTimeline.vue:23`。
- 本轮 `tests/test_materials.py` 通过，包含版本列表和新增版本相关服务/API路径。

**缺口**

- 更新说明是选填，PRD 的“能添加”虽然满足，但无法保证替换/修订时用户一定说明改动。
- 前端没有针对新版本弹窗、`change_note` 请求体和版本时间线展示的组件/交互测试。
- API 测试对鉴权、上传凭证、版本创建、时间线展示之间的完整端到端链路覆盖不足。

**结论**

通过偏弱。功能链路已经存在，用户可以添加并在版本历史看到更新说明；质量短板在必填策略和自动化测试深度。

## 第 5 轮：用户故事 21-25

| 用户故事 | 审计结论 | 主要判断 |
| --- | --- | --- |
| US-21 | 部分通过 | 资料级贡献历史可追踪，但版本级贡献、公开贡献档案和审核反馈记录不完整。 |
| US-22 | 部分通过 | 上传表单能阻止明显缺失必填字段，但引导偏弱，后端字段校验不够严格。 |
| US-23 | 部分通过 | 课程、学期、教师、分类字段贯通上传和模型；但教师为可选且展示/检索闭环不足。 |
| US-24 | 部分通过 | 用户能提交元数据修正建议，但缺少维护者处理入口和自动应用闭环。 |
| US-25 | 通过偏弱 | 新内容默认进入审核/风控流程，审核队列可用；但审核反馈、自动风控和通知语义仍有缺口。 |

### US-21：贡献历史可追溯到贡献者

PRD：作为一名贡献者，我希望我的贡献历史能被记录，以便有价值的贡献可追溯到贡献者。

**证据**

- 资料模型有 `contributor_id` 字段，指向用户：`scustack-api/app/models/material.py:65`。
- 创建资料时服务层默认写入 `contributor_id`：`scustack-api/app/services/material_service.py:107`。
- 用户 API 提供 `/me/contributions`，返回当前用户贡献列表和总数：`scustack-api/app/api/v1/users.py:46`。
- 用户服务按 `Material.contributor_id == user_id` 查询贡献，并按创建时间倒序排列：`scustack-api/app/services/user_service.py:30`。
- 前端「我的贡献」页面展示标题、分类、学期、审核状态、创建时间和下载数：`scustack-web/pages/user/contributions.vue:7`、`scustack-web/pages/user/contributions.vue:28`。
- 前端上传成功后跳转到 `/user/contributions`：`scustack-web/pages/upload.vue:375`、`scustack-web/pages/upload.vue:464`。
- 本轮 `tests/test_users.py` 通过，覆盖贡献列表鉴权、空列表和列表返回路径。

**缺口**

- 贡献历史只按资料创建者追踪；版本表虽然有 `uploaded_by`，但「我的贡献」页面不展示版本级贡献或修订记录。
- 贡献列表缺少课程名、评分、信任状态等上下文，难以全面体现“有价值的贡献”。
- 公开侧贡献者档案和隐私设置之间的产品边界不清；目前主要是个人中心私有列表。
- 被驳回或要求修改的原因没有在贡献页展示，贡献者难以理解贡献状态变化。

**结论**

部分通过。资料级贡献可追溯，个人贡献列表可用；但版本级贡献、公开可追溯档案和审核反馈记录仍不完整。

### US-22：上传表单引导填写必填字段

PRD：作为一名贡献者，我希望上传表单能引导我填写必填字段，以免误提交无法使用或描述不清的资源。

**证据**

- 上传页在标题、分类、学期、来源类型、外部链接、上传文件等字段上用 `*` 或条件输入标出必填项：`scustack-web/pages/upload.vue:17`、`scustack-web/pages/upload.vue:38`、`scustack-web/pages/upload.vue:48`、`scustack-web/pages/upload.vue:77`。
- `canSubmit` 会阻止单份上传缺少标题、课程、分类、学期、文件/外链时提交；批量上传会要求课程、学期、文件、每个文件标题和分类：`scustack-web/pages/upload.vue:219`。
- 批量上传逐文件展示标题、分类、上传进度、错误和成功状态：`scustack-web/pages/upload.vue:99`、`scustack-web/pages/upload.vue:124`。
- 表单使用 `maxlength` 限制标题、教师、描述等输入长度：`scustack-web/pages/upload.vue:18`、`scustack-web/pages/upload.vue:57`、`scustack-web/pages/upload.vue:138`。
- 上传页测试覆盖重复文件错误反馈和成功后“资料已提交审核”的用户反馈：`scustack-web/tests/UploadPage.test.ts:68`、`scustack-web/tests/UploadPage.test.ts:90`。

**缺口**

- 前端必填引导主要依赖按钮禁用和星号，缺少逐字段错误提示、滚动定位或提交前汇总；用户不知道具体卡在哪里。
- `MaterialCreate` 对 `title` 只限制最大长度，对 `category`、`semester` 等必填字符串没有最小长度或枚举校验，空字符串可能穿透后端边界：`scustack-api/app/schemas/material.py:7`。
- 描述仍是选填；PRD 中“描述不清”的风险没有通过质量提示或最低信息量校验处理。
- 前端测试没有直接断言缺失每个必填字段时按钮禁用、错误提示或请求不发出。

**结论**

部分通过。基本的必填阻止和成功/错误反馈已具备，但表单引导偏轻，后端边界校验不够硬，难以充分避免描述不清或无效资源误提交。

### US-23：标注适用学期、教师、课程与分类

PRD：作为一名贡献者，我希望能标注资料的适用学期、教师、课程与分类，以便平台正确归类资料。

**证据**

- 上传页通过 `CollegeCourseSelect` 选择课程，并填写分类、学期、教师：`scustack-web/pages/upload.vue:23`、`scustack-web/pages/upload.vue:38`、`scustack-web/pages/upload.vue:48`、`scustack-web/pages/upload.vue:56`。
- 单份托管和外链提交都会带上 `course_id`、`category`、`semester`、`teacher`：`scustack-web/pages/upload.vue:340`、`scustack-web/pages/upload.vue:353`。
- 资料模型将课程、分类、学期设为非空字段，教师为可选字段：`scustack-api/app/models/material.py:21`、`scustack-api/app/models/material.py:26`。
- `MaterialCreate` schema 支持课程、分类、学期、教师：`scustack-api/app/schemas/material.py:7`。
- 搜索降级结果和审核队列都返回课程/分类/学期等归类字段：`scustack-api/app/services/search_service.py:223`、`scustack-api/app/services/review_service.py:37`。

**缺口**

- 教师字段在模型和表单中是可选，平台不能保证资料都能按任课教师归类。
- 课程选择依赖前端级联组件；后端只校验 `course_id` 是 UUID，未在 schema 层验证课程存在或课程与学院选择一致。
- 学期和分类在前端来自枚举，但后端未做枚举校验，存在非标准值污染目录体系的风险。
- 教师在搜索结果卡片和资料详情展示不足，前序 US-04 的“按教师判断适配性”闭环仍未完全打通。

**结论**

部分通过。课程、学期、教师、分类的写入链路存在，能够支持基础归类；但后端规范化校验和教师维度的展示/检索闭环不足。

### US-24：对现有元数据提出修正建议

PRD：作为一名贡献者，我希望能对现有元数据提出修正建议，以便课程页面的信息能持续优化。

**证据**

- 资料详情页提供「建议修正」弹窗，可选择标题、描述、学期、教师、分类并提交建议值：`scustack-web/pages/material/[id].vue:38`、`scustack-web/pages/material/[id].vue:44`。
- 前端提交时带当前值和建议值，并在成功后提示「修正建议已提交」：`scustack-web/pages/material/[id].vue:275`。
- 后端 `/materials/{material_id}/corrections` 接收修正建议，字段包括 `field_name`、`current_value`、`suggested_value`、`reason`：`scustack-api/app/api/v1/corrections.py:18`。
- 后端对修正建议做每日 10 条限流，并对同一用户同一资料同一字段的 pending 建议做 upsert：`scustack-api/app/api/v1/corrections.py:32`、`scustack-api/app/api/v1/corrections.py:44`。
- `CorrectionSuggestion` 模型记录资料、用户、字段、当前值、建议值、状态、审核者和审核备注：`scustack-api/app/models/correction.py:11`。

**缺口**

- 未发现维护者查看、接受、拒绝修正建议的 admin 页面或 API；`status`、`reviewer_id`、`reviewer_note` 字段没有形成处理闭环。
- 修正建议没有自动应用到 `Material`，也没有进入审核队列、通知维护者或通知原贡献者。
- 前端弹窗没有填写修正理由，虽然后端 schema 支持 `reason`。
- 没有发现修正建议相关测试，提交、限流、upsert 和处理缺口都缺少回归保护。

**结论**

部分通过。用户侧“提出建议”已经实现，但“课程页面的信息能持续优化”所需的维护处理与应用闭环缺失。

### US-25：新提交内容进入审核流程

PRD：作为一名维护者，我希望新提交的内容进入审核流程，以便管控垃圾内容、版权风险与低质量资源。

**证据**

- `Material.review_status` 默认是 `pending`：`scustack-api/app/models/material.py:37`。
- 创建托管资料时强制设置 `review_status='pending'` 和 `virus_scan_status='queued'`：`scustack-api/app/api/v1/materials.py:100`。
- 外链提交会先做 URL 校验，新用户外链进入 pending；内容预筛任务可对外链自动通过或标记可疑/拒绝：`scustack-api/app/api/v1/materials.py:86`、`scustack-api/app/tasks/material_tasks.py:38`。
- 管理端审核队列 API 受 `MATERIALS_MODERATE` 权限保护，默认列出 pending/returned 项：`scustack-api/app/api/v1/admin.py:31`、`scustack-api/app/services/review_service.py:12`。
- 维护者可单条通过、驳回、要求修改，也可批量通过/驳回；操作写入 review log 和 audit log：`scustack-api/app/api/v1/admin.py:43`、`scustack-api/app/api/v1/admin.py:65`、`scustack-api/app/services/review_service.py:53`。
- 前端 admin 审核队列展示课程、分类、学期、格式、贡献者、提交时间，并提供通过/驳回/要求修改按钮：`scustack-web/pages/admin/review.vue:4`、`scustack-web/pages/admin/review.vue:51`、`scustack-web/pages/admin/review.vue:76`。
- 本轮 `tests/test_admin.py` 和 `tests/test_upload_pipeline.py` 通过，覆盖审核队列鉴权、审核动作、上传后 pending 等路径。

**缺口**

- 外链资料在非新用户且预筛干净时可能自动 approved；这未必违反产品策略，但与“新提交内容进入审核流程”的绝对表述存在语义偏差。
- 「要求修改」前端没有评论输入，后端虽支持 `comment`，贡献者端也没有明确展示退回原因，低质量资源治理反馈闭环不足。
- 病毒扫描依赖外部 `clamdscan`，缺失时只记录错误并设置扫描错误状态；是否阻断审核通过需要更清晰的策略：`scustack-api/app/tasks/material_tasks.py:26`。
- 审核队列只展示基础元数据，缺少版权风险、重复风险、扫描状态、外链域名信誉等风险摘要，维护者需要点进详情才能判断。

**结论**

通过偏弱。审核基础设施已经可用，托管资料会进入 pending，维护者有队列和操作入口；但外链自动通过、退回反馈、扫描失败策略和风险摘要仍影响治理质量。

## 第 6 轮：用户故事 26-30

| 用户故事 | 审计结论 | 主要判断 |
| --- | --- | --- |
| US-26 | 部分通过 | 通过、驳回、要求修改、批量通过/驳回已实现；合并资料缺失，要求修改缺少原因输入与贡献者反馈。 |
| US-27 | 部分通过 | 上传前 hash 查重和后台 hash/标题相似检测存在；链接重复、语义相似与合并处理不足。 |
| US-28 | 通过偏弱 | 四类信任状态、维护端标记和用户侧展示存在；但社区验证来源和测试覆盖不足。 |
| US-29 | 部分通过 | 举报和版权投诉处理链路存在，可接受举报并下架；但资料管理下架接口疑似错连，版权处理不自动下架目标资料。 |
| US-30 | 部分通过 | 审核、举报、信任标记等治理动作写入审计日志；上传、编辑、删除等关键动作留痕不足。 |

### US-26：对提交资料执行通过、驳回、合并、要求修改

PRD：作为一名维护者，我希望能对提交的资料执行通过、驳回、合并、要求修改等操作，以便管控平台内容质量。

**证据**

- 后端审核队列支持按 `pending|approved|rejected|returned` 查询，且需要 `MATERIALS_MODERATE` 权限：`scustack-api/app/api/v1/admin.py:31`。
- 单条审核接口支持 `approved`、`rejected`、`returned`，并写入 audit log：`scustack-api/app/api/v1/admin.py:65`、`scustack-api/app/schemas/review.py:7`。
- 批量审核接口支持批量通过/驳回，并记录批量 audit log：`scustack-api/app/api/v1/admin.py:43`。
- 服务层会变更 `review_status`，并写入 `ReviewLog`：`scustack-api/app/services/review_service.py:53`。
- 前端审核队列提供通过、驳回、要求修改、批量通过、批量驳回按钮：`scustack-web/pages/admin/review.vue:22`、`scustack-web/pages/admin/review.vue:76`。
- 本轮 `tests/test_admin.py` 通过，覆盖审核队列、单条审核、批量审核等路径。

**缺口**

- 未发现资料“合并”接口、服务逻辑或前端操作；PRD 明确要求的“合并”没有实现。
- 前端 `reviewItem` 只提交 `{ action }`，没有让维护者输入驳回或要求修改原因：`scustack-web/pages/admin/review.vue:204`。
- 后端 batch schema 不支持 `returned`，只能批量通过/驳回；批量要求修改缺失：`scustack-api/app/schemas/review.py:12`。
- 要求修改后的贡献者反馈闭环不足，贡献页不展示退回原因，上传/编辑页也未发现针对 returned 的再提交流程。

**结论**

部分通过。审核的基础动作可用，但“合并”缺失，要求修改更像状态切换而不是可执行的协作流程。

### US-27：相似文件与链接重复检测

PRD：作为一名维护者，我希望平台能对相似文件与链接进行重复检测，以免课程页面内容冗余杂乱。

**证据**

- 上传前提供 `/upload/check-duplicate`，按 `file_hash` 检测重复：`scustack-api/app/api/v1/upload.py:25`。
- 上传页在托管资料提交流程中先计算 SHA-256 并调用查重接口，发现重复会中止提交并展示已有资料标题：`scustack-web/pages/upload.vue:317`。
- 后台 `/admin/duplicates` 返回 hash 完全重复和同课程标题前 10 字符相似的结果：`scustack-api/app/api/v1/admin.py:770`。
- 前端重复资料检测页展示 SHA-256 完全匹配和标题相似列表，并链接到候选资料详情：`scustack-web/pages/admin/duplicates.vue:4`、`scustack-web/pages/admin/duplicates.vue:21`。
- 外链校验会对域名做日提交上限，降低同域垃圾链接提交风险：`scustack-api/app/services/upload_service.py:194`。
- 本轮 `tests/test_upload.py` 和 `tests/test_external_links.py` 通过，覆盖上传查重和外链校验附近逻辑。

**缺口**

- 后台重复检测没有按 `external_url` 做完全重复或规范化 URL 重复分组；PRD 中“链接重复检测”未完整实现。
- 标题相似检测只是 `LEFT(title, 10)`，不具备中文分词、语义相似、课程别名或版本号归一能力：`scustack-api/app/api/v1/admin.py:783`。
- 重复检测页只展示候选，不提供合并、保留、忽略、标记已处理等治理动作。
- 未发现 `/admin/duplicates` 的后端测试或重复检测页的前端测试。

**结论**

部分通过。文件 hash 查重和轻量标题相似检测存在，但链接重复、相似度质量和处理闭环都不足。

### US-28：为资料标记信任状态

PRD：作为一名维护者，我希望能为资料标记信任状态（如未验证、社区验证、维护者精选、存疑等），以便用户了解资料的可信程度。

**证据**

- 前端业务配置定义四类信任状态：维护者精选、社区验证、未验证、存疑，并绑定图标和颜色：`scustack-web/data/business.ts:26`。
- 后端 PATCH `/admin/materials/{material_id}/trust` 限定四类状态，并要求 `MATERIALS_MODERATE` 权限：`scustack-api/app/api/v1/admin.py:104`。
- 服务层 `set_trust_status` 更新 `material.trust_status` 并写入 `ReviewLog`：`scustack-api/app/services/review_service.py:111`。
- 管理端审核队列和资料管理页都提供信任状态下拉选择：`scustack-web/pages/admin/review.vue:69`、`scustack-web/pages/admin/materials.vue:37`。
- 用户侧资料卡片、资料详情和移动详情都展示 `TrustBadge`：`scustack-web/components/material/MaterialCard.vue:45`、`scustack-web/components/material/MaterialDetail.vue:8`、`scustack-web/components/mobile/MaterialDetailSheet.vue:36`。
- `TrustBadge` 使用图标、颜色和文字三重编码信任状态：`scustack-web/components/common/TrustBadge.vue:1`。
- 本轮后端 `test_set_trust_status` 和前端业务枚举/契约测试通过：`scustack-api/tests/test_admin.py:238`、`scustack-web/tests/backendContractConsistency.test.ts`。

**缺口**

- `community_verified` 的来源规则仍不清晰，缺少由评分、下载、用户投票或审核规则自动转入社区验证的机制。
- 审核通过会把信任状态重置为 `unverified`，可能覆盖预筛或维护前置判断：`scustack-api/app/services/review_service.py:65`。
- 前端没有专门针对 `TrustBadge` 四类状态渲染的组件测试。

**结论**

通过偏弱。维护者标记和用户侧展示链路完整，但“社区验证”的治理规则与测试覆盖仍偏弱。

### US-29：处理下架申请与版权投诉

PRD：作为一名维护者，我希望能处理下架申请与版权投诉，以便平台合规运营。

**证据**

- 用户可举报版权、过时、内容不当、重复、信息错误等问题；维护端可列出举报并接受/驳回：`scustack-api/app/api/v1/materials.py:317`、`scustack-api/app/api/v1/admin.py:127`、`scustack-api/app/api/v1/admin.py:139`。
- 接受举报时，`report_service.handle_report` 会把关联资料 `review_status` 设置为 `removed`：`scustack-api/app/services/report_service.py:65`。
- 前端举报处理页提供待处理/已处理/已驳回 tabs 和接受/驳回按钮：`scustack-web/pages/admin/reports.vue:4`、`scustack-web/pages/admin/reports.vue:45`。
- 版权投诉公开提交接口支持限流、生成 DMCA 工单号，并承诺 48 小时处理：`scustack-api/app/api/v1/copyright.py:19`。
- 版权投诉维护端接口支持列表和 resolve，并记录 `resolved_by`、`resolved_at`、`resolution_note`：`scustack-api/app/api/v1/copyright.py:51`、`scustack-api/app/services/copyright_service.py:78`。
- 审核页面的版权投诉 tab 可加载投诉并标记已处理/驳回：`scustack-web/pages/admin/review.vue:102`。
- 本轮 `tests/test_copyright.py -k "not TitleBlocklist"` 通过 9 个版权投诉相关测试。

**缺口**

- 资料管理页“下架”按钮调用 `/api/v1/admin/materials/{id}/review` 并传 `removed`，但后端没有该路由，审核 action 也不接受 `removed`：`scustack-web/pages/admin/materials.vue:88`、`scustack-api/app/api/v1/admin.py:65`。
- 通用删除接口 `DELETE /materials/{id}` 可软删除资料，但资料管理页没有使用它；维护者主动下架路径疑似不可用：`scustack-api/app/api/v1/materials.py:153`。
- 版权投诉 resolve 只更新投诉状态，不会自动定位并下架 `infringing_url` 对应资料；下架需要人工另行处理。
- 版权投诉处理没有写入 audit log；治理审计链路不完整。
- 本轮完整版权测试中 `TestTitleBlocklist` 4 个用例失败，测试仍以同步方式调用 async `check_title_blocklist`。

**结论**

部分通过。举报接受可下架资料，版权投诉工单可提交和处理；但资料管理主动下架接口错连、版权投诉不自动联动资料下架，合规处理闭环仍不稳。

### US-30：留存上传、编辑、举报、处理决策的审核日志

PRD：作为一名维护者，我希望能留存上传、编辑、举报、处理决策的审核日志，以便平台治理可审计。

**证据**

- `AuditLog` 模型记录 user、action、resource、detail、IP、UA 和创建时间：`scustack-api/app/models/audit_log.py:11`。
- `audit_service.log_action` 会脱敏 detail 中的 PII，并哈希 IP：`scustack-api/app/services/audit_service.py:24`。
- 管理端审核、批量审核、信任状态变更、举报处理等治理决策会写入 audit log：`scustack-api/app/api/v1/admin.py:55`、`scustack-api/app/api/v1/admin.py:79`、`scustack-api/app/api/v1/admin.py:116`、`scustack-api/app/api/v1/admin.py:153`。
- `/admin/audit-logs` 需要 `AUDIT_READ` 权限，并支持 action/user 过滤和分页：`scustack-api/app/api/v1/admin.py:165`。
- 前端审计日志页展示操作、资源、评论、时间和 IP，并提供常见治理操作筛选：`scustack-web/pages/admin/audit-logs.vue:4`、`scustack-web/pages/admin/audit-logs.vue:7`。
- 本轮 `tests/test_admin.py` 覆盖审计日志权限和列表 API：`scustack-api/tests/test_admin.py:254`。

**缺口**

- 资料上传创建、普通编辑、用户主动删除、修正建议提交等关键动作没有直接调用 `audit_service.log_action`，与 PRD 中“上传、编辑、举报、处理决策”覆盖范围不一致。
- 用户提交举报只创建 `Report`，未写 audit log；只有维护者处理举报时写 audit log。
- 版权投诉处理没有纳入 audit log。
- 审计日志页筛选项不包含上传、编辑、删除、版权投诉、信任状态变更等全部治理动作。
- 前端审计日志页没有测试覆盖。

**结论**

部分通过。治理决策留痕具备基础，但上传、编辑、举报提交和版权投诉等关键事件没有完整进入审计日志。

## 第 7 轮：用户故事 31-35

| 用户故事 | 审计结论 | 主要判断 |
| --- | --- | --- |
| US-31 | 部分通过 | 学院和课程可管理；学期与资料分类仍主要是前端/代码枚举，缺少维护端配置闭环。 |
| US-32 | 部分通过 | 课程别名和合并入口存在；但合并不迁移资料，存在“合并后资料分散/不可见”的风险。 |
| US-33 | 部分通过 | 资料 pin、课程页置顶排序和首页推荐算法存在；首页没有明确使用维护者置顶，后台 pin 入口也不完整。 |
| US-34 | 通过偏弱 | 首页、搜索、课程、资料浏览支持游客使用；但部分体验仍依赖登录，E2E 对免登录浏览断言偏弱。 |
| US-35 | 部分通过 | 收藏/关注和本地最近浏览存在；但最近浏览只在登录个人中心桌面端呈现，跨设备续用能力有限。 |

### US-31：管理学院、课程、学期与分类

PRD：作为一名维护者，我希望能管理学院、课程、学期与分类，以便保持目录结构的一致性。

**证据**

- 学院 API 支持公开列表和维护者创建、更新、删除，写操作需要 `MATERIALS_MODERATE` 权限：`scustack-api/app/api/v1/colleges.py:22`、`scustack-api/app/api/v1/colleges.py:64`。
- 课程 API 支持公开列表/详情和维护者创建、更新、合并：`scustack-api/app/api/v1/courses.py:22`、`scustack-api/app/api/v1/courses.py:89`、`scustack-api/app/api/v1/courses.py:100`。
- 前端后台有学院管理页，可新建、编辑、删除学院：`scustack-web/pages/admin/colleges.vue:4`、`scustack-web/pages/admin/colleges.vue:113`。
- 前端后台有课程管理页，可按学院过滤、创建、编辑、禁用/启用课程：`scustack-web/pages/admin/courses.vue:4`、`scustack-web/pages/admin/courses.vue:13`、`scustack-web/pages/admin/courses.vue:154`。
- 本轮 `tests/test_courses.py`、`tests/test_colleges.py` 通过，覆盖课程/学院基础服务和接口。

**缺口**

- 未发现学期管理 API 或独立后台页面；学期来自 `materialSemesters` 前端枚举：`scustack-web/data/business.ts:13`。
- 资料分类也主要来自 `materialCategories` 前端枚举和静态搜索配置，没有维护端 CRUD：`scustack-web/data/business.ts:1`、`scustack-api/app/services/search_service.py:17`。
- 课程后台的“分类”是自由输入，不是受控目录；后端也没有分类/学期枚举校验，目录一致性仍易被非标准值破坏。
- 学院/课程写操作未写 audit log，和维护目录结构的治理可追溯性不匹配。

**结论**

部分通过。学院和课程管理基本可用；学期与资料分类仍是代码配置/自由文本，尚未形成完整目录治理系统。

### US-32：合并重复课程或别名

PRD：作为一名维护者，我希望能合并重复课程或别名，以免用户在多个名称下分散查找资料。

**证据**

- 课程模型有 `aliases` JSONB 字段：`scustack-api/app/models/course.py:22`。
- 课程搜索服务支持按课程名和 aliases 查找：`scustack-api/app/services/course_service.py:44`。
- 后端提供 `/courses/{course_id}/merge?target_id=`，需要 `MATERIALS_MODERATE` 权限：`scustack-api/app/api/v1/courses.py:114`。
- `merge_courses` 会把源课程名称和 aliases 合并进目标课程 aliases，并将源课程 `is_active=False`：`scustack-api/app/services/course_service.py:60`。
- 前端课程管理页提供合并弹窗，可选择目标课程并调用 merge API：`scustack-web/pages/admin/courses.vue:78`、`scustack-web/pages/admin/courses.vue:191`。
- 课程详情页展示别名：`scustack-web/pages/course/[id].vue:9`。
- 本轮 `tests/test_courses.py` 通过，包含 `test_merge_courses` 和 alias 搜索相关测试。

**缺口**

- `merge_courses` 明确注释“Materials migration handled when materials table exists”，但当前资料表已存在，服务仍没有迁移 `Material.course_id`：`scustack-api/app/services/course_service.py:65`。
- 源课程被禁用后，其原有资料仍挂在源课程 ID；公开课程列表只查 `is_active=True`，可能造成资料入口分散甚至不可见。
- 合并没有处理书签、通知、搜索索引重建、课程关注者迁移或审计日志。
- 前端合并说明写着“原课程资料将迁移至目标课程”，与后端真实行为不一致：`scustack-web/pages/admin/courses.vue:82`。

**结论**

部分通过。别名合并和禁用源课程实现了“名称归一”的一部分，但没有迁移资料和用户关系，反而可能制造新的资料孤岛。

### US-33：课程页与首页置顶推荐优质资源

PRD：作为一名维护者，我希望能将优质资源在课程页与首页置顶推荐，以便学生更快找到可信资料。

**证据**

- 后端提供资料 pin/unpin 接口，权限为 `MATERIALS_PIN`：`scustack-api/app/api/v1/materials.py:334`。
- 服务层 pin/unpin 设置 `Material.is_pinned`：`scustack-api/app/services/review_service.py:132`。
- 资料列表服务按 `Material.is_pinned.desc()` 置顶，再按业务排序排序，因此课程页资料列表可体现置顶：`scustack-api/app/services/material_service.py:43`。
- 首页推荐算法将信任状态纳入质量权重，`maintainer_picked` 有更高倍数：`scustack-api/app/services/homepage_service.py:29`。
- 首页展示热门课程、为你推荐和近期更新：`scustack-web/pages/index.vue:31`、`scustack-web/pages/index.vue:48`、`scustack-web/pages/index.vue:77`。
- 本轮 `tests/test_homepage.py`、`tests/test_homepage_presentation.py` 和 `tests/test_admin.py` 中 pin 相关路径通过。

**缺口**

- 首页推荐算法没有显式优先 `is_pinned`，只依赖评分、热度、新鲜度、校历和信任状态；维护者 pin 不一定进入首页置顶。
- 前端后台资料管理页只提供信任状态和下架，没有发现 pin/unpin 操作入口；pin API 有后端但维护者 UI 不完整：`scustack-web/pages/admin/materials.vue:37`。
- pin/unpin 没有写 audit log。
- 首页“推荐”与“维护者置顶推荐”语义不同；目前无法配置具体资料固定在首页首屏推荐位。

**结论**

部分通过。课程页置顶排序具备后端能力；首页优质推荐有算法基础，但维护者明确置顶首页资源的闭环不足。

### US-34：无需 Git 或群聊即可搜索和浏览内容

PRD：作为一名首次访问的用户，我希望无需学习 Git、也无需加入群聊就能搜索和浏览内容，以便平台上手门槛低、易使用。

**证据**

- 首页、搜索页、课程列表和课程详情均无 auth middleware，支持公开访问：`scustack-web/pages/index.vue:127`、`scustack-web/pages/search.vue:86`、`scustack-web/pages/course/index.vue:118`。
- 搜索、课程、首页后端接口使用 `get_optional_user`，允许游客访问并配合发现接口限流：`scustack-api/app/api/v1/search.py:33`、`scustack-api/app/api/v1/courses.py:29`、`scustack-api/app/api/v1/homepage.py:22`。
- 首页提供热门课程、推荐资料、近期更新和“更多资料”入口，不要求用户理解 Git 或加入群聊：`scustack-web/pages/index.vue:31`、`scustack-web/pages/index.vue:48`、`scustack-web/pages/index.vue:77`。
- SearchBar 提供课程/资料搜索框、自动补全、搜索历史和热门搜索：`scustack-web/components/search/SearchBar.vue:1`、`scustack-web/components/search/SearchBar.vue:45`、`scustack-web/components/search/SearchBar.vue:180`。
- 搜索页提供筛选、排序、骨架屏、空状态和移动搜索视图：`scustack-web/pages/search.vue:18`、`scustack-web/pages/search.vue:55`、`scustack-web/pages/search.vue:76`。
- 本轮 `tests/SearchBar.test.ts`、`tests/HomePageDataLoading.test.ts` 通过。

**缺口**

- 下载、收藏、举报、修正建议等动作仍要求登录；这是合理权限边界，但首次用户从“浏览”到“获取资料”会遇到登录门槛。
- 现有 E2E 仍未强断言“未登录用户可完成首页 -> 搜索 -> 课程 -> 资料详情浏览”的完整路径。
- SearchBar 测试多为挂载/输入存在性，未验证真实建议、历史、热门搜索和键盘导航结果。

**结论**

通过偏弱。公开搜索和浏览主路径是存在的，产品门槛较低；但真实游客路径的自动化验证还不够强。

### US-35：从最近浏览课程与保存资源继续使用

PRD：作为一名回访用户，我希望能从最近浏览的课程与保存的资源继续使用，以便重复学习的流程更高效。

**证据**

- 本地体验状态保存最近浏览课程和资料，最多保留 20 条：`scustack-web/composables/useLocalExperienceState.ts:70`。
- 课程详情页访问后写入最近浏览：`scustack-web/pages/course/[id].vue:220`。
- 资料详情 composable 访问资料后写入最近浏览：`scustack-web/composables/useMaterial.ts:84`。
- 个人中心桌面端展示最近浏览列表，并链接回课程或资料：`scustack-web/pages/user/profile.vue:64`、`scustack-web/pages/user/profile.vue:205`。
- 后端书签 API 支持关注课程和收藏资料，前端「收藏与关注」页分 tab 展示关注课程和收藏资料：`scustack-api/app/api/v1/bookmarks.py:15`、`scustack-web/pages/user/bookmarks.vue:7`。
- 本轮 `tests/useLocalExperienceState.test.ts`、`tests/ProfilePage.test.ts`、`tests/test_users.py` 通过，覆盖本地最近浏览、个人中心和书签接口。

**缺口**

- 最近浏览只存在本机 localStorage，不会随账号跨设备同步。
- 个人中心最近浏览仅在桌面端完整展示；移动端个人中心只展示贡献、收藏、隐私入口，未展示最近浏览：`scustack-web/pages/user/profile.vue:133`。
- 最近浏览在个人中心登录后才可见；未登录回访用户虽然本地有记录，但没有明显入口继续浏览。
- 收藏列表的课程项 `college_name` 和 `material_count` 目前返回空/0，续用上下文不足：`scustack-api/app/services/user_service.py:81`。

**结论**

部分通过。回访续用有本地最近浏览和服务端收藏/关注两条线，但跨设备同步、移动端呈现和上下文丰富度还不足。

## 第 8 轮：用户故事 36-40

### 总览

| 编号 | 用户故事摘要 | 审计状态 | 主要结论 |
|---|---|---|---|
| US-36 | 慢网/不稳定网络下高效加载，并在下载前看到文件大小和格式 | 部分通过 | 后端返回格式/大小，预览会按文件大小降级，页面有懒加载和分页；但搜索/首页卡片未展示文件大小，弱网体验没有端到端验证。 |
| US-37 | 公开贡献不暴露不必要个人信息 | 部分通过 | 有隐私设置、PII 加密和关于页匿名展示；但资料详情贡献者响应仍暴露 `contributor_id`、`nickname`、头像等，未使用 `public_display_name`。 |
| US-38 | 平台不设置广告位 | 通过偏弱 | PRD/设计文档明确无广告，代码未发现广告槽；但首页 banner 可配置，缺少自动化约束来防止广告化内容进入推荐位。 |
| US-39 | 运营查看零结果搜索、热门课程、死链等分析 | 部分通过 | 零结果搜索、热门搜索、热门课程和死链检测均有实现；但后台分析视图未把热门课程/热词/死链整合成维护优先级闭环。 |
| US-40 | 课程/资料模型可适配未来微信小程序 | 通过偏弱 | REST API、Pydantic schema 和前端共享类型具有复用基础，且已有微信登录；但认证主要依赖浏览器 Cookie，没有小程序客户端契约测试。 |

### US-36：慢网/不稳定网络下高效加载，并在下载前看到文件大小和格式

PRD：作为一名网络环境较慢或不稳定的用户，我希望页面加载足够高效，并能在下载前看到文件大小和格式，以便判断是否值得下载。

**证据**

- 后端资料响应包含 `format`、`file_size`、`thumbnail_url` 等字段：`scustack-api/app/schemas/material.py:54`、`scustack-api/app/schemas/material.py:55`、`scustack-api/app/schemas/material.py:71`。
- 前端共享类型也声明 `format` 与 `file_size`：`scustack-web/types/api.ts:64`、`scustack-web/types/api.ts:65`。
- 资料详情页展示格式，并在下载按钮显示文件大小：`scustack-web/components/material/MaterialDetail.vue:19`、`scustack-web/components/material/MaterialDetail.vue:70`、`scustack-web/components/material/MaterialDetail.vue:71`。
- 移动详情抽屉也在下载按钮上显示文件大小：`scustack-web/components/mobile/MaterialDetailSheet.vue:52`、`scustack-web/components/mobile/MaterialDetailSheet.vue:53`。
- 预览组件按 `fileSize` 判断大 PDF，超过 25MB 时关闭在线预览并提示直接下载，避免慢网渲染成本：`scustack-web/components/preview/FilePreview.vue:60`、`scustack-web/components/preview/FilePreview.vue:63`、`scustack-web/components/preview/FilePreview.vue:70`。
- 首页接口使用 cursor/limit，并对发现流量做限流保护：`scustack-api/app/api/v1/homepage.py:20`、`scustack-api/app/api/v1/homepage.py:21`、`scustack-api/app/api/v1/homepage.py:24`。
- 资料卡片图片使用 `loading="lazy"`：`scustack-web/components/material/MaterialCard.vue:6`、`scustack-web/components/material/MaterialCard.vue:11`。
- 本轮 `tests/test_materials.py`、`tests/test_homepage.py`、`tests/test_discovery_protection.py` 和前端首页加载测试通过。

**缺口**

- `MaterialCard` 只展示格式、评分、下载量和时间，不展示 `file_size`，用户在搜索/首页卡片阶段无法稳定判断下载成本：`scustack-web/components/material/MaterialCard.vue:54`、`scustack-web/components/material/MaterialCard.vue:55`。
- 慢网/不稳定网络缺少 Playwright 网络节流或超时恢复测试，现有测试主要覆盖数据加载和接口行为。
- 文件大小展示集中在详情和移动下载按钮，尚未形成“下载前所有关键入口均可见”的一致体验。

**结论**

部分通过。性能基础和格式/大小字段都存在，但下载前判断信息没有覆盖到资料列表、搜索结果等高频入口，弱网体验也缺少真实浏览器验证。

### US-37：公开贡献不暴露不必要个人信息

PRD：作为一名关注隐私的用户，我希望公开贡献展示不暴露不必要个人信息，以便放心参与共享。

**证据**

- 用户隐私 API 可读取和更新 `public_display_name`：`scustack-api/app/api/v1/users.py:104`、`scustack-api/app/api/v1/users.py:115`、`scustack-api/app/api/v1/users.py:121`。
- 隐私设置页允许选择“匿名用户”或“使用昵称”，并提示资料详情页显示效果：`scustack-web/pages/user/privacy.vue:16`、`scustack-web/pages/user/privacy.vue:21`、`scustack-web/pages/user/privacy.vue:43`。
- 邮箱绑定使用 `encrypt_pii` 和 `blind_index_pii` 存储：`scustack-api/app/api/v1/users.py:208`、`scustack-api/app/api/v1/users.py:209`、`scustack-api/app/api/v1/users.py:210`。
- 关于页贡献榜使用 `public_display_name or nickname or "匿名用户"`：`scustack-api/app/services/about_service.py:107`、`scustack-api/app/services/about_service.py:108`。
- 本轮 `tests/test_users.py` 和 `tests/ProfilePage.test.ts` 通过。

**缺口**

- 资料详情的贡献者 schema 暴露 `id`、`nickname`、`avatar_url`、`trust_score` 和 badges，不包含 `public_display_name`：`scustack-api/app/schemas/material.py:32`、`scustack-api/app/schemas/material.py:35`、`scustack-api/app/schemas/material.py:36`。
- 资料响应额外暴露 `contributor_id`：`scustack-api/app/schemas/material.py:69`。
- `get_material` 直接把 `User` 对象挂到 `m.contributor`，没有按隐私设置投影成公开显示名：`scustack-api/app/services/material_service.py:88`、`scustack-api/app/services/material_service.py:96`。
- 前端类型同样以 `nickname` 建模公开贡献者，未体现匿名显示名：`scustack-web/types/api.ts:50`、`scustack-web/types/api.ts:51`。

**结论**

部分通过。隐私设置和 PII 存储方向正确，但最关键的资料公开贡献展示没有真正使用隐私投影，存在用户以为匿名、详情页仍暴露昵称/头像/ID 的风险。

### US-38：平台不设置广告位

PRD：作为一名平台运营者，我希望平台不设置任何广告位，以便清晰保持公益定位、保护用户信任。

**证据**

- PRD 明确“平台全程无广告”“无付费置顶、无商业排名”，并把广告与商业推广列为范围外：`docs/PRD-产品需求文档.md:26`、`docs/PRD-产品需求文档.md:85`、`docs/PRD-产品需求文档.md:111`。
- 设计文档也将“干净、无广告、无商业排名”列为公益原则：`docs/DESIGN-UI-UX.md:27`。
- 代码搜索未发现 `ads`、`sponsored`、广告位或商业排名字段。
- 首页接口返回的是运营配置的 `banners`、统计、校历推荐、近期更新、热门课程等内容，没有广告实体：`scustack-api/app/api/v1/homepage.py:45`、`scustack-api/app/api/v1/homepage.py:56`。

**缺口**

- 后台可更新首页 banner 配置，只记录 `banner_count`，没有内容类型、公益用途或禁止商业推广的校验：`scustack-api/app/api/v1/admin.py:540`、`scustack-api/app/api/v1/admin.py:546`、`scustack-api/app/api/v1/admin.py:550`。
- 缺少防回归测试，无法自动防止后续新增广告槽、赞助字段或商业推荐字段。

**结论**

通过偏弱。当前实现没有广告系统，符合 PRD 的产品方向；但“无广告”属于长期治理约束，需要配置校验或测试守住边界。

### US-39：运营查看零结果搜索、热门课程、死链等分析

PRD：作为一名平台运营者，我希望知道哪些搜索没有结果、哪些课程最热门、哪些外链失效，以便优先维护。

**证据**

- 搜索无结果时写入 `AuditLog(action='search_no_result')`：`scustack-api/app/api/v1/search.py:210`、`scustack-api/app/api/v1/search.py:216`。
- 搜索关键词写入 Redis 周榜，`/search/hot` 可返回热门搜索：`scustack-api/app/api/v1/search.py:221`、`scustack-api/app/api/v1/search.py:225`、`scustack-api/app/api/v1/search.py:254`。
- 后台搜索分析接口聚合零结果搜索 Top 30：`scustack-api/app/api/v1/admin.py:691`、`scustack-api/app/api/v1/admin.py:700`、`scustack-api/app/api/v1/admin.py:706`。
- 后台搜索分析页展示“零结果搜索 Top 30”：`scustack-web/pages/admin/search-analytics.vue:4`、`scustack-web/pages/admin/search-analytics.vue:8`、`scustack-web/pages/admin/search-analytics.vue:31`。
- 首页接口返回 `hot_courses`，服务端按热门课程供前台发现：`scustack-api/app/api/v1/homepage.py:38`、`scustack-api/app/api/v1/homepage.py:56`。
- 死链定时任务检查外链并写入状态与审计日志：`scustack-api/app/tasks/link_check.py:13`、`scustack-api/app/tasks/link_check.py:45`、`scustack-api/app/tasks/link_check.py:67`。
- 后台死链接口和页面均存在，并支持重新检测：`scustack-api/app/api/v1/admin.py:399`、`scustack-api/app/api/v1/admin.py:409`、`scustack-web/pages/admin/dead-links.vue:4`、`scustack-web/pages/admin/dead-links.vue:25`。
- 本轮 `tests/test_search.py`、`tests/test_admin.py`、`tests/test_external_links.py` 和 `tests/SearchBar.test.ts` 通过。

**缺口**

- 后台搜索分析页只展示零结果搜索，没有展示热门搜索词。
- 热门课程主要服务首页发现，后台运营分析页没有同等的热门课程列表、维护建议或缺资料提示。
- 死链页能列出和重检，但没有与资料下架、通知贡献者、创建修复任务形成闭环。

**结论**

部分通过。运营数据采集和若干后台页面已经具备，但“优先维护”的工作台还没有完全形成。

### US-40：课程/资料模型可适配未来微信小程序

PRD：作为一名未来可能使用微信小程序的用户，我希望核心课程与资料模型能在小程序中复用，以便后续不需要重新设计。

**证据**

- 后端以 FastAPI JSON API 和 Pydantic schema 输出课程、学院、资料等资源，资料响应字段结构清晰：`scustack-api/app/schemas/material.py:42`、`scustack-api/app/schemas/material.py:45`。
- 前端维护独立 TS API 类型，课程、学院、资料模型没有与页面组件强耦合：`scustack-web/types/api.ts:33`、`scustack-web/types/api.ts:49`。
- 认证服务已经包含微信登录 URL 与 callback：`scustack-api/app/api/v1/auth.py:315`、`scustack-api/app/api/v1/auth.py:321`。
- 微信登录服务创建或查找 `wechat_openid_lookup` 用户，并复用统一 token 发放：`scustack-api/app/services/auth_service.py:425`、`scustack-api/app/services/auth_service.py:442`、`scustack-api/app/services/auth_service.py:476`。
- 本轮后端和前端契约测试均通过。

**缺口**

- 当前登录态主要通过浏览器 Cookie 写入和读取：`scustack-api/app/api/v1/auth.py:52`、`scustack-api/app/api/v1/auth.py:53`、`scustack-api/app/dependencies.py:17`、`scustack-api/app/dependencies.py:18`。这对 Web 合理，但小程序通常需要显式 token 交换/存储契约。
- 微信 OAuth URL 使用 `open.weixin.qq.com/connect/qrconnect`，偏网页登录；未见小程序 `wx.login` code 换 session 的独立接口：`scustack-api/app/services/auth_service.py:419`、`scustack-api/app/services/auth_service.py:421`。
- 缺少面向小程序的 API 兼容性测试，例如 Cookie-free 认证、分页字段、下载链接和错误码契约。

**结论**

通过偏弱。核心模型和 API 有复用基础，微信身份也已有雏形；但真正的小程序适配还需要独立认证契约和兼容性测试来避免后续重构。

## 测试记录

### 第 1 轮

- `python -m pytest tests/test_search.py tests/test_courses.py tests/test_colleges.py`：通过，34 passed，耗时 204.75s。
- `pnpm --filter scustack-web vitest run tests/backendContractConsistency.test.ts`：未执行成功，pnpm 在非 TTY 环境触发 `ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY`。
- `scustack-web/node_modules/.bin/vitest.CMD run tests/backendContractConsistency.test.ts`：通过，3 tests passed。

### 第 2 轮

- `python -m pytest tests/test_materials.py tests/test_admin.py tests/test_external_links.py`：通过，59 passed，耗时 13.70s。
- `scustack-web/node_modules/.bin/vitest.CMD run tests/RatingWidget.test.ts tests/CommentSection.test.ts`：通过，7 tests passed。

### 第 3 轮

- `python -m pytest tests/test_admin.py tests/test_users.py tests/test_homepage.py tests/test_content_extract.py tests/test_search.py tests/test_discovery_protection.py`：通过，116 passed，耗时 201.65s。
- `scustack-web/node_modules/.bin/vitest.CMD run tests/authStore.test.ts tests/ProfilePage.test.ts tests/HomePageDataLoading.test.ts tests/accessibility.test.ts`：通过，15 tests passed。

### 第 4 轮

- `python -m pytest tests/test_search.py tests/test_upload.py tests/test_upload_pipeline.py tests/test_external_links.py tests/test_materials.py`：通过，74 passed，耗时 189.06s。
- `scustack-web/node_modules/.bin/vitest.CMD run tests/UploadPage.test.ts tests/DropZone.test.ts tests/backendContractConsistency.test.ts`：通过，11 tests passed。

### 第 5 轮

- `python -m pytest tests/test_users.py tests/test_upload.py tests/test_upload_pipeline.py tests/test_admin.py`：通过，65 passed，耗时 4.77s。
- `scustack-web/node_modules/.bin/vitest.CMD run tests/UploadPage.test.ts tests/ProfilePage.test.ts`：通过，4 tests passed。

### 第 6 轮

- `python -m pytest tests/test_admin.py tests/test_copyright.py tests/test_upload.py tests/test_external_links.py`：未完全通过，61 passed、4 failed；失败均来自 `tests/test_copyright.py::TestTitleBlocklist`，测试以同步方式调用 async `check_title_blocklist`，断言拿到 coroutine。
- `python -m pytest tests/test_copyright.py -k "not TitleBlocklist"`：通过，9 passed、4 deselected。
- `scustack-web/node_modules/.bin/vitest.CMD run tests/businessOptions.test.ts tests/backendContractConsistency.test.ts`：通过，5 tests passed。

### 第 7 轮

- `python -m pytest tests/test_courses.py tests/test_colleges.py tests/test_homepage.py tests/test_homepage_presentation.py tests/test_users.py`：通过，83 passed，耗时 41.43s。
- `scustack-web/node_modules/.bin/vitest.CMD run tests/SearchBar.test.ts tests/useLocalExperienceState.test.ts tests/ProfilePage.test.ts tests/HomePageDataLoading.test.ts`：通过，10 tests passed。

### 第 8 轮

- `python -m pytest tests/test_materials.py tests/test_search.py tests/test_homepage.py tests/test_homepage_presentation.py tests/test_users.py tests/test_admin.py tests/test_external_links.py tests/test_discovery_protection.py`：通过，153 passed，耗时 222.46s。
- 在仓库根目录执行 `scustack-web/node_modules/.bin/vitest.CMD run ...`：环境型失败，部分 `.vue` 文件未被 Vite Vue 插件解析。
- 在 `scustack-web` 目录执行 `node_modules/.bin/vitest.CMD run tests/HomePageDataLoading.test.ts tests/ProfilePage.test.ts tests/useLocalExperienceState.test.ts tests/backendContractConsistency.test.ts tests/businessOptions.test.ts tests/SearchBar.test.ts`：通过，15 tests passed。

## 高优先级问题

1. **学院/课程筛选入口缺失**：搜索页后端参数存在，但用户无法在筛选面板选择学院或课程，影响 US-02。
2. **多选筛选与单值 API 不一致**：分类/学期等筛选在前端表现为多选，后端却按单值接收，影响 US-02、US-03、US-05。
3. **教师/教学场景展示不完整**：`teacher` 有数据结构但详情页/卡片不展示，教学场景未建模，影响 US-04。
4. **E2E 断言过弱**：浏览和搜索路径主要验证页面可见，未验证结果内容、筛选语义或分类/学期/教师展示。
5. **预览复用下载接口导致体验风险**：在线预览依赖登录下载接口和 OSS 302，Office 还固定依赖 localhost OnlyOffice，影响 US-06。
6. **评分展示取整失真**：`RatingWidget` 将平均分四舍五入后展示，3.5 会显示为 4.0，影响 US-09。
7. **举报缺少反滥用限制**：举报提交可重复创建，缺少用户/资料维度限流或去重，影响 US-10 的治理质量。
8. **课程更新通知可能提前或重复**：资料提交和审核通过都通知课程关注者，可能通知尚未公开的资料，影响 US-12。
9. **首页推荐未使用真实校历事件**：当前按月份映射分类，不读取 `academic_calendar`，影响 US-13 的准确性。
10. **标签全文搜索缺失**：资料模型、上传表单和 ES mapping 都未体现 tags，影响 US-15。
11. **移动端关键路径缺少 viewport E2E**：移动组件存在，但缺少移动浏览、搜索、详情、下载、通知路径验证，影响 US-14。
12. **搜索结果卡片缺少课程和学期**：后端返回字段存在，但桌面/移动搜索结果未完整展示 PRD 要求的对比信息，影响 US-16。
13. **排序语义不满足 PRD**：缺少学期排序，且“最新”使用 `created_at` 而非 `updated_at`，影响 US-17。
14. **上传元数据维度不足**：标签和教学场景未建模，批量上传缺少逐文件描述等字段，影响 US-18。
15. **版本更新说明测试不足**：`change_note` 已贯通但前端交互和端到端链路缺少覆盖，影响 US-20 的回归可靠性。
16. **贡献历史粒度不足**：贡献页只展示资料级创建记录，不展示版本级修订、审核原因和公开贡献档案，影响 US-21。
17. **上传后端校验偏弱**：分类、学期等目录字段缺少枚举/非空字符串校验，影响 US-22、US-23。
18. **修正建议缺少维护闭环**：用户能提交建议，但维护端查看/处理/应用入口缺失，影响 US-24。
19. **审核退回反馈不完整**：维护者「要求修改」无法在前端输入原因，贡献者端也不展示退回说明，影响 US-25。
20. **资料合并能力缺失**：审核和重复检测均没有合并资料的接口或前端动作，影响 US-26、US-27。
21. **重复链接检测不足**：后台重复检测覆盖 hash 和标题前缀，未覆盖 external URL 规范化重复，影响 US-27。
22. **资料管理主动下架疑似不可用**：前端调用不存在的 admin review 路由且 action 不支持 `removed`，影响 US-29。
23. **版权投诉不联动资料下架和审计日志**：投诉 resolve 只改投诉状态，不自动处理关联资料，也不写 audit log，影响 US-29、US-30。
24. **审计日志覆盖不全**：上传、编辑、删除、举报提交和修正建议等关键治理事件未完整留痕，影响 US-30。
25. **版权黑名单测试失配**：`test_copyright.py::TestTitleBlocklist` 仍按同步函数测试 async 实现，当前 4 个测试失败，影响版权风险回归可信度。
26. **学期和资料分类缺少维护端配置**：学院/课程可管理，但学期和资料分类仍是代码枚举或自由文本，影响 US-31。
27. **课程合并不迁移资料**：merge 只合并 aliases 并禁用源课程，资料仍挂在源课程，影响 US-32。
28. **首页置顶推荐闭环不足**：`is_pinned` 影响资料列表排序，但首页推荐未显式使用 pin，前端后台也缺 pin 操作入口，影响 US-33。
29. **回访续用移动端和跨设备不足**：最近浏览为 localStorage 且移动个人中心不展示，收藏课程上下文字段为空/0，影响 US-35。
30. **文件大小下载前可见性不一致**：详情页和移动下载按钮展示 `file_size`，但资料卡片/搜索结果不展示，影响 US-36。
31. **公开贡献隐私投影未闭环**：资料详情贡献者仍按 `nickname`/头像/ID 暴露，没有使用 `public_display_name`，影响 US-37。
32. **无广告约束缺少自动化保护**：当前没有广告代码，但 homepage banner 配置缺少公益内容约束和回归测试，影响 US-38 的长期可信度。
33. **运营分析未形成统一维护工作台**：零结果搜索、热门搜索、热门课程和死链数据分散，缺少优先级建议和处理闭环，影响 US-39。
34. **小程序认证契约未独立设计**：当前认证以 Cookie 为主，缺少小程序 code 换 token、Cookie-free 调用和下载链接兼容测试，影响 US-40。

## 后续轮次

- 第 1 轮：US-01 至 US-05。已完成。
- 第 2 轮：US-06 至 US-10。已完成。
- 第 3 轮：US-11 至 US-15。已完成。
- 第 4 轮：US-16 至 US-20。已完成。
- 第 5 轮：US-21 至 US-25。已完成。
- 第 6 轮：US-26 至 US-30。已完成。
- 第 7 轮：US-31 至 US-35。已完成。
- 第 8 轮：US-36 至 US-40。已完成。
