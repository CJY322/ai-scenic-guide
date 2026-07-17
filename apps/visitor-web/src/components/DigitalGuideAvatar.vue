<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Headphones, Mic, Play, Sparkles, Volume2 } from '@lucide/vue'

const props = defineProps<{
  listening: boolean
  portraitMouthEnabled?: boolean
  portraitUrl?: string | null
  speaking: boolean
  thinking: boolean
  videoError?: string | null
  videoLoop?: boolean
  videoLoading?: boolean
  videoMuted?: boolean
  videoUrl?: string | null
}>()

const emit = defineEmits<{
  videoEnded: []
}>()

const portraitLoadFailed = ref(false)
const videoRef = ref<HTMLVideoElement | null>(null)
const videoNeedsStart = ref(false)
const showPortrait = computed(() => Boolean(props.portraitUrl) && !portraitLoadFailed.value)
const stateLabel = computed(() => {
  if (props.listening) {
    return '正在聆听'
  }
  if (props.videoError) {
    return props.videoError
  }
  if (props.thinking) {
    return '正在检索'
  }
  if (props.videoLoading) {
    return '生成真实讲解中'
  }
  if (props.videoUrl) {
    return '真实数字人讲解'
  }
  if (props.speaking) {
    return '正在讲解'
  }
  return '待机导览'
})

watch(
  () => props.portraitUrl,
  () => {
    portraitLoadFailed.value = false
  },
)

watch(
  () => props.videoUrl,
  () => {
    videoNeedsStart.value = false
    window.setTimeout(() => {
      if (videoRef.value) {
        videoRef.value.currentTime = 0
      }
      playVideo(videoRef.value)
    }, 0)
  },
)

function playVideo(video: HTMLVideoElement | null) {
  if (!video) {
    return
  }
  if (props.videoLoop && Number.isFinite(video.duration) && video.duration > 0.8 && video.currentTime < 0.08) {
    video.currentTime = 0.08
  }
  video
    .play()
    .then(() => {
      videoNeedsStart.value = false
    })
    .catch(() => {
      videoNeedsStart.value = true
    })
}

function handleVideoReady(event: Event) {
  playVideo(event.currentTarget as HTMLVideoElement)
}

function handleVideoProgress(event: Event) {
  const video = event.currentTarget as HTMLVideoElement
  if (!props.videoLoop || !Number.isFinite(video.duration) || video.duration <= 0.8) {
    return
  }

  const restartAt = Math.max(0.32, video.duration - 0.18)
  if (video.currentTime >= restartAt) {
    video.currentTime = Math.min(0.1, video.duration / 4)
    playVideo(video)
  }
}

function handleVideoEnded() {
  videoNeedsStart.value = false
  if (!props.videoLoop) {
    emit('videoEnded')
  }
}

function handleVideoPlay() {
  videoNeedsStart.value = false
}

function handleVideoPause(event: Event) {
  const video = event.currentTarget as HTMLVideoElement
  if (!video.ended && props.videoUrl) {
    videoNeedsStart.value = true
  }
}
</script>

<template>
  <section
    :class="[
      'digital-guide',
      {
        'digital-guide--listening': listening,
        'digital-guide--speaking': speaking,
        'digital-guide--thinking': thinking,
        'digital-guide--preparing': videoLoading,
        'digital-guide--portrait': showPortrait,
        'digital-guide--video': videoUrl,
      },
    ]"
    aria-label="数字人导游形象"
  >
    <div class="digital-guide__stage">
      <video
        v-if="videoUrl"
        ref="videoRef"
        :key="videoUrl"
        class="digital-guide__video"
        :src="videoUrl"
        :controls="false"
        :loop="videoLoop"
        :muted="videoMuted"
        autoplay
        controlslist="nodownload noplaybackrate noremoteplayback"
        disablepictureinpicture
        playsinline
        preload="auto"
        @canplay="handleVideoReady"
        @loadeddata="handleVideoReady"
        @loadedmetadata="handleVideoReady"
        @ended="handleVideoEnded"
        @pause="handleVideoPause"
        @play="handleVideoPlay"
        @timeupdate="handleVideoProgress"
      ></video>
      <button
        v-if="videoUrl && videoNeedsStart"
        type="button"
        class="digital-guide__play"
        @click="playVideo(videoRef)"
      >
        <Play :size="18" />
        <span>点击播放同步视频</span>
      </button>
      <div v-if="!videoUrl && showPortrait" class="digital-guide__portrait-wrap">
        <img class="digital-guide__portrait-backdrop" :src="portraitUrl ?? ''" alt="" />
        <img
          class="digital-guide__portrait"
          :src="portraitUrl ?? ''"
          alt=""
          @error="portraitLoadFailed = true"
        />
        <span v-if="portraitMouthEnabled !== false" class="portrait-mouth"></span>
        <span class="portrait-light portrait-light--one"></span>
        <span class="portrait-light portrait-light--two"></span>
      </div>
      <template v-if="!videoUrl && !showPortrait">
        <div class="mountain mountain--back"></div>
        <div class="mountain mountain--front"></div>
        <div class="guide-aura"></div>
        <div class="guide-figure">
          <div class="guide-hair"></div>
          <div class="guide-face">
            <span class="guide-eye guide-eye--left"></span>
            <span class="guide-eye guide-eye--right"></span>
            <span class="guide-mouth"></span>
          </div>
          <div class="guide-neck"></div>
          <div class="guide-body">
            <span class="guide-collar guide-collar--left"></span>
            <span class="guide-collar guide-collar--right"></span>
            <span class="guide-badge"></span>
          </div>
        </div>
        <span class="voice-wave voice-wave--one"></span>
        <span class="voice-wave voice-wave--two"></span>
        <span class="voice-wave voice-wave--three"></span>
      </template>
      <div v-if="videoLoading && !videoUrl" class="digital-guide__loading">
        <span class="digital-guide__loading-spinner"></span>
        <span>正在生成真实讲解，请稍候</span>
      </div>
      <div v-else-if="videoError && !videoUrl" class="digital-guide__error">
        {{ videoError }}
      </div>
    </div>

    <div class="digital-guide__status">
      <span class="status-icon">
        <Mic v-if="listening" :size="16" />
        <Volume2 v-else-if="speaking" :size="16" />
        <Sparkles v-else-if="thinking" :size="16" />
        <Headphones v-else :size="16" />
      </span>
      <span>{{ stateLabel }}</span>
    </div>
  </section>
</template>
