# 性能与成本观测基线

本基线覆盖 MVP 中最容易产生基础设施成本的公共路径：首页、搜索、资料详情、下载与预览/内容提取。

## 在线请求基线

后端 `CostObservabilityMiddleware` 会为关键公共路径添加响应头：

- `X-SCU-Route`: 归类后的路径，例如 `homepage`、`search`、`material_detail`、`download`
- `X-SCU-Cost-Units`: 粗粒度成本单位，用于比较同一路径优化前后的相对成本
- `X-SCU-Latency-Ms`: 应用层处理耗时

进程内聚合快照：

```bash
curl http://localhost:8403/api/v1/health/cost-baseline
```

返回的 `paths.*.avg_latency_ms`、`paths.*.p95_latency_ms` 和 `paths.*.avg_cost_units` 用于记录优化前后对比。该快照是轻量内存基线，进程重启会清空；生产长期趋势应接入 Sentry/APM 或日志采集。

## 首页推荐成本

匿名首页推荐通过 Redis 缓存 `homepage:anonymous_recommendations:v1` 保存推荐资料 ID，TTL 为 10 分钟。`/api/v1/homepage` 返回 `recommendation_cache`：

- `hit`: 命中缓存，只按 ID 回填资料
- `miss`: 本次重新计算并写入缓存
- `bypass`: Redis 不可用，直接计算
- `personalized`: 登录用户走个性化推荐，不复用匿名缓存

## 资料详情首屏

前端优先请求：

```text
GET /api/v1/materials/{material_id}/detail
```

该接口一次返回资料主体、版本预览、相关推荐和课程名，减少首屏 HTTP round-trip。旧的资料、版本、相关资料、课程接口仍作为前端兜底。

## 预览与内容提取成本

后台内容提取只处理有检索价值且成本可控的文件：

- 文本类文件最大 12 MiB
- PDF 最大 8 MiB
- PDF 最多提取前 30 页
- 下载与提取超时 15 秒

前端 PDF 在线预览超过 25 MiB 时直接展示下载兜底，避免浏览器加载大文件和 PDF worker 长时间渲染。

## 前端包体守卫

运行：

```bash
cd scustack-web
npm run build:guard
```

该命令先构建 Nuxt，再扫描 `.output/public/_nuxt` 下的 JS chunk。默认单 chunk 上限为 1000 KiB，可通过 `SCUSTACK_MAX_CHUNK_BYTES` 调整。Nuxt/Vite 已将 Element Plus、pdfjs、Shiki 拆为独立 vendor chunk，代码预览使用 Shiki web bundle 避免拉取全语言包，便于后续比较包体变化。
