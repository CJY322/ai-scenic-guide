import { computed, onBeforeUnmount, ref } from 'vue'

const AUTO_SPEAK_STORAGE_KEY = 'ai-scenic-guide-auto-speak'

export function useGuideSpeech() {
  const isSupported = typeof window !== 'undefined' && 'speechSynthesis' in window
  const activeMessageId = ref<string | null>(null)
  const isSpeaking = ref(false)
  const isPaused = ref(false)
  const autoSpeak = ref(readAutoSpeakPreference())

  const hasActiveSpeech = computed(() => activeMessageId.value !== null)

  function speak(messageId: string, text: string) {
    if (!isSupported || !text.trim()) {
      return
    }

    stop()

    const utterance = new SpeechSynthesisUtterance(text.trim())
    utterance.lang = 'zh-CN'
    utterance.rate = 0.95
    utterance.pitch = 1
    utterance.volume = 1
    utterance.onend = resetSpeechState
    utterance.onerror = resetSpeechState

    activeMessageId.value = messageId
    isSpeaking.value = true
    isPaused.value = false
    window.speechSynthesis.speak(utterance)
  }

  function toggle(messageId: string, text: string) {
    if (!isSupported) {
      return
    }

    if (activeMessageId.value !== messageId) {
      speak(messageId, text)
      return
    }

    if (isPaused.value) {
      window.speechSynthesis.resume()
      isPaused.value = false
      isSpeaking.value = true
      return
    }

    if (isSpeaking.value) {
      window.speechSynthesis.pause()
      isPaused.value = true
      isSpeaking.value = false
      return
    }

    speak(messageId, text)
  }

  function replay(messageId: string, text: string) {
    speak(messageId, text)
  }

  function stop() {
    if (!isSupported) {
      return
    }
    window.speechSynthesis.cancel()
    resetSpeechState()
  }

  function setAutoSpeak(value: boolean) {
    autoSpeak.value = value
    window.localStorage.setItem(AUTO_SPEAK_STORAGE_KEY, value ? 'true' : 'false')
  }

  function resetSpeechState() {
    activeMessageId.value = null
    isSpeaking.value = false
    isPaused.value = false
  }

  function readAutoSpeakPreference(): boolean {
    if (typeof window === 'undefined') {
      return false
    }
    return window.localStorage.getItem(AUTO_SPEAK_STORAGE_KEY) === 'true'
  }

  onBeforeUnmount(stop)

  return {
    activeMessageId,
    autoSpeak,
    hasActiveSpeech,
    isPaused,
    isSpeaking,
    isSupported,
    replay,
    setAutoSpeak,
    stop,
    toggle,
  }
}
