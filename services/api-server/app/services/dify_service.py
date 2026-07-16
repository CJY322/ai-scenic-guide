from __future__ import annotations

import logging
from typing import Any

import httpx

from app.schemas.chat import SourceItem
from app.services.guide_service import GuideAnswer, GuideServiceUnavailableError

logger = logging.getLogger(__name__)


class DifyGuideService:
    def __init__(self, api_base_url: str, api_key: str | None, timeout_seconds: float = 30.0) -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self._conversation_by_session: dict[str, str] = {}

    def ask(
        self,
        question: str,
        interests: list[str] | None = None,
        session_id: str | None = None,
    ) -> GuideAnswer:
        if not self.api_key:
            raise GuideServiceUnavailableError("Dify API key is not configured")

        user = session_id or "web-anonymous"
        payload: dict[str, Any] = {
            "inputs": {
                "scenic_area": "黄山风景区",
                "interests": interests or [],
            },
            "query": question,
            "response_mode": "blocking",
            "user": user,
        }

        conversation_id = self._conversation_by_session.get(user)
        if conversation_id:
            payload["conversation_id"] = conversation_id

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(
                    f"{self.api_base_url}/chat-messages",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.exception("dify chat request failed")
            raise GuideServiceUnavailableError("Dify chat service is unavailable") from exc

        new_conversation_id = data.get("conversation_id")
        if isinstance(new_conversation_id, str) and new_conversation_id:
            self._conversation_by_session[user] = new_conversation_id

        answer = str(data.get("answer") or "").strip()
        if not answer:
            return GuideAnswer(
                answer="暂未从黄山知识库检索到可用答案，请换一种问法或以黄山风景区官方信息为准。",
                sources=[],
                emotion="friendly",
                fallback=True,
            )

        return GuideAnswer(
            answer=answer,
            sources=self._extract_sources(data),
            emotion="friendly",
            fallback=False,
        )

    @staticmethod
    def _extract_sources(data: dict[str, Any]) -> list[SourceItem]:
        metadata = data.get("metadata")
        if not isinstance(metadata, dict):
            return []

        resources = metadata.get("retriever_resources")
        if not isinstance(resources, list):
            return []

        sources: list[SourceItem] = []
        seen: set[tuple[str, str | None]] = set()
        for resource in resources:
            if not isinstance(resource, dict):
                continue

            title = (
                resource.get("document_name")
                or resource.get("dataset_name")
                or resource.get("source")
                or "黄山知识库"
            )
            section = resource.get("segment_position") or resource.get("score") or resource.get("dataset_name")
            item = (str(title), str(section) if section is not None else None)
            if item in seen:
                continue
            seen.add(item)
            sources.append(SourceItem(title=item[0][:100], section=item[1][:100] if item[1] else None))
            if len(sources) >= 5:
                break

        return sources
