import axios, { AxiosError } from 'axios'
import type { ApiErrorResponse } from '../types/chat'
import type {
  AdminAnalyticsReport,
  AdminAppSettings,
  AdminAppSettingsUpdate,
  AdminAvatarProfile,
  AdminDashboardOverview,
  AdminFaqEntry,
  AdminKnowledgeFile,
  AdminKnowledgeFileContent,
  AdminSystemStatus,
} from '../types/admin'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export async function fetchAdminStatus(): Promise<AdminSystemStatus> {
  const response = await apiClient.get<AdminSystemStatus>('/api/v1/admin/status')
  return response.data
}

export async function fetchAnalyticsReport(): Promise<AdminAnalyticsReport> {
  const response = await apiClient.get<AdminAnalyticsReport>('/api/v1/admin/analytics/report')
  return response.data
}

export async function fetchDashboardOverview(): Promise<AdminDashboardOverview> {
  const response = await apiClient.get<AdminDashboardOverview>('/api/v1/admin/analytics/overview')
  return response.data
}

export async function fetchAdminSettings(): Promise<AdminAppSettings> {
  const response = await apiClient.get<AdminAppSettings>('/api/v1/admin/settings')
  return response.data
}

export async function updateAdminSettings(payload: AdminAppSettingsUpdate): Promise<AdminAppSettings> {
  const response = await apiClient.put<AdminAppSettings>('/api/v1/admin/settings', payload)
  return response.data
}

export async function fetchAvatarProfile(): Promise<AdminAvatarProfile> {
  const response = await apiClient.get<AdminAvatarProfile>('/api/v1/admin/avatar-profile')
  return response.data
}

export async function saveAvatarProfile(profile: AdminAvatarProfile): Promise<AdminAvatarProfile> {
  const response = await apiClient.put<AdminAvatarProfile>('/api/v1/admin/avatar-profile', profile)
  return response.data
}

export async function fetchKnowledgeFiles(): Promise<AdminKnowledgeFile[]> {
  const response = await apiClient.get<{ files: AdminKnowledgeFile[] }>('/api/v1/admin/knowledge')
  return response.data.files
}

export async function fetchKnowledgeFile(path: string): Promise<AdminKnowledgeFileContent> {
  const response = await apiClient.get<AdminKnowledgeFileContent>(`/api/v1/admin/knowledge/${encodePath(path)}`)
  return response.data
}

export async function saveKnowledgeFile(path: string, content: string): Promise<AdminKnowledgeFileContent> {
  const response = await apiClient.put<AdminKnowledgeFileContent>(`/api/v1/admin/knowledge/${encodePath(path)}`, {
    content,
  })
  return response.data
}

export async function fetchFaqEntries(): Promise<AdminFaqEntry[]> {
  const response = await apiClient.get<{ entries: AdminFaqEntry[] }>('/api/v1/admin/faq')
  return response.data.entries
}

export async function saveFaqEntries(entries: AdminFaqEntry[]): Promise<AdminFaqEntry[]> {
  const response = await apiClient.put<{ entries: AdminFaqEntry[] }>('/api/v1/admin/faq', { entries })
  return response.data.entries
}

export async function fetchRecommendedQuestions(): Promise<string[]> {
  const response = await apiClient.get<{ questions: string[] }>('/api/v1/admin/recommended-questions')
  return response.data.questions
}

export async function saveRecommendedQuestions(questions: string[]): Promise<string[]> {
  const response = await apiClient.put<{ questions: string[] }>('/api/v1/admin/recommended-questions', { questions })
  return response.data.questions
}

export function getAdminErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiErrorResponse>
    const apiMessage = axiosError.response?.data?.error?.message
    if (apiMessage) {
      return apiMessage
    }
    if (!axiosError.response) {
      return '无法连接管理接口，请确认后端已启动。'
    }
  }
  return '管理操作失败，请稍后重试。'
}

function encodePath(path: string): string {
  return path
    .split('/')
    .filter(Boolean)
    .map((segment) => encodeURIComponent(segment))
    .join('/')
}
