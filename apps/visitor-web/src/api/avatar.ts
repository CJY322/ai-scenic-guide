import axios, { AxiosError } from 'axios'
import type { ApiErrorResponse } from '../types/chat'
import type { AvatarStatusResponse, AvatarVideoRequest, AvatarVideoResponse } from '../types/avatar'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000',
  timeout: 960000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export async function fetchAvatarStatus(): Promise<AvatarStatusResponse> {
  const response = await apiClient.get<AvatarStatusResponse>('/api/v1/avatar/status')
  return response.data
}

export async function generateAvatarVideo(payload: AvatarVideoRequest): Promise<AvatarVideoResponse> {
  const response = await apiClient.post<AvatarVideoResponse>('/api/v1/avatar/video', payload)
  return response.data
}

export function resolveAvatarVideoUrl(videoUrl: string): string {
  if (/^https?:\/\//.test(videoUrl)) {
    return videoUrl
  }
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
  return `${baseUrl.replace(/\/$/, '')}${videoUrl.startsWith('/') ? videoUrl : `/${videoUrl}`}`
}

export function resolveAvatarAssetUrl(assetUrl: string): string {
  if (/^https?:\/\//.test(assetUrl)) {
    return assetUrl
  }
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
  return `${baseUrl.replace(/\/$/, '')}${assetUrl.startsWith('/') ? assetUrl : `/${assetUrl}`}`
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
