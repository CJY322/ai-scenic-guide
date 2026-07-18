<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  Activity,
  BarChart3,
  Bot,
  CheckCircle2,
  ClipboardList,
  Database,
  FileText,
  HelpCircle,
  Home,
  KeyRound,
  ListPlus,
  LoaderCircle,
  Palette,
  Plus,
  RotateCcw,
  Save,
  Settings,
  Trash2,
} from '@lucide/vue'
import {
  fetchAnalyticsReport,
  fetchAdminSettings,
  fetchAdminStatus,
  fetchAvatarProfile,
  fetchDashboardOverview,
  fetchFaqEntries,
  fetchKnowledgeFile,
  fetchKnowledgeFiles,
  fetchRecommendedQuestions,
  getAdminErrorMessage,
  saveFaqEntries,
  saveAvatarProfile,
  saveKnowledgeFile,
  saveRecommendedQuestions,
  updateAdminSettings,
} from '../api/admin'
import type {
  AdminAnalyticsReport,
  AdminAppSettings,
  AdminAvatarProfile,
  AdminDashboardOverview,
  AdminFaqEntry,
  AdminKnowledgeFile,
  AdminSystemStatus,
  GuideEmotion,
} from '../types/admin'

type AdminTab = 'overview' | 'status' | 'knowledge' | 'faq' | 'recommended' | 'settings' | 'avatar' | 'report'
type SettingsDraft = AdminAppSettings & { dify_api_key: string }
type ChartMetric = { label: string; value: number; ratio: number; color: string }
type SvgPoint = { x: number; y: number; value: number; label: string }

const tabs: Array<{ id: AdminTab; label: string; icon: unknown }> = [
  { id: 'overview', label: '数据大屏', icon: BarChart3 },
  { id: 'status', label: '运行状态', icon: Activity },
  { id: 'knowledge', label: '知识库资料', icon: Database },
  { id: 'faq', label: '常见问题', icon: HelpCircle },
  { id: 'recommended', label: '推荐问题', icon: ListPlus },
  { id: 'settings', label: 'Dify配置', icon: KeyRound },
  { id: 'avatar', label: '数字人形象', icon: Palette },
  { id: 'report', label: '感受度报告', icon: ClipboardList },
]
const emotions: GuideEmotion[] = ['neutral', 'friendly', 'happy', 'concerned', 'serious']
const chartColors = ['#176b4d', '#c65f36', '#2f7da1', '#8a6f22', '#6f5ca8', '#4f7c61', '#b24f4a', '#5e7c8a']
const sentimentColors: Record<string, string> = {
  positive: '#176b4d',
  neutral: '#2f7da1',
  concerned: '#c65f36',
}
const lineChartWidth = 560
const lineChartHeight = 240
const lineChartPadding = 34

const activeTab = ref<AdminTab>('overview')
const status = ref<AdminSystemStatus | null>(null)
const settingsDraft = ref<SettingsDraft | null>(null)
const avatarProfile = ref<AdminAvatarProfile | null>(null)
const analyticsReport = ref<AdminAnalyticsReport | null>(null)
const dashboardOverview = ref<AdminDashboardOverview | null>(null)
const knowledgeFiles = ref<AdminKnowledgeFile[]>([])
const activeKnowledgePath = ref('')
const knowledgeContent = ref('')
const newKnowledgePath = ref('new-note.md')
const faqEntries = ref<AdminFaqEntry[]>([])
const recommendedQuestions = ref<string[]>([])
const isLoading = ref(true)
const busyKey = ref<string | null>(null)
const notice = ref('')
const errorMessage = ref('')

const activeKnowledgeFile = computed(() =>
  knowledgeFiles.value.find((file) => file.path === activeKnowledgePath.value),
)
const statusCards = computed(() => {
  const current = status.value
  if (!current) {
    return []
  }
  return [
    {
      label: '接口服务',
      value: current.api.status === 'ok' ? '正常' : '异常',
      detail: current.api.message,
      ok: current.api.status === 'ok',
    },
    {
      label: 'Dify RAG',
      value: current.dify.enabled ? '已启用' : '未启用',
      detail: current.dify.api_key_configured ? 'API Key 已配置' : 'API Key 未配置',
      ok: current.dify.enabled && current.dify.api_key_configured,
    },
    {
      label: '数字人',
      value: current.avatar.enabled ? '已启用' : '轻量模式',
      detail: current.avatar.message,
      ok: current.avatar.enabled || current.avatar.supports_video,
    },
    {
      label: '内容资料',
      value: `${current.content.knowledge_file_count} 个文件`,
      detail: `${current.content.faq_entry_count} 条 FAQ / ${current.content.recommended_question_count} 条推荐问题`,
      ok: current.content.knowledge_file_count > 0,
    },
  ]
})
const overviewCards = computed(() => {
  const overview = dashboardOverview.value
  const report = analyticsReport.value
  if (!overview || !report) {
    return []
  }
  return [
    {
      label: '今日服务人次',
      value: String(overview.today_service_count),
      detail: `${overview.unique_sessions_today} 个独立会话`,
    },
    {
      label: '本周服务量',
      value: String(overview.week_service_count),
      detail: '近 7 日问答总量',
    },
    {
      label: '满意度估算',
      value: `${report.estimated_satisfaction_score}`,
      detail: '基于情绪与兜底率估算',
    },
    {
      label: '知识未命中率',
      value: formatPercent(report.fallback_rate),
      detail: '回答进入兜底的比例',
    },
  ]
})
const topicChartMetrics = computed<ChartMetric[]>(() =>
  (dashboardOverview.value?.topic_metrics ?? []).slice(0, 8).map((topic, index) => ({
    label: topic.topic,
    value: topic.count,
    ratio: topic.ratio,
    color: chartColors[index % chartColors.length],
  })),
)
const reportTopicChartMetrics = computed<ChartMetric[]>(() =>
  (analyticsReport.value?.topic_metrics ?? []).slice(0, 8).map((topic, index) => ({
    label: topic.topic,
    value: topic.count,
    ratio: topic.ratio,
    color: chartColors[index % chartColors.length],
  })),
)
const sentimentChartMetrics = computed<ChartMetric[]>(() =>
  (analyticsReport.value?.sentiment_metrics ?? []).map((item) => ({
    label: sentimentLabel(item.label),
    value: item.count,
    ratio: item.ratio,
    color: sentimentColors[item.label] ?? chartColors[0],
  })),
)
const topicDonutStyle = computed(() => ({ background: createDonutGradient(topicChartMetrics.value) }))
const reportTopicDonutStyle = computed(() => ({ background: createDonutGradient(reportTopicChartMetrics.value) }))
const sentimentDonutStyle = computed(() => ({ background: createDonutGradient(sentimentChartMetrics.value) }))
const trendChart = computed(() => createTrendChart(dashboardOverview.value?.satisfaction_trend ?? []))

onMounted(() => {
  void loadDashboard()
})

async function loadDashboard() {
  isLoading.value = true
  clearMessages()
  try {
    await Promise.all([
      refreshStatus(),
      refreshAnalytics(),
      loadSettings(),
      loadAvatarProfile(),
      loadKnowledgeFiles(),
      loadFaq(),
      loadRecommendedQuestions(),
    ])
    showNotice('管理后台已加载')
  } catch (error) {
    showError(getAdminErrorMessage(error))
  } finally {
    isLoading.value = false
  }
}

async function refreshStatus() {
  status.value = await fetchAdminStatus()
}

async function refreshAnalytics() {
  const [overview, report] = await Promise.all([fetchDashboardOverview(), fetchAnalyticsReport()])
  dashboardOverview.value = overview
  analyticsReport.value = report
}

async function loadSettings() {
  const settings = await fetchAdminSettings()
  settingsDraft.value = { ...settings, dify_api_key: '' }
}

async function loadAvatarProfile() {
  avatarProfile.value = await fetchAvatarProfile()
}

async function saveAvatarProfileDraft() {
  if (!avatarProfile.value) {
    return
  }

  busyKey.value = 'avatar-profile'
  clearMessages()
  try {
    avatarProfile.value = await saveAvatarProfile(avatarProfile.value)
    showNotice('数字人形象档案已保存')
  } catch (error) {
    showError(getAdminErrorMessage(error))
  } finally {
    busyKey.value = null
  }
}

async function saveSettings(tab: AdminTab) {
  if (!settingsDraft.value) {
    return
  }

  busyKey.value = tab
  clearMessages()
  try {
    const draft = settingsDraft.value
    const saved = await updateAdminSettings({
      answer_provider: draft.answer_provider,
      dify_api_base_url: draft.dify_api_base_url,
      dify_api_key: draft.dify_api_key.trim() || undefined,
      dify_timeout_seconds: Number(draft.dify_timeout_seconds),
      avatar_provider: draft.avatar_provider,
      avatar_assets_path: draft.avatar_assets_path,
      generated_assets_path: draft.generated_assets_path,
      sadtalker_root: draft.sadtalker_root ?? '',
      sadtalker_python: draft.sadtalker_python,
      sadtalker_source_image: draft.sadtalker_source_image ?? '',
      sadtalker_timeout_seconds: Number(draft.sadtalker_timeout_seconds),
      sadtalker_preprocess: draft.sadtalker_preprocess,
      sadtalker_expression_scale: Number(draft.sadtalker_expression_scale),
      sadtalker_still: draft.sadtalker_still,
      sadtalker_use_cpu: draft.sadtalker_use_cpu,
    })
    settingsDraft.value = { ...saved, dify_api_key: '' }
    await refreshStatus()
    showNotice('配置已保存')
  } catch (error) {
    showError(getAdminErrorMessage(error))
  } finally {
    busyKey.value = null
  }
}

async function loadKnowledgeFiles() {
  knowledgeFiles.value = await fetchKnowledgeFiles()
  if (!activeKnowledgePath.value && knowledgeFiles.value[0]) {
    await selectKnowledgeFile(knowledgeFiles.value[0].path)
  }
}

async function selectKnowledgeFile(path: string) {
  busyKey.value = `knowledge:${path}`
  clearMessages()
  try {
    const file = await fetchKnowledgeFile(path)
    activeKnowledgePath.value = file.path
    knowledgeContent.value = file.content
  } catch (error) {
    showError(getAdminErrorMessage(error))
  } finally {
    busyKey.value = null
  }
}

async function saveActiveKnowledgeFile() {
  if (!activeKnowledgePath.value) {
    return
  }

  busyKey.value = 'knowledge-save'
  clearMessages()
  try {
    const saved = await saveKnowledgeFile(activeKnowledgePath.value, knowledgeContent.value)
    activeKnowledgePath.value = saved.path
    knowledgeContent.value = saved.content
    await loadKnowledgeFiles()
    await refreshStatus()
    showNotice('知识库文件已保存')
  } catch (error) {
    showError(getAdminErrorMessage(error))
  } finally {
    busyKey.value = null
  }
}

async function createKnowledgeFile() {
  const path = newKnowledgePath.value.trim()
  if (!path) {
    showError('请输入文件名')
    return
  }

  busyKey.value = 'knowledge-create'
  clearMessages()
  try {
    const saved = await saveKnowledgeFile(path, `# ${path.replace(/\.(md|txt)$/i, '')}\n\n`)
    newKnowledgePath.value = 'new-note.md'
    await loadKnowledgeFiles()
    await selectKnowledgeFile(saved.path)
    await refreshStatus()
    showNotice('知识库文件已创建')
  } catch (error) {
    showError(getAdminErrorMessage(error))
  } finally {
    busyKey.value = null
  }
}

async function loadFaq() {
  faqEntries.value = await fetchFaqEntries()
}

async function saveFaq() {
  busyKey.value = 'faq'
  clearMessages()
  try {
    faqEntries.value = await saveFaqEntries(
      faqEntries.value
        .map((entry) => ({
          keywords: entry.keywords.map((keyword) => keyword.trim()).filter(Boolean),
          answer: entry.answer.trim(),
          source: {
            title: entry.source.title.trim() || '管理后台',
            section: entry.source.section?.trim() || null,
          },
          emotion: entry.emotion,
        }))
        .filter((entry) => entry.answer),
    )
    await refreshStatus()
    showNotice('常见问题已保存')
  } catch (error) {
    showError(getAdminErrorMessage(error))
  } finally {
    busyKey.value = null
  }
}

function addFaqEntry() {
  faqEntries.value.unshift({
    keywords: ['新问题'],
    answer: '请填写答案。',
    source: { title: '灵山胜境管理后台', section: 'FAQ' },
    emotion: 'friendly',
  })
}

function removeFaqEntry(index: number) {
  faqEntries.value.splice(index, 1)
}

function updateFaqKeywords(index: number, value: string) {
  faqEntries.value[index].keywords = value
    .split(/[，,]/)
    .map((keyword) => keyword.trim())
    .filter(Boolean)
}

async function loadRecommendedQuestions() {
  recommendedQuestions.value = await fetchRecommendedQuestions()
}

async function saveRecommended() {
  busyKey.value = 'recommended'
  clearMessages()
  try {
    recommendedQuestions.value = await saveRecommendedQuestions(
      recommendedQuestions.value.map((question) => question.trim()).filter(Boolean),
    )
    await refreshStatus()
    showNotice('推荐问题已保存')
  } catch (error) {
    showError(getAdminErrorMessage(error))
  } finally {
    busyKey.value = null
  }
}

function addRecommendedQuestion() {
  recommendedQuestions.value.push('新的推荐问题')
}

function removeRecommendedQuestion(index: number) {
  recommendedQuestions.value.splice(index, 1)
}

function clearMessages() {
  notice.value = ''
  errorMessage.value = ''
}

function showNotice(message: string) {
  notice.value = message
  errorMessage.value = ''
}

function showError(message: string) {
  errorMessage.value = message
  notice.value = ''
}

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`
}

function sentimentLabel(label: string) {
  const labels: Record<string, string> = {
    positive: '积极',
    neutral: '中性',
    concerned: '疑虑',
  }
  return labels[label] ?? label
}

function priorityLabel(priority: string) {
  const labels: Record<string, string> = {
    high: '高优先级',
    medium: '中优先级',
    low: '低优先级',
  }
  return labels[priority] ?? priority
}

function createDonutGradient(items: ChartMetric[]) {
  if (!items.length) {
    return 'conic-gradient(#e5efe9 0deg 360deg)'
  }

  let cursor = 0
  const segments = items.map((item) => {
    const start = cursor
    const end = Math.min(360, cursor + item.ratio * 360)
    cursor = end
    return `${item.color} ${start.toFixed(1)}deg ${end.toFixed(1)}deg`
  })
  if (cursor < 360) {
    segments.push(`#e5efe9 ${cursor.toFixed(1)}deg 360deg`)
  }
  return `conic-gradient(${segments.join(', ')})`
}

function createTrendChart(points: AdminDashboardOverview['satisfaction_trend']) {
  const labels = points.map((point) => point.date.slice(5))
  const linePoints = points.map((point, index) => {
    const x = scaleX(index, points.length)
    const y = scaleY(point.satisfaction_score, 0, 100)
    return { x, y, value: point.satisfaction_score, label: point.date.slice(5) }
  })
  const maxServiceCount = Math.max(1, ...points.map((point) => point.service_count))
  const barWidth = Math.max(18, (lineChartWidth - lineChartPadding * 2) / Math.max(1, points.length) * 0.42)
  const bars = points.map((point, index) => {
    const x = scaleX(index, points.length) - barWidth / 2
    const height = (point.service_count / maxServiceCount) * (lineChartHeight - lineChartPadding * 2) * 0.54
    const y = lineChartHeight - lineChartPadding - height
    return { x, y, width: barWidth, height, value: point.service_count, label: point.date.slice(5) }
  })
  const linePath = createLinePath(linePoints)
  const areaPath = createAreaPath(linePoints)

  return { labels, linePoints, bars, linePath, areaPath }
}

function scaleX(index: number, length: number) {
  if (length <= 1) {
    return lineChartWidth / 2
  }
  return lineChartPadding + index * ((lineChartWidth - lineChartPadding * 2) / (length - 1))
}

function scaleY(value: number, min: number, max: number) {
  const ratio = (value - min) / Math.max(1, max - min)
  return lineChartHeight - lineChartPadding - ratio * (lineChartHeight - lineChartPadding * 2)
}

function createLinePath(points: SvgPoint[]) {
  if (!points.length) {
    return ''
  }
  return points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(' ')
}

function createAreaPath(points: SvgPoint[]) {
  if (!points.length) {
    return ''
  }
  const baseline = lineChartHeight - lineChartPadding
  return `${createLinePath(points)} L ${points[points.length - 1].x.toFixed(1)} ${baseline} L ${points[0].x.toFixed(1)} ${baseline} Z`
}
</script>

<template>
  <main class="admin-shell">
    <aside class="admin-sidebar">
      <div class="admin-brand">
        <div class="admin-brand__icon">
          <Settings :size="25" />
        </div>
        <div>
          <p class="guide-kicker">灵山胜境</p>
          <h1>管理后台</h1>
        </div>
      </div>

      <nav class="admin-nav" aria-label="管理模块">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          :class="['admin-nav__button', { 'admin-nav__button--active': activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          <component :is="tab.icon" :size="18" />
          <span>{{ tab.label }}</span>
        </button>
      </nav>

      <a class="admin-home-link" href="/">
        <Home :size="17" />
        返回游客端
      </a>
    </aside>

    <section class="admin-main" aria-label="后台内容">
      <header class="admin-header">
        <div>
          <p class="guide-kicker">后台配置</p>
          <h2>{{ tabs.find((tab) => tab.id === activeTab)?.label }}</h2>
        </div>
        <button type="button" class="admin-action-button" :disabled="isLoading" @click="loadDashboard">
          <RotateCcw :size="16" :class="{ 'spin-icon': isLoading }" />
          刷新
        </button>
      </header>

      <div v-if="notice || errorMessage" class="admin-toast" :class="{ 'admin-toast--error': errorMessage }">
        <CheckCircle2 v-if="notice" :size="17" />
        <span>{{ notice || errorMessage }}</span>
      </div>

      <div v-if="isLoading" class="admin-loading">
        <LoaderCircle :size="22" class="spin-icon" />
        <span>加载中</span>
      </div>

      <template v-else>
        <section v-if="activeTab === 'overview'" class="admin-section">
          <div class="admin-stat-grid">
            <article v-for="card in overviewCards" :key="card.label" class="admin-stat-card admin-stat-card--large">
              <span class="admin-stat-card__label">{{ card.label }}</span>
              <strong>{{ card.value }}</strong>
              <span>{{ card.detail }}</span>
            </article>
          </div>

          <div class="admin-dashboard-grid">
            <section class="admin-metric-panel">
              <div class="admin-panel-title">
                <BarChart3 :size="17" />
                <strong>热门问答</strong>
              </div>
              <div v-if="dashboardOverview?.hot_questions.length" class="admin-ranking-list">
                <div v-for="(item, index) in dashboardOverview.hot_questions" :key="item.question" class="admin-ranking-row">
                  <span>{{ index + 1 }}</span>
                  <strong>{{ item.question }}</strong>
                  <em>{{ item.count }} 次</em>
                </div>
              </div>
              <p v-else class="admin-empty-text">暂无真实问答记录，游客端产生对话后会自动统计。</p>
            </section>

            <section class="admin-metric-panel">
              <div class="admin-panel-title">
                <Activity :size="17" />
                <strong>关注点占比</strong>
              </div>
              <div v-if="topicChartMetrics.length" class="admin-donut-layout">
                <div class="admin-donut-chart" :style="topicDonutStyle">
                  <div class="admin-donut-chart__center">
                    <strong>{{ dashboardOverview?.week_service_count ?? 0 }}</strong>
                    <span>本周咨询</span>
                  </div>
                </div>
                <div class="admin-chart-legend">
                  <div v-for="item in topicChartMetrics" :key="item.label" class="admin-chart-legend__row">
                    <i :style="{ background: item.color }"></i>
                    <span>{{ item.label }}</span>
                    <strong>{{ formatPercent(item.ratio) }}</strong>
                  </div>
                </div>
              </div>
              <p v-else class="admin-empty-text">暂无关注点数据。</p>
            </section>

            <section class="admin-metric-panel admin-metric-panel--wide">
              <div class="admin-panel-title">
                <CheckCircle2 :size="17" />
                <strong>近 7 日服务量 / 满意度趋势</strong>
              </div>
              <div class="admin-combo-chart">
                <svg
                  class="admin-line-chart"
                  :viewBox="`0 0 ${lineChartWidth} ${lineChartHeight}`"
                  role="img"
                  aria-label="近 7 日服务量和满意度趋势图"
                >
                  <line x1="34" y1="206" x2="526" y2="206" class="admin-chart-axis" />
                  <line x1="34" y1="34" x2="34" y2="206" class="admin-chart-axis" />
                  <line x1="34" y1="120" x2="526" y2="120" class="admin-chart-gridline" />
                  <rect
                    v-for="bar in trendChart.bars"
                    :key="`bar-${bar.label}`"
                    class="admin-service-bar"
                    :x="bar.x"
                    :y="bar.y"
                    :width="bar.width"
                    :height="bar.height"
                    rx="5"
                  />
                  <path v-if="trendChart.areaPath" class="admin-line-area" :d="trendChart.areaPath" />
                  <path v-if="trendChart.linePath" class="admin-line-path" :d="trendChart.linePath" />
                  <g v-for="point in trendChart.linePoints" :key="point.label">
                    <circle class="admin-line-point" :cx="point.x" :cy="point.y" r="4.5" />
                    <text class="admin-line-value" :x="point.x" :y="point.y - 10" text-anchor="middle">
                      {{ point.value }}
                    </text>
                  </g>
                  <text
                    v-for="point in dashboardOverview?.satisfaction_trend ?? []"
                    :key="`label-${point.date}`"
                    class="admin-axis-label"
                    :x="trendChart.linePoints.find((item) => item.label === point.date.slice(5))?.x ?? 34"
                    y="228"
                    text-anchor="middle"
                  >
                    {{ point.date.slice(5) }}
                  </text>
                </svg>
                <div class="admin-chart-caption">
                  <span><i class="admin-caption-line"></i>满意度估算</span>
                  <span><i class="admin-caption-bar"></i>服务人次</span>
                </div>
              </div>
            </section>
          </div>
        </section>

        <section v-else-if="activeTab === 'status'" class="admin-section">
          <div class="admin-stat-grid">
            <article v-for="card in statusCards" :key="card.label" class="admin-stat-card">
              <span class="admin-stat-card__label">{{ card.label }}</span>
              <strong :class="{ 'admin-stat-card__value--warn': !card.ok }">{{ card.value }}</strong>
              <span>{{ card.detail }}</span>
            </article>
          </div>

          <div v-if="status" class="admin-info-grid">
            <div class="admin-info-row">
              <span>知识库目录</span>
              <code>{{ status.content.knowledge_path }}</code>
            </div>
            <div class="admin-info-row">
              <span>FAQ 文件</span>
              <code>{{ status.content.faq_path }}</code>
            </div>
            <div class="admin-info-row">
              <span>Dify 地址</span>
              <code>{{ status.dify.api_base_url }}</code>
            </div>
            <div class="admin-info-row">
              <span>缓存视频</span>
              <code>{{ status.avatar.generated_video_count }} 个</code>
            </div>
          </div>
        </section>

        <section v-else-if="activeTab === 'knowledge'" class="admin-section admin-editor-layout">
          <div class="admin-file-list">
            <div class="admin-inline-form">
              <input v-model="newKnowledgePath" type="text" />
              <button type="button" class="admin-icon-button" :disabled="busyKey === 'knowledge-create'" @click="createKnowledgeFile">
                <Plus :size="16" />
              </button>
            </div>
            <button
              v-for="file in knowledgeFiles"
              :key="file.path"
              type="button"
              :class="['admin-file-button', { 'admin-file-button--active': activeKnowledgePath === file.path }]"
              @click="selectKnowledgeFile(file.path)"
            >
              <FileText :size="16" />
              <span>{{ file.name }}</span>
            </button>
          </div>

          <div class="admin-editor">
            <div class="admin-editor__bar">
              <div>
                <strong>{{ activeKnowledgeFile?.name || '未选择文件' }}</strong>
                <span v-if="activeKnowledgeFile">{{ activeKnowledgeFile.size_bytes }} bytes</span>
              </div>
              <button type="button" class="admin-action-button" :disabled="!activeKnowledgePath || busyKey === 'knowledge-save'" @click="saveActiveKnowledgeFile">
                <Save :size="16" />
                保存
              </button>
            </div>
            <textarea v-model="knowledgeContent" class="admin-code-editor" spellcheck="false"></textarea>
          </div>
        </section>

        <section v-else-if="activeTab === 'faq'" class="admin-section">
          <div class="admin-section-toolbar">
            <button type="button" class="admin-action-button" @click="addFaqEntry">
              <Plus :size="16" />
              新增
            </button>
            <button type="button" class="admin-action-button admin-action-button--primary" :disabled="busyKey === 'faq'" @click="saveFaq">
              <Save :size="16" />
              保存 FAQ
            </button>
          </div>

          <div class="admin-faq-list">
            <article v-for="(entry, index) in faqEntries" :key="index" class="admin-faq-item">
              <div class="admin-faq-item__header">
                <input :value="entry.keywords.join('，')" type="text" @input="updateFaqKeywords(index, ($event.target as HTMLInputElement).value)" />
                <select v-model="entry.emotion">
                  <option v-for="emotion in emotions" :key="emotion" :value="emotion">{{ emotion }}</option>
                </select>
                <button type="button" class="admin-icon-button admin-icon-button--danger" @click="removeFaqEntry(index)">
                  <Trash2 :size="16" />
                </button>
              </div>
              <textarea v-model="entry.answer" rows="4"></textarea>
              <div class="admin-two-columns">
                <input v-model="entry.source.title" type="text" />
                <input v-model="entry.source.section" type="text" />
              </div>
            </article>
          </div>
        </section>

        <section v-else-if="activeTab === 'recommended'" class="admin-section">
          <div class="admin-section-toolbar">
            <button type="button" class="admin-action-button" @click="addRecommendedQuestion">
              <Plus :size="16" />
              新增
            </button>
            <button type="button" class="admin-action-button admin-action-button--primary" :disabled="busyKey === 'recommended'" @click="saveRecommended">
              <Save :size="16" />
              保存推荐问题
            </button>
          </div>

          <div class="admin-question-list">
            <div v-for="(_, index) in recommendedQuestions" :key="index" class="admin-question-row">
              <input v-model="recommendedQuestions[index]" type="text" />
              <button type="button" class="admin-icon-button admin-icon-button--danger" @click="removeRecommendedQuestion(index)">
                <Trash2 :size="16" />
              </button>
            </div>
          </div>
        </section>

        <section v-else-if="activeTab === 'report'" class="admin-section">
          <div class="admin-report-summary" v-if="analyticsReport">
            <article>
              <span>累计交互</span>
              <strong>{{ analyticsReport.total_interactions }}</strong>
            </article>
            <article>
              <span>本周交互</span>
              <strong>{{ analyticsReport.week_interactions }}</strong>
            </article>
            <article>
              <span>平均响应</span>
              <strong>{{ analyticsReport.avg_latency_ms }}ms</strong>
            </article>
            <article>
              <span>满意度估算</span>
              <strong>{{ analyticsReport.estimated_satisfaction_score }}</strong>
            </article>
          </div>

          <div class="admin-dashboard-grid" v-if="analyticsReport">
            <section class="admin-metric-panel">
              <div class="admin-panel-title">
                <CheckCircle2 :size="17" />
                <strong>情感趋势报告</strong>
              </div>
              <div class="admin-donut-layout">
                <div class="admin-donut-chart admin-donut-chart--sentiment" :style="sentimentDonutStyle">
                  <div class="admin-donut-chart__center">
                    <strong>{{ analyticsReport.estimated_satisfaction_score }}</strong>
                    <span>满意度</span>
                  </div>
                </div>
                <div class="admin-chart-legend">
                  <div v-for="item in sentimentChartMetrics" :key="item.label" class="admin-chart-legend__row">
                    <i :style="{ background: item.color }"></i>
                    <span>{{ item.label }}</span>
                    <strong>{{ item.value }} / {{ formatPercent(item.ratio) }}</strong>
                  </div>
                </div>
              </div>
            </section>

            <section class="admin-metric-panel">
              <div class="admin-panel-title">
                <Database :size="17" />
                <strong>游客关注点分析</strong>
              </div>
              <div v-if="reportTopicChartMetrics.length" class="admin-donut-layout">
                <div class="admin-donut-chart admin-donut-chart--compact" :style="reportTopicDonutStyle">
                  <div class="admin-donut-chart__center">
                    <strong>{{ analyticsReport.week_interactions }}</strong>
                    <span>本周</span>
                  </div>
                </div>
                <div class="admin-chart-legend">
                  <div v-for="topic in reportTopicChartMetrics" :key="topic.label" class="admin-chart-legend__row">
                    <i :style="{ background: topic.color }"></i>
                    <span>{{ topic.label }}</span>
                    <strong>{{ topic.value }} 次</strong>
                  </div>
                </div>
              </div>
              <p v-else class="admin-empty-text">暂无关注点数据。</p>
            </section>

            <section class="admin-metric-panel admin-metric-panel--wide">
              <div class="admin-panel-title">
                <ClipboardList :size="17" />
                <strong>服务建议</strong>
              </div>
              <div class="admin-suggestion-list">
                <article v-for="suggestion in analyticsReport.service_suggestions" :key="suggestion.title" class="admin-suggestion-item">
                  <span :class="['admin-priority', `admin-priority--${suggestion.priority}`]">
                    {{ priorityLabel(suggestion.priority) }}
                  </span>
                  <strong>{{ suggestion.title }}</strong>
                  <p>{{ suggestion.detail }}</p>
                </article>
              </div>
            </section>

            <section class="admin-metric-panel admin-metric-panel--wide">
              <div class="admin-panel-title">
                <HelpCircle :size="17" />
                <strong>高频原始问题</strong>
              </div>
              <div v-if="analyticsReport.hot_questions.length" class="admin-ranking-list">
                <div v-for="(item, index) in analyticsReport.hot_questions" :key="item.question" class="admin-ranking-row">
                  <span>{{ index + 1 }}</span>
                  <strong>{{ item.question }}</strong>
                  <em>{{ item.count }} 次</em>
                </div>
              </div>
              <p v-else class="admin-empty-text">暂无问答记录，游客端开始使用后会自动生成。</p>
            </section>
          </div>
        </section>

        <section v-else-if="activeTab === 'settings' && settingsDraft" class="admin-section admin-form-grid">
          <label class="admin-field">
            <span>回答来源</span>
            <select v-model="settingsDraft.answer_provider">
              <option value="mock">本地 FAQ</option>
              <option value="dify">Dify RAG</option>
            </select>
          </label>
          <label class="admin-field">
            <span>Dify API Base URL</span>
            <input v-model="settingsDraft.dify_api_base_url" type="text" />
          </label>
          <label class="admin-field">
            <span>Dify API Key</span>
            <input v-model="settingsDraft.dify_api_key" type="password" :placeholder="settingsDraft.dify_api_key_masked || '未配置'" />
          </label>
          <label class="admin-field">
            <span>Dify 超时秒数</span>
            <input v-model.number="settingsDraft.dify_timeout_seconds" min="3" max="180" type="number" />
          </label>
          <div class="admin-section-toolbar admin-section-toolbar--end">
            <button type="button" class="admin-action-button admin-action-button--primary" :disabled="busyKey === 'settings'" @click="saveSettings('settings')">
              <Save :size="16" />
              保存 Dify 配置
            </button>
          </div>
        </section>

        <section v-else-if="activeTab === 'avatar' && settingsDraft && avatarProfile" class="admin-section admin-avatar-layout">
          <div class="admin-metric-panel">
            <div class="admin-panel-title">
              <Palette :size="17" />
              <strong>形象与文化设定</strong>
            </div>
            <div class="admin-form-grid admin-form-grid--single">
              <label class="admin-field">
                <span>数字人名称</span>
                <input v-model="avatarProfile.display_name" type="text" />
              </label>
              <label class="admin-field">
                <span>人格设定</span>
                <textarea v-model="avatarProfile.persona" rows="3"></textarea>
              </label>
              <label class="admin-field">
                <span>外观风格</span>
                <textarea v-model="avatarProfile.appearance_style" rows="3"></textarea>
              </label>
              <label class="admin-field">
                <span>服装风格</span>
                <textarea v-model="avatarProfile.clothing_style" rows="3"></textarea>
              </label>
              <label class="admin-field">
                <span>景区文化元素</span>
                <textarea v-model="avatarProfile.scenic_elements" rows="3"></textarea>
              </label>
              <label class="admin-field">
                <span>欢迎语</span>
                <textarea v-model="avatarProfile.welcome_line" rows="3"></textarea>
              </label>
              <label class="admin-field">
                <span>待机/回答动作</span>
                <textarea v-model="avatarProfile.idle_behavior" rows="3"></textarea>
              </label>
              <label class="admin-field">
                <span>文化讲解注意事项</span>
                <textarea v-model="avatarProfile.culture_notes" rows="3"></textarea>
              </label>
            </div>
          </div>

          <div class="admin-metric-panel">
            <div class="admin-panel-title">
              <Bot :size="17" />
              <strong>声音与引擎参数</strong>
            </div>
            <div class="admin-form-grid admin-form-grid--single">
              <label class="admin-field">
                <span>声音名称</span>
                <input v-model="avatarProfile.voice_name" type="text" />
              </label>
              <label class="admin-field">
                <span>声音风格</span>
                <textarea v-model="avatarProfile.voice_style" rows="3"></textarea>
              </label>
              <div class="admin-three-columns">
                <label class="admin-field">
                  <span>语速</span>
                  <input v-model.number="avatarProfile.voice_rate" min="0.5" max="1.5" step="0.05" type="number" />
                </label>
                <label class="admin-field">
                  <span>音调</span>
                  <input v-model.number="avatarProfile.voice_pitch" min="0.5" max="1.5" step="0.05" type="number" />
                </label>
                <label class="admin-field">
                  <span>音量</span>
                  <input v-model.number="avatarProfile.voice_volume" min="0" max="1" step="0.05" type="number" />
                </label>
              </div>

              <label class="admin-field">
                <span>数字人引擎</span>
                <select v-model="settingsDraft.avatar_provider">
                  <option value="disabled">关闭</option>
                  <option value="sadtalker">SadTalker</option>
                </select>
              </label>
              <label class="admin-field">
                <span>头像资源目录</span>
                <input v-model="settingsDraft.avatar_assets_path" type="text" />
              </label>
              <label class="admin-field">
                <span>生成视频目录</span>
                <input v-model="settingsDraft.generated_assets_path" type="text" />
              </label>
              <label class="admin-field">
                <span>SadTalker 根目录</span>
                <input v-model="settingsDraft.sadtalker_root" type="text" />
              </label>
              <label class="admin-field">
                <span>SadTalker Python</span>
                <input v-model="settingsDraft.sadtalker_python" type="text" />
              </label>
              <label class="admin-field">
                <span>导游源图</span>
                <input v-model="settingsDraft.sadtalker_source_image" type="text" />
              </label>
              <div class="admin-three-columns">
                <label class="admin-field">
                  <span>预处理</span>
                  <select v-model="settingsDraft.sadtalker_preprocess">
                    <option value="full">full</option>
                    <option value="crop">crop</option>
                    <option value="resize">resize</option>
                  </select>
                </label>
                <label class="admin-field">
                  <span>表情强度</span>
                  <input v-model.number="settingsDraft.sadtalker_expression_scale" min="0.2" max="5" step="0.1" type="number" />
                </label>
                <label class="admin-field">
                  <span>超时秒数</span>
                  <input v-model.number="settingsDraft.sadtalker_timeout_seconds" min="30" max="3600" type="number" />
                </label>
              </div>
              <div class="admin-two-columns">
                <label class="admin-check-field">
                  <input v-model="settingsDraft.sadtalker_still" type="checkbox" />
                  <span>Still 模式</span>
                </label>
                <label class="admin-check-field">
                  <input v-model="settingsDraft.sadtalker_use_cpu" type="checkbox" />
                  <span>使用 CPU</span>
                </label>
              </div>
              <div class="admin-section-toolbar admin-section-toolbar--end">
                <button type="button" class="admin-action-button" :disabled="busyKey === 'avatar-profile'" @click="saveAvatarProfileDraft">
                  <Save :size="16" />
                  保存形象档案
                </button>
                <button type="button" class="admin-action-button admin-action-button--primary" :disabled="busyKey === 'avatar'" @click="saveSettings('avatar')">
                  <Save :size="16" />
                  保存引擎配置
                </button>
              </div>
            </div>
          </div>
        </section>
      </template>
    </section>
  </main>
</template>
