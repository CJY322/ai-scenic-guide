from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.core.config import Settings, get_settings
from app.core.request_id import generate_request_id
from app.schemas.admin import (
    AdminAnalyticsReportResponse,
    AdminAppSettingsResponse,
    AdminAppSettingsUpdateRequest,
    AdminAvatarProfile,
    AdminAvatarProfileUpdateRequest,
    AdminDashboardOverviewResponse,
    AdminFaqResponse,
    AdminFaqUpdateRequest,
    AdminKnowledgeFileResponse,
    AdminKnowledgeListResponse,
    AdminKnowledgeUpdateRequest,
    AdminRecommendedQuestionsResponse,
    AdminRecommendedQuestionsUpdateRequest,
    AdminSystemStatusResponse,
)
from app.schemas.chat import ErrorResponse
from app.services.admin_service import AdminDataError, AdminService
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/admin", tags=["admin"])


def get_admin_service(settings: Settings = Depends(get_settings)) -> AdminService:
    return AdminService(settings)


@router.get("/status", response_model=AdminSystemStatusResponse)
def admin_status(service: AdminService = Depends(get_admin_service)) -> AdminSystemStatusResponse:
    return service.get_status()


@router.get("/analytics/report", response_model=AdminAnalyticsReportResponse)
def analytics_report() -> AdminAnalyticsReportResponse:
    return AnalyticsService().build_report()


@router.get("/analytics/overview", response_model=AdminDashboardOverviewResponse)
def analytics_overview() -> AdminDashboardOverviewResponse:
    return AnalyticsService().build_overview()


@router.get("/settings", response_model=AdminAppSettingsResponse)
def admin_settings(service: AdminService = Depends(get_admin_service)) -> AdminAppSettingsResponse:
    return service.get_app_settings()


@router.put("/settings", response_model=AdminAppSettingsResponse, responses={500: {"model": ErrorResponse}})
def update_admin_settings(
    payload: AdminAppSettingsUpdateRequest,
    service: AdminService = Depends(get_admin_service),
) -> AdminAppSettingsResponse | JSONResponse:
    try:
        service.update_app_settings(payload)
        _clear_runtime_caches()
        return AdminService(get_settings()).get_app_settings()
    except AdminDataError as exc:
        return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "ADMIN_SETTINGS_SAVE_FAILED", str(exc))


@router.get("/avatar-profile", response_model=AdminAvatarProfile, responses={500: {"model": ErrorResponse}})
def avatar_profile(service: AdminService = Depends(get_admin_service)) -> AdminAvatarProfile | JSONResponse:
    try:
        return service.get_avatar_profile()
    except AdminDataError as exc:
        return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "ADMIN_AVATAR_PROFILE_READ_FAILED", str(exc))


@router.put("/avatar-profile", response_model=AdminAvatarProfile, responses={500: {"model": ErrorResponse}})
def save_avatar_profile(
    payload: AdminAvatarProfileUpdateRequest,
    service: AdminService = Depends(get_admin_service),
) -> AdminAvatarProfile | JSONResponse:
    try:
        return service.save_avatar_profile(payload)
    except AdminDataError as exc:
        return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "ADMIN_AVATAR_PROFILE_SAVE_FAILED", str(exc))


@router.get("/knowledge", response_model=AdminKnowledgeListResponse, responses={500: {"model": ErrorResponse}})
def list_knowledge(service: AdminService = Depends(get_admin_service)) -> AdminKnowledgeListResponse | JSONResponse:
    try:
        return AdminKnowledgeListResponse(files=service.list_knowledge_files())
    except AdminDataError as exc:
        return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "ADMIN_KNOWLEDGE_READ_FAILED", str(exc))


@router.get(
    "/knowledge/{relative_path:path}",
    response_model=AdminKnowledgeFileResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def read_knowledge_file(
    relative_path: str,
    service: AdminService = Depends(get_admin_service),
) -> AdminKnowledgeFileResponse | JSONResponse:
    try:
        return service.read_knowledge_file(relative_path)
    except AdminDataError as exc:
        return _error_response(status.HTTP_404_NOT_FOUND, "ADMIN_KNOWLEDGE_FILE_UNAVAILABLE", str(exc))


@router.put(
    "/knowledge/{relative_path:path}",
    response_model=AdminKnowledgeFileResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
def save_knowledge_file(
    relative_path: str,
    payload: AdminKnowledgeUpdateRequest,
    service: AdminService = Depends(get_admin_service),
) -> AdminKnowledgeFileResponse | JSONResponse:
    try:
        return service.save_knowledge_file(relative_path, payload.content)
    except AdminDataError as exc:
        return _error_response(status.HTTP_400_BAD_REQUEST, "ADMIN_KNOWLEDGE_SAVE_FAILED", str(exc))


@router.get("/faq", response_model=AdminFaqResponse, responses={500: {"model": ErrorResponse}})
def list_faq(service: AdminService = Depends(get_admin_service)) -> AdminFaqResponse | JSONResponse:
    try:
        return AdminFaqResponse(entries=service.list_faq_entries())
    except AdminDataError as exc:
        return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "ADMIN_FAQ_READ_FAILED", str(exc))


@router.put("/faq", response_model=AdminFaqResponse, responses={500: {"model": ErrorResponse}})
def save_faq(
    payload: AdminFaqUpdateRequest,
    service: AdminService = Depends(get_admin_service),
) -> AdminFaqResponse | JSONResponse:
    try:
        service.save_faq_entries(payload.entries)
        _clear_guide_cache()
        return AdminFaqResponse(entries=service.list_faq_entries())
    except AdminDataError as exc:
        return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "ADMIN_FAQ_SAVE_FAILED", str(exc))


@router.get("/recommended-questions", response_model=AdminRecommendedQuestionsResponse)
def list_recommended_questions(
    service: AdminService = Depends(get_admin_service),
) -> AdminRecommendedQuestionsResponse:
    return AdminRecommendedQuestionsResponse(questions=service.list_recommended_questions())


@router.put(
    "/recommended-questions",
    response_model=AdminRecommendedQuestionsResponse,
    responses={500: {"model": ErrorResponse}},
)
def save_recommended_questions(
    payload: AdminRecommendedQuestionsUpdateRequest,
    service: AdminService = Depends(get_admin_service),
) -> AdminRecommendedQuestionsResponse | JSONResponse:
    try:
        service.save_recommended_questions(payload.questions)
        return AdminRecommendedQuestionsResponse(questions=service.list_recommended_questions())
    except AdminDataError as exc:
        return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "ADMIN_RECOMMENDED_SAVE_FAILED", str(exc))


def _clear_runtime_caches() -> None:
    get_settings.cache_clear()
    _clear_guide_cache()
    from app.api.routes.avatar import get_avatar_service

    get_avatar_service.cache_clear()


def _clear_guide_cache() -> None:
    from app.api.routes.chat import get_guide_service

    get_guide_service.cache_clear()


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": generate_request_id(),
            }
        },
    )
