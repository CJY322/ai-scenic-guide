export interface AvatarStatusResponse {
  enabled: boolean
  provider: string
  supports_video: boolean
  message: string
}

export interface AvatarVideoRequest {
  text: string
  message_id?: string
  session_id?: string
}

export interface AvatarVideoResponse {
  request_id: string
  provider: string
  video_url: string
  cached: boolean
  latency_ms: number
}

export interface AvatarCancelRequest {
  message_id?: string
  session_id?: string
}

export interface AvatarCancelResponse {
  request_id: string
  cancelled: number
  message: string
}
