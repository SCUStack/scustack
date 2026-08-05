# 上线前安全与质量审计报告

审计日期：2026-08-04

范围：`scustack-api` FastAPI 服务、`scustack-web` Nuxt/Vue 应用、上传与资料版本链路、生产配置与构建门禁。

## 执行摘要

本次审计发现的问题已完成一轮上线前修复：生产默认关闭调试并禁用生产文档端点；托管文件统一走受信上传票据和副本解析层；待审核资料及其版本差异不再对匿名用户公开；公开健康检查不再泄露依赖状态。当前可以进入部署验证，但仍需满足本报告末尾的外部依赖与基础设施验收项。

## 本轮修复状态

- 已修复 SEC-001：`DEBUG` 默认关闭，生产环境若开启调试或未配置可信 Host 将拒绝启动。
- 已修复 SEC-002 与 SEC-004：新增用户绑定、大小绑定、15 分钟有效且原子单次消费的上传票据；浏览器仅向本平台上传，LFS Token 不会离开后端；版本创建同样必须消费受信上传对象。
- 已修复 SEC-003：资料详情、下载和版本差异只公开已审核资料；资料所有者、维护者和管理员可访问待审核内容。
- 已修复 SEC-006 与 SEC-008：生产禁用 OpenAPI/Swagger/ReDoc；CORS 保持显式来源并放行 `X-CSRF-Token`。
- 已部分修复 SEC-005 与 SEC-007：公网 `/health` 仅返回 liveness，成本快照要求 `audit:read`；生产必须提供 `TRUSTED_HOSTS`，应用会注册 `TrustedHostMiddleware`。
- 已优化故障降级：Redis 连接和读写超时默认收紧至 `200ms`，可通过 `SCUSTACK_REDIS_CONNECT_TIMEOUT_SECONDS` 覆盖，限流与搜索可更快进入既有降级策略。

## Critical

### SEC-001：生产环境默认开启调试并向客户端回显异常

- 规则 ID：FASTAPI-DEPLOY-002
- 位置：[scustack-api/app/core/config.py](scustack-api/app/core/config.py) `Settings.DEBUG`（第 9 行）；[scustack-api/app/main.py](scustack-api/app/main.py) `global_exception_handler`（第 102-121 行）
- 证据：`DEBUG: bool = True`；全局异常处理在 `settings.DEBUG` 时返回 `detail: str(exc)`，生产启动检查只验证三个密钥的默认值，不验证 `DEBUG`。
- 影响：只要部署者设置 `SCUSTACK_APP_ENV=prod` 而遗漏 `SCUSTACK_DEBUG=false`，任意未处理异常都会向攻击者泄露 SQL、路径、第三方服务和业务内部信息。
- 修复：生产配置默认 `DEBUG=False`，并在 `APP_ENV == 'prod' and DEBUG` 时拒绝启动；保持生产错误响应为固定信息。
- 缓解：在入口网关统一替换 5xx 响应不能代替应用层修复。
- 误报说明：无。配置逻辑可独立复现。

## High

### SEC-002：资料新版本绕过对象校验、扫描和审核状态

- 规则 ID：FASTAPI-FILES-001、FASTAPI-AUTHZ-001
- 位置：[scustack-api/app/api/v1/materials.py](scustack-api/app/api/v1/materials.py) `create_version`（第 268-288 行）；[scustack-api/app/services/material_service.py](scustack-api/app/services/material_service.py) `add_version`（第 167-195 行）
- 证据：首次创建资料会调用 `verify_uploaded_object` 并排队 `virus_scan`，但 `create_version` 只验证资料所有者后将客户端提交的 `storage_key`、`file_hash` 和 `file_size` 直接写入。`add_version` 不改变 `review_status`，下载接口又总是取最新版本。
- 影响：已获审核通过资料的贡献者可将任意 `materials/` 前缀对象设为最新版本，绕过大小/格式核验、病毒扫描、内容预审和重新审核后立即向其他用户分发。
- 修复：将版本提交收敛到与首次上传相同的服务流程：校验对象归属、存在性、大小、格式及哈希；设为待审核；在提交后排队病毒扫描和内容预审；只有审核通过的版本可以成为公开下载版本。
- 缓解：上线前临时关闭版本创建入口，或仅向管理员开放。
- 误报说明：无。当前代码路径没有调用这些保护措施。

### SEC-003：版本差异接口公开返回存储对象文本内容

- 规则 ID：FASTAPI-AUTHZ-001、FASTAPI-RESP-001
- 位置：[scustack-api/app/api/v1/materials.py](scustack-api/app/api/v1/materials.py) `version_diff`（第 291-297 行）；[scustack-api/app/services/material_service.py](scustack-api/app/services/material_service.py) `get_version_diff`（第 241-304 行）
- 证据：路由没有认证或对象级授权；服务为任意版本生成签名下载 URL、读取前后两个对象，并将最多 500 行 diff 返回。资料详情接口也只排除 `removed` 状态而不排除 `pending`（第 318-333 行）。
- 影响：知道资料和版本 UUID 的未登录用户可读取文本资料内容，包括待审核资料和历史版本；UUID 不是授权检查。
- 修复：公开访问仅允许已审核的公开版本；待审核或已移除资料仅允许资料所有者和具备审核权限的人员访问。将版本内容读取和差异计算放在同一授权服务中，并为该场景添加匿名、所有者、审核员三类测试。
- 缓解：在修复前禁用公开 `/versions/{version_id}/diff` 路由。
- 误报说明：无。该路由没有 `Depends(get_current_user)` 或审核状态判断。

### SEC-004：预签名上传令牌没有实际配额或频率控制

- 规则 ID：FASTAPI-LIMITS-001
- 位置：[scustack-api/app/api/v1/upload.py](scustack-api/app/api/v1/upload.py) `request_upload_token`（第 13-22 行）；[scustack-api/app/services/upload_service.py](scustack-api/app/services/upload_service.py) `generate_upload_token`（第 63-67 行）；[scustack-api/app/core/oss.py](scustack-api/app/core/oss.py) `generate_upload_token`（第 19-41 行）
- 证据：`DAILY_UPLOAD_LIMIT` 与 `check_storage_quota` 已定义，但未被任何路由调用。一个已登录账号可持续请求 200 MB 的预签名 PUT URL。孤儿对象只在 30 天后、每周清理一次。
- 影响：攻击者可在清理宽限期内消耗 OSS 存储、带宽和对象数量配额，形成可计费拒绝服务。
- 修复：令牌签发前按用户在 Redis 中原子限流并计入保留配额；令牌和对象键与用户、大小、过期时间绑定；将未完成上传的对象生命周期缩短到数小时；成功创建资料后再确认使用额度。
- 缓解：在 OSS Bucket 配置对象生命周期、预算告警和每账号 PUT 限制。
- 误报说明：现有周度孤儿清理降低长期残留，但不能限制 30 天窗口内的写入。

## Medium

### SEC-005：公开健康检查泄露依赖状态与实时业务负载

- 规则 ID：FASTAPI-RESP-001
- 位置：[scustack-api/app/api/v1/health.py](scustack-api/app/api/v1/health.py) `health_check`（第 13-65 行）、`cost_baseline`（第 95-102 行）
- 证据：匿名请求可获知运行环境、数据库、Redis、Elasticsearch、ClamAV 和 OSS 状态；`cost-baseline` 返回进程启动以来的请求计数与延迟分位数。
- 影响：攻击者可据此识别组件、观察负载、选择攻击窗口，并将健康依赖检查放大为昂贵的匿名探测。
- 修复：仅保留无详情的公网 liveness；将 readiness、依赖详情与成本快照限制到内网或 `AUDIT_READ` 权限；为探测端点配置轻量缓存和限流。
- 缓解：在入口网关按来源 IP/网络策略隔离详细健康检查。
- 误报说明：若生产负载均衡器已隔离这些路由，影响会降低；仓库内没有该配置。

### SEC-006：生产 OpenAPI、Swagger 与 ReDoc 默认公开

- 规则 ID：FASTAPI-OPENAPI-001
- 位置：[scustack-api/app/main.py](scustack-api/app/main.py) `FastAPI(...)`（第 42-47 行）
- 证据：未按环境覆盖 `docs_url`、`redoc_url`、`openapi_url`，FastAPI 将使用公开默认值。
- 影响：完整暴露管理端、权限端点和请求模型，降低攻击者枚举成本。
- 修复：生产禁用文档端点，或置于认证和内网网关之后；非生产环境保持开发体验。
- 缓解：通过反向代理拒绝 `/docs`、`/redoc`、`/openapi.json`。
- 误报说明：若边缘已限制这些路径则不构成公网暴露，需部署时验证。

### SEC-007：缺少可配置的 Host 头校验

- 规则 ID：FASTAPI-HOST-001
- 位置：[scustack-api/app/main.py](scustack-api/app/main.py) 中间件注册；[scustack-api/app/middleware/anti_proxy.py](scustack-api/app/middleware/anti_proxy.py)（第 7-66 行）
- 证据：应用没有 `TrustedHostMiddleware`。`AntiProxyMiddleware` 校验的是浏览器 `Origin`/`Referer` 的硬编码主机名，不校验 HTTP `Host`。
- 影响：若入口层没有主机白名单，畸形 Host 头可污染基于请求 URL 的生成逻辑、缓存和日志。
- 修复：新增从环境读取的允许主机列表并使用 `TrustedHostMiddleware`；反向代理也应拒绝未知 Host。
- 缓解：在 CDN/Ingress 中配置同等 Host allowlist。
- 误报说明：应用代码没有基于 Host 生成敏感回调 URL；风险取决于基础设施配置。

### SEC-008：前端 CSRF 请求头未列入 CORS allowlist

- 规则 ID：VUE-CSRF-001、FASTAPI-CORS-001
- 位置：[scustack-web/plugins/csrf.client.ts](scustack-web/plugins/csrf.client.ts)（第 30 行）；[scustack-api/app/main.py](scustack-api/app/main.py) CORS 配置（第 57-63 行）
- 证据：前端对有认证 Cookie 的写请求自动加入 `X-CSRF-Token`，但后端仅允许 `Content-Type` 和 `X-Requested-With`。前后端跨源部署时浏览器预检将拒绝该头。
- 影响：登录后的跨源写操作会在浏览器层失败，属于上线可用性阻断；测试中的 fetch mock 未覆盖真实预检。
- 修复：在严格来源白名单不变的前提下增加 `X-CSRF-Token`，并用真实浏览器 E2E 覆盖登录后的 POST/PATCH/DELETE。
- 缓解：同源部署可暂时避开预检，但不应作为唯一部署前提。
- 误报说明：若 Nuxt 与 API 完全同源，CORS 不参与请求；当前默认端口和 `apiBase` 配置显示两者可跨源运行。

## 发布治理与优化项

1. 后端全量测试已按两个互不重叠的执行组完成：`190 passed` 与 `150 passed`，合计 `340 passed`。单命令运行仍受本地执行窗口限制，CI 应保留分组、junit 报告和合理总时限。
2. `ruff check app tests` 报告 979 项问题，其中大量 `B008` 是 FastAPI 的依赖注入惯用写法，不应机械修复；仍应建立项目级 ruff 忽略策略并清理真实的未使用导入、重复导入和长行，避免上线前噪声掩盖缺陷。
3. 前端 20 个 Vitest 文件、67 项测试已通过，但 `useInfiniteScroll` 和 `useKeyboardShortcuts` 测试有 Vue 生命周期警告。应使用组件挂载环境测试 composable，防止测试通过而运行时生命周期错误。
4. `pnpm audit --prod` 无法运行，因为当前 `.npmrc` 指向的镜像站未实现 audit API；`pip-audit` 在 124 秒内超时。CI 应使用支持审计接口的 registry 或生成 SBOM 后交由独立扫描器检查依赖漏洞。
5. `pnpm --dir scustack-web build:guard` 在 124 秒内超时，未得到成功构建证据。将构建和体积门禁移至资源受控的 CI 任务，保留构建日志和产物大小基线。

## 已验证的控制

- JWT 解码固定了算法白名单；访问和刷新令牌使用 HttpOnly Cookie，写请求有双提交 CSRF 校验。
- CORS 使用显式来源而非通配符；SQL 原生语句使用绑定参数。
- 首次托管资料创建包含对象大小/格式验证，并提交病毒扫描与内容预审任务。
- 前端代码高亮由 Shiki 生成，资料卡片搜索高亮先转义用户标题；未发现 `eval`、`new Function`、`document.write` 或令牌写入 `localStorage` 的生产代码路径。

## 修复顺序与验收

1. SEC-001：以 `APP_ENV=prod`、`DEBUG` 未显式设置启动，进程必须拒绝启动；生产 500 响应不得包含异常文本。
2. SEC-002：已审核资料提交新版本后不得立即公开下载；对象校验、病毒扫描、预审和审核完成前返回受控状态。
3. SEC-003：匿名用户不能读取待审核/已移除资料或版本差异；所有者和审核员按权限访问。
4. SEC-004：单账户无法无限签发上传 URL；过期未绑定对象按短生命周期删除。
5. SEC-005 至 SEC-008：在真实 HTTPS、跨源和反向代理环境执行 Playwright 冒烟测试，并保存响应头、CORS 预检和访问控制结果。
