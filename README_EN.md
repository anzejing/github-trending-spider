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

**AI Daily Frontier** automatically crawls GitHub Trending, Hacker News, TLDR AI, OpenAI, Anthropic, and InfoQ AI Development daily. It generates Chinese summaries via GitHub Models API (GPT-4o) and serves content through a FastAPI read-only API and Vue frontend news feed.

Live demo: **https://www.gdufe888.top/ai/?lang=en**

## Screenshots

<p align="center">
  <img src="scripts/img/day.png" width="800" alt="Day mode" />
</p>

<p align="center">
  <img src="scripts/img/open.png" width="800" alt="Content view" />
</p>

## Features

- **6 Sources** — GitHub Trending (daily/weekly), Hacker News, TLDR AI, OpenAI, Anthropic, InfoQ AI
- **AI Summaries** — GPT-4o generates Chinese summaries focused on backend engineering
- **Bilingual UI** — Switch via `?lang=en` / `?lang=zh`; English users see original summaries
- **Unified JSON** — All sources output consistent field structure at `output/latest.json`
- **Archival** — Permanent disk archives + Redis 3-day hot cache
- **Fault Tolerant** — Each source fails independently without blocking others
- **Built-in Scheduler** — In-process scheduler, 3 collections per day by default
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
curl http://localhost:8000/api/health              # Health check
curl http://localhost:8000/api/sources             # Source list
curl http://localhost:8000/api/sources/github-daily/latest  # Single source data
```

## Architecture

```
Collection: main.py → github_trending / hacker_news / tldr_ai / official_ai_sources
Data:       content_items.py → content_store.py → Redis + Disk archive
Service:    api.py (FastAPI) + scheduler.py (scheduled collection)
Frontend:   frontend/ (Vue 3) → Nginx static hosting
```

## Configuration

All config via environment variables with sensible defaults:

| Variable | Default | Description |
| --- | --- | --- |
| `GITHUB_TOKEN` | - | GitHub Models API token (required) |
| `GITHUB_TRENDING_TOP_COUNT` | 10 | Top N repos per GitHub chart |
| `HN_TOP_COUNT` | 10 | Top N HN stories |
| `TLDR_AI_TOP_COUNT` | 10 | Top N TLDR AI items |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection URL |
| `SPIDER_SCHEDULE_TIMES` | 07:50,15:50,23:50 | Daily collection times |
| `SEND_EMAIL_ENABLED` | false | Enable email sending |

> Full configuration options in `config.py`

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

## License

[MIT](LICENSE)
