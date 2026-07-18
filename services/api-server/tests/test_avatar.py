from fastapi.testclient import TestClient

from app.api.routes.avatar import get_avatar_service
from app.main import app
from app.services.avatar_service import AvatarGenerationUnavailableError

client = TestClient(app)


class FakeDisabledAvatarService:
    def status(self):
        class Status:
            enabled = False
            provider = "disabled"
            supports_video = False
            message = "真实数字人未启用"

        return Status()

    def generate_video(self, text: str, session_id: str | None = None, message_id: str | None = None):
        raise AvatarGenerationUnavailableError("真实数字人未启用")


def test_avatar_status_is_disabled_by_default() -> None:
    app.dependency_overrides[get_avatar_service] = lambda: FakeDisabledAvatarService()

    try:
        response = client.get("/api/v1/avatar/status")
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 200
    assert body["enabled"] is False
    assert body["supports_video"] is False


def test_avatar_video_returns_503_when_unconfigured() -> None:
    app.dependency_overrides[get_avatar_service] = lambda: FakeDisabledAvatarService()

    try:
        response = client.post("/api/v1/avatar/video", json={"text": "欢迎来到灵山胜境。"})
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 503
    assert body["error"]["code"] == "AVATAR_UNAVAILABLE"


def test_avatar_video_returns_generated_video() -> None:
    class FakeAvatarService:
        def generate_video(self, text: str, session_id: str | None = None, message_id: str | None = None):
            class Video:
                provider = "sadtalker"
                video_url = "/generated/avatar/demo.mp4"
                cached = False

            return Video()

    app.dependency_overrides[get_avatar_service] = lambda: FakeAvatarService()

    try:
        response = client.post(
            "/api/v1/avatar/video",
            json={"message_id": "guide-001", "text": "欢迎来到灵山胜境。"},
        )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 200
    assert body["provider"] == "sadtalker"
    assert body["video_url"] == "/generated/avatar/demo.mp4"
    assert body["cached"] is False
    assert body["latency_ms"] >= 0


def test_avatar_cancel_returns_cancel_count() -> None:
    class FakeAvatarService:
        def cancel_jobs(self, session_id: str | None = None, message_id: str | None = None):
            class Result:
                cancelled = 2

            assert session_id == "web-demo"
            return Result()

    app.dependency_overrides[get_avatar_service] = lambda: FakeAvatarService()

    try:
        response = client.post("/api/v1/avatar/cancel?session_id=web-demo")
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 200
    assert body["cancelled"] == 2
    assert body["message"]
