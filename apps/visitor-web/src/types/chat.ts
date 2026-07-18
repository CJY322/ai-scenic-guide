export type GuideEmotion = 'neutral' | 'friendly' | 'happy' | 'concerned' | 'serious'

export interface SourceItem {
  title: string
  section?: string | null
}

export interface ChatRequest {
  session_id: string
  question: string
  interests?: string[]
}

export interface ChatResponse {
  request_id: string
  answer: string
  sources: SourceItem[]
  emotion: GuideEmotion
  latency_ms: number
  fallback: boolean
}

export interface RecommendationRequest {
  interests: string[]
}

export interface RecommendationInterestOption {
  id: string
  label: string
  description: string
}

export interface PersonalizedRecommendation {
  request_id: string
  matched_interests: string[]
  route_title: string
  route_summary: string
  duration: string
  stops: string[]
  focus_points: string[]
  tips: string[]
  suggested_questions: string[]
  interest_options: RecommendationInterestOption[]
}

export interface ApiErrorResponse {
  error?: {
    code: string
    message: string
    request_id: string
  }
}

export type ChatRole = 'visitor' | 'guide'
export type ChatMessageStatus = 'normal' | 'loading' | 'error'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
  createdAt: Date
  status: ChatMessageStatus
  sources?: SourceItem[]
  requestId?: string
  latencyMs?: number
  fallback?: boolean
  retryQuestion?: string
}
