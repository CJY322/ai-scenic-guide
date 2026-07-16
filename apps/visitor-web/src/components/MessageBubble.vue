<script setup lang="ts">
import { computed } from 'vue'
import { CircleAlert, Clock3, RotateCcw, Sparkles, UserRound } from '@lucide/vue'
import type { ChatMessage } from '../types/chat'

const props = defineProps<{
  message: ChatMessage
}>()

const emit = defineEmits<{
  retry: [question: string]
}>()

const senderLabel = computed(() => (props.message.role === 'visitor' ? '游客' : '数字人导游'))
const hasSources = computed(() => props.message.sources && props.message.sources.length > 0)

function retry() {
  if (props.message.retryQuestion) {
    emit('retry', props.message.retryQuestion)
  }
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
    </div>
  </article>
</template>
