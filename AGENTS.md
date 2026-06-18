# AGENTS.md

本文件为本仓库的 AI 协作约定。所有自动化助手在读取、修改或评审本项目时必须遵守。

## 项目定位

**AI Daily Frontier(每日AI前沿信息)** —— Python + Vue 全栈 AI 与技术信息聚合项目。

每天定时抓取 **9 个**中英文 AI / 开源 / 社区信息源,通过 GitHub Models API(GPT-4o)生成中文摘要,按来源永久归档到磁盘 + Redis 3 天热数据缓存,并对外提供:

- FastAPI 只读 JSON / RSS / 历史归档接口
- Vue 3 资讯流前端(中英双语,默认 `?lang=zh`,英文 `?lang=en`)
- 可选 SMTP 邮件日报
- `tech-trend-spider` Skill(供其他 AI 助手通过线上 API 消费已采集数据)

线上地址:https://www.gdufe888.top/ai/

## 仓库拓扑

```
.
├── main.py                # 入口:跑一次完整采集 → JSON + 归档 + 邮件
├── config.py              # 所有可调参数(读环境变量)
├── api.py                 # FastAPI 公开只读接口
├── scheduler.py           # FastAPI 进程内定时调度(非 cron)
├── access_log.py          # API 访问日志中间件 + 每小时统计
├── logging_config.py      # 共享 logging 初始化(rotating file + stream)
├── content_items.py       # 统一信息项 + 跨源适配 + 统一 AI 摘要
├── content_store.py       # 按来源归档 + Redis 读写 + 历史归档
├── redis_client.py        # 进程级 Redis 连接池
├── source_registry.py     # 9 个 source id 的单一事实源
├── rss_builder.py         # /api/rss.xml 聚合 feed
├── github_trending.py     # github-daily / github-weekly 抓取 + 摘要
├── hacker_news.py         # hacker-news 抓取 + 评论 + 摘要
├── linux_do_news.py       # linux-do: 解析 news.linuxe.top 日报
├── v2ex.py                # v2ex: 全站热帖 + 节点白名单 + 回复 + 摘要
├── tldr_ai.py             # tldr-ai 抓取 + 中文整理
├── official_ai_sources.py # openai / anthropic / infoq 抓取
├── email_builder.py       # HTML 邮件模板
├── email_sender.py        # SMTP 发送 + 失败通知
├── test_email.py          # SMTP 发送测试脚本
├── frontend/              # Vue 3 + Vue CLI 前端(1444 行 App.vue)
├── tests/                 # unittest 风格单元测试
├── scripts/               # 部署 / 启动 / 日志统计
├── skills/tech-trend-spider/  # 供其他 AI 助手消费的 Skill
├── docs/                  # 公开文档(rss-api-guide.md 等)
├── requirements.txt       # 5 个依赖(见下方)
├── .env.example           # 环境变量模板
├── AGENTS.md / README*    # 本文件与项目说明
└── LICENSE                # MIT
```

## 9 个信息源(source id 是稳定契约)

| source id | 中文 label | 类别 | 抓取模块 | 备注 |
|---|---|---|---|---|
| `github-daily` | GitHub 日榜 | 开源趋势 | `github_trending.py` | GitHub Trending Daily |
| `github-weekly` | GitHub 周榜 | 开源趋势 | `github_trending.py` | GitHub Trending Weekly |
| `hacker-news` | Hacker News | 社区讨论 | `hacker_news.py` | 含 Top 评论 |
| `linux-do` | Linux.do 技术日报 | 社区讨论 | `linux_do_news.py` | 只解析 `news.linuxe.top` 日报页,**不**抓原帖正文 |
| `v2ex` | V2EX | 社区讨论 | `v2ex.py` | 节点白名单,技术帖排前 |
| `tldr-ai` | TLDR AI | AI 快讯 | `tldr_ai.py` | 最新一期 |
| `openai` | OpenAI | AI 官方更新 | `official_ai_sources.py` | openai.com/news |
| `anthropic` | Anthropic | AI 官方更新 | `official_ai_sources.py` | anthropic.com/news |
| `infoq` | InfoQ AI | AI 工程实践 | `official_ai_sources.py` | 聚合多个 InfoQ RSS |

**新增源时必须先在 `source_registry.SOURCE_DEFINITIONS` 注册 source id**,否则:
- API `/api/sources` 不会列出
- `content_store.persist_source_snapshots` 会跳过该源(因为找不到 `get_source_by_content_source`)
- 前端 `/api/sources` 列表中也看不到

## 统一信息项(content_items.py)

```python
make_content_item(
    source, category, title, url,
    published_at="",
    original_summary="",
    chinese_summary="",
    backend_focus="",
    meta={},
)
```

- `source`(字符串)必须匹配 `source_registry.SOURCE_BY_CONTENT_SOURCE` 中的某个 content_source(GitHub Trending Daily / Hacker News / Linux.do / V2EX / TLDR AI / OpenAI / Anthropic / InfoQ AI Development)
- `meta` 是源特定的额外信息(语言、stars、回复数、节点名等)
- AI 摘要失败 / 缺 `GITHUB_TOKEN` 时,`chinese_summary` 自动填入降级文案,卡片仍可展示

Skill 数据契约:`skills/tech-trend-spider/references/output-schema.md`

## 关键运行机制(改代码前必读)

1. **独立容错**:`main.run_spider()` 中每个源都有自己的 try/except,任一源失败不影响其他源
2. **降级摘要**:无 `GITHUB_TOKEN` 时所有 AI 摘要走降级文案,卡片仍有原文摘要
3. **Redis 可选**:`redis_client.get_redis_client()` 失败返回 None,API 自动降级读磁盘归档(`served_from=archive`)
4. **进程内调度**:`scheduler.py` 用 `threading.Lock` + 单线程定时跑 `run_spider()`,**生产部署必须用单 worker uvicorn**(`--workers 1`),否则多 worker 同时启动调度器会重复跑采集并写多份归档
5. **写盘每日归档**:`output/<source>/<YYYY-MM-DD>/<batch>.json`,批号自增(同一天内多次采集会写出 `01.json`, `02.json` ...)
6. **API 数据只读**:FastAPI 接口只读取已有快照,**不**触发实时爬虫;只有 `scheduler` 才会主动跑采集

## 环境变量

**敏感信息只能通过环境变量配置**,不要写入代码、README 示例真实值或提交记录。`.env` 已 gitignore。

**唯一必填**:`GITHUB_TOKEN`(GitHub Settings → Tokens,勾选 `models:read`)。
缺失时:所有 AI 摘要走降级,卡片仍有原文摘要。

完整清单(全部读自 `config.py`,默认值与说明以源码为准):

核心 AI:
- `GITHUB_TOKEN`(必填)— GitHub Models API token
- `AI_API_URL`(默认 `https://models.inference.ai.azure.com`)
- `AI_MODEL`(默认 `gpt-4o`,可选 `gpt-4o-mini` / `deepseek-r1`)

数量(每个源的上限;实际不足时按源实际返回):
- `GITHUB_TRENDING_TOP_COUNT`(10)、`HN_TOP_COUNT`(10)、`HN_COMMENTS_PER_STORY`(10)
- `TLDR_AI_TOP_COUNT`(10)、`V2EX_TOP_COUNT`(10)、`V2EX_REPLIES_PER_TOPIC`(10)
- `LINUX_DO_MAX_ITEMS`(0 = 全部)、`OPENAI_NEWS_COUNT`(10)、`ANTHROPIC_NEWS_COUNT`(10)、`INFOQ_AI_NEWS_COUNT`(10)

可调 URL:
- `HN_API_BASE`、`TLDR_AI_HOME_URL`、`V2EX_API_BASE`、`LINUX_DO_NEWS_URL`
- `OPENAI_NEWS_URL` / `OPENAI_NEWS_RSS_URL`、`ANTHROPIC_NEWS_URL`、`INFOQ_AI_RSS_URLS`(逗号分隔多 RSS)

重试 / 节流:
- `HN_MAX_RETRIES`(5)、`HN_CONCURRENT_WORKERS`(10)、`TLDR_AI_MAX_RETRIES`(5)
- `V2EX_MAX_RETRIES`(5)、`V2EX_REQUEST_INTERVAL`(0.5 秒)、`LINUX_DO_MAX_RETRIES`(5)、`OFFICIAL_AI_MAX_RETRIES`(5)

Redis / API:
- `REDIS_URL`、`REDIS_KEY_PREFIX`、`REDIS_SNAPSHOT_TTL_SECONDS`(默认 3 天)、`REDIS_SOCKET_TIMEOUT_SECONDS`
- `API_MAX_ITEMS_PER_SOURCE`(100)、`API_CORS_ORIGINS`(逗号分隔,空 = 不开 CORS)

调度:
- `SPIDER_SCHEDULER_ENABLED`(默认 true,API 进程内是否启用)
- `SPIDER_SCHEDULE_TIMES`(默认 `07:50,15:50,23:50`,逗号分隔 HH:MM)
- `SPIDER_RUN_ON_STARTUP`(默认 false,API 启动时是否立即跑一次)

邮件:
- `SMTP_SERVER`/`SMTP_PORT`(默认 465)/`SMTP_USER`/`SMTP_PASSWORD`/`MAIL_FROM`/`MAIL_TO`
- `MAIL_TO_BY_TIME`(JSON 对象,按调度时间映射收件人,优先于 `MAIL_TO` / `EMAIL_SEND_TIMES`)
- `SEND_EMAIL_ENABLED`(默认 false)、`EMAIL_SEND_TIMES`(默认 `07:50`,白名单)
- 决策逻辑:`scheduler` 传入 `scheduled_time`,`main._email_send_decision` 决定是否发、收件人是谁

日志 / 输出:
- `LOG_FILE`(默认 `/root/logs/github-python/trending.log`,`TimedRotatingFileHandler` midnight,`backupCount=30`)
- `OUTPUT_JSON_PATH`(默认 `output/latest.json`)、`OUTPUT_ARCHIVE_DIR`(默认 `output`)

## 本地开发

```bash
# 安装依赖(只 5 个:requests / beautifulsoup4 / fastapi / uvicorn / redis)
pip3 install -r requirements.txt

# 单次采集(GITHUB_TOKEN 必填,否则 AI 摘要会走降级文案)
source .env 2>/dev/null || true
python3 main.py

# 启动 API(含进程内调度 + 访问日志 + 统计)
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000

# 前端开发(默认 127.0.0.1:8080)
cd frontend && npm install && npm run serve

# 运行测试(标准 unittest)
python3 -m unittest discover tests -v
```

注意:
- 本地没有 `/root/logs/github-python/` 目录时,`logging_config.setup_logging()` 会自动 `os.makedirs(log_dir, exist_ok=True)`;若目录不可写,请 `LOG_FILE=/tmp/spider.log python3 main.py`
- `LOG_FILE` 由 `main.py` 和 `api.py` 双方共享,启动任一入口都会创建 rotating file handler
- 测试运行不依赖网络,使用 `unittest.mock.patch` 隔离 requests

## 公开接口(api.py)

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 健康检查,固定返回 `{status:"ok"}` |
| GET | `/api/sources` | 注册来源列表 + count |
| GET | `/api/sources/{source_id}/latest` | 单来源最新快照;返回 `served_from`: `redis` / `archive` / `empty` |
| GET | `/api/rss.xml` | RSS 2.0 聚合 feed(只读快照,不触发爬虫) |
| GET | `/api/history/dates` | 最近 7 天历史归档日期(**不**含今天) |
| GET | `/api/history/sources/{source_id}/dates/{date_text}` | 指定来源、日期的历史归档快照 |

未知 source_id 返 404;非法日期 `YYYY-MM-DD` 返 400。

字段映射细节见 `docs/rss-api-guide.md`(RSS 字段表)。

## 前端约定

- 路由:`/ai/`(Nginx 静态托管 `frontend/dist/`),`/api/` 反代到 FastAPI `:8000`
- 双语:`?lang=zh` / `?lang=en`,优先级 URL 参数 > localStorage > 默认 `zh`
- 来源展示名覆盖:`SOURCE_DISPLAY_MAP` / `SOURCE_DISPLAY_MAP_EN`,只在 `frontend/src/App.vue` 内,**不**改后端 `source_registry.py`
- 页面 title(`public/index.html`):"每日AI前沿信息"

## 部署脚本

- `scripts/start_backend.sh`:装依赖 + kill 旧 uvicorn + 后台启动新进程。会读 `~/.bash_profile` 与 `.env`
- `scripts/start_frontend.sh`:开发模式 `npm run serve`(默认 127.0.0.1:8080);**生产用 `cd frontend && npm run build` 然后 Nginx 托管 `dist/`**
- `scripts/start_all.sh`:先后台启动 backend / frontend,pid 写入 `.runtime/`(已 gitignore)
- `scripts/log_stats.py`:解析 access log,出访问统计 + 数据来源(Redis 命中 / 磁盘降级)

## 日志标签

| 标签 | 含义 |
|---|---|
| `[访问]` | 每次 API 请求记录(IP / 路径 / 状态码 / 耗时) |
| `[数据]` | API 数据来源追踪(来源 / 读取自 redis-archive / 条数 / 数据生成时间) |
| `[统计]` | 每小时访问汇总(独立 IP / 热门接口 Top 5 / 活跃 IP Top 5) |
| `[RSS]` | `/api/rss.xml` 请求汇总(来源数 / 条数) |
| `[启动]` / `[关闭]` | API 进程生命周期 |

排查命令:

```bash
python3 scripts/log_stats.py                # 当天
python3 scripts/log_stats.py 2026-06-15     # 指定日期
python3 scripts/log_stats.py --all          # 全部日志(含轮转文件 trending.log.YYYY-MM-DD)
python3 scripts/log_stats.py --file /path/to.log
```

## 任务文件规则

- 所有新任务计划写入 `.task/YYYY-MM-DD_N-short-slug.md`,**不要**新增根目录任务文件
- 命名:`YYYY-MM-DD_N-short-slug.md`,N 是当天的序号(`_1`, `_2`, ...)
- 任务文件内至少记录:目标、涉及文件、执行步骤、验证结果、遗留问题
- 生成新任务前,**必须**先 `ls .task/` 看最近同类任务文件,沿用任务粒度 / 勾选写法 / 验证记录格式

## 开发约定

1. **新增源**:必须先注册到 `source_registry.SOURCE_DEFINITIONS` 并实现 `fetch_xxx()` + `ai_summarize_xxx()`(或适配到 `content_items.build_all_content_items`)。**优先用官方 RSS / API**,HTML 解析只作兜底
2. **每个源独立容错**:在 `main.py` 中包 try/except,失败后该源空列表继续走其他源,不要让单个源挂掉整次采集
3. **AI 摘要失败降级**:`content_items.summarize_content_items` 已处理降级文案,新源摘要函数也应遵守
4. **数量配置**:每个源 TOP_N 走环境变量,默认值写 `config.py`,业务逻辑读 `config` 模块
5. **真实密钥**:token / SMTP 授权码 / 邮箱密码只能报告"已设置/未设置/长度",禁止明文写入任何文件
6. **不要提交**:`output/`、`.env`、`.task/`、`.runtime/`、`__pycache__/`、`frontend/dist/`、`frontend/node_modules/`、`.log`(均在 `.gitignore`)
7. **生产 uvicorn 单 worker**:`--workers 1`,否则 scheduler 会在多个进程里同时启动,采集会重复执行并产生多份归档

## fork 同步策略(本仓库上下文)

- `origin` = 个人 fork(`anzejing/github-trending-spider`),GitHub 默认分支 `dev`
- `upstream` = 原仓库(`wenbochang888/github-trending-spider`),默认 `master`
- 同步 upstream 时:**`upstream/master` → 本地 `master`(merge/rebase)→ 必要时再 merge 到 `dev`**,不要让 upstream 直接污染 `dev`

## 沟通与安全

- 回答用户时默认使用中文
- 对不确定点先询问,不要猜测
- 修改前先查代码事实,避免凭 README 或记忆判断
- 任何真实 token / 邮箱授权码 / 密码只允许报告"已设置 / 未设置 / 长度",不要明文输出
