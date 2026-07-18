export type AnswerProvider = 'mock' | 'dify'
export type AvatarProvider = 'disabled' | 'sadtalker'
export type GuideEmotion = 'neutral' | 'friendly' | 'happy' | 'concerned' | 'serious'

export interface AdminSource {
  title: string
  section?: string | null
}

export interface AdminFaqEntry {
  keywords: string[]
  answer: string
  source: AdminSource
  emotion: GuideEmotion
}

export interface AdminKnowledgeFile {
  name: string
  path: string
  size_bytes: number
  updated_at: string
}

export interface AdminKnowledgeFileContent {
  name: string
  path: string
  content: string
  updated_at: string
}

export interface AdminAppSettings {
  answer_provider: AnswerProvider
  dify_api_base_url: string
  dify_api_key_masked?: string | null
  dify_timeout_seconds: number
  avatar_provider: AvatarProvider
  avatar_assets_path: string
  generated_assets_path: string
  sadtalker_root?: string | null
  sadtalker_python: string
  sadtalker_source_image?: string | null
  sadtalker_timeout_seconds: number
  sadtalker_preprocess: string
  sadtalker_expression_scale: number
  sadtalker_still: boolean
  sadtalker_use_cpu: boolean
}

export interface AdminAppSettingsUpdate {
  answer_provider?: AnswerProvider
  dify_api_base_url?: string
  dify_api_key?: string
  dify_timeout_seconds?: number
  avatar_provider?: AvatarProvider
  avatar_assets_path?: string
  generated_assets_path?: string
  sadtalker_root?: string
  sadtalker_python?: string
  sadtalker_source_image?: string
  sadtalker_timeout_seconds?: number
  sadtalker_preprocess?: string
  sadtalker_expression_scale?: number
  sadtalker_still?: boolean
  sadtalker_use_cpu?: boolean
}

export interface AdminAvatarProfile {
  display_name: string
  persona: string
  appearance_style: string
  clothing_style: string
  scenic_elements: string
  voice_name: string
  voice_style: string
  voice_rate: number
  voice_pitch: number
  voice_volume: number
  welcome_line: string
  idle_behavior: string
  culture_notes: string
}

export interface AdminSystemStatus {
  api: {
    status: string
    message: string
  }
  dify: {
    enabled: boolean
    api_base_url: string
    api_key_configured: boolean
  }
  avatar: {
    provider: string
    enabled: boolean
    supports_video: boolean
    source_image_exists: boolean
    generated_video_count: number
    message: string
  }
  content: {
    knowledge_file_count: number
    faq_entry_count: number
    recommended_question_count: number
    knowledge_path: string
    faq_path: string
    recommended_questions_path: string
  }
}

export interface AdminHotQuestion {
  question: string
  count: number
}

export interface AdminTopicMetric {
  topic: string
  count: number
  ratio: number
}

export interface AdminSentimentMetric {
  label: 'positive' | 'neutral' | 'concerned'
  count: number
  ratio: number
}

export interface AdminTrendPoint {
  date: string
  service_count: number
  satisfaction_score: number
  positive_count: number
  neutral_count: number
  concerned_count: number
}

export interface AdminServiceSuggestion {
  title: string
  detail: string
  priority: 'high' | 'medium' | 'low'
}

export interface AdminAnalyticsReport {
  generated_at: string
  total_interactions: number
  today_interactions: number
  week_interactions: number
  unique_sessions_today: number
  avg_latency_ms: number
  fallback_rate: number
  estimated_satisfaction_score: number
  hot_questions: AdminHotQuestion[]
  topic_metrics: AdminTopicMetric[]
  sentiment_metrics: AdminSentimentMetric[]
  trend: AdminTrendPoint[]
  service_suggestions: AdminServiceSuggestion[]
}

export interface AdminDashboardOverview {
  generated_at: string
  today_service_count: number
  week_service_count: number
  unique_sessions_today: number
  hot_questions: AdminHotQuestion[]
  satisfaction_trend: AdminTrendPoint[]
  topic_metrics: AdminTopicMetric[]
}
