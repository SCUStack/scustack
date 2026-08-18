# 川流课栈上线前全链路验收报告

> 验收日期：2026-08-18  
> 验收环境：Windows 本地开发环境，Nuxt 3 + FastAPI + PostgreSQL 16 + Redis 7 + Elasticsearch 8  
> 结论：核心用户链路和 LFS 文件链路已通过，可继续进入 staging；尚不建议直接进入生产环境。

## 1. 验收摘要

| 领域 | 结果 | 说明 |
| --- | --- | --- |
| 基础设施 | 通过 | PostgreSQL、Redis、Elasticsearch 容器均为 healthy |
| 前后端服务 | 通过 | 前端 `http://localhost:3000`，API `http://localhost:8403` |
| 身份认证 | 通过 | 普通学生账号真实登录成功 |
| 搜索 | 通过 | 搜索“高等数学”返回 54 条结果 |
| 资料上传 | 通过 | LFS 真实上传成功，上传后进入“审核中” |
| 管理审核 | 通过 | 维护者审核通过，待审列表查询问题已修复 |
| 在线预览 | 通过 | 真实 TXT 内容可预览，鉴权和跨域问题已修复 |
| 资料下载 | 通过 | Relay 32 下载 102 字节文件，SHA-256 与原文件一致 |
| 文件删除 | 通过 | LFS 删除返回 200，删除后文件 URL 返回 404 |
| 管理分析 | 通过 | 安全监控与趋势分析页面均正常 |
| 移动端 | 通过 | 390 x 844 视口无明显遮挡或错位 |
| 自动化测试 | 通过 | 后端 347 项，前端 72 项，Playwright 全量 30 项，全部通过 |
| 可访问性 | 通过（仓库内专项） | 12 项 axe WCAG A/AA 与键盘 Skip Link 检查通过 |
| 类型检查 | 通过 | `vue-tsc --noEmit` 通过 |
| 生产构建 | 通过 | Nuxt/Nitro node-server 构建成功 |
| 生产就绪 | 阻塞 | 存在密钥、数据库、容量、监控、备案和演练项 |

## 2. 上线清单逐项验收

### 2.1 自动化门禁

| 清单项 | 结果 | 当前证据 |
| --- | --- | --- |
| 前端类型检查 | 通过 | `pnpm typecheck` 退出码 0 |
| 前端单元/组件测试 | 通过 | 24 个测试文件、72 项测试通过 |
| 后端测试全集 | 通过 | 347 项测试通过 |
| 反爬、首页配置、搜索专项 | 通过 | 指定的 3 个测试文件共 33 项通过 |
| 浏览器关键路径 | 通过 | Chromium 串行执行 30 项通过 |
| WCAG A/AA 与键盘专项 | 通过（本地） | 12 项 axe/Skip Link 检查通过 |
| 生产构建 | 通过 | Nuxt/Nitro node-server 构建成功 |
| 生产 Compose 解析 | 通过 | 必需变量注入后 `docker compose ... config --quiet` 通过 |

### 2.2 人工与运行时冒烟

| 清单项 | 结果 | 当前证据 |
| --- | --- | --- |
| 首页横幅与近期更新 | 通过（本地） | 真实首页渲染；首页与 recent-updates API 返回 200 / code 0 |
| 普通搜索 | 通过（本地） | “高等数学”搜索返回 200，实际返回 54 条结果 |
| 高风险匿名搜索挑战 | 通过（本地） | 快速深翻页返回 HTTP 429、业务码 `42920`、level `challenge` |
| 登录与鉴权写操作 | 通过（本地） | 普通学生和维护者真实登录；上传、审核操作成功 |
| 托管上传保持 pending | 通过（真实 LFS） | 上传完成后保持“审核中”，未提前公开 |
| 管理审核通过资料 | 通过（本地） | 维护者审核后资料转为 approved |
| 托管下载 | 通过（真实 LFS） | Relay 32 下载成功，SHA-256 与原文件一致 |
| 安全监控展示保护事件 | 通过（本地） | 触发挑战后，维护者页面显示“搜索验证触发”和 `search_query` |
| Office 文件处理 | 条件通过 | 已移除生产 localhost 硬编码；配置网关时生成预览 URL，MVP 未配置时明确提示并提供鉴权下载。目标网关尚未部署 |
| 三个健康端点 | 通过（本地） | `/health`、`/health/live`、`/health/ready` 均返回 200 |

以上“本地”结果不能替代 Section 7 中要求的 staging/生产候选环境复验。

## 3. LFS 存储验收

- `SCUSTACK_STORAGE_DEFAULT_PROVIDER` 已设为 `lfs`。
- `SCUSTACK_LFS_API_TOKEN` 已填写；本报告不记录、不回显 Token。
- OSS Access Key、Secret、Endpoint 和 Bucket 均未配置，当前链路不依赖阿里云 OSS。
- 上传、审核、预览、下载和删除均使用真实 LFS 服务完成，不是 mock。
- 下载后对文件进行 SHA-256 校验，与上传原文件一致。
- 验收资料、LFS 文件和本地临时文件已清理，数据库中测试资料剩余 0 条。

## 4. 本轮发现并修复的问题

1. 管理员趋势分析接口缺少 `Material` 导入，真实页面请求返回 500。已补充导入和回归测试。
2. 待审页在“待审核”标签下传送空 `status` 查询参数，后端返回 422，前端误显示 0 项。现在待审状态不发送该参数。
3. 文本预览未携带登录 Cookie，且没有拦截非 2xx 响应。已增加 `credentials: 'include'` 和状态检查。
4. LFS Relay 32 重定向与浏览器 CORS 冲突。新增受控预览接口 `GET /api/v1/materials/{id}/preview`，后端下载并返回文件，限制 25 MB，响应后自动删除临时文件。
5. Redis 下载计数增量直接赋给 ORM 字段，触发 autoflush 和 `MissingGreenlet`。已改为 `set_committed_value`，资料列表和详情恢复 200。
6. Alembic 存在重复 revision `030`。文件已调整为 `031_create_material_file_replicas.py`，迁移链现在只有一个 head `031`，并新增迁移历史回归测试。
7. 生产配置此前仅校验默认值；现在 JWT 密钥、应用加密密钥和数据库密码均增加最小长度校验，弱密钥会在启动时拒绝。
8. 补齐关键页面的可访问性细节：文档语言、表单标签、星级按钮名称、键盘 Skip Link、焦点入口、滚动区域语义和正文链接对比度。
9. Office 预览服务地址硬编码为 `localhost:8088`，生产浏览器会请求用户本机。现在改用 `NUXT_PUBLIC_OFFICE_PREVIEW_BASE`；生产未配置时显示可操作的下载降级状态，并新增组件和浏览器发布门禁测试。
10. 微调高频交互：搜索框增加搜索键盘提示与组合框语义；桌面头像点击直接绑定按钮；登录弹窗打开后自动聚焦，支持 Esc 关闭，并补齐自动填充、关闭按钮和模式状态语义。

## 5. 自动化验证证据

| 命令 | 结果 |
| --- | --- |
| `cd scustack-api && pytest -q` | `347 passed` |
| `cd scustack-web && pnpm test` | `24 passed` 测试文件，`72 passed` 测试 |
| `cd scustack-api && pytest -q tests/test_anti_scraping_regression.py tests/test_homepage_presentation.py tests/test_search.py` | `33 passed` |
| `cd scustack-web && pnpm exec playwright test e2e/accessibility.spec.ts --project=chromium --reporter=line --retries=0` | `12 passed`，包含 axe WCAG A/AA 与键盘 Skip Link |
| `cd scustack-web && pnpm exec playwright test --project=chromium --reporter=line --retries=0` | `30 passed`，串行执行 |
| `cd scustack-web && pnpm typecheck` | 通过，退出码 0 |
| `cd scustack-web && NUXT_IGNORE_LOCK=1 pnpm build` | Nuxt/Nitro 生产构建成功，退出码 0 |
| `docker compose -f docker-compose.yml -f docker-compose.production.yml config --quiet` | 注入必需验证变量后通过 |
| `git diff --check` | 通过，无空白错误 |
| Alembic ScriptDirectory 测试 | 单一 head `031`，revision 无重复 |

说明：第一次将 `pnpm typecheck` 与 `pnpm build` 并行执行时，两者同时改写 `.nuxt` 生成目录，产生了短暂的生成类型报错。构建完成后单独重跑 `pnpm typecheck` 退出码为 0，确认不是源码类型回归。

## 6. 已知质量债务

- Pyright 全库检查存在 949 个历史类型错误。它们不是本轮修复引入，但应分模块逐步清理并纳入 CI 基线。
- Ruff 存在较多历史格式和 lint 问题。不建议在上线前一次性批量修复，以免扩大变更面。
- Vitest 中少量 composable 测试会输出 Vue 生命周期警告，测试仍通过，建议后续用组件容器挂载这些 composable。
- 生产构建包含依赖库注释和 deprecated exports 警告，未影响构建成功。

## 7. 生产上线阻塞项

| 优先级 | 阻塞项 | 完成标准 |
| --- | --- | --- |
| P0 | 生产密钥仍需由部署方注入 | 生成强随机 `SCUSTACK_JWT_SECRET_KEY`、`SCUSTACK_ENCRYPTION_KEY`，并使用长度满足要求的数据库密码，注入部署密钥管理 |
| P0 | PostgreSQL 仍使用开发默认密码 | 更换数据库用户密码，同步部署配置并验证连接 |
| P0 | 未做 staging 回滚演练 | 验证数据库备份恢复、Alembic 升降级和应用版本回滚 |
| P1 | PgBouncer 未完成 | 生产连接池接入并通过并发连接验证 |
| P1 | Elasticsearch 仍是本地单节点配置 | 完成生产容量、副本、持久化、备份和访问控制配置 |
| P1 | 未做真实负载测试 | 使用预期峰值对登录、搜索、详情、上传和下载链路压测 |
| P1 | Sentry DSN 未配置 | 生产错误能够上报、分组并触发告警 |
| P1 | ICP/公安备案仍为占位文本 | 获得正式备案号并替换全站展示内容 |
| P2 | 正式目标环境无障碍审查未完成 | 仓库内关键页面专项已通过；仍需在 staging/生产候选环境完成人工键盘、焦点、语义、对比度和读屏审查 |

截至验收时，GitHub Issue `#106`、`#107`、`#112`、`#120`、`#223` 均仍为 OPEN，未获得发布负责人书面豁免。

## 8. 上线建议

1. 先更换 JWT 和数据库密钥，不应将密钥提交到 Git。
2. 使用 `docker-compose.production.yml` 部署 staging，完成数据库迁移、回滚、备份恢复和真实 LFS 再验证。
3. 完成 PgBouncer、Elasticsearch 生产配置、Sentry 告警和关键链路负载测试。
4. 备案信息和无障碍审查完成后，再执行一次与本报告同范围的生产候选版本验收。
