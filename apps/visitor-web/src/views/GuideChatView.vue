<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Clapperboard,
  MapPin,
  Maximize2,
  Mic,
  Minimize2,
  Route,
  ShieldCheck,
  Sparkles,
  Volume2,
  Wifi,
} from '@lucide/vue'
import {
  fetchAvatarStatus,
  generateAvatarVideo,
  getAvatarErrorMessage,
  resolveAvatarAssetUrl,
  resolveAvatarVideoUrl,
} from '../api/avatar'
import { getChatErrorMessage, sendChatMessage } from '../api/chat'
import ChatInput from '../components/ChatInput.vue'
import DigitalGuideAvatar from '../components/DigitalGuideAvatar.vue'
import MessageBubble from '../components/MessageBubble.vue'
import SuggestedQuestions from '../components/SuggestedQuestions.vue'
import { useGuideSpeech } from '../composables/useGuideSpeech'
import type { ChatMessage } from '../types/chat'

const SESSION_STORAGE_KEY = 'ai-scenic-guide-session-id'
const AUTO_SEND_VOICE_STORAGE_KEY = 'ai-scenic-guide-auto-send-voice'
const REAL_AVATAR_STORAGE_KEY = 'ai-scenic-guide-real-avatar'
const AVATAR_VIDEO_TEXT_LIMIT = 50

const suggestedQuestions = [
  '景区有哪些值得参观的景点？',
  '景区几点开放？',
  '带老人游览需要注意什么？',
  '半日游路线怎么安排？',
]

const sessionId = getOrCreateSessionId()
const autoSendVoice = ref(readBooleanPreference(AUTO_SEND_VOICE_STORAGE_KEY))
const avatarEnabled = ref(false)
const avatarPortraitUrl = resolveAvatarAssetUrl('/avatar-assets/huangshan-guide.png')
const avatarSupported = ref(false)
const avatarVideoError = ref<string | null>(null)
const avatarVideoLoading = ref(false)
const avatarVideoUrl = ref<string | null>(null)
const isAvatarAnswering = ref(false)
const isPresentationMode = ref(false)
const isLoading = ref(false)
const isVoiceListening = ref(false)
const scrollAnchor = ref<HTMLElement | null>(null)
const {
  activeMessageId: activeSpeechMessageId,
  autoSpeak,
  hasActiveSpeech,
  isPaused: isSpeechPaused,
  isSpeaking: isSpeechPlaying,
  isSupported: speechSupported,
  replay: replaySpeech,
  setAutoSpeak,
  stop: stopSpeech,
  toggle: toggleSpeech,
} = useGuideSpeech()
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
let avatarAnimationTimer: number | undefined

onMounted(async () => {
  try {
    const avatarStatus = await fetchAvatarStatus()
    avatarSupported.value = avatarStatus.enabled
    avatarEnabled.value = avatarStatus.enabled && readBooleanPreference(REAL_AVATAR_STORAGE_KEY)
  } catch {
    avatarSupported.value = false
    avatarEnabled.value = false
  }
})

onBeforeUnmount(() => {
  stopAvatarAnswerAnimation()
})

watch(activeSpeechMessageId, (messageId) => {
  if (avatarEnabled.value && !avatarVideoLoading.value && messageId === null) {
    avatarVideoUrl.value = null
  }
})

function getOrCreateSessionId(): string {
  const existing = window.localStorage.getItem(SESSION_STORAGE_KEY)
  if (existing) {
    return existing
  }

  const id = `web-${crypto.randomUUID ? crypto.randomUUID() : createMessageId('session')}`
  window.localStorage.setItem(SESSION_STORAGE_KEY, id)
  return id
}

function readBooleanPreference(key: string): boolean {
  return window.localStorage.getItem(key) === 'true'
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

  stopSpeech()
  stopAvatarAnswerAnimation()
  avatarVideoError.value = null
  avatarVideoUrl.value = null
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
    const guideMessage: ChatMessage = {
      id: response.request_id,
      role: 'guide',
      content: response.answer,
      createdAt: new Date(),
      status: 'normal',
      sources: response.sources,
      requestId: response.request_id,
      latencyMs: response.latency_ms,
      fallback: response.fallback,
    }
    messages.value.push(guideMessage)
    if (avatarEnabled.value) {
      stopSpeech()
      stopAvatarAnswerAnimation()
      void playAvatarAnswerVideo(guideMessage)
    } else if (autoSpeak.value) {
      startAvatarAnswerAnimation(guideMessage.content)
      toggleSpeech(guideMessage.id, guideMessage.content)
    }
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

function handleAutoSpeakChange(event: Event) {
  const target = event.target as HTMLInputElement
  setAutoSpeak(target.checked)
}

function handleAutoSendVoiceChange(event: Event) {
  const target = event.target as HTMLInputElement
  autoSendVoice.value = target.checked
  window.localStorage.setItem(AUTO_SEND_VOICE_STORAGE_KEY, target.checked ? 'true' : 'false')
}

function handleAvatarEnabledChange(event: Event) {
  const target = event.target as HTMLInputElement
  avatarEnabled.value = target.checked
  window.localStorage.setItem(REAL_AVATAR_STORAGE_KEY, target.checked ? 'true' : 'false')
  if (target.checked) {
    stopSpeech()
    stopAvatarAnswerAnimation()
  }
  if (!target.checked) {
    avatarVideoError.value = null
    avatarVideoUrl.value = null
  }
}

function handleVoiceListeningChange(listening: boolean) {
  isVoiceListening.value = listening
}

function handleToggleSpeech(message: ChatMessage) {
  toggleSpeech(message.id, message.content)
}

function handleReplaySpeech(message: ChatMessage) {
  replaySpeech(message.id, message.content)
}

function handleAvatarVideoEnded() {
  isAvatarAnswering.value = false
}

function togglePresentationMode() {
  isPresentationMode.value = !isPresentationMode.value

  if (isPresentationMode.value && document.fullscreenEnabled && !document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(() => undefined)
    return
  }

  if (!isPresentationMode.value && document.fullscreenElement) {
    document.exitFullscreen().catch(() => undefined)
  }
}

async function playAvatarAnswerVideo(message: ChatMessage) {
  const avatarSpeechText = createAvatarSpeechText(message.content)
  if (!avatarSpeechText) {
    return
  }

  avatarVideoLoading.value = true
  avatarVideoError.value = null
  avatarVideoUrl.value = null
  isAvatarAnswering.value = false

  try {
    const response = await generateAvatarVideo({
      message_id: message.id,
      text: avatarSpeechText,
    })
    avatarVideoUrl.value = resolveAvatarVideoUrl(response.video_url)
    isAvatarAnswering.value = true
  } catch (error) {
    console.warn(getAvatarErrorMessage(error))
    avatarVideoError.value = '真实视频生成失败，请重试或缩短问题'
  } finally {
    avatarVideoLoading.value = false
  }
}

function createAvatarSpeechText(text: string) {
  const normalizedText = text
    .replace(/\*\*/g, '')
    .replace(/[`#>-]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
  return Array.from(normalizedText).slice(0, AVATAR_VIDEO_TEXT_LIMIT).join('')
}

function startAvatarAnswerAnimation(text: string) {
  stopAvatarAnswerAnimation()
  const durationMs = Math.min(20000, Math.max(5000, text.trim().length * 120))
  isAvatarAnswering.value = true
  avatarAnimationTimer = window.setTimeout(() => {
    isAvatarAnswering.value = false
    avatarAnimationTimer = undefined
  }, durationMs)
}

function stopAvatarAnswerAnimation() {
  if (avatarAnimationTimer) {
    window.clearTimeout(avatarAnimationTimer)
    avatarAnimationTimer = undefined
  }
  isAvatarAnswering.value = false
}

async function scrollToBottom() {
  await nextTick()
  scrollAnchor.value?.scrollIntoView({ behavior: 'smooth', block: 'end' })
}
</script>

<template>
  <main :class="['guide-shell', { 'guide-shell--stage': isPresentationMode }]">
    <aside class="guide-panel" aria-label="导游信息">
      <section class="guide-profile">
        <div class="guide-avatar" aria-hidden="true">
          <Sparkles :size="30" />
        </div>
        <div>
          <p class="guide-kicker">黄山导游终端</p>
          <h1>AI景区数字人导游</h1>
          <p>您好，我会用清晰、稳妥的方式回答景点、路线、交通和服务设施问题，并支持语音提问与导游播报。</p>
        </div>
      </section>

      <DigitalGuideAvatar
        :listening="isVoiceListening"
        :portrait-mouth-enabled="!avatarEnabled"
        :portrait-url="avatarPortraitUrl"
        :speaking="!avatarVideoLoading && (isSpeechPlaying || isAvatarAnswering)"
        :thinking="isLoading"
        :video-error="avatarVideoError"
        :video-loop="false"
        :video-loading="avatarVideoLoading"
        :video-muted="false"
        :video-url="avatarVideoUrl"
        @video-ended="handleAvatarVideoEnded"
      />

      <section class="guide-status" aria-label="运行状态">
        <div class="status-row">
          <Wifi :size="18" />
          <span>FastAPI接口</span>
          <strong>HTTP</strong>
        </div>
        <div class="status-row">
          <ShieldCheck :size="18" />
          <span>数据来源</span>
          <strong>Dify RAG</strong>
        </div>
        <div class="status-row">
          <MapPin :size="18" />
          <span>当前阶段</span>
          <strong>Phase 5</strong>
        </div>
        <div class="status-row">
          <Clapperboard :size="18" />
          <span>数字人引擎</span>
          <strong>{{ avatarSupported ? 'SadTalker' : '轻量模式' }}</strong>
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
        <div class="chat-header__controls">
          <label class="auto-speak-toggle" :class="{ 'auto-speak-toggle--disabled': !speechSupported }">
            <input
              type="checkbox"
              :checked="autoSpeak"
              :disabled="!speechSupported"
              @change="handleAutoSpeakChange"
            />
            <span class="toggle-track" aria-hidden="true">
              <span class="toggle-thumb"></span>
            </span>
            <span class="auto-speak-toggle__text">
              <Volume2 :size="15" />
              自动播报
            </span>
          </label>
          <label class="auto-speak-toggle">
            <input type="checkbox" :checked="autoSendVoice" @change="handleAutoSendVoiceChange" />
            <span class="toggle-track" aria-hidden="true">
              <span class="toggle-thumb"></span>
            </span>
            <span class="auto-speak-toggle__text">
              <Mic :size="15" />
              识别后发送
            </span>
          </label>
          <label v-if="avatarSupported" class="auto-speak-toggle">
            <input type="checkbox" :checked="avatarEnabled" @change="handleAvatarEnabledChange" />
            <span class="toggle-track" aria-hidden="true">
              <span class="toggle-thumb"></span>
            </span>
            <span class="auto-speak-toggle__text">
              <Clapperboard :size="15" />
              真实数字人
            </span>
          </label>
          <button v-if="hasActiveSpeech" type="button" class="stop-speech-button" @click="stopSpeech">停止</button>
          <button type="button" class="display-mode-button" @click="togglePresentationMode">
            <Minimize2 v-if="isPresentationMode" :size="15" />
            <Maximize2 v-else :size="15" />
            {{ isPresentationMode ? '退出展示' : '展示模式' }}
          </button>
          <span class="session-chip">{{ sessionId.slice(0, 18) }}</span>
        </div>
      </header>

      <div class="message-list" aria-live="polite">
        <MessageBubble
          v-for="message in messages"
          :key="message.id"
          :message="message"
          :active-speech-message-id="activeSpeechMessageId"
          :is-speech-paused="isSpeechPaused"
          :is-speech-playing="isSpeechPlaying"
          :speech-supported="speechSupported && !avatarEnabled"
          @replay-speech="handleReplaySpeech"
          @retry="sendQuestion"
          @toggle-speech="handleToggleSpeech"
        />
        <div ref="scrollAnchor" class="scroll-anchor"></div>
      </div>

      <ChatInput
        :auto-send-after-voice="autoSendVoice"
        :disabled="isLoading"
        @send="handleSend"
        @voice-listening-change="handleVoiceListeningChange"
      />
    </section>
  </main>
</template>
