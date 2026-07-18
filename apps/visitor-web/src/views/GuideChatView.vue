<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  Clapperboard,
  Compass,
  Footprints,
  Heart,
  Maximize2,
  Mic,
  Minimize2,
  Route,
  Sparkles,
  Settings,
  Volume2,
} from '@lucide/vue'
import {
  cancelAvatarTasks,
  fetchAvatarStatus,
  generateAvatarVideo,
  getAvatarErrorMessage,
  isAvatarRequestCancelled,
  resolveAvatarAssetUrl,
  resolveAvatarVideoUrl,
  sendAvatarCancelBeacon,
} from '../api/avatar'
import { fetchAvatarProfile, fetchRecommendedQuestions } from '../api/admin'
import {
  fetchPersonalizedRecommendation,
  getChatErrorMessage,
  isChatRequestCancelled,
  sendChatMessage,
} from '../api/chat'
import ChatInput from '../components/ChatInput.vue'
import DigitalGuideAvatar from '../components/DigitalGuideAvatar.vue'
import MessageBubble from '../components/MessageBubble.vue'
import SuggestedQuestions from '../components/SuggestedQuestions.vue'
import { useGuideSpeech } from '../composables/useGuideSpeech'
import type { ChatMessage, PersonalizedRecommendation, RecommendationInterestOption } from '../types/chat'

const SESSION_STORAGE_KEY = 'ai-scenic-guide-session-id'
const AUTO_SEND_VOICE_STORAGE_KEY = 'ai-scenic-guide-auto-send-voice'
const REAL_AVATAR_STORAGE_KEY = 'ai-scenic-guide-real-avatar'
const SELECTED_INTERESTS_STORAGE_KEY = 'ai-scenic-guide-selected-interests'
const AVATAR_VIDEO_TEXT_LIMIT = 50
const LIGHTWEIGHT_AVATAR_LOOP_TEXT = '您好，欢迎来到灵山胜境。'

const defaultSuggestedQuestions = [
  '灵山胜境有哪些必看景点？',
  '九龙灌浴和灵山大佛怎么讲？',
  '带老人孩子游览怎么安排？',
  '半日游路线怎么走？',
]
const defaultInterestOptions: RecommendationInterestOption[] = [
  { id: 'history', label: '历史文化', description: '佛教文化、古建故事、深度讲解' },
  { id: 'nature', label: '自然风光', description: '太湖视野、山水观景、轻松散步' },
  { id: 'family', label: '亲子家庭', description: '老人孩子同行、低强度游览' },
  { id: 'photo', label: '摄影打卡', description: '代表性取景点和拍摄顺序' },
  { id: 'first-time', label: '首次到访', description: '经典必看、半日重点路线' },
]
const suggestedQuestions = ref(defaultSuggestedQuestions)

const sessionId = getOrCreateSessionId()
const autoSendVoice = ref(readBooleanPreference(AUTO_SEND_VOICE_STORAGE_KEY))
const selectedInterests = ref<string[]>(readSelectedInterests())
const interestOptions = ref<RecommendationInterestOption[]>(defaultInterestOptions)
const personalizedRecommendation = ref<PersonalizedRecommendation | null>(null)
const recommendationError = ref<string | null>(null)
const recommendationLoading = ref(false)
const avatarEnabled = ref(false)
const avatarPortraitUrl = resolveAvatarAssetUrl('/avatar-assets/guide-avatar.png')
const avatarSupported = ref(false)
const avatarVideoError = ref<string | null>(null)
const avatarVideoLoading = ref(false)
const avatarVideoUrl = ref<string | null>(null)
const isLightweightAvatarLoop = ref(false)
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
  setSpeechProfile,
  stop: stopSpeech,
  toggle: toggleSpeech,
} = useGuideSpeech()
const messages = ref<ChatMessage[]>([
  {
    id: createMessageId('guide'),
    role: 'guide',
    content: '您好，我是灵山胜境AI数字人导游。今天可以为您介绍灵山大佛、九龙灌浴、梵宫、五印坛城、路线安排和游览注意事项。',
    createdAt: new Date(),
    status: 'normal',
    sources: [{ title: '灵山胜境欢迎语', section: '游客接待' }],
  },
])
let lightweightAvatarLoopRequestId = 0
let chatAbortController: AbortController | null = null
let avatarAbortController: AbortController | null = null
let recommendationAbortController: AbortController | null = null
let browserExitCancelSent = false

onMounted(async () => {
  try {
    const questions = await fetchRecommendedQuestions()
    if (questions.length > 0) {
      suggestedQuestions.value = questions
    }
  } catch {
    suggestedQuestions.value = defaultSuggestedQuestions
  }

  try {
    const profile = await fetchAvatarProfile()
    setSpeechProfile({
      rate: profile.voice_rate,
      pitch: profile.voice_pitch,
      volume: profile.voice_volume,
      voiceName: profile.voice_name,
    })
  } catch {
    // Keep browser speech defaults if the admin profile is unavailable.
  }

  try {
    const avatarStatus = await fetchAvatarStatus()
    avatarSupported.value = avatarStatus.enabled
    avatarEnabled.value = avatarStatus.enabled && readBooleanPreference(REAL_AVATAR_STORAGE_KEY)
  } catch {
    avatarSupported.value = false
    avatarEnabled.value = false
  }

  await refreshPersonalizedRecommendation()

  window.addEventListener('pagehide', handleBrowserExit)
  window.addEventListener('beforeunload', handleBrowserExit)
})

onBeforeUnmount(() => {
  window.removeEventListener('pagehide', handleBrowserExit)
  window.removeEventListener('beforeunload', handleBrowserExit)
  handleBrowserExit()
})

watch(activeSpeechMessageId, (messageId) => {
  if (avatarEnabled.value && !avatarVideoLoading.value && messageId === null) {
    avatarVideoUrl.value = null
  }
  if (!avatarEnabled.value && messageId === null) {
    stopLightweightAvatarLoop()
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

function readSelectedInterests(): string[] {
  try {
    const rawInterests = JSON.parse(window.localStorage.getItem(SELECTED_INTERESTS_STORAGE_KEY) || '[]')
    if (!Array.isArray(rawInterests)) {
      return []
    }
    return rawInterests.map((item) => String(item).trim()).filter(Boolean).slice(0, 5)
  } catch {
    return []
  }
}

function createMessageId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function inferInterests(question: string): string[] {
  const interests: string[] = []
  if (/历史|文化|古建|故事/.test(question)) {
    interests.push('历史文化')
  }
  if (/自然|风光|山水|太湖|观景|散步|慢游/.test(question)) {
    interests.push('自然风光')
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
  stopLightweightAvatarLoop()
  cancelActiveAvatarTasks()
  avatarVideoError.value = null
  avatarVideoUrl.value = null
  const loadingId = createMessageId('loading')
  const requestController = new AbortController()
  chatAbortController?.abort()
  chatAbortController = requestController
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
      interests: buildQuestionInterests(trimmedQuestion),
    }, requestController.signal)

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
      stopLightweightAvatarLoop()
      void playAvatarAnswerVideo(guideMessage)
    } else if (autoSpeak.value) {
      void playSpeechWithLightweightAvatarLoop(guideMessage, 'toggle')
    }
  } catch (error) {
    if (isChatRequestCancelled(error)) {
      removeMessage(loadingId)
      return
    }
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
    if (chatAbortController === requestController) {
      chatAbortController = null
    }
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

function buildQuestionInterests(question: string): string[] {
  return Array.from(new Set([...selectedInterests.value, ...inferInterests(question)])).slice(0, 5)
}

function toggleInterest(label: string) {
  const nextInterests = selectedInterests.value.includes(label)
    ? selectedInterests.value.filter((interest) => interest !== label)
    : [...selectedInterests.value, label].slice(0, 5)

  selectedInterests.value = nextInterests
  window.localStorage.setItem(SELECTED_INTERESTS_STORAGE_KEY, JSON.stringify(nextInterests))
  void refreshPersonalizedRecommendation()
}

async function refreshPersonalizedRecommendation() {
  const requestController = new AbortController()
  recommendationAbortController?.abort()
  recommendationAbortController = requestController
  recommendationLoading.value = true
  recommendationError.value = null

  try {
    const recommendation = await fetchPersonalizedRecommendation(
      { interests: selectedInterests.value },
      requestController.signal,
    )
    if (requestController.signal.aborted) {
      return
    }
    personalizedRecommendation.value = recommendation
    if (recommendation.interest_options.length > 0) {
      interestOptions.value = recommendation.interest_options
    }
  } catch (error) {
    if (isChatRequestCancelled(error)) {
      return
    }
    recommendationError.value = '推荐路线暂不可用'
  } finally {
    if (recommendationAbortController === requestController) {
      recommendationAbortController = null
      recommendationLoading.value = false
    }
  }
}

function handleAvatarEnabledChange(event: Event) {
  const target = event.target as HTMLInputElement
  avatarEnabled.value = target.checked
  window.localStorage.setItem(REAL_AVATAR_STORAGE_KEY, target.checked ? 'true' : 'false')
  if (target.checked) {
    stopSpeech()
    stopLightweightAvatarLoop()
    cancelActiveAvatarTasks()
  }
  if (!target.checked) {
    avatarVideoError.value = null
    avatarVideoUrl.value = null
    stopLightweightAvatarLoop()
  }
}

function handleVoiceListeningChange(listening: boolean) {
  isVoiceListening.value = listening
}

function handleToggleSpeech(message: ChatMessage) {
  if (avatarEnabled.value) {
    return
  }

  if (activeSpeechMessageId.value === message.id && isSpeechPlaying.value) {
    toggleSpeech(message.id, message.content)
    stopLightweightAvatarLoop()
    return
  }

  void playSpeechWithLightweightAvatarLoop(message, 'toggle')
}

function handleReplaySpeech(message: ChatMessage) {
  if (avatarEnabled.value) {
    return
  }

  void playSpeechWithLightweightAvatarLoop(message, 'replay')
}

function handlePlayAvatarVideo(message: ChatMessage) {
  if (!avatarEnabled.value) {
    return
  }
  stopSpeech()
  stopLightweightAvatarLoop()
  void playAvatarAnswerVideo(message)
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

  cancelActiveAvatarTasks()
  const requestController = new AbortController()
  avatarAbortController = requestController
  avatarVideoLoading.value = true
  avatarVideoError.value = null
  avatarVideoUrl.value = null
  isLightweightAvatarLoop.value = false
  isAvatarAnswering.value = false

  try {
    const response = await generateAvatarVideo({
      message_id: message.id,
      session_id: sessionId,
      text: avatarSpeechText,
    }, requestController.signal)
    if (requestController.signal.aborted) {
      return
    }
    avatarVideoUrl.value = resolveAvatarVideoUrl(response.video_url)
    isAvatarAnswering.value = true
  } catch (error) {
    if (isAvatarRequestCancelled(error)) {
      return
    }
    console.warn(getAvatarErrorMessage(error))
    avatarVideoError.value = '真实视频生成失败，请重试或缩短问题'
  } finally {
    if (avatarAbortController === requestController) {
      avatarAbortController = null
      avatarVideoLoading.value = false
    }
  }
}

async function playSpeechWithLightweightAvatarLoop(message: ChatMessage, action: 'toggle' | 'replay') {
  stopSpeech()
  cancelActiveAvatarTasks()
  const requestId = ++lightweightAvatarLoopRequestId
  avatarVideoError.value = null
  avatarVideoUrl.value = null
  isLightweightAvatarLoop.value = true
  isAvatarAnswering.value = false
  const requestController = new AbortController()
  avatarAbortController = requestController

  if (avatarSupported.value) {
    avatarVideoLoading.value = true
    try {
      const response = await generateAvatarVideo({
        message_id: 'lightweight-loop',
        session_id: sessionId,
        text: LIGHTWEIGHT_AVATAR_LOOP_TEXT,
      }, requestController.signal)
      if (requestId !== lightweightAvatarLoopRequestId || avatarEnabled.value) {
        return
      }
      if (requestController.signal.aborted) {
        return
      }
      avatarVideoUrl.value = resolveAvatarVideoUrl(response.video_url)
      isAvatarAnswering.value = true
    } catch (error) {
      if (requestId !== lightweightAvatarLoopRequestId || avatarEnabled.value) {
        return
      }
      if (isAvatarRequestCancelled(error)) {
        return
      }
      console.warn(getAvatarErrorMessage(error))
      avatarVideoError.value = '口型循环视频生成失败，已改用语音播报'
      isLightweightAvatarLoop.value = false
    } finally {
      if (requestId === lightweightAvatarLoopRequestId) {
        avatarVideoLoading.value = false
      }
      if (avatarAbortController === requestController) {
        avatarAbortController = null
      }
    }
  } else {
    isLightweightAvatarLoop.value = false
  }

  if (requestId !== lightweightAvatarLoopRequestId || avatarEnabled.value) {
    return
  }

  if (action === 'replay') {
    replaySpeech(message.id, message.content)
    return
  }
  toggleSpeech(message.id, message.content)
}

function createAvatarSpeechText(text: string) {
  const normalizedText = text
    .replace(/\*\*/g, '')
    .replace(/[`#>-]/g, '')
    .replace(/\s+/g, ' ')
    .trim()
  return Array.from(normalizedText).slice(0, AVATAR_VIDEO_TEXT_LIMIT).join('')
}

function stopLightweightAvatarLoop() {
  lightweightAvatarLoopRequestId += 1
  cancelActiveAvatarTasks()
  if (isLightweightAvatarLoop.value) {
    avatarVideoUrl.value = null
    avatarVideoError.value = null
    avatarVideoLoading.value = false
    isLightweightAvatarLoop.value = false
  }
  isAvatarAnswering.value = false
}

async function scrollToBottom() {
  await nextTick()
  scrollAnchor.value?.scrollIntoView({ behavior: 'smooth', block: 'end' })
}

function cancelActiveAvatarTasks() {
  const shouldNotifyBackend =
    avatarAbortController !== null ||
    avatarVideoLoading.value ||
    isLightweightAvatarLoop.value ||
    isAvatarAnswering.value

  if (avatarAbortController) {
    avatarAbortController.abort()
    avatarAbortController = null
  }

  if (avatarVideoLoading.value || isLightweightAvatarLoop.value || isAvatarAnswering.value) {
    avatarVideoLoading.value = false
    isAvatarAnswering.value = false
  }

  if (shouldNotifyBackend && !browserExitCancelSent) {
    void cancelAvatarTasks({ session_id: sessionId }).catch(() => undefined)
  }
}

function handleBrowserExit() {
  if (browserExitCancelSent) {
    return
  }

  browserExitCancelSent = true
  stopSpeech()
  chatAbortController?.abort()
  chatAbortController = null
  recommendationAbortController?.abort()
  recommendationAbortController = null
  if (avatarAbortController) {
    avatarAbortController.abort()
    avatarAbortController = null
  }
  lightweightAvatarLoopRequestId += 1
  isLoading.value = false
  isLightweightAvatarLoop.value = false
  isAvatarAnswering.value = false
  avatarVideoLoading.value = false
  sendAvatarCancelBeacon({ session_id: sessionId })
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
          <p class="guide-kicker">灵山胜境导游终端</p>
          <h1>AI景区数字人导游</h1>
          <p>您好，我会用清晰、稳妥的方式回答灵山胜境景点、路线、演出和服务设施问题，并支持语音提问与导游播报。</p>
        </div>
      </section>

      <DigitalGuideAvatar
        :listening="isVoiceListening"
        :portrait-mouth-enabled="false"
        :portrait-url="avatarPortraitUrl"
        :speaking="!avatarVideoLoading && (isSpeechPlaying || isAvatarAnswering)"
        :thinking="isLoading"
        :video-error="avatarVideoError"
        :video-loop="isLightweightAvatarLoop"
        :video-loading="avatarVideoLoading"
        :video-muted="isLightweightAvatarLoop"
        :video-show-play-button="!isLightweightAvatarLoop"
        :video-url="avatarVideoUrl"
        @video-ended="handleAvatarVideoEnded"
      />

      <section class="route-note" aria-label="游览建议">
        <Route :size="18" />
        <p>推荐先确认九龙灌浴与梵宫演出时间，再按体力安排灵山大佛、祥符禅寺和五印坛城。</p>
      </section>

      <section class="personalized-route" aria-label="个性化推荐">
        <div class="personalized-route__header">
          <Compass :size="18" />
          <strong>个性化路线</strong>
        </div>

        <div class="interest-chip-list">
          <button
            v-for="option in interestOptions"
            :key="option.id"
            type="button"
            :class="['interest-chip', { 'interest-chip--active': selectedInterests.includes(option.label) }]"
            :title="option.description"
            @click="toggleInterest(option.label)"
          >
            {{ option.label }}
          </button>
        </div>

        <article v-if="personalizedRecommendation" class="recommendation-summary">
          <div class="recommendation-summary__title">
            <strong>{{ personalizedRecommendation.route_title }}</strong>
            <span>{{ personalizedRecommendation.duration }}</span>
          </div>
          <p>{{ personalizedRecommendation.route_summary }}</p>

          <div class="route-stop-list" aria-label="推荐路线">
            <span v-for="stop in personalizedRecommendation.stops" :key="stop">{{ stop }}</span>
          </div>

          <div class="recommendation-focus-list">
            <div v-for="focus in personalizedRecommendation.focus_points.slice(0, 4)" :key="focus">
              <Heart :size="14" />
              <span>{{ focus }}</span>
            </div>
          </div>

          <div class="recommendation-tip-list">
            <div v-for="tip in personalizedRecommendation.tips.slice(0, 2)" :key="tip">
              <Footprints :size="14" />
              <span>{{ tip }}</span>
            </div>
          </div>

          <div class="recommendation-question-list">
            <button
              v-for="question in personalizedRecommendation.suggested_questions.slice(0, 2)"
              :key="question"
              type="button"
              :disabled="isLoading"
              @click="sendQuestion(question)"
            >
              {{ question }}
            </button>
          </div>
        </article>

        <p v-else-if="recommendationLoading" class="recommendation-state">正在匹配路线</p>
        <p v-else-if="recommendationError" class="recommendation-state recommendation-state--error">
          {{ recommendationError }}
        </p>
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
          <a class="display-mode-button" href="/admin">
            <Settings :size="15" />
            管理后台
          </a>
          <span class="session-chip">{{ sessionId.slice(0, 18) }}</span>
        </div>
      </header>

      <div class="message-list" aria-live="polite">
        <MessageBubble
          v-for="message in messages"
          :key="message.id"
          :message="message"
          :active-speech-message-id="activeSpeechMessageId"
          :avatar-video-loading="avatarVideoLoading"
          :avatar-video-supported="avatarEnabled && avatarSupported"
          :is-speech-paused="isSpeechPaused"
          :is-speech-playing="isSpeechPlaying"
          :speech-supported="speechSupported && !avatarEnabled"
          @play-avatar-video="handlePlayAvatarVideo"
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
