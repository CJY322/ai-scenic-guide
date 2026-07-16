<script setup lang="ts">
import { MessageSquareText } from '@lucide/vue'

const props = defineProps<{
  questions: string[]
  disabled: boolean
}>()

const emit = defineEmits<{
  select: [question: string]
}>()

function selectQuestion(question: string) {
  if (!props.disabled) {
    emit('select', question)
  }
}
</script>

<template>
  <div class="suggested-questions" aria-label="推荐问题">
    <button
      v-for="question in questions"
      :key="question"
      type="button"
      class="suggested-question"
      :disabled="disabled"
      @click="selectQuestion(question)"
    >
      <MessageSquareText :size="16" aria-hidden="true" />
      <span>{{ question }}</span>
    </button>
  </div>
</template>
