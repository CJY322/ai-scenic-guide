import { onBeforeUnmount, ref } from 'vue'

type SpeechRecognitionResultHandler = (transcript: string, isFinal: boolean) => void

interface SpeechRecognitionAlternativeLike {
  transcript: string
}

interface SpeechRecognitionResultLike {
  readonly isFinal: boolean
  readonly length: number
  [index: number]: SpeechRecognitionAlternativeLike
}

interface SpeechRecognitionResultListLike {
  readonly length: number
  [index: number]: SpeechRecognitionResultLike
}

interface SpeechRecognitionEventLike extends Event {
  readonly resultIndex: number
  readonly results: SpeechRecognitionResultListLike
}

interface SpeechRecognitionErrorEventLike extends Event {
  readonly error: string
}

interface SpeechRecognitionLike {
  continuous: boolean
  interimResults: boolean
  lang: string
  maxAlternatives: number
  onend: (() => void) | null
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null
  onresult: ((event: SpeechRecognitionEventLike) => void) | null
  onstart: (() => void) | null
  abort: () => void
  start: () => void
  stop: () => void
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike

const SPEECH_RECOGNITION_ERRORS: Record<string, string> = {
  'audio-capture': '未检测到可用麦克风',
  aborted: '语音输入已取消',
  'not-allowed': '麦克风权限未开启',
  network: '语音识别网络不可用',
  'no-speech': '没有识别到语音',
}

export function useSpeechRecognition(onResult: SpeechRecognitionResultHandler) {
  const isListening = ref(false)
  const interimTranscript = ref('')
  const error = ref('')
  const RecognitionConstructor = getSpeechRecognitionConstructor()
  const isSupported = Boolean(RecognitionConstructor)
  let recognition: SpeechRecognitionLike | null = null

  function start() {
    if (!RecognitionConstructor || isListening.value) {
      return
    }

    error.value = ''
    interimTranscript.value = ''
    recognition = new RecognitionConstructor()
    recognition.lang = 'zh-CN'
    recognition.continuous = false
    recognition.interimResults = true
    recognition.maxAlternatives = 1
    recognition.onstart = () => {
      isListening.value = true
    }
    recognition.onresult = handleResult
    recognition.onerror = handleError
    recognition.onend = () => {
      isListening.value = false
    }

    try {
      recognition.start()
    } catch {
      error.value = '语音输入启动失败'
      isListening.value = false
    }
  }

  function stop() {
    recognition?.stop()
    isListening.value = false
  }

  function abort() {
    recognition?.abort()
    isListening.value = false
  }

  function toggle() {
    if (isListening.value) {
      stop()
      return
    }
    start()
  }

  function handleResult(event: SpeechRecognitionEventLike) {
    let finalTranscript = ''
    let interimText = ''

    for (let index = event.resultIndex; index < event.results.length; index += 1) {
      const result = event.results[index]
      const transcript = result[0]?.transcript ?? ''
      if (result.isFinal) {
        finalTranscript += transcript
      } else {
        interimText += transcript
      }
    }

    if (finalTranscript.trim()) {
      const text = finalTranscript.trim()
      interimTranscript.value = ''
      onResult(text, true)
      return
    }

    if (interimText.trim()) {
      const text = interimText.trim()
      interimTranscript.value = text
      onResult(text, false)
    }
  }

  function handleError(event: SpeechRecognitionErrorEventLike) {
    error.value = SPEECH_RECOGNITION_ERRORS[event.error] ?? '语音识别失败'
    isListening.value = false
  }

  onBeforeUnmount(abort)

  return {
    error,
    interimTranscript,
    isListening,
    isSupported,
    start,
    stop,
    toggle,
  }
}

function getSpeechRecognitionConstructor(): SpeechRecognitionConstructor | null {
  if (typeof window === 'undefined') {
    return null
  }

  const browserWindow = window as Window & {
    SpeechRecognition?: SpeechRecognitionConstructor
    webkitSpeechRecognition?: SpeechRecognitionConstructor
  }

  return browserWindow.SpeechRecognition ?? browserWindow.webkitSpeechRecognition ?? null
}
