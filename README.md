# 川流课栈

## 招募通知

> 川流课栈正在招募核心共建成员，面向四川大学同学与校友开放。
>
> 目前招募三类岗位：
> - 技术组：前端 / 后端 / 全栈开发 + 部署运维 + 测试补齐 + 线上支持
> - 学院负责人：负责本学院资料征集、课程目录校对、协作推进
> - 资料审核员：负责资料审核、举报处理、内容质量把关
>
> 欢迎愿意长期参与公益项目建设的同学加入。报名时请附上：学院 / 专业 / 年级、意向岗位、相关经历、每周可投入时间、联系方式。
>
> 如果你不能长期参与，也欢迎帮忙转发、推荐同学、提供资料或参与测试反馈。

面向四川大学全学科的公益型课程资料共享平台。以「学院 - 课程 - 学期 - 资料分类」为核心目录体系，让学生以低门槛、高效率、可信赖的方式查找、贡献、评价和维护课程资料。

**公益 · 无广告 · 开源**

[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![CI](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/yeyixiang2007/scustack/actions)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](CONTRIBUTING.md)

## 技术栈

| 层级 | 技术 |
|---|---|
| 前端 | Nuxt 3 (Vue 3 + TypeScript) + Element Plus + Tailwind CSS |
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) + Celery |
| 数据库 | PostgreSQL 16 + Redis 7 |
| 搜索 | Elasticsearch 8.x + IK 分词器 |
| 文件存储 | 阿里云 OSS + CDN |
| 文档预览 | PDF.js + OnlyOffice (自托管) + Shiki |
| 部署 | 阿里云 ECS + RDS + Docker |

## 快速开始

### 环境要求

- Node.js ≥ 20
- Python ≥ 3.12
- Docker & Docker Compose
- pnpm ≥ 9

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/your-org/scustack.git
cd scustack

# 安装前端依赖
cd scustack-web
pnpm install

# 安装后端依赖
cd ../scustack-api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# 启动基础设施 (PostgreSQL, Redis, Elasticsearch, OnlyOffice)
cd ..
docker compose up -d

# 运行数据库迁移
cd scustack-api
alembic upgrade head

# 启动开发服务器
# 终端 1: 后端
uvicorn app.main:app --reload --port 8403

# 终端 2: 前端
cd ../scustack-web
pnpm dev
```

前端运行于 `http://localhost:3000`，后端 API 运行于 `http://localhost:8403`，Swagger 文档位于 `http://localhost:8403/docs`。

### 导入种子数据

```bash
cd scustack-api
python scripts/seed_colleges.py    # 导入学院数据
python -m scripts.seed_mock_data   # 导入课程与示例数据（staging / 本地）
```

## 项目结构

```
scustack/
├── scustack-web/              # 前端 (Nuxt 3)
│   ├── pages/                 # 页面路由
│   ├── components/            # Vue 组件
│   ├── composables/           # 组合式函数
│   ├── server/                # Nuxt 服务端 (API 代理)
│   └── stores/                # Pinia 状态管理
├── scustack-api/              # 后端 (FastAPI)
│   ├── app/
│   │   ├── api/v1/            # API 路由
│   │   ├── models/            # SQLAlchemy ORM
│   │   ├── schemas/           # Pydantic 模型
│   │   ├── services/          # 业务逻辑
│   │   ├── core/              # 基础设施 (DB, Redis, ES, OSS)
│   │   ├── middleware/        # 中间件 (认证, 限流, CORS, 审计)
│   │   └── tasks/             # Celery 异步任务
│   ├── alembic/               # 数据库迁移
│   └── tests/                 # 测试
├── docs/                      # 项目文档
│   ├── PRD.md                 # 产品需求文档
│   ├── ARCHITECTURE.md        # 技术架构书
│   └── UI-UX-DESIGN.md        # UI/UX 设计书
└── docker-compose.yml         # 本地开发基础设施
```

## 文档

- [产品需求文档 (PRD)](docs/PRD.md) — 用户故事、产品决策、MVP 范围
- [技术架构书](docs/ARCHITECTURE.md) — 技术选型、数据库设计、API 规范、部署运维
- [UI/UX 设计书](docs/UI-UX-DESIGN.md) — 设计系统、页面设计、组件库、交互模式
- [生产部署 Runbook](docs/DEPLOYMENT.md) — 上线步骤、环境变量、健康检查、监控与回滚
- [主站上线检查清单](docs/LAUNCH-CHECKLIST.md) — 站内已完成项、手工验证项、真实上线阻塞项

## 核心功能

- 结构化课程目录：学院 → 课程 → 学期 → 资料分类
- 全文搜索：Elasticsearch + IK 分词 + 自定义词典，支持中英混合和专业术语
- 托管文件与外部链接双模式：同一资料模型下支持上传文件和引用外部资源
- 在线预览：PDF、Office 文档、代码、Markdown，附带动态盲水印
- 双轨版本管理：文本/代码类支持 diff 对比，二进制文件版本号+元数据管理
- 分层信任体系：维护者精选 → 社区验证 → 未验证 → 存疑，四状态可视化
- 审核与举报：自动化内容安全预审 + 人工审核队列 + 举报处理
- 校历驱动推荐：根据学期阶段（选课/期中/期末）规则化推荐相关分类资料
- 响应式设计：适配桌面、平板、手机，无需安装 App

## 贡献指南

川流课栈是开源公益项目，欢迎四川大学学生和开发者参与贡献。

详细的开发环境搭建、测试运行和 PR 流程请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

### 代码规范

- 前端：ESLint + Prettier，Vue 3 Composition API + TypeScript
- 后端：Ruff + Pyright，FastAPI 分层架构（Router → Service → Model）
- 提交信息：遵循 Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`)

## 许可

[MIT License](LICENSE)

---

> 让查找课程资料不再依赖群聊和网盘。
