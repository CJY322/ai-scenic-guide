import logging
from functools import lru_cache
from time import perf_counter

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.core.request_id import generate_request_id
from app.schemas.avatar import AvatarStatusResponse, AvatarVideoRequest, AvatarVideoResponse
from app.schemas.chat import ErrorResponse
from app.services.avatar_service import (
    AvatarGenerationError,
    AvatarGenerationUnavailableError,
    SadTalkerAvatarService,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@lru_cache
def get_avatar_service() -> SadTalkerAvatarService:
    settings = get_settings()
    return SadTalkerAvatarService(
        provider=settings.avatar_provider,
        generated_assets_path=settings.generated_assets_path,
        sadtalker_root=settings.sadtalker_root,
        sadtalker_python=settings.sadtalker_python,
        sadtalker_source_image=settings.sadtalker_source_image,
        sadtalker_timeout_seconds=settings.sadtalker_timeout_seconds,
        sadtalker_preprocess=settings.sadtalker_preprocess,
        sadtalker_expression_scale=settings.sadtalker_expression_scale,
        sadtalker_still=settings.sadtalker_still,
        sadtalker_use_cpu=settings.sadtalker_use_cpu,
        tts_script_path=settings.sadtalker_tts_script_path,
    )


@router.get("/avatar/status", response_model=AvatarStatusResponse)
def avatar_status(service: SadTalkerAvatarService = Depends(get_avatar_service)) -> AvatarStatusResponse:
    status_info = service.status()
    return AvatarStatusResponse(
        enabled=status_info.enabled,
        provider=status_info.provider,
        supports_video=status_info.supports_video,
        message=status_info.message,
    )


@router.post(
    "/avatar/video",
    response_model=AvatarVideoResponse,
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def avatar_video(
    payload: AvatarVideoRequest,
    request: Request,
    service: SadTalkerAvatarService = Depends(get_avatar_service),
) -> AvatarVideoResponse | JSONResponse:
    start = perf_counter()
    request_id = generate_request_id()
    status_code = status.HTTP_200_OK

    try:
        video = service.generate_video(payload.text)
        latency_ms = max(0, round((perf_counter() - start) * 1000))
        return AvatarVideoResponse(
            request_id=request_id,
            provider=video.provider,
            video_url=video.video_url,
            cached=video.cached,
            latency_ms=latency_ms,
        )
    except AvatarGenerationUnavailableError:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.info("avatar unavailable request_id=%s", request_id)
        return _error_response(
            status_code=status_code,
            code="AVATAR_UNAVAILABLE",
            message="真实数字人暂未配置完成",
            request_id=request_id,
        )
    except AvatarGenerationError:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        logger.exception("avatar generation failed request_id=%s", request_id)
        return _error_response(
            status_code=status_code,
            code="AVATAR_GENERATION_FAILED",
            message="真实数字人视频生成失败，请检查 SadTalker 安装和模型权重",
            request_id=request_id,
        )
    except Exception:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        logger.exception("internal avatar error request_id=%s", request_id)
        return _error_response(
            status_code=status_code,
            code="INTERNAL_ERROR",
            message="真实数字人服务暂时不可用",
            request_id=request_id,
        )
    finally:
        latency_ms = max(0, round((perf_counter() - start) * 1000))
        logger.info(
            "request_id=%s message_id=%s method=%s path=%s status=%s latency_ms=%s",
            request_id,
            payload.message_id,
            request.method,
            request.url.path,
            status_code,
            latency_ms,
        )


def _error_response(status_code: int, code: str, message: str, request_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
            }
        },
    )
