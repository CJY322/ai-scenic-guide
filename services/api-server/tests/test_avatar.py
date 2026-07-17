from fastapi.testclient import TestClient

from app.api.routes.avatar import get_avatar_service
from app.main import app

client = TestClient(app)


def test_avatar_status_is_disabled_by_default() -> None:
    response = client.get("/api/v1/avatar/status")

    body = response.json()
    assert response.status_code == 200
    assert body["enabled"] is False
    assert body["supports_video"] is False


def test_avatar_video_returns_503_when_unconfigured() -> None:
    response = client.post("/api/v1/avatar/video", json={"text": "欢迎来到黄山。"})

    body = response.json()
    assert response.status_code == 503
    assert body["error"]["code"] == "AVATAR_UNAVAILABLE"


def test_avatar_video_returns_generated_video() -> None:
    class FakeAvatarService:
        def generate_video(self, text: str):
            class Video:
                provider = "sadtalker"
                video_url = "/generated/avatar/demo.mp4"
                cached = False

            return Video()

    app.dependency_overrides[get_avatar_service] = lambda: FakeAvatarService()

    try:
        response = client.post(
            "/api/v1/avatar/video",
            json={"message_id": "guide-001", "text": "欢迎来到黄山。"},
        )
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 200
    assert body["provider"] == "sadtalker"
    assert body["video_url"] == "/generated/avatar/demo.mp4"
    assert body["cached"] is False
    assert body["latency_ms"] >= 0
