export interface AvatarStatusResponse {
  enabled: boolean
  provider: string
  supports_video: boolean
  message: string
}

export interface AvatarVideoRequest {
  text: string
  message_id?: string
}

export interface AvatarVideoResponse {
  request_id: string
  provider: string
  video_url: string
  cached: boolean
  latency_ms: number
}
