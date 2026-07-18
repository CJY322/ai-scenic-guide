import axios, { AxiosError } from 'axios'
import type { ApiErrorResponse } from '../types/chat'
import type {
  AvatarCancelRequest,
  AvatarCancelResponse,
  AvatarStatusResponse,
  AvatarVideoRequest,
  AvatarVideoResponse,
} from '../types/avatar'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 960000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export async function fetchAvatarStatus(): Promise<AvatarStatusResponse> {
  const response = await apiClient.get<AvatarStatusResponse>('/api/v1/avatar/status')
  return response.data
}

export async function generateAvatarVideo(
  payload: AvatarVideoRequest,
  signal?: AbortSignal,
): Promise<AvatarVideoResponse> {
  const response = await apiClient.post<AvatarVideoResponse>('/api/v1/avatar/video', payload, { signal })
  return response.data
}

export async function cancelAvatarTasks(payload: AvatarCancelRequest): Promise<AvatarCancelResponse> {
  const response = await apiClient.post<AvatarCancelResponse>('/api/v1/avatar/cancel', undefined, {
    params: payload,
    timeout: 5000,
  })
  return response.data
}

export function sendAvatarCancelBeacon(payload: AvatarCancelRequest): boolean {
  const url = new URL('/api/v1/avatar/cancel', API_BASE_URL)
  if (payload.session_id) {
    url.searchParams.set('session_id', payload.session_id)
  }
  if (payload.message_id) {
    url.searchParams.set('message_id', payload.message_id)
  }

  if (typeof navigator !== 'undefined' && typeof navigator.sendBeacon === 'function') {
    return navigator.sendBeacon(url.toString())
  }

  void fetch(url.toString(), {
    method: 'POST',
    mode: 'cors',
    keepalive: true,
  }).catch(() => undefined)
  return true
}

export function resolveAvatarVideoUrl(videoUrl: string): string {
  if (/^https?:\/\//.test(videoUrl)) {
    return videoUrl
  }
  return `${API_BASE_URL.replace(/\/$/, '')}${videoUrl.startsWith('/') ? videoUrl : `/${videoUrl}`}`
}

export function resolveAvatarAssetUrl(assetUrl: string): string {
  if (/^https?:\/\//.test(assetUrl)) {
    return assetUrl
  }
  return `${API_BASE_URL.replace(/\/$/, '')}${assetUrl.startsWith('/') ? assetUrl : `/${assetUrl}`}`
}

export function getAvatarErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorResponse>
    const apiMessage = axiosError.response?.data?.error?.message
    if (apiMessage) {
      return apiMessage
    }
    if (axiosError.code === 'ECONNABORTED') {
      return '数字人视频生成超时，请稍后重试。'
    }
    if (!axiosError.response) {
      return '无法连接数字人服务，请确认后端已启动。'
    }
  }
  return '数字人视频暂时不可用。'
}

export function isAvatarRequestCancelled(error: unknown): boolean {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError
    return axiosError.code === 'ERR_CANCELED'
  }
  return axios.isCancel(error)
}
