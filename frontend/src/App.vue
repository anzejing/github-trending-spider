<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark">AI</div>
        <div class="brand-text">
          <h1>每日AI前沿信息</h1>
          <p>开源趋势 · 社区热议 · AI 动态</p>
        </div>
      </div>
      <div class="update-chip">⏱ {{ countdownText }}</div>
    </header>

    <main class="layout">
      <aside class="source-panel">
        <button
          v-for="source in sources"
          :key="source.id"
          class="source-tab"
          :class="{ active: source.id === activeSourceId }"
          type="button"
          @click="selectSource(source.id)"
        >
          <span>{{ getDisplayLabel(source) }}</span>
          <small>{{ getDisplayCategory(source) }}</small>
        </button>
      </aside>

      <section class="feed-panel">
        <div class="feed-toolbar">
          <h2>{{ activeSourceLabel }}</h2>
        </div>

        <div v-if="loading" class="skeleton-list">
          <div v-for="n in 3" :key="n" class="skeleton-card">
            <div class="skeleton-line title"></div>
            <div class="skeleton-line body"></div>
            <div class="skeleton-line body short"></div>
          </div>
        </div>
        <div v-else-if="errorMessage" class="state-box error">{{ errorMessage }}</div>
        <div v-else-if="items.length === 0" class="state-box">
          当前来源暂无内容
        </div>

        <article
          v-for="item in items"
          v-else
          :key="item.url + item.title"
          class="feed-item"
        >
          <div class="item-main">
            <a class="item-title" :href="item.url" target="_blank" rel="noreferrer">
              {{ item.title }}
            </a>
            <p class="item-summary">{{ item.chinese_summary || item.original_summary }}</p>
            <div class="item-tags" v-if="getItemTags(item).length">
              <span
                v-for="tag in getItemTags(item)"
                :key="tag.label"
                class="item-tag"
                :class="'item-tag--' + tag.type"
              >
                <span v-if="tag.dotColor" class="lang-dot" :style="{ background: tag.dotColor }"></span>
                {{ tag.label }}
              </span>
            </div>
          </div>
          <a
            class="open-link"
            :href="isHN(item) ? ((item.meta && item.meta.hn_url) || item.url) : item.url"
            target="_blank"
            rel="noreferrer"
          >
            {{ isHN(item) ? '查看讨论 →' : '阅读原文 →' }}
          </a>
        </article>
      </section>
    </main>
  </div>
</template>

<script>
const API_PREFIX = '/api';

const SOURCE_DISPLAY_MAP = {
  'github-daily':  { label: '今日开源热榜', category: 'GitHub · 日榜' },
  'github-weekly': { label: '本周开源精选', category: 'GitHub · 周榜' },
  'hacker-news':   { label: '硅谷社区热议', category: 'Hacker News'   },
  'v2ex':          { label: '中文技术社区热议', category: 'V2EX'          },
  'tldr-ai':       { label: 'AI 速报精选',   category: 'TLDR AI'       },
  'openai':        { label: 'OpenAI 最新动态', category: '官方更新'    },
  'anthropic':     { label: 'Anthropic 最新动态', category: '官方更新' },
  'infoq':         { label: 'AI 工程实践',    category: 'InfoQ AI'     },
};

const TLDR_CATEGORY_MAP = {
  'BIG TECH & STARTUPS': '大厂动态',
  'SCIENCE & FUTURISTIC TECHNOLOGY': '前沿科技',
  'PROGRAMMING, DESIGN & DATA SCIENCE': '编程与数据',
  'AI': 'AI 快讯',
};

const CONTENT_TYPE_MAP = {
  'Product': '产品发布',
  'Research': '研究',
  'Safety': '安全',
  'Announcements': '公告',
  'Company': '公司动态',
};

const INFOQ_CATEGORY_MAP = {
  'InfoQ Artificial Intelligence': '人工智能',
  'InfoQ Generative AI': '生成式 AI',
  'InfoQ AI Development': 'AI 工程实践',
  'AI 工程实践': 'AI 工程实践',
  'Artificial Intelligence': '人工智能',
  'Generative AI': '生成式 AI',
  'AI Development': 'AI 工程实践',
  'Machine Learning': '机器学习',
};

const LANGUAGE_COLORS = {
  'JavaScript':       '#f1e05a',
  'TypeScript':       '#3178c6',
  'Python':           '#3572A5',
  'Go':               '#00ADD8',
  'Rust':             '#dea584',
  'Java':             '#b07219',
  'C++':              '#f34b7d',
  'C':                '#555555',
  'C#':               '#178600',
  'Ruby':             '#701516',
  'Swift':            '#F05138',
  'Kotlin':           '#A97BFF',
  'Shell':            '#89e051',
  'HTML':             '#e34c26',
  'CSS':              '#563d7c',
  'Vue':              '#41b883',
  'PHP':              '#4F5D95',
  'Scala':            '#c22d40',
  'Dart':             '#00B4AB',
  'Elixir':           '#6e4a7e',
  'Haskell':          '#5e5086',
  'Lua':              '#000080',
  'R':                '#198CE7',
  'Jupyter Notebook': '#DA5B0B',
  'CUDA':             '#3A4E3A',
  'Makefile':         '#427819',
  'Nix':              '#7e7eff',
  'Zig':              '#ec915c',
  'OCaml':            '#ef7a08',
  'Perl':             '#0298c3',
  'Dockerfile':       '#384d54',
};

// 每日定时更新时间（24小时制）
const SCHEDULE_TIMES = [
  { hour: 7, minute: 50 },
  { hour: 15, minute: 50 },
  { hour: 23, minute: 50 },
];

export default {
  name: 'App',
  data() {
    return {
      sources: [],
      activeSourceId: '',
      items: [],
      generatedAt: '',
      loading: false,
      errorMessage: '',
      countdownText: '每 8 小时更新',
      countdownTimer: null
    };
  },
  computed: {
    activeSourceLabel() {
      const override = SOURCE_DISPLAY_MAP[this.activeSourceId];
      if (override) return override.label;
      const source = this.sources.find((s) => s.id === this.activeSourceId);
      return source ? source.label : '最新内容';
    }
  },
  async created() {
    await this.loadSources();
  },
  mounted() {
    this.updateCountdown();
    this.countdownTimer = setInterval(() => {
      this.updateCountdown();
    }, 1000);
  },
  beforeUnmount() {
    if (this.countdownTimer) {
      clearInterval(this.countdownTimer);
      this.countdownTimer = null;
    }
  },
  methods: {
    updateCountdown() {
      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      let nextUpdate = null;

      // 找今天剩余的更新时间
      for (const t of SCHEDULE_TIMES) {
        const candidate = new Date(today.getTime() + t.hour * 3600000 + t.minute * 60000);
        if (candidate > now) {
          nextUpdate = candidate;
          break;
        }
      }

      // 如果今天的更新时间都过了，取明天第一个
      if (!nextUpdate) {
        const tomorrow = new Date(today.getTime() + 86400000);
        const first = SCHEDULE_TIMES[0];
        nextUpdate = new Date(tomorrow.getTime() + first.hour * 3600000 + first.minute * 60000);
      }

      const diff = nextUpdate - now;
      const hours = Math.floor(diff / 3600000);
      const minutes = Math.floor((diff % 3600000) / 60000);
      const seconds = Math.floor((diff % 60000) / 1000);

      if (hours > 0) {
        this.countdownText = hours + '时' + minutes + '分后更新';
      } else if (minutes > 0) {
        this.countdownText = minutes + '分' + seconds + '秒后更新';
      } else {
        this.countdownText = seconds + '秒后更新';
      }
    },
    getDisplayLabel(source) {
      return (SOURCE_DISPLAY_MAP[source.id] || source).label;
    },
    getDisplayCategory(source) {
      return (SOURCE_DISPLAY_MAP[source.id] || source).category;
    },
    isHN(item) {
      return item.source === 'Hacker News';
    },
    formatDate(str) {
      if (!str) return '';
      const s = String(str).trim();
      // Unix timestamp（HN 使用，9-10 位纯数字）
      if (/^\d{9,10}$/.test(s)) {
        return new Date(Number(s) * 1000).toISOString().slice(0, 10);
      }
      // 已是 YYYY-MM-DD 格式，直接返回
      if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s;
      // ISO 8601 / RFC 2822 等，用 Date 解析后取前10位
      const d = new Date(s);
      if (!isNaN(d.getTime())) return d.toISOString().slice(0, 10);
      // 尝试提取字符串中的 YYYY-MM-DD
      const m = s.match(/(\d{4}-\d{2}-\d{2})/);
      if (m) return m[1];
      return s;
    },
    getItemTags(item) {
      const tags = [];
      const meta = item.meta || {};
      const src = item.source || '';

      if (src === 'GitHub Trending Daily' || src === 'GitHub Trending Weekly') {
        if (meta.language)     tags.push({ label: meta.language, type: 'lang', dotColor: LANGUAGE_COLORS[meta.language] || '#888' });
        if (meta.stars)        tags.push({ label: '⭐ ' + meta.stars.toLocaleString(), type: 'stat' });
        if (meta.forks)        tags.push({ label: '🍴 ' + meta.forks.toLocaleString(), type: 'fork' });
        if (meta.stars_period) tags.push({ label: meta.stars_period, type: 'growth' });
      } else if (src === 'Hacker News') {
        if (meta.score != null)    tags.push({ label: '▲ ' + meta.score, type: 'stat' });
        if (meta.comments != null) tags.push({ label: '💬 ' + meta.comments + ' 评论', type: 'fork' });
      } else if (src === 'TLDR AI') {
        const cat = TLDR_CATEGORY_MAP[item.category];
        if (cat) tags.push({ label: cat, type: 'category' });
      } else if (src === 'OpenAI' || src === 'Anthropic') {
        const ct = CONTENT_TYPE_MAP[meta.content_type];
        if (ct) tags.push({ label: ct, type: 'category' });
        if (item.published_at) tags.push({ label: this.formatDate(item.published_at), type: 'date' });
      } else if (src === 'InfoQ AI Development') {
        const cat = INFOQ_CATEGORY_MAP[item.category];
        if (cat) tags.push({ label: cat, type: 'category' });
        if (item.published_at) tags.push({ label: this.formatDate(item.published_at), type: 'date' });
      }
      return tags;
    },
    async loadSources() {
      this.loading = true;
      this.errorMessage = '';
      try {
        const response = await fetch(`${API_PREFIX}/sources`);
        if (!response.ok) {
          throw new Error(`来源接口返回 ${response.status}`);
        }
        const payload = await response.json();
        this.sources = payload.sources || [];
        if (this.sources.length > 0) {
          await this.selectSource(this.sources[0].id);
        }
      } catch (error) {
        this.errorMessage = `加载来源失败：${error.message}`;
      } finally {
        this.loading = false;
      }
    },
    async selectSource(sourceId) {
      this.activeSourceId = sourceId;
      this.loading = true;
      this.errorMessage = '';
      try {
        const response = await fetch(`${API_PREFIX}/sources/${sourceId}/latest`);
        if (!response.ok) {
          throw new Error(`数据接口返回 ${response.status}`);
        }
        const payload = await response.json();
        this.items = payload.items || [];
        this.generatedAt = payload.generated_at || '';
      } catch (error) {
        this.items = [];
        this.generatedAt = '';
        this.errorMessage = `加载内容失败：${error.message}`;
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style>
:root {
  --primary:       #0057FF;
  --primary-soft:  #EEF3FF;
  --bg:            #F2F5FA;
  --surface:       #FFFFFF;
  --border:        #E4E8F0;
  --text-1:        #0D1117;
  --text-2:        #4B5563;
  --text-3:        #9CA3AF;
  --brand-grad:    linear-gradient(135deg, #0057FF 0%, #7C3AED 100%);
  --radius-card:   10px;
  --shadow-card:   0 1px 3px rgba(0, 0, 0, .06), 0 4px 12px rgba(0, 0, 0, .04);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  color: var(--text-1);
  background: var(--bg);
  background-image: radial-gradient(circle, #c8d0de 1px, transparent 1px);
  background-size: 28px 28px;
  font-family: 'DM Sans', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
}

a {
  color: inherit;
  text-decoration: none;
}

.app-shell {
  min-height: 100vh;
}

/* ── Topbar ───────────────────────────────── */

.topbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 0 32px;
  height: 64px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.brand-mark {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--brand-grad);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  letter-spacing: 0.5px;
}

.brand-text h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: -0.3px;
  color: var(--text-1);
  font-family: 'Bricolage Grotesque', 'DM Sans', sans-serif;
}

.brand-text p {
  margin: 2px 0 0;
  font-size: 12px;
  color: var(--text-3);
  letter-spacing: 0.2px;
}

.update-chip {
  padding: 5px 13px;
  border-radius: 20px;
  background: #F1F3F8;
  color: var(--text-2);
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  flex-shrink: 0;
}

/* ── Layout ───────────────────────────────── */

.layout {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 24px 56px;
}

/* ── Source panel ─────────────────────────── */

.source-panel {
  position: sticky;
  top: 84px;
  align-self: start;
  padding: 6px;
  border-radius: var(--radius-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
}

.source-tab {
  position: relative;
  display: flex;
  width: 100%;
  min-height: 52px;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  padding: 10px 12px 10px 16px;
  border: 0;
  border-radius: 8px;
  background: transparent;
  color: var(--text-1);
  cursor: pointer;
  text-align: left;
  transition: background 150ms ease;
  overflow: hidden;
}

.source-tab + .source-tab {
  margin-top: 2px;
}

.source-tab::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 0 2px 2px 0;
  background: transparent;
  transition: background 150ms ease;
}

.source-tab span {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.3;
}

.source-tab small {
  margin-top: 3px;
  color: var(--text-3);
  font-size: 11px;
  font-weight: 400;
}

.source-tab.active {
  background: var(--primary-soft);
  color: var(--primary);
}

.source-tab.active small {
  color: #6B9BFF;
}

.source-tab.active::before {
  background: var(--primary);
}

.source-tab:hover:not(.active) {
  background: #F7F8FB;
}

/* ── Feed panel ───────────────────────────── */

.feed-panel {
  min-width: 0;
  border-radius: var(--radius-card);
  background: var(--surface);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.feed-toolbar {
  padding: 20px 24px 18px;
  border-bottom: 1px solid var(--border);
}

.feed-toolbar h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.3px;
  color: var(--text-1);
  font-family: 'Bricolage Grotesque', 'DM Sans', sans-serif;
}

/* ── Feed item ────────────────────────────── */

.feed-item {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px;
  padding: 22px 24px;
  border-bottom: 1px solid var(--border);
  transition: background 150ms ease;
}

.feed-item:last-child {
  border-bottom: 0;
}

.feed-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: transparent;
  transition: background 150ms ease;
}

.feed-item:hover {
  background: #F6F9FF;
}

.feed-item:hover::before {
  background: var(--primary);
}

.item-title {
  display: inline;
  color: var(--text-1);
  font-size: 16px;
  line-height: 1.5;
  font-weight: 600;
  letter-spacing: -0.1px;
  transition: color 150ms ease;
}

.item-title:hover {
  color: var(--primary);
}

.item-summary {
  margin: 8px 0 0;
  color: var(--text-2);
  font-size: 14px;
  line-height: 1.7;
}

/* ── Item tags ────────────────────────────── */

.item-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 10px 0 0;
}

.item-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 9px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1.7;
  white-space: nowrap;
  border: 1px solid transparent;
}

/* 语言 tag — 灰色胶囊 + 彩色圆点 */
.item-tag--lang {
  background: #F3F4F6;
  color: #374151;
  border-color: #E5E7EB;
}

/* 圆点 */
.lang-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Stars — 暖金 */
.item-tag--stat {
  background: #FFFBEB;
  color: #92400E;
  border-color: #FDE68A;
}

/* Forks / 评论 — 蓝灰 */
.item-tag--fork {
  background: #F0F4FF;
  color: #3B5BDB;
  border-color: #C5D0FA;
}

/* Stars today — 绿色 */
.item-tag--growth {
  background: #F0FDF4;
  color: #166534;
  border-color: #BBF7D0;
}

/* 分类 — 主色蓝 */
.item-tag--category {
  background: var(--primary-soft);
  color: var(--primary);
  border-color: #C7D9FF;
}

/* 日期 — 中性灰 */
.item-tag--date {
  background: #F9FAFB;
  color: #6B7280;
  border-color: #E5E7EB;
}

.open-link {
  align-self: start;
  flex-shrink: 0;
  color: var(--primary);
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  padding: 2px 0;
  transition: opacity 150ms ease;
}

.open-link:hover {
  opacity: 0.75;
}

/* ── Skeleton ─────────────────────────────── */

@keyframes shimmer {
  0%   { background-position: -600px 0; }
  100% { background-position:  600px 0; }
}

.skeleton-card {
  padding: 22px 24px;
  border-bottom: 1px solid var(--border);
}

.skeleton-card:last-child {
  border-bottom: 0;
}

.skeleton-line {
  border-radius: 6px;
  background: linear-gradient(90deg, #EAECF0 25%, #F5F6F8 50%, #EAECF0 75%);
  background-size: 600px 100%;
  animation: shimmer 1.4s infinite linear;
}

.skeleton-line.title {
  height: 20px;
  width: 65%;
  margin-bottom: 14px;
}

.skeleton-line.body {
  height: 13px;
  width: 100%;
  margin-bottom: 8px;
}

.skeleton-line.short {
  width: 50%;
  margin-bottom: 0;
}

/* ── State box ────────────────────────────── */

.state-box {
  margin: 32px 24px;
  padding: 32px;
  border: 1px dashed var(--border);
  border-radius: 8px;
  color: var(--text-3);
  text-align: center;
  font-size: 14px;
}

.state-box.error {
  border-color: #FECACA;
  color: #B91C1C;
  background: #FEF2F2;
}

/* ── Mobile ───────────────────────────────── */

@media (max-width: 860px) {
  .topbar {
    position: static;
    height: auto;
    flex-wrap: wrap;
    padding: 12px 16px;
    gap: 8px;
  }

  .update-chip {
    font-size: 11px;
    padding: 4px 10px;
  }

  .layout {
    display: block;
    padding: 12px 16px 40px;
  }

  .source-panel {
    position: static;
    display: flex;
    gap: 8px;
    margin-bottom: 16px;
    padding: 8px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .source-tab {
    width: 140px;
    flex: 0 0 140px;
    min-height: 48px;
    border: 1px solid var(--border);
  }

  .source-tab + .source-tab {
    margin-top: 0;
  }

  .source-tab::before {
    display: none;
  }

  .feed-toolbar,
  .feed-item {
    padding: 16px;
  }

  .feed-item {
    display: block;
  }

  .open-link {
    display: inline-block;
    margin-top: 10px;
  }
}
</style>
