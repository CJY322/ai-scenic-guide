import logging
from functools import lru_cache
from time import perf_counter

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.core.request_id import generate_request_id
from app.schemas.chat import ChatRequest, ChatResponse, ErrorResponse
from app.services.dify_service import DifyGuideService
from app.services.guide_service import GuideService, GuideServiceUnavailableError

router = APIRouter()
logger = logging.getLogger(__name__)


@lru_cache
def get_guide_service() -> GuideService | DifyGuideService:
    settings = get_settings()
    if settings.answer_provider == "dify":
        return DifyGuideService(
            api_base_url=settings.dify_api_base_url,
            api_key=settings.dify_api_key,
            timeout_seconds=settings.dify_timeout_seconds,
        )
    return GuideService(settings.mock_data_path)


@router.get("/health")
def health(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.version,
    }


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def chat(
    payload: ChatRequest,
    request: Request,
    service: GuideService | DifyGuideService = Depends(get_guide_service),
) -> ChatResponse | JSONResponse:
    start = perf_counter()
    request_id = generate_request_id()
    status_code = status.HTTP_200_OK

    try:
        guide_answer = service.ask(payload.question, payload.interests, session_id=payload.session_id)
        latency_ms = max(0, round((perf_counter() - start) * 1000))
        return ChatResponse(
            request_id=request_id,
            answer=guide_answer.answer,
            sources=guide_answer.sources,
            emotion=guide_answer.emotion,
            latency_ms=latency_ms,
            fallback=guide_answer.fallback,
        )
    except GuideServiceUnavailableError:
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        logger.exception("guide service unavailable request_id=%s", request_id)
        return _error_response(
            status_code=status_code,
            code="GUIDE_SERVICE_UNAVAILABLE",
            message="导游服务暂时不可用，请稍后重试",
            request_id=request_id,
        )
    except Exception:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        logger.exception("internal chat error request_id=%s", request_id)
        return _error_response(
            status_code=status_code,
            code="INTERNAL_ERROR",
            message="服务暂时开小差了，请稍后再试",
            request_id=request_id,
        )
    finally:
        latency_ms = max(0, round((perf_counter() - start) * 1000))
        logger.info(
            "request_id=%s session_id=%s question_length=%s method=%s path=%s status=%s latency_ms=%s",
            request_id,
            payload.session_id,
            len(payload.question),
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
