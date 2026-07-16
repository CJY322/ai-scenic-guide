<script setup lang="ts">
import { computed, ref } from 'vue'
import { SendHorizontal } from '@lucide/vue'

const MAX_LENGTH = 500

const props = defineProps<{
  disabled: boolean
}>()

const emit = defineEmits<{
  send: [question: string]
}>()

const text = ref('')
const error = ref('')

const trimmedText = computed(() => text.value.trim())
const isSubmitDisabled = computed(() => props.disabled)

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

    <button type="submit" class="send-button" :disabled="isSubmitDisabled" aria-label="发送">
      <SendHorizontal :size="20" />
    </button>

    <p v-if="error" class="input-error">{{ error }}</p>
  </form>
</template>
