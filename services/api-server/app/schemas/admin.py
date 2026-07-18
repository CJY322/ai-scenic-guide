from typing import Literal

from pydantic import BaseModel, Field


Emotion = Literal["neutral", "friendly", "happy", "concerned", "serious"]


class AdminSource(BaseModel):
    title: str = Field(default="管理后台", max_length=80)
    section: str | None = Field(default=None, max_length=80)


class AdminFaqEntry(BaseModel):
    keywords: list[str] = Field(default_factory=list, max_length=20)
    answer: str = Field(min_length=1, max_length=3000)
    source: AdminSource = Field(default_factory=AdminSource)
    emotion: Emotion = "friendly"


class AdminFaqResponse(BaseModel):
    entries: list[AdminFaqEntry]


class AdminFaqUpdateRequest(BaseModel):
    entries: list[AdminFaqEntry] = Field(default_factory=list, max_length=100)


class AdminKnowledgeFile(BaseModel):
    name: str
    path: str
    size_bytes: int
    updated_at: str


class AdminKnowledgeListResponse(BaseModel):
    files: list[AdminKnowledgeFile]


class AdminKnowledgeFileResponse(BaseModel):
    name: str
    path: str
    content: str
    updated_at: str


class AdminKnowledgeUpdateRequest(BaseModel):
    content: str = Field(max_length=120000)


class AdminRecommendedQuestionsResponse(BaseModel):
    questions: list[str]


class AdminRecommendedQuestionsUpdateRequest(BaseModel):
    questions: list[str] = Field(default_factory=list, max_length=12)


class AdminAvatarProfile(BaseModel):
    display_name: str = Field(default="灵山胜境AI导游", max_length=40)
    persona: str = Field(default="亲切、稳重、熟悉灵山佛教文化的景区讲解员", max_length=300)
    appearance_style: str = Field(default="年轻女性导游形象，亲和自然，适合景区游客服务场景", max_length=300)
    clothing_style: str = Field(default="新中式导游制服，搭配灵山胜境文化元素", max_length=300)
    scenic_elements: str = Field(default="灵山大佛、莲花、太湖、梵宫纹样", max_length=300)
    voice_name: str = Field(default="zh-CN female", max_length=80)
    voice_style: str = Field(default="温和清晰，语速适中，适合老人和亲子游客", max_length=300)
    voice_rate: float = Field(default=0.95, ge=0.5, le=1.5)
    voice_pitch: float = Field(default=1.0, ge=0.5, le=1.5)
    voice_volume: float = Field(default=1.0, ge=0, le=1)
    welcome_line: str = Field(default="您好，我是灵山胜境AI数字人导游。", max_length=300)
    idle_behavior: str = Field(default="待机时保持微笑，回答时配合口型和轻微点头", max_length=300)
    culture_notes: str = Field(default="讲解时注意佛教文化表达准确、庄重，避免夸张娱乐化。", max_length=500)


class AdminAvatarProfileUpdateRequest(AdminAvatarProfile):
    pass


class AdminAppSettingsResponse(BaseModel):
    answer_provider: Literal["mock", "dify"]
    dify_api_base_url: str
    dify_api_key_masked: str | None
    dify_timeout_seconds: float
    avatar_provider: Literal["disabled", "sadtalker"]
    avatar_assets_path: str
    generated_assets_path: str
    sadtalker_root: str | None
    sadtalker_python: str
    sadtalker_source_image: str | None
    sadtalker_timeout_seconds: float
    sadtalker_preprocess: str
    sadtalker_expression_scale: float
    sadtalker_still: bool
    sadtalker_use_cpu: bool


class AdminAppSettingsUpdateRequest(BaseModel):
    answer_provider: Literal["mock", "dify"] | None = None
    dify_api_base_url: str | None = Field(default=None, max_length=300)
    dify_api_key: str | None = Field(default=None, max_length=500)
    dify_timeout_seconds: float | None = Field(default=None, ge=3, le=180)
    avatar_provider: Literal["disabled", "sadtalker"] | None = None
    avatar_assets_path: str | None = Field(default=None, max_length=500)
    generated_assets_path: str | None = Field(default=None, max_length=500)
    sadtalker_root: str | None = Field(default=None, max_length=500)
    sadtalker_python: str | None = Field(default=None, max_length=500)
    sadtalker_source_image: str | None = Field(default=None, max_length=500)
    sadtalker_timeout_seconds: float | None = Field(default=None, ge=30, le=3600)
    sadtalker_preprocess: str | None = Field(default=None, max_length=40)
    sadtalker_expression_scale: float | None = Field(default=None, ge=0.2, le=5)
    sadtalker_still: bool | None = None
    sadtalker_use_cpu: bool | None = None


class AdminStatusSection(BaseModel):
    status: str
    message: str


class AdminContentStatus(BaseModel):
    knowledge_file_count: int
    faq_entry_count: int
    recommended_question_count: int
    knowledge_path: str
    faq_path: str
    recommended_questions_path: str


class AdminDifyStatus(BaseModel):
    enabled: bool
    api_base_url: str
    api_key_configured: bool


class AdminAvatarStatus(BaseModel):
    provider: str
    enabled: bool
    supports_video: bool
    source_image_exists: bool
    generated_video_count: int
    message: str


class AdminSystemStatusResponse(BaseModel):
    api: AdminStatusSection
    dify: AdminDifyStatus
    avatar: AdminAvatarStatus
    content: AdminContentStatus


class AdminHotQuestion(BaseModel):
    question: str
    count: int


class AdminTopicMetric(BaseModel):
    topic: str
    count: int
    ratio: float


class AdminSentimentMetric(BaseModel):
    label: str
    count: int
    ratio: float


class AdminTrendPoint(BaseModel):
    date: str
    service_count: int
    satisfaction_score: float
    positive_count: int
    neutral_count: int
    concerned_count: int


class AdminServiceSuggestion(BaseModel):
    title: str
    detail: str
    priority: Literal["high", "medium", "low"]


class AdminAnalyticsReportResponse(BaseModel):
    generated_at: str
    total_interactions: int
    today_interactions: int
    week_interactions: int
    unique_sessions_today: int
    avg_latency_ms: int
    fallback_rate: float
    estimated_satisfaction_score: float
    hot_questions: list[AdminHotQuestion]
    topic_metrics: list[AdminTopicMetric]
    sentiment_metrics: list[AdminSentimentMetric]
    trend: list[AdminTrendPoint]
    service_suggestions: list[AdminServiceSuggestion]


class AdminDashboardOverviewResponse(BaseModel):
    generated_at: str
    today_service_count: int
    week_service_count: int
    unique_sessions_today: int
    hot_questions: list[AdminHotQuestion]
    satisfaction_trend: list[AdminTrendPoint]
    topic_metrics: list[AdminTopicMetric]
