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
  const availableVoices = ref<SpeechSynthesisVoice[]>([])
  const speechProfile = ref<GuideSpeechProfile>({
    rate: 0.95,
    pitch: 1,
    volume: 1,
  })

  const hasActiveSpeech = computed(() => activeMessageId.value !== null)

  if (isSupported) {
    loadSpeechVoices()
    window.speechSynthesis.addEventListener('voiceschanged', loadSpeechVoices)
  }

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

  function loadSpeechVoices() {
    if (!isSupported) {
      availableVoices.value = []
      return
    }
    availableVoices.value = window.speechSynthesis.getVoices()
  }

  function findVoice(voiceName?: string) {
    if (!isSupported || !voiceName) {
      return undefined
    }
    const normalizedName = voiceName.toLowerCase()
    const voices = availableVoices.value.length ? availableVoices.value : window.speechSynthesis.getVoices()
    const exactVoice = voices.find(
      (voice) => voice.name === voiceName || voice.voiceURI === voiceName || voice.name.toLowerCase().includes(normalizedName),
    )
    if (exactVoice) {
      return exactVoice
    }

    const chineseVoices = voices.filter(
      (voice) => voice.lang.toLowerCase().includes('zh') || /chinese|mandarin|普通话|中文/.test(voice.name.toLowerCase()),
    )
    if (!chineseVoices.length) {
      return undefined
    }

    if (normalizedName.includes('female')) {
      return findVoiceByKeywords(chineseVoices, ['xiaoxiao', 'xiaoyi', 'yaoyao', 'huihui', 'female']) ?? chineseVoices[0]
    }
    if (normalizedName.includes('male')) {
      return findVoiceByKeywords(chineseVoices, ['yunxi', 'yunjian', 'yunyang', 'kangkang', 'male']) ?? chineseVoices[0]
    }
    return chineseVoices[0]
  }

  function findVoiceByKeywords(voices: SpeechSynthesisVoice[], keywords: string[]) {
    return voices.find((voice) => {
      const voiceName = voice.name.toLowerCase()
      return keywords.some((keyword) => voiceName.includes(keyword))
    })
  }

  onBeforeUnmount(() => {
    stop()
    if (isSupported) {
      window.speechSynthesis.removeEventListener('voiceschanged', loadSpeechVoices)
    }
  })

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
