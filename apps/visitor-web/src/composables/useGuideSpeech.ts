import { computed, onBeforeUnmount, ref } from 'vue'

const AUTO_SPEAK_STORAGE_KEY = 'ai-scenic-guide-auto-speak'

interface GuideSpeechProfile {
  rate?: number
  pitch?: number
  volume?: number
  voiceName?: string
}

export function useGuideSpeech() {
  const isSupported = typeof window !== 'undefined' && 'speechSynthesis' in window
  const activeMessageId = ref<string | null>(null)
  const isSpeaking = ref(false)
  const isPaused = ref(false)
  const autoSpeak = ref(readAutoSpeakPreference())
  const speechProfile = ref<GuideSpeechProfile>({
    rate: 0.95,
    pitch: 1,
    volume: 1,
  })

  const hasActiveSpeech = computed(() => activeMessageId.value !== null)

  function speak(messageId: string, text: string) {
    if (!isSupported || !text.trim()) {
      return
    }

    stop()

    const utterance = new SpeechSynthesisUtterance(text.trim())
    utterance.lang = 'zh-CN'
    utterance.rate = speechProfile.value.rate ?? 0.95
    utterance.pitch = speechProfile.value.pitch ?? 1
    utterance.volume = speechProfile.value.volume ?? 1
    const voice = findVoice(speechProfile.value.voiceName)
    if (voice) {
      utterance.voice = voice
    }
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

  function setSpeechProfile(profile: GuideSpeechProfile) {
    speechProfile.value = {
      rate: profile.rate ?? speechProfile.value.rate,
      pitch: profile.pitch ?? speechProfile.value.pitch,
      volume: profile.volume ?? speechProfile.value.volume,
      voiceName: profile.voiceName ?? speechProfile.value.voiceName,
    }
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

  function findVoice(voiceName?: string) {
    if (!isSupported || !voiceName) {
      return undefined
    }
    const normalizedName = voiceName.toLowerCase()
    return window.speechSynthesis
      .getVoices()
      .find((voice) => voice.name.toLowerCase().includes(normalizedName) || voice.lang.toLowerCase().includes('zh'))
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
    setSpeechProfile,
    stop,
    toggle,
  }
}
