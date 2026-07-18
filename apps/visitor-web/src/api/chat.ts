import axios, { AxiosError } from 'axios'
import type { ApiErrorResponse, ChatRequest, ChatResponse, PersonalizedRecommendation, RecommendationRequest } from '../types/chat'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000',
  timeout: 12000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export async function sendChatMessage(payload: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
  const response = await apiClient.post<ChatResponse>('/api/v1/chat', payload, { signal })
  return response.data
}

export async function fetchPersonalizedRecommendation(
  payload: RecommendationRequest,
  signal?: AbortSignal,
): Promise<PersonalizedRecommendation> {
  const response = await apiClient.post<PersonalizedRecommendation>('/api/v1/recommendations', payload, { signal })
  return response.data
}

export function getChatErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorResponse>
    const apiMessage = axiosError.response?.data?.error?.message
    if (apiMessage) {
      return apiMessage
    }
    if (axiosError.code === 'ECONNABORTED') {
      return '请求超时，请稍后重试。'
    }
    if (!axiosError.response) {
      return '无法连接导游服务，请确认后端已启动。'
    }
  }
  return '导游服务暂时不可用，请稍后重试。'
}

export function isChatRequestCancelled(error: unknown): boolean {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError
    return axiosError.code === 'ERR_CANCELED'
  }
  return axios.isCancel(error)
}
