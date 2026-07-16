<script setup lang="ts">
import { computed } from 'vue'
import { CircleAlert, Clock3, Pause, Play, RotateCcw, Sparkles, UserRound } from '@lucide/vue'
import type { ChatMessage } from '../types/chat'

const props = defineProps<{
  message: ChatMessage
  activeSpeechMessageId?: string | null
  isSpeechPaused?: boolean
  isSpeechPlaying?: boolean
  speechSupported?: boolean
}>()

const emit = defineEmits<{
  retry: [question: string]
  replaySpeech: [message: ChatMessage]
  toggleSpeech: [message: ChatMessage]
}>()

const senderLabel = computed(() => (props.message.role === 'visitor' ? '游客' : '数字人导游'))
const hasSources = computed(() => props.message.sources && props.message.sources.length > 0)
const canSpeak = computed(
  () =>
    props.speechSupported &&
    props.message.role === 'guide' &&
    props.message.status === 'normal' &&
    props.message.content.trim().length > 0,
)
const isSpeechActive = computed(() => props.activeSpeechMessageId === props.message.id)
const speechButtonLabel = computed(() => {
  if (!isSpeechActive.value) {
    return '播放'
  }
  return props.isSpeechPaused ? '继续' : '暂停'
})

function retry() {
  if (props.message.retryQuestion) {
    emit('retry', props.message.retryQuestion)
  }
}

function toggleSpeech() {
  emit('toggleSpeech', props.message)
}

function replaySpeech() {
  emit('replaySpeech', props.message)
}
</script>

<template>
  <article :class="['message', `message--${message.role}`, `message--${message.status}`]">
    <div class="message-avatar" aria-hidden="true">
      <UserRound v-if="message.role === 'visitor'" :size="18" />
      <Sparkles v-else :size="18" />
    </div>

    <div class="message-body">
      <div class="message-meta">
        <span>{{ senderLabel }}</span>
        <span v-if="message.status === 'loading'" class="message-meta__status">
          <Clock3 :size="14" />
          正在思考
        </span>
      </div>

      <p v-if="message.status !== 'loading'" class="message-text">{{ message.content }}</p>
      <div v-else class="typing-indicator" aria-label="正在思考">
        <span></span>
        <span></span>
        <span></span>
      </div>

      <div v-if="hasSources" class="source-list" aria-label="来源">
        <span v-for="source in message.sources" :key="`${source.title}-${source.section ?? ''}`" class="source-tag">
          {{ source.title }}<template v-if="source.section"> · {{ source.section }}</template>
        </span>
      </div>

      <div v-if="message.status === 'error'" class="message-actions">
        <CircleAlert :size="16" aria-hidden="true" />
        <button type="button" class="retry-button" @click="retry">
          <RotateCcw :size="16" />
          重新发送
        </button>
      </div>

      <div v-if="canSpeak" class="speech-actions" aria-label="语音播报">
        <button type="button" class="speech-button" :title="speechButtonLabel" @click="toggleSpeech">
          <Pause v-if="isSpeechActive && isSpeechPlaying" :size="16" />
          <Play v-else :size="16" />
          {{ speechButtonLabel }}
        </button>
        <button type="button" class="speech-icon-button" title="重播" aria-label="重播" @click="replaySpeech">
          <RotateCcw :size="16" />
        </button>
      </div>
    </div>
  </article>
</template>
