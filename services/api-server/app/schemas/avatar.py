from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

AvatarText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1200)]
MessageId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class AvatarStatusResponse(BaseModel):
    enabled: bool
    provider: str
    supports_video: bool
    message: str


class AvatarVideoRequest(BaseModel):
    text: AvatarText
    message_id: MessageId | None = None
    session_id: MessageId | None = None


class AvatarVideoResponse(BaseModel):
    request_id: str
    provider: str
    video_url: str
    cached: bool = False
    latency_ms: int = Field(ge=0)


class AvatarCancelResponse(BaseModel):
    request_id: str
    cancelled: int = Field(ge=0)
    message: str
