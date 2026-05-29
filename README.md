<h1 align="center">AI Daily Frontier</h1>

<p align="center">
  <em>多源 AI 信息聚合 · 每日自动采集 · 中文智能摘要</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3572A5" alt="Python" />
  <img src="https://img.shields.io/badge/Vue-3-41b883" alt="Vue 3" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688" alt="FastAPI" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License" />
</p>

<p align="center">
  中文 | <a href="README_EN.md">English</a>
</p>

---

**AI Daily Frontier** 每日自动爬取 GitHub Trending、Hacker News、TLDR AI、OpenAI、Anthropic、InfoQ AI Development 等信息源，通过 GitHub Models API (GPT-4o) 生成中文摘要，提供 FastAPI 只读接口和 Vue 前端资讯流页面。

线上地址：**https://www.gdufe888.top/ai/**

## 截图

<p align="center">
  <img src="scripts/img/day.png" width="800" alt="日间模式" />
</p>

<p align="center">
  <img src="scripts/img/open.png" width="800" alt="内容展示" />
</p>

## 功能特性

- **6 大信息源** — GitHub Trending (日/周)、Hacker News、TLDR AI、OpenAI、Anthropic、InfoQ AI
- **AI 中文摘要** — GPT-4o 生成面向后端工程师的中文总结，关注工程落地
- **中英双语** — 前端支持 `?lang=en` / `?lang=zh` 切换，英文用户直接看原文摘要
- **统一 JSON** — 所有来源输出统一字段结构，`output/latest.json`
- **按来源归档** — 磁盘永久保留 + Redis 3 天热数据缓存
- **独立容错** — 任一源失败不影响其他源输出
- **内置定时采集** — FastAPI 进程内调度器，默认每天 3 次
- **Vue 前端** — 卡片式资讯流，骨架屏加载，响应式设计

## 快速开始

```bash
# 克隆 & 安装
git clone https://github.com/wenbochang888/github-trending-spider.git
cd github-trending-spider
pip3 install -r requirements.txt

# 配置（必须）
export GITHUB_TOKEN="ghp_your_token"  # GitHub Settings → Tokens → models:read

# 测试采集
python3 main.py

# 启动 API 服务
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000

# 启动前端（开发）
cd frontend && npm install && npm run serve
```

## API

```bash
curl http://localhost:8000/api/health              # 健康检查
curl http://localhost:8000/api/sources             # 来源列表
curl http://localhost:8000/api/sources/github-daily/latest  # 单来源数据
```

## 技术架构

```
采集层: main.py → github_trending / hacker_news / tldr_ai / official_ai_sources
数据层: content_items.py → content_store.py → Redis + 磁盘归档
服务层: api.py (FastAPI) + scheduler.py (定时采集)
展示层: frontend/ (Vue 3) → Nginx 静态托管
```

## 配置

所有配置通过环境变量，均有合理默认值：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `GITHUB_TOKEN` | - | GitHub Models API token (必须) |
| `GITHUB_TRENDING_TOP_COUNT` | 10 | GitHub 各榜单取前 N 条 |
| `HN_TOP_COUNT` | 10 | HN 取前 N 条 |
| `TLDR_AI_TOP_COUNT` | 10 | TLDR AI 取前 N 条 |
| `REDIS_URL` | redis://localhost:6379/0 | Redis 连接地址 |
| `SPIDER_SCHEDULE_TIMES` | 07:50,15:50,23:50 | 每天采集时间 |
| `SEND_EMAIL_ENABLED` | false | 是否发送邮件 |

> 完整配置项见源码 `config.py`

## 部署

```bash
# 后端启动（后台运行）
bash scripts/start_backend.sh

# 前端构建
cd frontend && npm run build

# 访问链路
# https://your-domain.com/ai/     → Nginx 托管 frontend/dist/
# https://your-domain.com/api/... → Nginx 反代 → FastAPI :8000
```

## License

[MIT](LICENSE)
