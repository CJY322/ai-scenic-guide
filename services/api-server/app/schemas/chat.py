from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

Emotion = Literal["neutral", "friendly", "happy", "concerned", "serious"]

SessionId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Question = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Interest = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class SourceItem(BaseModel):
    title: ShortText
    section: ShortText | None = None


class ChatRequest(BaseModel):
    session_id: SessionId
    question: Question
    interests: list[Interest] = Field(default_factory=list, max_length=5)


class ChatResponse(BaseModel):
    request_id: str
    answer: str
    sources: list[SourceItem] = Field(default_factory=list)
    emotion: Emotion = "friendly"
    latency_ms: int = Field(ge=0)
    fallback: bool = False


class RecommendationRequest(BaseModel):
    interests: list[Interest] = Field(default_factory=list, max_length=5)


class RecommendationInterestOption(BaseModel):
    id: str
    label: ShortText
    description: str


class PersonalizedRecommendationResponse(BaseModel):
    request_id: str
    matched_interests: list[ShortText]
    route_title: ShortText
    route_summary: str
    duration: ShortText
    stops: list[ShortText]
    focus_points: list[str]
    tips: list[str]
    suggested_questions: list[ShortText]
    interest_options: list[RecommendationInterestOption]


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
