<script setup lang="ts">
import { computed, ref } from 'vue'
import { Mic, MicOff, SendHorizontal } from '@lucide/vue'
import { useSpeechRecognition } from '../composables/useSpeechRecognition'

const MAX_LENGTH = 500

const props = defineProps<{
  autoSendAfterVoice: boolean
  disabled: boolean
}>()

const emit = defineEmits<{
  send: [question: string]
}>()

const text = ref('')
const error = ref('')
const {
  error: voiceError,
  interimTranscript,
  isListening,
  isSupported: voiceSupported,
  toggle: toggleVoiceInput,
} = useSpeechRecognition(handleVoiceResult)

const trimmedText = computed(() => text.value.trim())
const isSubmitDisabled = computed(() => props.disabled)
const voiceStatus = computed(() => {
  if (!voiceSupported) {
    return '当前浏览器不支持语音输入'
  }
  if (voiceError.value) {
    return voiceError.value
  }
  if (isListening.value) {
    return interimTranscript.value ? `正在识别：${interimTranscript.value}` : '正在听...'
  }
  return ''
})

function submit() {
  if (props.disabled) {
    return
  }
  if (!trimmedText.value) {
    error.value = '请输入问题'
    return
  }
  if (trimmedText.value.length > MAX_LENGTH) {
    error.value = `问题不能超过${MAX_LENGTH}字`
    return
  }

  emit('send', trimmedText.value)
  text.value = ''
  error.value = ''
}

function handleInput() {
  if (error.value && trimmedText.value) {
    error.value = ''
  }
}

function handleVoiceResult(transcript: string, isFinal: boolean) {
  const nextText = transcript.trim().slice(0, MAX_LENGTH)
  if (!nextText) {
    return
  }

  text.value = nextText
  error.value = ''

  if (isFinal && props.autoSendAfterVoice && !props.disabled) {
    submit()
  }
}
</script>

<template>
  <form class="chat-input" @submit.prevent="submit">
    <div class="chat-input__field">
      <textarea
        v-model="text"
        :maxlength="MAX_LENGTH"
        :disabled="disabled"
        rows="2"
        placeholder="想问开放时间、路线或历史故事..."
        @input="handleInput"
        @keydown.enter.exact.prevent="submit"
      ></textarea>
      <span class="character-count">{{ text.length }}/{{ MAX_LENGTH }}</span>
    </div>

    <button
      type="button"
      :class="['voice-button', { 'voice-button--active': isListening }]"
      :disabled="disabled || !voiceSupported"
      :title="isListening ? '停止语音输入' : '开始语音输入'"
      aria-label="语音输入"
      @click="toggleVoiceInput"
    >
      <MicOff v-if="isListening" :size="20" />
      <Mic v-else :size="20" />
    </button>

    <button type="submit" class="send-button" :disabled="isSubmitDisabled" aria-label="发送">
      <SendHorizontal :size="20" />
    </button>

    <p v-if="error" class="input-error">{{ error }}</p>
    <p v-if="voiceStatus" class="voice-status" aria-live="polite">{{ voiceStatus }}</p>
  </form>
</template>
