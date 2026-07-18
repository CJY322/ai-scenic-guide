from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes.admin import router as admin_router
from app.api.routes.avatar import router as avatar_router
from app.api.routes.chat import router as chat_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.request_id import generate_request_id

configure_logging()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI景区数字人导游第一阶段文字问答MVP接口",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.avatar_assets_path.mkdir(parents=True, exist_ok=True)
settings.generated_assets_path.mkdir(parents=True, exist_ok=True)
app.mount("/avatar-assets", StaticFiles(directory=settings.avatar_assets_path), name="avatar-assets")
app.mount("/generated", StaticFiles(directory=settings.generated_assets_path), name="generated")

app.include_router(admin_router, prefix=settings.api_prefix)
app.include_router(avatar_router, prefix=settings.api_prefix)
app.include_router(chat_router, prefix=settings.api_prefix)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "INVALID_QUESTION",
                "message": "请求参数不符合要求",
                "request_id": generate_request_id(),
            }
        },
    )
