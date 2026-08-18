# 川流课栈

川流课栈（SCU Course Stack）是面向四川大学学生的公益型课程资料共享平台。项目围绕“学院 -> 课程 -> 学期 -> 资料分类”组织资料，帮助同学更高效地查找、贡献、评价和维护课程相关内容。

**公益 · 无广告 · 开源 · 面向长期共建**

[![CI](https://github.com/SCUStack/scustack/actions/workflows/pr-checks.yml/badge.svg)](https://github.com/SCUStack/scustack/actions/workflows/pr-checks.yml)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)

## 项目目标

很多课程资料长期散落在群聊、网盘、个人收藏夹和往届同学的硬盘里。川流课栈希望把这些资料整理成可检索、可维护、可审核的公共知识基础设施：

- 让新同学少走弯路，快速找到对应课程的可靠资料
- 让贡献资料的同学获得明确署名、反馈和长期价值
- 让学院、课程、学期、资料类型形成清晰目录
- 用审核、举报、版权投诉和信任标记降低滥用风险
- 在可负担的成本内，把公益项目做成可持续维护的系统

## 核心功能

- 课程目录：按学院、课程、学期组织课程资料
- 资料检索：支持关键词搜索、分类筛选、排序和热门推荐
- 资料详情：展示简介、课程归属、下载信息、评分、评论和相关资料
- 资料上传：支持托管文件和外部链接两种模式
- 在线预览：支持 PDF、图片、文本、代码和 Office 文档的分级预览
- 信任体系：维护者精选、社区验证、未验证、存疑四类状态
- 用户中心：贡献记录、收藏、徽章、隐私设置和账号管理
- 心愿系统：提交资料需求，社区投票和认领补全
- 管理后台：资料审核、举报处理、公告、课程维护、数据分析和安全日志
- 安全与合规：CSRF、防刷、限流、审计日志、版权投诉、PII 加密设计

## 技术栈

| 层级 | 技术 |
|---|---|
| 前端 | Nuxt 3, Vue 3, TypeScript, Element Plus, Tailwind CSS, Pinia |
| 后端 | Python 3.12, FastAPI, SQLAlchemy 2.0 async, Pydantic v2, Celery |
| 数据库 | PostgreSQL 16 |
| 缓存与队列 | Redis 7 |
| 搜索 | Elasticsearch 8 + IK 分词，MVP 阶段可回退到 PostgreSQL 基础搜索 |
| 文件存储 | 阿里云 OSS / 兼容对象存储 / 外部链接 |
| 预览 | PDF.js, 原生图片/文本/代码预览，OnlyOffice 作为可选组件 |
| 部署 | Docker Compose，单机低成本部署优先 |

## 仓库结构

```text
scustack/
├── scustack-web/              # Nuxt 3 前端
│   ├── pages/                 # 文件路由
│   ├── components/            # Vue 组件
│   ├── composables/           # 组合式函数
│   ├── stores/                # Pinia 状态
│   └── tests/                 # Vitest 单元测试
├── scustack-api/              # FastAPI 后端
│   ├── app/
│   │   ├── api/v1/            # API 路由
│   │   ├── models/            # SQLAlchemy ORM
│   │   ├── schemas/           # Pydantic Schema
│   │   ├── services/          # 业务逻辑
│   │   ├── core/              # DB / Redis / ES / OSS / 安全配置
│   │   ├── middleware/        # 中间件
│   │   └── tasks/             # Celery 异步任务
│   ├── alembic/               # 数据库迁移
│   └── tests/                 # pytest 测试
├── packages/shared-types/     # 前后端共享类型
├── docs/                      # 产品、架构、设计和部署文档
├── docker/                    # 本地基础设施配置
└── docker-compose.yml
```

## 快速开始

### 环境要求

- Node.js >= 20
- pnpm >= 9
- Python >= 3.12
- Docker Desktop 或 Docker Compose v2

### 安装依赖

```bash
git clone https://github.com/SCUStack/scustack.git
cd scustack

pnpm install

cd scustack-api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 启动基础设施

```bash
cd scustack
docker compose up -d postgres redis elasticsearch
```

本地 `docker-compose.yml` 将 PostgreSQL 和 Redis 暴露在非默认端口：

```bash
cd scustack-api
cp .env.example .env
```

如果后端在宿主机运行，请把 `.env` 中的端口调整为：

```env
SCUSTACK_DB_PORT=25432
SCUSTACK_REDIS_URL=redis://localhost:26379/0
```

### 初始化数据库

```bash
cd scustack-api
alembic upgrade head
python scripts/seed_colleges.py
python -m scripts.seed_mock_data
```

### 启动开发服务

在仓库根目录运行：

```bash
pnpm dev
```

也可以分别启动：

```bash
# 后端
cd scustack-api
uvicorn app.main:app --reload --port 8403

# 前端
cd scustack-web
pnpm dev
```

默认地址：

- 前端：http://localhost:3000
- 后端 API：http://localhost:8403
- Swagger 文档：http://localhost:8403/docs

## 常用命令

```bash
# 前端
pnpm --filter scustack-web test
pnpm --filter scustack-web typecheck
pnpm --filter scustack-web build

# 后端
cd scustack-api
pytest
pytest --cov=app --cov-report=term-missing
ruff check .
pyright

# 根目录
pnpm lint
pnpm typecheck
```

## 文档

- [产品需求文档](docs/PRD-产品需求文档.md)
- [技术架构书](docs/ARCHITECTURE-技术架构.md)
- [UI/UX 设计书](docs/DESIGN-UI-UX.md)
- [部署手册](docs/DEPLOYMENT-部署手册.md)
- [上线检查清单](docs/CHECKLIST-上线检查.md)
- [贡献指南](CONTRIBUTING.md)

## 共建招募

川流课栈欢迎四川大学同学、校友和开源开发者长期参与。当前主要需要：

- 技术组：前端、后端、全栈、测试、部署运维、线上支持
- 学院负责人：课程目录校对、资料征集、学院侧协作
- 资料审核员：资料审核、举报处理、内容质量维护
- 产品与设计：用户调研、交互优化、可访问性和移动端体验

如果你暂时不能长期参与，也欢迎提交资料、反馈 bug、补充文档、转发项目或推荐合适的同学。

## 贡献方式

项目采用 issue-driven development。开始开发前请先阅读目标 issue、确认阻塞项，并按“数据库 -> API -> UI -> 测试”的完整纵向切片提交。

提交约定：

- 分支：`issue-NNN-short-description`
- Commit：Conventional Commits，例如 `feat: add material rating`
- PR：说明关联 issue、实现范围、测试结果和截图

更多流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

许可证文件尚未加入仓库。正式发布前需要补充 `LICENSE` 并在本节更新授权说明。

---

> 让查找课程资料不再依赖群聊和网盘。
