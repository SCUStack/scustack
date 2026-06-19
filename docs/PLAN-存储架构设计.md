# 川流课栈 存储架构设计方案

| 字段 | 内容 |
|---|---|
| Type | `plan` |
| Status | `active` |
| Owner | `team` |
| Last Updated | `2026-06-19` |
| Source of Truth | `no` |
| Scope | 低预算阶段文件存储的抽象协议、多后端接入、副本管理和后续迁移路径。 |

> 本文用于细化文件存储专项方案，重点回答“前期没有高耐久对象存储时，如何做到可接入、可迁移、可补副本”。系统级最终口径以 `ARCHITECTURE-技术架构.md` 为准。

## 1. 背景与约束

当前阶段的真实约束：

- 首年预算目标约 `¥400`
- 前期无法默认拥有高耐久、企业级 SLA 的主存储
- 文件来源天然异构：对象存储、改造图床、网盘外链都可能同时存在
- 项目业务真相必须掌握在平台自己手里，不能绑死到某一个第三方后端

当前代码现状：

- 上传链路以 `app/core/oss.py` 为单一存储入口
- `material_versions.storage_key` 直接承载物理存储位置
- `cleanup.py`、`content_extract.py`、缩略图与下载链路均默认只有一个托管后端

这意味着：现状适合快速 MVP，但不适合承载“多终端冗余、可迁移、可修复”的目标。

## 2. 设计目标

### 2.1 目标

- 抽象统一存储协议，支持多种后端接入
- 区分“平台可写入托管存储”和“平台仅引用的外部链接”
- 一份资料允许拥有多个副本，并可记录副本健康状态
- 上传后支持异步补副本，而不是同步阻塞式多写
- 为未来接入正式高耐久对象存储保留平滑迁移路径

### 2.2 非目标

- 不在 v1 阶段实现真正的分布式文件系统
- 不实现多后端强一致写入
- 不承诺所有外部网盘/图床都具备与对象存储等价的 durability
- 不在前期实现跨 provider 双向同步

## 3. 架构原则

- **业务真相归平台**：课程资料的元数据、审核状态、权限状态、下载统计和副本状态都保存在平台数据库中
- **对象存储与外链分层**：托管型存储和引用型存储能力不同，不强行抽成同一语义
- **主链路最短**：用户上传成功的判定只依赖主副本写入成功，其余副本异步补齐
- **可降级**：任一副本失效时可切换到其他健康副本，不因为单一后端故障导致资料整体不可用
- **可迁移**：任何物理存储位置都不能直接写死进业务模型

## 4. 存储后端分层

### 4.1 Managed Storage Provider

由平台主动管理，可执行上传、删除、元数据读取、探活和签名下载。

适用后端：

- 阿里云 OSS / 腾讯云 COS / Cloudflare R2 / Backblaze B2
- 基于 API 的私有上传网关，如 `CloudFlare-ImgBed` 二开实例
- 未来支持的 WebDAV / S3 兼容对象存储

### 4.2 Referenced Storage Provider

平台只持有链接或远端文件标识，不能承诺真实写入和删除。

适用后端：

- 百度网盘、夸克网盘、阿里云盘等分享链接
- 用户提供的外部下载页
- 其他第三方分发链接

### 4.3 设计结论

- 只有 `Managed Storage Provider` 参与“副本数保证”
- `Referenced Storage Provider` 只参与“可访问性检测”和“下载兜底”

## 5. 存储协议

建议新增 `app/core/storage/` 目录，以 provider 协议替代单一 `oss.py` 语义。

### 5.1 核心接口

```python
class ManagedStorageProvider(Protocol):
    provider_type: str
    provider_instance: str

    async def create_upload_target(
        self,
        object_name: str,
        content_type: str,
        file_size: int,
    ) -> UploadTarget: ...

    async def confirm_upload(self, locator: str) -> StoredObjectMeta: ...
    async def delete_object(self, locator: str) -> None: ...
    async def get_download_url(self, locator: str, expires: int = 600) -> str: ...
    async def head_object(self, locator: str) -> StoredObjectMeta | None: ...
    async def healthcheck(self) -> ProviderHealth: ...
```

```python
class ReferencedStorageProvider(Protocol):
    provider_type: str
    provider_instance: str

    async def validate_reference(self, url: str) -> ReferenceMeta: ...
    async def check_reference(self, url: str) -> ReferenceHealth: ...
    async def get_access_url(self, url: str) -> str: ...
```

### 5.2 返回对象约定

- `UploadTarget`：上传地址、表单字段、过期时间、逻辑对象 key
- `StoredObjectMeta`：locator、size、content_type、etag/checksum、last_modified
- `ProviderHealth`：`healthy` / `degraded` / `down`
- `ReferenceHealth`：`alive` / `timeout` / `dead`

## 6. 逻辑文件模型

### 6.1 逻辑对象与物理副本分离

从模型语义上，将“文件”拆成两层：

- **逻辑文件对象**：某个 `material_version` 代表的课程资料版本
- **物理副本**：该版本在某个 provider 上的具体落点

### 6.2 建议新增副本表

```sql
CREATE TABLE material_file_replicas (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    material_version_id UUID NOT NULL REFERENCES material_versions(id) ON DELETE CASCADE,
    provider_type       VARCHAR(50) NOT NULL,
    provider_instance   VARCHAR(100) NOT NULL,
    locator             VARCHAR(2000) NOT NULL,
    access_url          VARCHAR(2000),
    status              VARCHAR(20) NOT NULL DEFAULT 'pending',
    role                VARCHAR(20) NOT NULL,
    checksum            VARCHAR(64),
    file_size           BIGINT,
    content_type        VARCHAR(100),
    last_checked_at     TIMESTAMPTZ,
    failure_count       INTEGER NOT NULL DEFAULT 0,
    meta                JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.3 与现有 `storage_key` 的关系

- `material_versions.storage_key` 在迁移初期保留
- 它只作为兼容字段，指向当前主托管副本的 locator
- 新功能应优先读写 `material_file_replicas`

## 7. 上传、复制与下载流程

### 7.1 上传流程

1. 用户请求上传凭证
2. 平台选择一个 `primary managed provider`
3. 返回直传目标或中转上传目标
4. 用户完成上传
5. 平台创建 `material` / `material_version`
6. 平台插入一条 `primary` 副本记录
7. Celery 异步触发副本复制任务

### 7.2 副本复制流程

1. `replicate_material_version(version_id)` 查询目标副本策略
2. 筛选缺失副本或 `failed` 副本
3. 从当前健康主副本读取源文件
4. 写入目标 provider
5. 校验 `checksum` / `size`
6. 更新 `material_file_replicas.status = ready`

### 7.3 下载解析流程

1. 读取该版本所有 `ready` 副本
2. 按优先级选择：
   - `primary`
   - 同类托管 `replica`
   - `fallback`
   - `external_link`
3. 生成最终访问地址或 302 跳转地址
4. 若主副本失败，记录故障并切换

## 8. 副本策略

### 8.1 v0 低预算策略

- 默认目标副本数：`1`
- 高价值资料目标副本数：`2`
- 外链资料允许只有 `referenced` 记录

### 8.2 v1 稳定化策略

- `primary`: 一个托管型 provider
- `replica`: 第二个托管型 provider 或私有上传网关
- `fallback`: 用户原始外链

### 8.3 为什么不做“所有后端同时写”

- 主链路失败点太多
- 无法保障低质量 provider 的稳定性
- 用户上传体验会被最慢后端拖垮
- 失败补偿和回滚复杂度过高

## 9. 健康检查与修复

### 9.1 定时任务

- `check_storage_replicas`：巡检托管副本元数据和可下载性
- `check_referenced_links`：检查外链是否失效
- `repair_under_replicated_files`：少于目标副本数时自动补副本
- `gc_orphan_replicas`：删除数据库中已解除引用的托管副本

### 9.2 降级规则

- `primary` 失败时切到其他 `ready` 托管副本
- 所有托管副本失败时，如果有外链型 `fallback`，允许继续提供下载
- 若所有副本都不可达，将资料状态标记为 `storage_degraded`，进入后台告警列表

## 10. 与现有业务的关系

### 10.1 内容提取

`content_extract.py` 不应直接依赖 `oss.generate_download_url(storage_key)`，而应通过统一的 `storage_resolver` 获取最佳可读副本。

### 10.2 缩略图与预览

- 缩略图仍可先集中存放在单一托管 provider
- 原始资料文件改由副本解析层决定下载源
- 预览与下载都不再直接绑定单一 OSS 实现

### 10.3 垃圾回收

`cleanup.py` 后续应从“扫描 `materials/` 前缀删孤儿对象”升级为“基于副本表进行引用清理”，避免误删仍被其他 provider 或旧版本引用的对象。

## 11. 分阶段落地

### 阶段 1：抽象层落地

- 新增 `storage` provider 抽象
- 保留现有 `oss.py`，作为 `OSSProvider` 适配器
- 新增 `material_file_replicas` 表

### 阶段 2：双读写兼容

- 上传创建副本记录
- 下载优先走副本解析
- `storage_key` 继续兼容旧逻辑

### 阶段 3：接入第二 provider

- 接入 `CloudFlare-ImgBed` 类托管网关
- 启用异步复制任务
- 对精选资料启用双副本

### 阶段 4：迁移与收敛

- 新代码完全基于副本表
- `storage_key` 降级为兼容字段或迁移删除
- 统一后台存储统计、巡检和修复能力

## 12. 当前建议结论

在低预算前提下，最优解不是“提前拥有完美高耐久存储”，而是：

- 先建立统一存储协议
- 先把文件副本状态掌握在自己库里
- 先支持多后端接入和后续迁移
- 再逐步把高价值资料补成双副本

这能让川流课栈前期使用便宜甚至不稳定的存储后端启动，同时避免未来被某一个图床、网盘或临时对象存储绑死。
