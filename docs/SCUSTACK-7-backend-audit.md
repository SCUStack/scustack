# SCUSTACK-7 后端优化探查清单

> 探查范围：`scustack-api`。本文件只记录静态读取证据和可拆分的后续工单，不在本工单修改后端实现。
>
> 证据状态：带“已确认”的内容来自当前工作树实际读取到的文件/行；“待验证”明确标注为需要 CI、`EXPLAIN (ANALYZE, BUFFERS)`、压测或生产指标确认的假设。行号以本次探查时的工作树为准。

## 基线与方法

- `scustack-api` 当前实际存在 **41** 个 `test_*.py` 测试文件（`find tests -type f -name 'test_*.py'`），不是工单描述中的 43 个；测试总量/通过数以 CI 为准，本地按约束未安装依赖、未运行测试。
- 规模基线：`app/api/v1/admin.py` 920 行/41 个路由，`app/services/homepage_service.py` 695 行/9 个异步函数，`app/api/v1/materials.py` 499 行/17 个异步函数。三者的行数和路由数由本次静态命令直接统计确认。
- 仓库约定要求 Router → Schema → Service → Model；后续拆分应保持此边界，不把查询直接搬回 Router。

## 优化清单（按收益 ÷ 风险排序）

### 1. 审核队列 N+1 查询（高收益 / 低风险）

- **问题**：审核队列先查一页材料，再对每条材料单独查课程名。
- **证据（已确认）**：`scustack-api/app/services/review_service.py:18-35`；`items_result` 得到材料后，`for m in materials` 内每次执行 `select(Course.name).where(Course.id == m.course_id)`。页大小上限由 `scustack-api/app/api/v1/admin.py:128-137` 的 `limit <= 50` 可见，因此最坏为 1 次 count + 1 次列表 + 50 次课程查询。
- **影响**：已确认是请求级 N+1；页大小为 N 时查询数为 O(N)。实际延迟和数据库负载待 CI/集成环境用 query counter 与 EXPLAIN 验证。
- **建议改法**：改为一次 `join(Course)` 的投影查询，或 `selectinload`/批量 `Course.id.in_(...)`；保留返回字段和分页契约。新增 service 测试断言返回内容及查询次数。
- **风险**：低；只改读查询和 DTO 拼装。
- **优先级**：P0。
- **测试兜底**：`scustack-api/tests/test_admin.py`、`tests/test_admin_dashboard.py`。

### 2. 举报列表 N+1 查询（高收益 / 低风险）

- **问题**：举报列表逐条查询材料标题。
- **证据（已确认）**：`scustack-api/app/services/report_service.py:35-62`；列表读取 `Report` 后，`for r in reports` 内执行 `select(Material.title).where(Material.id == r.material_id)`。分页上限由 `app/api/v1/admin.py:224-233` 为 50。
- **影响**：最坏 52 次数据库操作（count、列表、每条材料查询）；当材料被删除时还会逐条走空结果。实际 P95 待验证。
- **建议改法**：列表查询直接 outer join `Material` 并投影标题，或批量按 material_id 查询后映射；补充已删除材料的回归用例。
- **风险**：低。
- **优先级**：P0。
- **测试兜底**：`tests/test_admin.py`、`tests/test_security.py`（管理权限/接口行为）。

### 3. 首页推荐每次扫描全量材料并重复计算（高收益 / 中风险）

- **问题**：匿名缓存只缓存推荐 ID，命中后仍查库取材料；个性化推荐完全绕过匿名缓存，每次请求全量扫描并计算。
- **证据（已确认）**：`app/api/v1/homepage.py:27-40` 每个首页请求执行 stats、推荐、recent、hot、presentation 五组工作；`app/services/homepage_service.py:217-225` 和 `:464-472` 都无分页地查询全部 approved 且非 doubtful 材料；`:235-248`/`:481-493` 另查新人和贡献数；`:255-329`/`:506-626` 在 Python 中评分、排序、选择，并逐个 `await bump_exposure`；匿名缓存实现位于 `:347-368`，命中只复用 ID，仍在 `:334-344` 访问数据库。
- **影响**：已确认复杂度随 approved 材料总数增长，而不是随首页 10 个槽位增长；首页还组合多次统计查询。全量规模和 P95 增长曲线待验证。
- **建议改法**：拆出可独立缓存的站点统计、匿名推荐快照和热课程快照；推荐刷新任务预计算候选/ID，个性化路径限制候选集；曝光记录批量写入 Redis pipeline。先用 query counter/固定 fixture 建立基线，再改策略。
- **风险**：中；推荐结果、缓存失效和曝光公平性可能变化。
- **优先级**：P0。
- **测试兜底**：`tests/test_homepage.py`、`tests/test_homepage_presentation.py`、`tests/test_preview_cache.py`（缓存行为的现有测试模式）。

### 4. 材料详情首屏串行多次查询且重复加载材料（高收益 / 中风险）

- **问题**：详情首屏由多个串行查询组成，关联材料接口还重复执行材料详情加载。
- **证据（已确认）**：`app/services/material_service.py:109-135` 的 `get_material` 查询材料后，分别查询 contributor、badge、ratings 分布；`:351-365` 随后再查版本、相关材料、课程名，至少形成 5 个串行数据库阶段；`app/api/v1/materials.py:124-136` 调用首屏服务；相关接口 `:442-456` 先调用 `get_material`，而 `get_material` 本身会计算 badge 和 rating distribution，再查 related。
- **影响**：已确认详情请求存在串行 I/O 和不必要的完整版本列表（之后只取 `versions[:3]`）。重复/串行延迟待用 SQLAlchemy query counter 与接口压测量化。
- **建议改法**：设计一个首屏专用投影查询，使用 join/selectinload 一次装载 contributor/course/前 3 个版本；rating distribution 独立聚合或按需加载；不要让 related 端点加载详情专属字段。先补契约测试再替换查询。
- **风险**：中；MaterialResponse/DetailResponse 依赖 ORM 属性和非映射字段。
- **优先级**：P0。
- **测试兜底**：`tests/test_materials.py`、`tests/test_models.py`。

### 5. 愿望列表用户投票状态 N+1（中高收益 / 低风险）

- **问题**：登录用户查看愿望列表时逐条查询是否投票。
- **证据（已确认）**：`app/services/wish_service.py:54-77` 先取愿望列表，随后在 `for w in wishes` 内对每个 wish 执行 `WishVote` 查询；API 页大小由 `app/api/v1/wishes.py` 的列表契约及 service 默认 `limit=20`（service `:50-52`）约束。
- **影响**：登录用户列表为 1 + N 次查询；`WishVote` 仅有 `wish_id` 单列索引，`user_id` 在 `app/models/wish.py:43-44` 未单列索引，但唯一约束 `(wish_id,user_id)` 对当前 wish_id 驱动查询可用性待 EXPLAIN 验证。
- **建议改法**：一次查询 `WishVote.wish_id`，条件为当前用户和当前页 wish IDs，再用 set 映射；结合 EXPLAIN 决定是否补复合索引。
- **风险**：低。
- **优先级**：P1。
- **测试兜底**：`tests/test_wishes.py`。

### 6. 高访问首页/统计缺少 Redis 缓存（中高收益 / 中风险）

- **问题**：Redis 能力已存在，但首页 stats 和 hot courses 每次请求查库；只有匿名推荐 ID和首页 presentation 做了缓存。
- **证据（已确认）**：`app/core/redis.py:21-31` 提供 `cache_get/cache_set/cache_delete`；`app/services/homepage_service.py:183-197` 的 `get_stats` 每次执行 3 个 count；`:644-684` 的 `get_hot_courses` 执行聚合，缺数据时再查 padding courses，并查询 college 映射；`app/services/homepage_presentation_service.py:20-35` 明确已有 Redis cache，说明能力可复用；首页 `app/api/v1/homepage.py:27-40` 每次调用 stats/hot。
- **影响**：已确认重复数据库工作；请求量、命中率、统计新鲜度目标待产品/生产指标确认。
- **建议改法**：先定义 TTL/失效事件，再为 stats/hot courses 建版本化 key；材料审核、课程、上传等写路径按事件删除或刷新。不要缓存带用户权限的数据。
- **风险**：中；缓存陈旧和失效遗漏会影响展示。
- **优先级**：P1。
- **测试兜底**：`tests/test_homepage.py`、`tests/test_homepage_presentation.py`、`tests/test_config.py`。

### 7. 关键过滤/排序索引覆盖不完整（中高收益 / 中风险）

- **问题**：已有基础索引，但多个高频组合过滤/排序依赖单列索引或无索引字段。
- **证据（已确认）**：`app/models/material.py:21-24,46-50,63-71` 仅明确 course_id、thumbnail_version_id 等单列索引；`alembic/versions/004_create_materials.py:51-54` 有 course、`(review_status,trust_status)`、hash、created_at 索引；首页 recent 在 `homepage_service.py:634-641` 使用 `review_status='approved' ORDER BY created_at DESC`，详情 related 在 `material_service.py:341-348` 使用 course_id + review_status + download_count 排序；审核队列 `review_service.py:18-30` 使用 review_status + created_at；愿望列表 `wish_service.py:54-63` 使用 status/course_id + vote_count/created_at。模型/迁移中未找到这些组合索引的定义。
- **影响**：索引缺口是已确认的“查询形状与现有索引不匹配”，但是否造成 Seq Scan、成本多少必须以目标数据量的 EXPLAIN 证实，不应直接假设收益。
- **建议改法**：先在 CI/基准数据库对四类查询执行 EXPLAIN；只为证实热点新增 Alembic 索引（必要时 partial/composite），并测写入成本与迁移耗时。
- **风险**：中；索引占用空间、写放大和迁移锁风险。
- **优先级**：P1。
- **测试兜底**：`tests/test_migrations.py`、`tests/test_homepage.py`、`tests/test_materials.py`、`tests/test_admin.py`、`tests/test_wishes.py`。

### 8. 阻塞文件/CPU 工作进入请求路径（中收益 / 中风险）

- **问题**：预览缓存清理和文本 diff 的文件/CPU 工作在 async 请求调用链中同步执行。
- **证据（已确认）**：`app/api/v1/materials.py:337-350` 在请求处理内调用同步 `cleanup_cache()`；`app/core/preview_cache.py:32-50` 同步遍历目录、`stat`、`unlink` 并计算总大小；`app/services/material_service.py:371-411` 在 async service 中下载内容后用 `unified_diff`、`splitlines`、截断 diff，CPU/内存随文件内容增长。另有 `app/core/thumbnails.py:52-131` 的 subprocess/PyMuPDF，但其调用点主要位于 `app/tasks/material_tasks.py` Celery 任务，应与请求路径区分，不能误报为当前 API 阻塞。
- **影响**：已确认 event loop 阻塞风险；缓存目录大小、diff 文件大小和并发下延迟待压测验证。
- **建议改法**：将缓存清理放后台任务/受控线程，或限制单次同步工作量；对 diff 做大小上限并用 `asyncio.to_thread`/任务队列承载 CPU 工作；保留超时和响应契约。
- **风险**：中；线程/任务调度、资源上限和超时行为需要设计。
- **优先级**：P1。
- **测试兜底**：`tests/test_materials.py`、`tests/test_preview_cache.py`、`tests/test_thumbnails.py`。

### 9. admin.py 多职责超载拆分（中收益 / 中风险）

- **问题**：一个 Router 模块承载 AI provider、feedback、审核、举报、审计、日历、用户、统计、存储、上传、搜索安全日志、重复检测和 homepage presentation 等互不相关职责。
- **证据（已确认）**：`app/api/v1/admin.py:24-83` AI；`:85-115` feedback；`:126-257` review/report；`:260-332` audit/calendar；`:335-408` users；`:411-731` analytics/storage；`:734-888` upload/search/security/duplicate；`:890-920` material and homepage presentation。共 920 行/41 路由。
- **影响**：已确认单文件变更冲突面大、权限与响应拼装难定位；拆分前后的运行时收益不应假设，维护性收益可由模块大小、测试定位和变更冲突统计验证。
- **建议改法**：按现有 service 边界拆为 `admin/review.py`、`admin/reports.py`、`admin/users.py`、`admin/analytics.py`、`admin/config.py` 等 Router，统一由 `admin/__init__.py` 注册；本子工单只搬运路由和测试，不改变 URL、依赖或响应。
- **风险**：中；路由注册顺序、OpenAPI operationId、导入路径可能变化。
- **优先级**：P1。
- **测试兜底**：`tests/test_admin.py`、`tests/test_admin_dashboard.py`、`tests/test_main.py`。

### 10. homepage_service.py 职责拆分（中收益 / 中风险）

- **问题**：首页 service 同时负责统计、推荐算法、Redis exposure、匿名缓存、个性化 affinity、分页 feed、热课程和日历展示标签。
- **证据（已确认）**：`app/services/homepage_service.py:183-197` stats；`:200-331` 推荐打分/槽位/曝光；`:334-368` 缓存；`:374-440` affinity；`:443-628` 个性化推荐；`:631-684` recent/hot courses；总 695 行。
- **影响**：算法、缓存和简单 feed 变更共享同一大文件；当前无运行时收益结论，维护性风险由测试修改范围和依赖图验证。
- **建议改法**：切成 `homepage_stats_service`、`recommendation_service`、`homepage_feed_service`，先保持原 public API 或在 facade 中转发；每个子模块一次只迁移一类职责，并逐步补充 query-count/cache-hit 测试。
- **风险**：中；函数间共享常量和缓存 key 需保持兼容。
- **优先级**：P2（先完成 P0 查询问题后）。
- **测试兜底**：`tests/test_homepage.py`、`tests/test_homepage_presentation.py`。

### 11. materials.py 路由层职责过重、重复授权与响应拼装（中收益 / 中风险）

- **问题**：materials Router 同时处理材料 CRUD、上传消费、版本、下载、预览缓存、相关材料、举报、置顶；并重复执行 owner/admin 判断和 `MaterialResponse.model_validate(...).model_dump(...)`。
- **证据（已确认）**：文件 499 行/17 路由；`app/api/v1/materials.py:40-47` 定义 `_can_access_material`，但 `:89-91`、`:104-106`、`:131-136`、`:298`、`:327`、`:433` 等多处再组合访问检查；`:74`、`:91`、`:199`、`:219`、`:456` 等重复响应转换；版本创建 `:395-422` 和材料创建 `:140-195` 还混合存储、数据库和 Celery 触发。
- **影响**：已确认授权/响应契约重复点；重复代码本身不等于 bug，需通过静态 AST 计数和回归测试确认拆分收益。
- **建议改法**：先抽 service 层的 owner/admin authorization helper 和 response adapter；再按 `materials_public`、`materials_mutation`、`material_versions` 拆 Router。不要在本子工单同时改变权限语义。
- **风险**：中高；材料访问和下载是安全敏感路径。
- **优先级**：P2。
- **测试兜底**：`tests/test_materials.py`、`tests/test_security_hardening.py`、`tests/test_upload.py`、`tests/test_upload_pipeline.py`。

### 12. 审计/统计查询索引与聚合专项（中收益 / 中风险）

- **问题**：后台统计在单请求内串行执行多次聚合，审计 JSONB 查询缺少与访问形状对应的复合索引证据。
- **证据（已确认）**：`app/api/v1/admin.py:413-444` analytics 先调用 3 次 stats 查询，再查询 pending review/report；`:448-503` trends 执行 uploads、users、category 三次聚合；`:736-774` upload-stats 执行 format/source/review 三组统计和 contributors；`:789-804` 按 `AuditLog.detail['query'].astext` 分组；模型 `app/models/audit_log.py:14-28` 未定义 action/created_at/detail 的模型索引，但迁移 `009_create_review_reports_audit.py:71-73` 有 action、created_at 单列索引。
- **影响**：已确认管理统计请求有多次串行 round-trip；具体是否成为线上热点待访问日志确认。JSONB 分组成本待 EXPLAIN 验证。
- **建议改法**：独立后台 analytics service；在确认访问量后合并可合并聚合、增加时间窗口条件；为高频审计查询设计索引或汇总表。不要把低频后台统计和首页缓存混为同一子工单。
- **风险**：中。
- **优先级**：P2。
- **测试兜底**：`tests/test_admin_dashboard.py`、`tests/test_admin.py`、`tests/test_observability.py`。

## 测试覆盖与安全边界

已确认有直接测试的模块/路径：

- 首页/推荐/首页配置：`tests/test_homepage.py`、`tests/test_homepage_presentation.py`。
- 材料/上传/预览缓存/缩略图：`tests/test_materials.py`、`tests/test_upload.py`、`tests/test_upload_pipeline.py`、`tests/test_preview_cache.py`、`tests/test_thumbnails.py`。
- 搜索：`tests/test_search.py`、`tests/test_search_pressure.py`。
- 管理/仪表盘/迁移/模型：`tests/test_admin.py`、`tests/test_admin_dashboard.py`、`tests/test_migrations.py`、`tests/test_models.py`。
- 愿望/用户/课程/报告相关接口覆盖分散在 `tests/test_wishes.py`、`tests/test_users.py`、`tests/test_courses.py` 等。

本次文件名扫描未发现与以下 service 同名的专门测试文件，后续修改前必须先补最小 service 测试或明确由接口测试兜底：`report_service.py`、`review_service.py`、`material_service.py`、`about_service.py`、`badge_service.py`、`collection_service.py`、`comment_service.py`、`audit_service.py`。这表示“没有专门文件”，不表示完全没有间接覆盖；是否覆盖到具体分支需 CI coverage/pytest collection 确认。

不应在没有测试的情况下直接做的高风险变更：材料访问权限、下载/预览、审核状态流转、缓存失效语义、推荐排序语义、Alembic 索引迁移。查询优化子工单应先固定响应契约和 query-count/SQL 形状测试。

## 建议子工单与依赖关系

统一叠加到长期分支 `feat/SCUSTACK-7-backend-audit`（或项目经理指定的等价优化分支），不各自向 `main` 开 PR。

1. **SCUSTACK-7.1 审核队列批量课程查询**：P0、低风险。无前置；先做，作为 N+1 的模板。
2. **SCUSTACK-7.2 举报列表批量材料查询**：P0、低风险。无前置；可与 7.1 并行，但合并时跑 admin 回归。
3. **SCUSTACK-7.3 愿望投票状态批量查询**：P1、低风险。无前置；与 7.1/7.2 独立。
4. **SCUSTACK-7.4 材料详情首屏查询整合**：P0、中风险。依赖先确认 `tests/test_materials.py` 当前契约；建议在 7.1/7.2 后做，避免同时处理多个查询形状。
5. **SCUSTACK-7.5 首页推荐基准与预计算/缓存**：P0、中风险。依赖 7.4 的材料响应基线和新增 query-count fixture；先测量再改缓存/算法。
6. **SCUSTACK-7.6 高频查询 EXPLAIN 与 Alembic 组合索引**：P1、中风险。依赖 7.1–7.5 的最终 SQL 形状；否则可能为即将改变的查询错误建索引。
7. **SCUSTACK-7.7 async 请求阻塞工作隔离**：P1、中风险。依赖 `test_materials`/preview cache 回归基线；与索引工作可并行，但不要混在详情重构提交中。
8. **SCUSTACK-7.8 admin Router 按职责拆分**：P1、中风险。依赖 admin 测试基线；只搬运路由，不改 service/query。
9. **SCUSTACK-7.9 homepage service 按职责拆分**：P2、中风险。依赖 7.5 稳定缓存/推荐契约；保留 facade 后再逐块迁移。
10. **SCUSTACK-7.10 materials Router 授权/响应适配器与子 Router**：P2、中高风险。依赖材料详情和权限回归（7.4、7.7）；最后做以减少安全路径同时变化。
11. **SCUSTACK-7.11 后台 analytics 聚合专项**：P2、中风险。依赖访问日志和 EXPLAIN 证据；若确认不是热点则降级为维护性拆分。

## CI 可验证验收矩阵

每个后续子工单必须在 CI 至少执行：

```text
cd scustack-api
pytest tests/test_admin.py tests/test_admin_dashboard.py   # 管理/审核/举报子工单
pytest tests/test_wishes.py                                # 愿望子工单
pytest tests/test_materials.py tests/test_preview_cache.py tests/test_upload.py tests/test_upload_pipeline.py
pytest tests/test_homepage.py tests/test_homepage_presentation.py
pytest tests/test_migrations.py
ruff check .
pyright
```

查询优化子工单另需在 CI/专用 PostgreSQL fixture 输出 query-count 断言；索引子工单需输出迁移成功和目标 SQL 的 `EXPLAIN` 结果。首页缓存/推荐子工单需断言 cache hit、cache miss、Redis 不可用降级和推荐结果契约。以上是建议的可验证证据，不代表本工单本地已运行；本地按工单约束只做静态检查。
