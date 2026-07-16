<script setup lang="ts">
import { nextTick, ref } from 'vue'
import { MapPin, Route, ShieldCheck, Sparkles, Wifi } from '@lucide/vue'
import { getChatErrorMessage, sendChatMessage } from '../api/chat'
import ChatInput from '../components/ChatInput.vue'
import MessageBubble from '../components/MessageBubble.vue'
import SuggestedQuestions from '../components/SuggestedQuestions.vue'
import type { ChatMessage } from '../types/chat'

const SESSION_STORAGE_KEY = 'ai-scenic-guide-session-id'

const suggestedQuestions = [
  '景区有哪些值得参观的景点？',
  '景区几点开放？',
  '带老人游览需要注意什么？',
  '半日游路线怎么安排？',
]

const sessionId = getOrCreateSessionId()
const isLoading = ref(false)
const scrollAnchor = ref<HTMLElement | null>(null)
const messages = ref<ChatMessage[]>([
  {
    id: createMessageId('guide'),
    role: 'guide',
    content: '您好，我是AI景区数字人导游。今天可以为您介绍景点、路线、服务设施和游览注意事项。',
    createdAt: new Date(),
    status: 'normal',
    sources: [{ title: '欢迎语（模拟数据）', section: '游客接待' }],
  },
])

function getOrCreateSessionId(): string {
  const existing = window.localStorage.getItem(SESSION_STORAGE_KEY)
  if (existing) {
    return existing
  }

  const id = `web-${crypto.randomUUID ? crypto.randomUUID() : createMessageId('session')}`
  window.localStorage.setItem(SESSION_STORAGE_KEY, id)
  return id
}

function createMessageId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function inferInterests(question: string): string[] {
  const interests: string[] = []
  if (/历史|文化|古建|故事/.test(question)) {
    interests.push('历史文化')
  }
  if (/路线|半日|一日|老人|孩子/.test(question)) {
    interests.push('路线规划')
  }
  if (/拍照|摄影|观景/.test(question)) {
    interests.push('摄影打卡')
  }
  return interests.slice(0, 5)
}

async function handleSend(question: string) {
  await sendQuestion(question)
}

async function sendQuestion(question: string) {
  const trimmedQuestion = question.trim()
  if (!trimmedQuestion || isLoading.value) {
    return
  }

  const loadingId = createMessageId('loading')
  isLoading.value = true
  messages.value.push({
    id: createMessageId('visitor'),
    role: 'visitor',
    content: trimmedQuestion,
    createdAt: new Date(),
    status: 'normal',
  })
  messages.value.push({
    id: loadingId,
    role: 'guide',
    content: '',
    createdAt: new Date(),
    status: 'loading',
  })
  await scrollToBottom()

  try {
    const response = await sendChatMessage({
      session_id: sessionId,
      question: trimmedQuestion,
      interests: inferInterests(trimmedQuestion),
    })

    removeMessage(loadingId)
    messages.value.push({
      id: response.request_id,
      role: 'guide',
      content: response.answer,
      createdAt: new Date(),
      status: 'normal',
      sources: response.sources,
      requestId: response.request_id,
      latencyMs: response.latency_ms,
      fallback: response.fallback,
    })
  } catch (error) {
    removeMessage(loadingId)
    messages.value.push({
      id: createMessageId('error'),
      role: 'guide',
      content: getChatErrorMessage(error),
      createdAt: new Date(),
      status: 'error',
      retryQuestion: trimmedQuestion,
    })
  } finally {
    isLoading.value = false
    await scrollToBottom()
  }
}

function removeMessage(id: string) {
  messages.value = messages.value.filter((message) => message.id !== id)
}

async function scrollToBottom() {
  await nextTick()
  scrollAnchor.value?.scrollIntoView({ behavior: 'smooth', block: 'end' })
}
</script>

<template>
  <main class="guide-shell">
    <aside class="guide-panel" aria-label="导游信息">
      <section class="guide-profile">
        <div class="guide-avatar" aria-hidden="true">
          <Sparkles :size="30" />
        </div>
        <div>
          <p class="guide-kicker">文字问答MVP</p>
          <h1>AI景区数字人导游</h1>
          <p>您好，我会用清晰、稳妥的方式回答景点、路线、交通和服务设施问题。</p>
        </div>
      </section>

      <section class="guide-status" aria-label="运行状态">
        <div class="status-row">
          <Wifi :size="18" />
          <span>FastAPI接口</span>
          <strong>HTTP</strong>
        </div>
        <div class="status-row">
          <ShieldCheck :size="18" />
          <span>数据来源</span>
          <strong>Mock</strong>
        </div>
        <div class="status-row">
          <MapPin :size="18" />
          <span>当前阶段</span>
          <strong>Phase 1</strong>
        </div>
      </section>

      <section class="route-note" aria-label="游览建议">
        <Route :size="18" />
        <p>推荐从游客中心开始，先确认当天开放信息，再按体力安排观景台和文化展陈。</p>
      </section>

      <SuggestedQuestions :questions="suggestedQuestions" :disabled="isLoading" @select="sendQuestion" />
    </aside>

    <section class="chat-panel" aria-label="游客问答">
      <header class="chat-header">
        <div>
          <p class="guide-kicker">游客问答</p>
          <h2>景区导览对话</h2>
        </div>
        <span class="session-chip">{{ sessionId.slice(0, 18) }}</span>
      </header>

      <div class="message-list" aria-live="polite">
        <MessageBubble
          v-for="message in messages"
          :key="message.id"
          :message="message"
          @retry="sendQuestion"
        />
        <div ref="scrollAnchor" class="scroll-anchor"></div>
      </div>

      <ChatInput :disabled="isLoading" @send="handleSend" />
    </section>
  </main>
</template>
