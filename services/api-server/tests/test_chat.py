from fastapi.testclient import TestClient
import pytest

from app.api.routes.chat import get_guide_service
from app.main import app
from app.schemas.chat import SourceItem

client = TestClient(app)


class FakeGuideAnswer:
    def __init__(self, answer: str, sources: list[SourceItem], fallback: bool) -> None:
        self.answer = answer
        self.sources = sources
        self.emotion = "friendly"
        self.fallback = fallback


class FakeGuideService:
    def ask(
        self,
        question: str,
        interests: list[str] | None = None,
        session_id: str | None = None,
    ) -> FakeGuideAnswer:
        if "火星" in question:
            return FakeGuideAnswer(
                answer="暂未查询到相关资料。当前为第一阶段模拟回答，建议以景区官方公告为准。",
                sources=[],
                fallback=True,
            )
        return FakeGuideAnswer(
            answer="建议优先参观迎客松、莲花峰和光明顶，并结合当天开放信息安排路线。",
            sources=[SourceItem(title="测试知识库", section="主要景点")],
            fallback=False,
        )


@pytest.fixture(autouse=True)
def use_fake_guide_service():
    app.dependency_overrides[get_guide_service] = lambda: FakeGuideService()
    yield
    app.dependency_overrides.clear()


def valid_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "session_id": "test-session-001",
        "question": "景区有哪些值得参观的景点？",
        "interests": ["历史文化"],
    }
    payload.update(overrides)
    return payload


def test_chat_returns_mock_answer() -> None:
    response = client.post("/api/v1/chat", json=valid_payload())

    body = response.json()
    assert response.status_code == 200
    assert body["request_id"].startswith("req-")
    assert body["answer"]
    assert body["sources"]
    assert body["emotion"] in {"neutral", "friendly", "happy", "concerned", "serious"}
    assert body["latency_ms"] >= 0
    assert body["fallback"] is False


def test_chat_rejects_empty_question() -> None:
    response = client.post("/api/v1/chat", json=valid_payload(question="   "))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_QUESTION"


def test_chat_rejects_question_over_500_characters() -> None:
    response = client.post("/api/v1/chat", json=valid_payload(question="景" * 501))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_QUESTION"


def test_chat_rejects_more_than_five_interests() -> None:
    response = client.post(
        "/api/v1/chat",
        json=valid_payload(interests=["历史", "自然", "摄影", "亲子", "美食", "研学"]),
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_QUESTION"


def test_chat_returns_fallback_when_mock_data_misses() -> None:
    response = client.post("/api/v1/chat", json=valid_payload(question="火星基地今天几点发射？", interests=[]))

    body = response.json()
    assert response.status_code == 200
    assert body["fallback"] is True
    assert "暂未查询到相关资料" in body["answer"]
    assert body["sources"] == []


def test_chat_hides_internal_error_details() -> None:
    class BrokenGuideService:
        def ask(
            self,
            question: str,
            interests: list[str] | None = None,
            session_id: str | None = None,
        ) -> None:
            raise RuntimeError("database password leaked in stack")

    app.dependency_overrides[get_guide_service] = lambda: BrokenGuideService()

    try:
        response = client.post("/api/v1/chat", json=valid_payload())
    finally:
        app.dependency_overrides.clear()

    body = response.json()
    assert response.status_code == 500
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert "database password" not in body["error"]["message"]
