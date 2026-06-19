# 川流课栈文档规范

| 字段 | 内容 |
|---|---|
| Type | `standards` |
| Status | `active` |
| Owner | `team` |
| Last Updated | `2026-06-19` |
| Source of Truth | `yes` |
| Scope | `docs/` 目录下文档的命名、文档头、状态标记和维护规则。 |

> 本文是项目文档规范的主文档，用于统一命名和文档头格式，减少重复、过期和多版本冲突。

## 1. 目标

本规范用于统一 `docs/` 目录下的文档命名、文档头、状态标记和维护方式。

希望解决的问题：

- 文件名风格混乱
- 看不出文档是否过期
- 同一主题存在多个“准权威”版本
- 审计、方案、清单、状态文档边界不清

## 2. 命名规范

### 2.1 总体规则

- 文件名统一使用“英文前缀 + 中文主题”
- 前缀用于表达文档类型，主题使用中文，便于团队直接沟通
- 文件名允许使用英文字母、中文、数字、半角连字符 `-`
- 扩展名统一为 `.md`
- 日期统一使用 `YYYY-MM-DD`
- 长期主文档优先使用固定名，不在文件名里加日期
- 审计、快照、复盘类文档必须带日期

### 2.2 推荐命名模式

长期主文档：

- `PRD-产品需求文档.md`
- `ARCHITECTURE-技术架构.md`
- `DEPLOYMENT-部署手册.md`
- `STANDARDS-文档规范.md`

审计类：

- `AUDIT-<中文主题>-<YYYY-MM-DD>.md`

清单类：

- `CHECKLIST-<中文主题>.md`

方案类：

- `PLAN-<中文主题>.md`

状态类：

- `STATE-<中文主题>.md`

矩阵类：

- `MATRIX-<中文主题>.md`

设计类：

- `DESIGN-<中文主题>.md`

### 2.3 当前文档目标命名

| 当前文件名 | 推荐目标名 |
|---|---|
| `技术架构.md` | `ARCHITECTURE-技术架构.md` |
| `部署手册.md` | `DEPLOYMENT-部署手册.md` |
| `产品需求文档.md` | `PRD-产品需求文档.md` |
| `文档规范.md` | `STANDARDS-文档规范.md` |
| `设计-UI-UX.md` | `DESIGN-UI-UX.md` |
| `清单-上线检查.md` | `CHECKLIST-上线检查.md` |
| `矩阵-反爬策略.md` | `MATRIX-反爬策略.md` |
| `状态-本地体验.md` | `STATE-本地体验.md` |
| `方案-云资源采购.md` | `PLAN-云资源采购.md` |

## 3. 文档头规范

每份文档开头都应包含：

1. 一级标题
2. 文档头元信息表
3. 一段简短用途说明

### 3.1 标准模板

```md
# 文档标题

| 字段 | 内容 |
|---|---|
| Type | `architecture` / `deployment` / `plan` / `audit` / `checklist` / `state` / `matrix` / `design` / `prd` / `standards` |
| Status | `draft` / `active` / `snapshot` / `deprecated` / `superseded` |
| Owner | `team` / 具体负责人 |
| Last Updated | `YYYY-MM-DD` |
| Source of Truth | `yes` / `no` |
| Scope | 一句话描述本文覆盖范围 |

> 1-2 句话说明：这份文档解决什么问题，不解决什么问题。
```

### 3.2 状态取值

- `draft`：草稿
- `active`：当前有效
- `snapshot`：历史快照，仅供参考
- `deprecated`：已弃用
- `superseded`：已被其他文档替代

## 4. 维护规则

- 一个主题只能有一个 `Source of Truth = yes` 的长期主文档
- 历史审计报告不覆盖旧内容，应使用带日期文件保留
- 如果文档已过期但仍需保留，修改 `Status`
- 新增文档前先判断是否应该补充到已有主文档

## 5. 当前执行约定

- 新增文档必须遵守中文命名规范
- 新增文档必须带标准文档头
- 历史快照文档默认不长期保留，确认失效后可直接删除
