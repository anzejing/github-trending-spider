<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">
        <div class="brand-mark-wrapper">
          <div class="brand-mark-ring"></div>
          <div class="brand-mark">AI</div>
        </div>
        <div class="brand-text">
          <h1>{{ t('siteTitle') }}</h1>
          <p>{{ t('subtitle') }}</p>
        </div>
      </div>
      <div class="topbar-actions">
        <div class="lang-switch">
          <button :class="{ active: lang === 'zh' }" @click="switchLang('zh')">中文</button>
          <span class="lang-sep">|</span>
          <button :class="{ active: lang === 'en' }" @click="switchLang('en')">EN</button>
        </div>
        <div class="update-chip">⏱ {{ countdownText }}</div>
        <button class="history-button" type="button" @click="openHistoryDrawer">
          {{ t('historyArchive') }}
        </button>
        <a class="gh-link" href="https://github.com/wenbochang888/github-trending-spider" target="_blank" rel="noreferrer" aria-label="GitHub 仓库">
          <svg width="18" height="18" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
        </a>
      </div>
    </header>

    <div
      class="history-drawer-mask"
      :class="{ open: historyDrawerOpen }"
      @click="closeHistoryDrawer"
    >
      <aside class="history-drawer" @click.stop>
        <div class="history-drawer-head">
          <div>
            <h2>{{ t('historyDrawerTitle') }}</h2>
            <p>{{ t('historyDrawerDesc') }}</p>
          </div>
          <button class="history-drawer-close" type="button" @click="closeHistoryDrawer">×</button>
        </div>

        <div v-if="historyDatesLoading" class="history-drawer-state">
          {{ t('historyLoading') }}
        </div>
        <div v-else-if="historyDatesError" class="history-drawer-state error">
          {{ historyDatesError }}
        </div>
        <div v-else class="history-date-list">
          <button
            v-for="dateInfo in historyDates"
            :key="dateInfo.date"
            class="history-date-row"
            :class="{
              active: selectedHistoryDate === dateInfo.date,
              disabled: !dateInfo.has_archive
            }"
            type="button"
            :disabled="!dateInfo.has_archive"
            @click="selectHistoryDate(dateInfo)"
          >
            <strong>{{ formatHistoryDate(dateInfo.date) }}</strong>
            <span>{{ getHistoryDateSummary(dateInfo) }}</span>
          </button>
        </div>
      </aside>
    </div>

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
          <div>
            <h2>{{ feedTitle }}</h2>
            <p v-if="feedSubtitle" class="feed-subtitle">{{ feedSubtitle }}</p>
          </div>
          <button
            v-if="historyMode"
            class="back-today-button"
            type="button"
            @click="backToToday"
          >
            {{ t('backToToday') }}
          </button>
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
          {{ t('noContent') }}
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
            <p class="item-summary">{{ getDisplaySummary(item) }}</p>
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
            :href="getOpenUrl(item)"
            target="_blank"
            rel="noreferrer"
          >
            {{ isDiscussion(item) ? t('viewDiscussion') : t('readOriginal') }}
          </a>
        </article>
      </section>
    </main>
    <footer class="site-footer">
      <button class="footer-easter-egg" type="button" @click="showEmailHint">
        {{ t('footerEmailEgg') }}
      </button>
    </footer>
  </div>
</template>

<script>
const API_PREFIX = '/api';

// ── i18n：语言优先级 URL 参数 > localStorage > 默认 'zh' ──
function getInitialLang() {
  const params = new URLSearchParams(window.location.search);
  const urlLang = params.get('lang');
  if (urlLang === 'en' || urlLang === 'zh') return urlLang;
  const stored = localStorage.getItem('lang');
  if (stored === 'en' || stored === 'zh') return stored;
  return 'zh';
}

const I18N = {
  zh: {
    siteTitle: '每日AI前沿信息',
    subtitle: '开源趋势 · 社区热议 · AI 动态',
    updateEvery8h: '每 8 小时更新',
    countdownHour: '时',
    countdownMin: '分',
    countdownSec: '秒',
    countdownSuffix: '后更新',
    noContent: '当前来源暂无内容',
    loadSourceErr: '加载来源失败：',
    loadContentErr: '加载内容失败：',
    sourceApiErr: '来源接口返回 ',
    dataApiErr: '数据接口返回 ',
    historyApiErr: '历史接口返回 ',
    readOriginal: '阅读原文 →',
    viewDiscussion: '查看讨论 →',
    defaultLabel: '最新内容',
    historyArchive: '历史归档',
    historyDrawerTitle: '历史归档',
    historyDrawerDesc: '最近 7 天，不包含今天。选择日期后读取当天历史资讯。',
    historyLoading: '正在加载历史归档',
    historyLoadErr: '加载历史归档失败：',
    historyTitle: '历史资讯',
    backToToday: '返回今日资讯',
    noArchive: '暂无归档',
    archiveSources: ' 个来源',
    historySourcePrefix: '当前来源：',
    footerEmailEgg: '隐藏小彩蛋: 支持邮件接收AI讯息',
    emailHint: '请将您的邮箱发送至727987105@qq.com',
    comments: ' 评论',
    replies: ' 回复',
  },
  en: {
    siteTitle: 'Daily AI Frontier',
    subtitle: 'Open Source · Community · AI Updates',
    updateEvery8h: 'Updates every 8h',
    countdownHour: 'h ',
    countdownMin: 'm ',
    countdownSec: 's',
    countdownSuffix: ' until next update',
    noContent: 'No content available for this source',
    loadSourceErr: 'Failed to load sources: ',
    loadContentErr: 'Failed to load content: ',
    sourceApiErr: 'Sources API returned ',
    dataApiErr: 'Data API returned ',
    historyApiErr: 'History API returned ',
    readOriginal: 'Read More →',
    viewDiscussion: 'View Discussion →',
    defaultLabel: 'Latest',
    historyArchive: 'Archive',
    historyDrawerTitle: 'Archive',
    historyDrawerDesc: 'Last 7 days, excluding today. Pick a date to read archived news.',
    historyLoading: 'Loading archive',
    historyLoadErr: 'Failed to load archive: ',
    historyTitle: 'Archive',
    backToToday: 'Back to Today',
    noArchive: 'No archive',
    archiveSources: ' sources',
    historySourcePrefix: 'Source: ',
    footerEmailEgg: 'Hidden easter egg: Support receiving AI updates by email',
    emailHint: 'Please send your email address to 727987105@qq.com',
    comments: ' comments',
    replies: ' replies',
  }
};

const SOURCE_DISPLAY_MAP = {
  'github-daily':  { label: '今日开源热榜', category: 'GitHub · 日榜' },
  'github-weekly': { label: '本周开源精选', category: 'GitHub · 周榜' },
  'hacker-news':   { label: '硅谷社区热议', category: 'Hacker News'   },
  'linux-do':      { label: 'Linux.do 技术日报', category: '社区讨论'     },
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

// ── 英文版来源映射 ──
const SOURCE_DISPLAY_MAP_EN = {
  'github-daily':  { label: 'GitHub Daily Trending', category: 'GitHub · Daily' },
  'github-weekly': { label: 'GitHub Weekly Picks',   category: 'GitHub · Weekly' },
  'hacker-news':   { label: 'Hacker News Hot',       category: 'Hacker News' },
  'linux-do':      { label: 'Linux.do Daily',        category: 'Community' },
  'v2ex':          { label: 'V2EX Hot Topics',       category: 'V2EX' },
  'tldr-ai':       { label: 'TLDR AI Digest',        category: 'TLDR AI' },
  'openai':        { label: 'OpenAI Updates',        category: 'Official' },
  'anthropic':     { label: 'Anthropic Updates',     category: 'Official' },
  'infoq':         { label: 'AI Engineering',        category: 'InfoQ AI' },
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
      lang: getInitialLang(),
      sources: [],
      activeSourceId: '',
      items: [],
      generatedAt: '',
      loading: false,
      errorMessage: '',
      historyDrawerOpen: false,
      historyDates: [],
      historyDatesLoading: false,
      historyDatesError: '',
      historyMode: false,
      selectedHistoryDate: '',
      countdownText: '',
      countdownTimer: null
    };
  },
  computed: {
    activeSourceLabel() {
      const map = this.lang === 'en' ? SOURCE_DISPLAY_MAP_EN : SOURCE_DISPLAY_MAP;
      const override = map[this.activeSourceId];
      if (override) return override.label;
      const source = this.sources.find((s) => s.id === this.activeSourceId);
      return source ? source.label : this.t('defaultLabel');
    },
    feedTitle() {
      if (this.historyMode && this.selectedHistoryDate) {
        return `${this.t('historyTitle')} · ${this.selectedHistoryDate}`;
      }
      return this.activeSourceLabel;
    },
    feedSubtitle() {
      if (!this.historyMode) {
        return '';
      }
      return `${this.t('historySourcePrefix')}${this.activeSourceLabel}`;
    }
  },
  async created() {
    document.title = this.t('siteTitle');
    this.countdownText = this.t('updateEvery8h');
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
    t(key) {
      return (I18N[this.lang] && I18N[this.lang][key]) || I18N['zh'][key] || key;
    },
    switchLang(newLang) {
      this.lang = newLang;
      localStorage.setItem('lang', newLang);
      const url = new URL(window.location);
      url.searchParams.set('lang', newLang);
      history.replaceState(null, '', url);
      document.title = this.t('siteTitle');
      this.updateCountdown();
    },
    showEmailHint() {
      window.alert(this.t('emailHint'));
    },
    async openHistoryDrawer() {
      this.historyDrawerOpen = true;
      if (this.historyDates.length === 0 && !this.historyDatesLoading) {
        await this.loadHistoryDates();
      }
    },
    closeHistoryDrawer() {
      this.historyDrawerOpen = false;
    },
    async loadHistoryDates() {
      this.historyDatesLoading = true;
      this.historyDatesError = '';
      try {
        const response = await fetch(`${API_PREFIX}/history/dates`);
        if (!response.ok) {
          throw new Error(`${this.t('historyApiErr')}${response.status}`);
        }
        const payload = await response.json();
        this.historyDates = payload.dates || [];
      } catch (error) {
        this.historyDates = [];
        this.historyDatesError = `${this.t('historyLoadErr')}${error.message}`;
      } finally {
        this.historyDatesLoading = false;
      }
    },
    async selectHistoryDate(dateInfo) {
      if (!dateInfo || !dateInfo.has_archive) {
        return;
      }
      this.selectedHistoryDate = dateInfo.date;
      this.historyMode = true;
      this.historyDrawerOpen = false;
      await this.loadHistorySource(this.activeSourceId);
    },
    async loadHistorySource(sourceId) {
      this.activeSourceId = sourceId;
      this.loading = true;
      this.errorMessage = '';
      try {
        const response = await fetch(`${API_PREFIX}/history/sources/${sourceId}/dates/${this.selectedHistoryDate}`);
        if (!response.ok) {
          throw new Error(`${this.t('dataApiErr')}${response.status}`);
        }
        const payload = await response.json();
        this.items = payload.items || [];
        this.generatedAt = payload.generated_at || '';
      } catch (error) {
        this.items = [];
        this.generatedAt = '';
        this.errorMessage = `${this.t('loadContentErr')}${error.message}`;
      } finally {
        this.loading = false;
      }
    },
    async backToToday() {
      this.historyMode = false;
      this.selectedHistoryDate = '';
      await this.selectSource(this.activeSourceId);
    },
    formatHistoryDate(dateText) {
      if (!dateText) {
        return '';
      }
      return dateText.slice(5);
    },
    getHistoryDateSummary(dateInfo) {
      if (!dateInfo.has_archive) {
        return this.t('noArchive');
      }
      return `${dateInfo.source_count}${this.t('archiveSources')}`;
    },
    getDisplaySummary(item) {
      if (this.lang === 'zh') {
        return item.chinese_summary || item.original_summary || '';
      }
      let text = item.original_summary || item.chinese_summary || '';
      // 替换后端 original_summary 中的中文标签为英文
      text = text.replace(/语言:\s*/g, 'Language: ');
      text = text.replace(/分数:\s*/g, 'Score: ');
      text = text.replace(/评论数:\s*/g, 'Comments: ');
      text = text.replace(/作者:\s*/g, 'Author: ');
      text = text.replace(/节点:\s*/g, 'Node: ');
      text = text.replace(/分组:\s*/g, 'Section: ');
      text = text.replace(/回复数:\s*/g, 'Replies: ');
      return text;
    },
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
        this.countdownText = hours + this.t('countdownHour') + minutes + this.t('countdownMin') + this.t('countdownSuffix');
      } else if (minutes > 0) {
        this.countdownText = minutes + this.t('countdownMin') + seconds + this.t('countdownSec') + this.t('countdownSuffix');
      } else {
        this.countdownText = seconds + this.t('countdownSec') + this.t('countdownSuffix');
      }
    },
    getDisplayLabel(source) {
      const map = this.lang === 'en' ? SOURCE_DISPLAY_MAP_EN : SOURCE_DISPLAY_MAP;
      return (map[source.id] || source).label;
    },
    getDisplayCategory(source) {
      const map = this.lang === 'en' ? SOURCE_DISPLAY_MAP_EN : SOURCE_DISPLAY_MAP;
      return (map[source.id] || source).category;
    },
    isDiscussion(item) {
      return item.source === 'Hacker News' || item.source === 'Linux.do';
    },
    getOpenUrl(item) {
      if (item.source === 'Hacker News') {
        return (item.meta && item.meta.hn_url) || item.url;
      }
      return item.url;
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
        if (meta.comments != null) tags.push({ label: '💬 ' + meta.comments + this.t('comments'), type: 'fork' });
      } else if (src === 'Linux.do') {
        if (meta.section_title) tags.push({ label: meta.section_title, type: 'category' });
        if (meta.reply_count != null) tags.push({ label: '💬 ' + meta.reply_count + this.t('replies'), type: 'fork' });
        if (item.published_at) tags.push({ label: this.formatDate(item.published_at), type: 'date' });
      } else if (src === 'TLDR AI') {
        const cat = this.lang === 'en' ? item.category : TLDR_CATEGORY_MAP[item.category];
        if (cat) tags.push({ label: cat, type: 'category' });
      } else if (src === 'OpenAI' || src === 'Anthropic') {
        const ct = this.lang === 'en' ? meta.content_type : CONTENT_TYPE_MAP[meta.content_type];
        if (ct) tags.push({ label: ct, type: 'category' });
        if (item.published_at) tags.push({ label: this.formatDate(item.published_at), type: 'date' });
      } else if (src === 'InfoQ AI Development') {
        const cat = this.lang === 'en' ? item.category : INFOQ_CATEGORY_MAP[item.category];
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
          throw new Error(`${this.t('sourceApiErr')}${response.status}`);
        }
        const payload = await response.json();
        this.sources = payload.sources || [];
        if (this.sources.length > 0) {
          await this.selectSource(this.sources[0].id);
        }
      } catch (error) {
        this.errorMessage = `${this.t('loadSourceErr')}${error.message}`;
      } finally {
        this.loading = false;
      }
    },
    async selectSource(sourceId) {
      if (this.historyMode && this.selectedHistoryDate) {
        await this.loadHistorySource(sourceId);
        return;
      }
      this.activeSourceId = sourceId;
      this.loading = true;
      this.errorMessage = '';
      try {
        const response = await fetch(`${API_PREFIX}/sources/${sourceId}/latest`);
        if (!response.ok) {
          throw new Error(`${this.t('dataApiErr')}${response.status}`);
        }
        const payload = await response.json();
        this.items = payload.items || [];
        this.generatedAt = payload.generated_at || '';
      } catch (error) {
        this.items = [];
        this.generatedAt = '';
        this.errorMessage = `${this.t('loadContentErr')}${error.message}`;
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

.brand-mark-wrapper {
  position: relative;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
}

.brand-mark-ring {
  position: absolute;
  inset: -4px;
  border-radius: 14px;
  background: var(--brand-grad);
  opacity: 0.3;
  animation: pulse-ring 2s ease-in-out infinite;
}

@keyframes pulse-ring {
  0%, 100% { transform: scale(1); opacity: 0.3; }
  50% { transform: scale(1.15); opacity: 0.1; }
}

.brand-mark {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--brand-grad);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: grid;
  place-items: center;
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

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.history-button {
  border: 0;
  border-radius: 6px;
  background: transparent;
  color: var(--text-3);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  padding: 5px 8px;
  transition: color 150ms ease, background 150ms ease;
}

.history-button:hover,
.history-button:focus-visible {
  background: #F1F3F8;
  color: var(--primary);
  outline: none;
}

.gh-link {
  display: flex;
  align-items: center;
  color: var(--text-3);
  transition: color 150ms ease;
}

.gh-link:hover {
  color: var(--text-1);
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
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
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

.feed-subtitle {
  margin: 6px 0 0;
  color: var(--text-3);
  font-size: 13px;
  line-height: 1.5;
}

.back-today-button {
  flex-shrink: 0;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  padding: 7px 11px;
  transition: border-color 150ms ease, color 150ms ease, background 150ms ease;
}

.back-today-button:hover,
.back-today-button:focus-visible {
  border-color: #C7D9FF;
  background: var(--primary-soft);
  color: var(--primary);
  outline: none;
}

/* ── History drawer ───────────────────────── */

.history-drawer-mask {
  position: fixed;
  inset: 0;
  z-index: 20;
  display: none;
  background: rgba(15, 23, 42, 0.22);
}

.history-drawer-mask.open {
  display: block;
}

.history-drawer {
  position: absolute;
  top: 0;
  right: 0;
  width: min(440px, 100vw);
  height: 100%;
  overflow-y: auto;
  background: var(--surface);
  box-shadow: -18px 0 40px rgba(15, 23, 42, 0.16);
}

.history-drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 22px;
  border-bottom: 1px solid var(--border);
}

.history-drawer-head h2 {
  margin: 0;
  color: var(--text-1);
  font-size: 20px;
  line-height: 1.3;
}

.history-drawer-head p {
  margin: 6px 0 0;
  color: var(--text-3);
  font-size: 13px;
  line-height: 1.6;
}

.history-drawer-close {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text-2);
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
}

.history-drawer-close:hover,
.history-drawer-close:focus-visible {
  background: #F7F8FB;
  outline: none;
}

.history-date-list {
  padding: 14px;
}

.history-date-row {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  width: 100%;
  min-height: 62px;
  margin-bottom: 8px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: #F8FAFC;
  color: var(--text-1);
  cursor: pointer;
  text-align: left;
  transition: border-color 150ms ease, background 150ms ease;
}

.history-date-row:hover:not(:disabled) {
  border-color: #C7D9FF;
  background: #F6F9FF;
}

.history-date-row.active {
  border-color: var(--primary);
  background: var(--primary-soft);
}

.history-date-row.disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.history-date-row strong {
  font-size: 15px;
  line-height: 1.2;
}

.history-date-row span {
  min-width: 0;
  color: var(--text-3);
  font-size: 12px;
  line-height: 1.4;
}

.history-drawer-state {
  margin: 18px 14px;
  padding: 22px;
  border: 1px dashed var(--border);
  border-radius: 8px;
  color: var(--text-3);
  text-align: center;
  font-size: 14px;
}

.history-drawer-state.error {
  border-color: #FECACA;
  color: #B91C1C;
  background: #FEF2F2;
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
  white-space: pre-line;
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

  .topbar-actions {
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .history-button {
    font-size: 12px;
    padding: 4px 6px;
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

  .feed-toolbar {
    display: block;
  }

  .feed-item {
    display: block;
  }

  .back-today-button {
    margin-top: 12px;
  }

  .history-drawer {
    width: 100vw;
  }

  .open-link {
    display: inline-block;
    margin-top: 10px;
  }
}

/* ── Footer ──────────────────────────────── */
.site-footer {
  text-align: center;
  padding: 24px 0;
  color: var(--text-3);
  font-size: 13px;
  border-top: 1px solid var(--border);
  margin-top: 32px;
}

.footer-easter-egg {
  border: none;
  background: transparent;
  color: inherit;
  font: inherit;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: color 150ms ease, background 150ms ease;
}

.footer-easter-egg:hover,
.footer-easter-egg:focus-visible {
  color: var(--text-1);
  background: rgba(15, 23, 42, 0.05);
  outline: none;
}

/* ── Language Switch ─────────────────────── */
.lang-switch {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.lang-switch button {
  border: none;
  background: transparent;
  color: var(--text-3);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: 4px;
  transition: color 150ms ease, background 150ms ease;
}

.lang-switch button:hover {
  color: var(--text-1);
}

.lang-switch button.active {
  color: var(--primary);
  font-weight: 600;
}

.lang-sep {
  color: var(--text-3);
  font-size: 13px;
  user-select: none;
}
</style>
