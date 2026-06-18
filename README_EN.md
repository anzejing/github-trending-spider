<h1 align="center">AI Daily Frontier</h1>

<p align="center">
  <em>Multi-source AI news aggregation · Auto-collected daily · AI-powered summaries</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-3572A5" alt="Python" />
  <img src="https://img.shields.io/badge/Vue-3-41b883" alt="Vue 3" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688" alt="FastAPI" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License" />
</p>

<p align="center">
  <a href="README.md">中文</a> | English
</p>

---

**AI Daily Frontier** automatically crawls GitHub Trending, Hacker News, Linux.do, V2EX, TLDR AI, OpenAI, Anthropic, and InfoQ AI Development daily. It generates Chinese summaries via GitHub Models API (GPT-4o) and serves content through a FastAPI read-only API, an aggregated RSS feed, a 7-day history archive, and a Vue frontend news feed.

Live demo: **https://www.gdufe888.top/ai/?lang=en**

## Screenshots

<p align="center">
  <img src="scripts/img/day.png" width="800" alt="Day mode" />
</p>

<p align="center">
  <img src="scripts/img/open.png" width="800" alt="Content view" />
</p>

## Features

- **9 Sources** — GitHub Trending (daily / weekly), Hacker News, Linux.do, V2EX, TLDR AI, OpenAI, Anthropic, InfoQ AI
- **AI Summaries** — GPT-4o generates Chinese summaries focused on backend engineering
- **Bilingual UI** — Switch via `?lang=en` / `?lang=zh`; English users see original summaries
- **Unified JSON** — All sources output consistent field structure at `output/latest.json`
- **Archival** — Permanent disk archives + Redis 3-day hot cache
- **Fault Tolerant** — Each source fails independently without blocking others
- **Built-in Scheduler** — In-process scheduler, 3 collections per day by default
- **Aggregated RSS** — `GET /api/rss.xml` merges all sources (read-only, never triggers crawlers)
- **History Archive** — Last 7 days of per-source snapshots exposed via `/api/history/*`
- **Skill Integration** — Companion `tech-trend-spider` Skill lets other AI assistants consume the collected snapshots through the public read-only API
- **Vue Frontend** — Card-based news feed with skeleton loading and responsive design

## Quick Start

```bash
# Clone & install
git clone https://github.com/wenbochang888/github-trending-spider.git
cd github-trending-spider
pip3 install -r requirements.txt

# Configure (required)
export GITHUB_TOKEN="ghp_your_token"  # GitHub Settings → Tokens → models:read

# Test collection
python3 main.py

# Start API server
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000

# Start frontend (dev)
cd frontend && npm install && npm run serve
```

## API

```bash
curl http://localhost:8000/api/health                          # Health check
curl http://localhost:8000/api/sources                         # Source list
curl http://localhost:8000/api/sources/github-daily/latest     # Single source data
curl http://localhost:8000/api/rss.xml                         # Aggregated RSS feed
curl http://localhost:8000/api/history/dates                  # Last 7 days of archive dates
curl http://localhost:8000/api/history/sources/github-daily/dates/2026-06-15  # Historical snapshot
```

### RSS

A single aggregated RSS 2.0 feed is published at `/api/rss.xml`. It only reads existing snapshots and never triggers live crawlers. If Redis is unavailable, the endpoint transparently falls back to the on-disk archive. See `docs/rss-api-guide.md` for the full field mapping.

### Skill

The `tech-trend-spider` Skill (in `skills/tech-trend-spider/`) lets other AI assistants query the collected snapshots through the public read-only API. Consumers do not need the repo source or Python dependencies — just the live API base.

## Architecture

```
Collection: main.py
  → github_trending (github-daily / github-weekly)
  → hacker_news (with comments)
  → linux_do_news (linux-do, news.linuxe.top daily only)
  → v2ex (with replies, tech-node whitelist)
  → tldr_ai
  → official_ai_sources (openai / anthropic / infoq)
Data:       content_items.py (unified schema) → content_store.py → Redis 3d + disk archive
Service:    api.py (FastAPI read-only + RSS + history)
  + scheduler.py (in-process scheduled collection, single-worker uvicorn)
  + access_log.py (access log + hourly stats)
Frontend:   frontend/ (Vue 3, bilingual) → Nginx static hosting
Consumer:   skills/tech-trend-spider/ (for other AI assistants)
```

## Configuration

All config via environment variables with sensible defaults. Template: `.env.example`. Full definition: `config.py`.

| Variable | Default | Description |
| --- | --- | --- |
| `GITHUB_TOKEN` | - | GitHub Models API token (required; falls back to plain summary when missing) |
| `AI_API_URL` | `https://models.inference.ai.azure.com` | GitHub Models endpoint |
| `AI_MODEL` | `gpt-4o` | Also `gpt-4o-mini` / `deepseek-r1` |
| `GITHUB_TRENDING_TOP_COUNT` | 10 | Top N per GitHub chart |
| `HN_TOP_COUNT` / `HN_COMMENTS_PER_STORY` | 10 / 10 | Top N HN stories / top N comments per story |
| `TLDR_AI_TOP_COUNT` | 10 | Top N TLDR AI items |
| `V2EX_TOP_COUNT` / `V2EX_REPLIES_PER_TOPIC` | 10 / 10 | Top N V2EX topics / top N replies per topic |
| `LINUX_DO_MAX_ITEMS` | 0 (all) | Top N Linux.do daily items |
| `OPENAI_NEWS_COUNT` / `ANTHROPIC_NEWS_COUNT` / `INFOQ_AI_NEWS_COUNT` | 10 / 10 / 10 | Top N per official AI source |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis URL (falls back to disk archive when unavailable) |
| `REDIS_SNAPSHOT_TTL_SECONDS` | 259200 (3 days) | Redis snapshot TTL |
| `API_MAX_ITEMS_PER_SOURCE` | 100 | Max items per public API response |
| `API_CORS_ORIGINS` | empty | Comma-separated whitelist; empty = CORS off |
| `SPIDER_SCHEDULER_ENABLED` | true | Enable in-process scheduler |
| `SPIDER_SCHEDULE_TIMES` | 07:50,15:50,23:50 | Daily collection times (HH:MM, comma-separated) |
| `SPIDER_RUN_ON_STARTUP` | false | Run one collection immediately on API startup |
| `SEND_EMAIL_ENABLED` | false | Enable email sending |
| `EMAIL_SEND_TIMES` | 07:50 | Allowed send times when `MAIL_TO_BY_TIME` is not set |
| `MAIL_TO_BY_TIME` | - | Per-time recipient map (JSON object); overrides `MAIL_TO` |
| `LOG_FILE` | `/root/logs/github-python/trending.log` | Log path (midnight rotation, 30 backups) |

> Retry / rate-limit knobs (`HN_MAX_RETRIES`, `V2EX_REQUEST_INTERVAL`, `OFFICIAL_AI_MAX_RETRIES`, ...) live in `config.py`.

## Deployment

```bash
# Start backend (background)
bash scripts/start_backend.sh

# Build frontend
cd frontend && npm run build

# Access flow
# https://your-domain.com/ai/     → Nginx serves frontend/dist/
# https://your-domain.com/api/... → Nginx reverse proxy → FastAPI :8000
```

## Friendly Links

- [Linux.do](https://linux.do)

## License

[MIT](LICENSE)
