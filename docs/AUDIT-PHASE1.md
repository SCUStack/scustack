# 川流课栈 第一阶段审计报告

> 审计日期：2026-06-15 | 审计范围：ARCHITECTURE.md / ISSUES.md / PRD.md / UI-UX-DESIGN.md 交叉审计 + 代码实现验证

---

## 一、总体进展

| 维度 | 数据 |
|---|---|
| 已完成 Epic | 11/13（Epic 0–10 主体完成，Epic 11 部分完成） |
| 已完成 Issue | ~104/120 (87%) |
| 待完成 Issue | ~16 个（Epic 11 剩余 + Epic 12 大部 + DOC 3 个） |
| 后端 API 端点 | 13 个路由文件，覆盖全部核心域 |
| 前端页面 | 19 个页面，覆盖全部用户/管理路由 |
| 前端组件 | 23 个 Vue 组件，覆盖核心交互 |
| 测试文件 | 15 个 pytest 文件，0 个 vitest/E2E 文件 |

**第一阶段覆盖了所有面向用户的核心功能**：认证、学院/课程目录、资料上传与管理、全文搜索、文件预览（含盲水印）、版本管理、评分、收藏、举报、审核队列、管理后台、安全加固。

---

## 二、四文档交叉一致性审计

### 2.1 数据模型一致性：合格

PRD → ARCHITECTURE → ISSUES 之间对核心实体定义一致。`users`、`colleges`、`courses`、`materials`、`material_versions`、`ratings`、`bookmarks`、`review_logs`、`reports`、`audit_logs`、`academic_calendar` 在三个文档中字段对齐。

**发现**：ARCHITECTURE §4.2 定义 `material_versions.file_hash` 为 `VARCHAR(64)`，但 ISSUE-036 和 ISSUE-043 中 SHA-256 实际输出为 64 位十六进制（无误）。OK。

### 2.2 搜索策略一致性：有歧义

ARCHITECTURE.md §4 同时描述了 PostgreSQL `zhparser` 全文索引（§4.2、§4.4）和 Elasticsearch IK 分词器（§5）。搜索 API（ISSUE-046）明确走 ES，但数据库层 GIN 索引仍然存在。

**风险**：两份搜索能力并存会令新加入的开发者混淆"搜索到底走哪个引擎"。建议在 ARCHITECTURE.md 中明确：PG GIN 仅用于课程名本地过滤（`GET /courses?college_id=` 内嵌搜索），ES 是全平台搜索的权威引擎。

### 2.3 消息队列选型不一致

| 文档位置 | 描述 |
|---|---|
| ARCHITECTURE.md §1.2 技术选型表 | "Redis Streams / RabbitMQ" |
| ARCHITECTURE.md §3.4 异步任务 | Celery（未指定 broker） |
| 实际代码 (`core/celery_app.py`) | Redis broker |
| docker-compose.yml | Redis 单实例，无 RabbitMQ |

**结论**：技术选型表的措辞"Redis Streams / RabbitMQ"容易造成误解。实际全部使用 Redis 作为 Celery broker。建议将选型表修正为"Celery (Redis broker)"，删除 RabbitMQ 引用（或标注为"未来可选升级"）。

### 2.4 下载配额数值不一致

| 文档位置 | 学生 | 贡献者 | 维护者 |
|---|---|---|---|
| ARCHITECTURE.md §6.5 下载流程 | 50 次/天 | 100 次/天 | 无限 |
| ARCHITECTURE.md §9.5 速率限制表 | `GET /api/materials/:id/download` → 100 req/hour | 同 | 同 |
| ISSUE-111 验收标准 | 50 次/天 | 100 次/天 | 无限 |

**冲突**：§9.5 写的是 100 req/**hour**（基于 Redis 滑动窗口速率限制），§6.5 写的是 50 次/**天**（基于每日配额计数器）。这是**两层不同的限制机制**——每小时速率限制和每日配额限制——但文档没有解释两者的关系。

**建议**：明确两层机制并存：① Redis 滑动窗口 100 req/hour（防瞬时刷量）② 每日计数器 50 次/天（防日积月累）。两者同时生效，任一超限即返回 429。

### 2.5 学期字段格式

PRD、ISSUES、ARCHITECTURE 均使用 `2024-2025-1` 格式，但 UI-UX-DESIGN §4.5 上传表单写的是"适用学期 * (下拉选择)"，没有规定生成逻辑。如果学期下拉是硬编码列表，需要维护者定期更新。建议在 ARCHITECTURE.md 中补充学期生成规则（如基于当前月份自动生成最近 6 个学期选项）。

### 2.6 首页渲染模式：ARCHITECTURE vs UI-UX 一致，但实际实现可能有问题

| 文档 | 描述 |
|---|---|
| ARCHITECTURE.md §2.3 | `/` → ISR (5min) |
| UI-UX-DESIGN.md §4.1 | `/` → ISR (5min) |
| ISSUE-078 | ISR + `routeRules: { '/': { swr: 300 } }` |

OK，三文档一致。但需要注意的是 ISR 与 CDN 缓存（ISSUE-110）叠加时，首页个性化内容（如"关注课程更新"——需登录态）无法在 ISR 页面中呈现，必须通过客户端 CSR 注入。ARCHITECTURE.md 未说明这种混合模式。

---

## 三、规范 vs 实现差距

### 3.1 API 端点实现状态

对照 ARCHITECTURE.md §11.1 的 API 设计，逐端点核对：

| 端点 | 规范 | 实现 | 状态 |
|---|---|---|---|
| `GET /api/v1/colleges` | ✓ | `colleges.py` | ✅ |
| `POST /api/v1/colleges` | ✓ | `admin.py` 内 | ✅ |
| `GET /api/v1/colleges/:id/courses` | ✓ | `colleges.py` | ✅ |
| `GET /api/v1/courses` | ✓ | `courses.py` | ✅ |
| `POST /api/v1/courses` | ✓ | `admin.py` 内 | ✅ |
| `PATCH /api/v1/courses/:id` | ✓ | `admin.py` 内 | ✅ |
| `POST /api/v1/courses/:id/merge` | ✓ | `courses.py` | ✅ |
| `GET /api/v1/courses/:id/materials` | ✓ | `courses.py` | ✅ |
| `GET /api/v1/materials` | ✓ | `materials.py` | ✅ |
| `POST /api/v1/materials` | ✓ | `materials.py` | ✅ |
| `PATCH /api/v1/materials/:id` | ✓ | `materials.py` | ✅ |
| `DELETE /api/v1/materials/:id` | ✓ | `materials.py` | ✅ |
| `GET /api/v1/materials/:id/versions` | ✓ | `materials.py` | ✅ |
| `POST /api/v1/materials/:id/versions` | ✓ | `materials.py` | ✅ |
| `GET /api/v1/materials/:id/versions/:vid/diff` | ✓ | `materials.py` | ✅ |
| `GET /api/v1/materials/:id/download` | ✓ | `materials.py` | ✅ |
| `POST /api/v1/materials/:id/ratings` | ✓ | `materials.py` | ✅ |
| `POST /api/v1/materials/:id/reports` | ✓ | `materials.py` | ✅ |
| `GET /api/v1/search` | ✓ | `search.py` | ✅ |
| `GET /api/v1/search/suggest` | ✓ | `search.py` | ✅ |
| `POST /api/v1/upload/token` | ✓ | `upload.py` | ✅ |
| `POST /api/v1/upload/check-duplicate` | ✓ | `upload.py` | ✅ |
| `POST /api/v1/auth/sms/send` | ✓ | `auth.py` | ✅ |
| `POST /api/v1/auth/sms/verify` | ✓ | `auth.py` | ✅ |
| `POST /api/v1/auth/wechat/url` | ✓ | `auth.py` | ✅ |
| `POST /api/v1/auth/wechat/callback` | ✓ | `auth.py` | ✅ |
| `POST /api/v1/auth/refresh` | ✓ | `auth.py` | ✅ |
| `POST /api/v1/auth/logout` | ✓ | `auth.py` | ✅ |
| `GET /api/v1/admin/review-queue` | ✓ | `admin.py` | ✅ |
| `POST /api/v1/admin/review/:material_id` | ✓ | `admin.py` | ✅ |
| `GET /api/v1/admin/reports` | ✓ | `admin.py` | ✅ |
| `POST /api/v1/admin/reports/:id/handle` | ✓ | `admin.py` | ✅ |
| `GET /api/v1/admin/audit-logs` | ✓ | `admin.py` | ✅ |
| `DELETE /api/v1/admin/users/:id` | ✓ | `admin.py` | ✅ |
| `GET /api/v1/homepage` | ✓ | `homepage.py` | ✅ |
| `POST /api/v1/materials/:id/pin` | ✓ | `materials.py` | ✅ |
| `DELETE /api/v1/materials/:id/pin` | ✓ | `materials.py` | ✅ |
| `GET /api/v1/materials/:id/related` | 未在规范中 | `materials.py` | ⚠️ 额外 |

**结论**：API 层覆盖完整。额外端点 `GET /materials/:id/related` 未在 ARCHITECTURE.md 中记录，应补充。

### 3.2 缺失的 Issue 实现

以下 Issue 在代码中有 API 端点或前端页面，但对应的完整验收可能未达成：

| Issue | 声称状态 | 实际差距 |
|---|---|---|
| ISSUE-065 文本 diff 视图 | API 已实现 (`version_diff`) | 前端 `DiffView` 组件未找到，可能未实现 side-by-side diff 渲染 |
| ISSUE-070 失效链接检测 | 外部链接资料展示已实现 | Celery Beat 定时 `HEAD` 检测任务未确认是否存在 |
| ISSUE-112 性能压测 | 未实现 | Locust 脚本不存在 |
| ISSUE-113 全站响应式适配 | 页面已建 | 未逐页验证 375/768/1024/1280 四个断点 |
| ISSUE-119 prefers-reduced-motion | 未实现 | 全局 CSS 规则未找到 |
| ISSUE-120 A11y 审查 | 未实现 | 无 axe-core 扫描记录 |

### 3.3 测试覆盖差距

ARCHITECTURE.md 附录 A 目录结构中列出的测试文件 vs 实际：

| 预期测试文件 | 实际存在 | 差距 |
|---|---|---|
| `test_auth.py` | ✅ 存在 | — |
| `test_courses.py` | ❌ 缺失 | 课程 CRUD、别名搜索、合并 |
| `test_materials.py` | ❌ 缺失 | 资料 CRUD、版本、评分、下载 |
| `test_search.py` | ❌ 缺失 | 搜索 API、ES 同步、中文分词 |
| `test_upload.py` | ❌ 缺失 | 上传 token、安全校验管道 |

前端测试：0 个 vitest 文件，0 个 Playwright E2E 文件。ISSUES.md 中每个 Epic 的最后一个 Issue 都要求"集成测试/E2E 通过"，但实际均未实现。

**这是整个第一阶段最严重的债务**——完整的前端测试和业务层接口测试缺失。

### 3.4 前端组件 vs UI-UX 规范

UI-UX-DESIGN.md §5 定义了 7 个核心组件的详细规格，对照实现：

| 组件 | 规范要求 | 实现状态 |
|---|---|---|
| MaterialCard | 格式图标 + 标题 2 行截断 + 信任徽章 + 元数据行 + 底部评分/下载 | ✅ `MaterialCard.vue` 存在 |
| SearchBar | 两种尺寸(Hero h-14 / 导航 h-10) + debounce 300ms + 补全分类 | ✅ `SearchBar.vue` 存在 |
| TrustBadge | 4 状态 颜色+图标+文字 三重编码 | ✅ `TrustBadge.vue` 存在 |
| RatingWidget | 5 星可交互 + 半星 + 乐观更新 | ✅ `RatingWidget.vue` 存在 |
| FilterPanel | 桌面侧栏 sticky / 移动端 Bottom Sheet | ✅ `FilterGroup.vue` 存在（但移动端 Bottom Sheet 未确认） |
| DropZone | 5 态（Default/DragOver/Selected/Uploading/Error） | ✅ `DropZone.vue` 存在 |
| VersionTimeline | 垂直时间线 + 蓝点当前版本 + 灰色历史 | ❌ **未找到独立组件** |

### 3.5 盲水印实现

ARCHITECTURE.md §6.3 要求所有预览叠加动态盲水印（UUID 后 8 位 + 时间戳，opacity 0.06-0.10）。`useWatermark.ts` composable 存在。需确认是否覆盖全部 4 种预览引擎（PDF Canvas → PDF.js、Office → OnlyOffice API、图片 → OSS 参数、文本/代码 → CSS 伪元素），目前仅 CSS 水印方案可确认。

---

## 四、架构决策风险

### 4.1 高风险：无 PgBouncer 的生产部署

ARCHITECTURE.md §10.2 详细论述了 PgBouncer 的必要性（"若不引入 PgBouncer，期末季弹性扩容新增 ECS 实例时，连接数将直接压垮数据库"）。但 ISSUE-106 标记为 HITL 且未完成。

**影响**：如果 Phase 2 直接上线而不部署 PgBouncer，期末高峰弹性扩容会导致数据库连接数线性增长直至崩溃。

**建议**：Phase 2 必须优先完成 ISSUE-106，并在上线前进行连接池压力测试。

### 4.2 中风险：Elasticsearch 单节点

ARCHITECTURE.md §1.4 MVP 资源规划为 ES 单节点（2C8G）。单节点无副本意味着：
- 节点故障 → 搜索完全不可用
- 无故障转移能力

**建议**：至少在期末季前升级为 3 节点集群（或 2 节点 + 1 个投票专用节点），或接受搜索不可用的风险并在 SLI 中明确标注。

### 4.3 中风险：双轨版本管理的文本 diff 实现质量

PRD §实现决策明确要求"文本与代码类资料支持面向文本的版本历史与差异友好存储"。ISSUE-065（diff 视图）的 API 端点已存在，但 `diff-match-patch` 库对中文文本的差异计算质量未经充分验证。

### 4.4 低风险：潮汐扩容的冷启动

ARCHITECTURE.md §10.4 设计了期末预热机制（提前一周增加至 3 台），但 ISSUE-107（弹性伸缩配置）标记 HITL 未完成。如果不上弹性伸缩而手动扩容，响应速度不足以应对突发流量。

---

## 五、Phase 2 优先级建议

### P0（阻塞上线的关键项）

| 编号 | 内容 | 类型 |
|---|---|---|
| ISSUE-106 | PgBouncer 连接池部署 | HITL — 需运维决策 |
| — | 补充业务层测试：`test_courses.py`、`test_materials.py`、`test_search.py`、`test_upload.py` | AFK |
| — | 补充前端 vitest 测试 | AFK |
| ISSUE-113 | 全站响应式逐页审查与修复 | AFK |
| ISSUE-DOC-2 | 中文隐私政策与用户协议（PIPL 合规上线必需） | HITL — 需法务审核 |

### P1（上线前应完成）

| 编号 | 内容 | 类型 |
|---|---|---|
| ISSUE-107 | 弹性伸缩（ESS）配置 | HITL |
| ISSUE-112 | 性能压测（Locust） | HITL |
| ISSUE-065 | 前端 DiffView 组件（若未完成） | AFK |
| ISSUE-070 | 失效链接定时检测任务 | AFK |
| ISSUE-120 | A11y 审查与修复 | HITL |
| ISSUE-DOC-3 | 生产环境部署文档 | HITL |

### P2（上线后可迭代）

| 编号 | 内容 | 类型 |
|---|---|---|
| ISSUE-119 | prefers-reduced-motion 动效回退 | AFK |
| ISSUE-DOC-1 | 贡献指南与开发者文档 | HITL |
| — | 4 文档一致性修正（见 §2 发现的问题） | AFK |
| — | ARCHITECTURE.md 补充 `GET /materials/:id/related` 端点文档 | AFK |

---

## 六、文档修正清单

基于交叉审计发现的需修正项：

1. **ARCHITECTURE.md §1.2**：将"Redis Streams / RabbitMQ"改为"Celery (Redis broker)"，删除 RabbitMQ 引用或标注为远期可选
2. **ARCHITECTURE.md §6.5 / §9.5**：明确两层下载限制的关系（每小时速率限制 + 每日配额限制），避免维护者误解
3. **ARCHITECTURE.md §11.1**：补充 `GET /api/v1/materials/:id/related` 端点文档
4. **ARCHITECTURE.md §4**：明确 PG GIN 索引与 ES 的职责边界——PG 仅用于课程名本地过滤，ES 是搜索权威引擎
5. **ISSUES.md Epic 11**：将已完成的 ISSUE-105/108/109/110/111 标记为已完成
6. **UI-UX-DESIGN.md §4.5**：补充学期下拉选项的自动生成规则

---

## 七、总结

第一阶段完成了 **87% 的计划 Issue（104/120）**，API 层和前端页面层覆盖完整，架构分层严格遵从 ARCHITECTURE.md 规范。核心用户路径（浏览→搜索→预览→下载→上传→审核）已全部贯通。

**最大的三笔债务**：
1. **测试覆盖严重不足**——无业务层接口测试、无前端单元测试、无 E2E 测试
2. **PgBouncer 未部署**——数据库连接池是潮汐扩容的前提条件
3. **弹性伸缩未配置**——期末高峰靠手动扩容不可行

这三项应在 Phase 2 最高优先级推进。
