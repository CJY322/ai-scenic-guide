import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from app.schemas.chat import Emotion, SourceItem

_ALLOWED_EMOTIONS: set[str] = {"neutral", "friendly", "happy", "concerned", "serious"}


class GuideServiceUnavailableError(RuntimeError):
    """Raised when the guide data source cannot be loaded."""


@dataclass(frozen=True)
class GuideAnswer:
    answer: str
    sources: list[SourceItem]
    emotion: Emotion
    fallback: bool


@dataclass(frozen=True)
class FaqEntry:
    keywords: list[str]
    answer: str
    source: SourceItem
    emotion: Emotion


class GuideService:
    def __init__(self, data_path: Path) -> None:
        self.data_path = data_path
        self._entries: list[FaqEntry] | None = None

    def ask(self, question: str, interests: list[str] | None = None) -> GuideAnswer:
        entries = self._load_entries()
        normalized_question = question.lower()
        normalized_interests = " ".join(interests or []).lower()

        ranked_matches: list[tuple[int, FaqEntry]] = []
        for entry in entries:
            score = self._score_entry(entry, normalized_question, normalized_interests)
            if score > 0:
                ranked_matches.append((score, entry))

        if ranked_matches:
            _, best_entry = max(ranked_matches, key=lambda item: item[0])
            return GuideAnswer(
                answer=best_entry.answer,
                sources=[best_entry.source],
                emotion=best_entry.emotion,
                fallback=False,
            )

        return GuideAnswer(
            answer=(
                "暂未查询到相关资料。当前为第一阶段模拟回答，"
                "建议以景区官方公告、现场导览牌和工作人员说明为准。"
            ),
            sources=[],
            emotion="friendly",
            fallback=True,
        )

    def _load_entries(self) -> list[FaqEntry]:
        if self._entries is not None:
            return self._entries

        try:
            raw_entries = json.loads(self.data_path.read_text(encoding="utf-8-sig"))
        except OSError as exc:
            raise GuideServiceUnavailableError("Mock guide data is unavailable") from exc
        except json.JSONDecodeError as exc:
            raise GuideServiceUnavailableError("Mock guide data is invalid") from exc

        if not isinstance(raw_entries, list):
            raise GuideServiceUnavailableError("Mock guide data must be a list")

        self._entries = [self._parse_entry(item) for item in raw_entries if isinstance(item, dict)]
        return self._entries

    @staticmethod
    def _parse_entry(item: dict) -> FaqEntry:
        source = item.get("source") or {}
        emotion = str(item.get("emotion", "friendly"))
        if emotion not in _ALLOWED_EMOTIONS:
            emotion = "friendly"

        return FaqEntry(
            keywords=[str(keyword).lower() for keyword in item.get("keywords", [])],
            answer=str(item.get("answer", "")),
            source=SourceItem(
                title=str(source.get("title", "模拟数据")),
                section=str(source.get("section")) if source.get("section") else None,
            ),
            emotion=cast(Emotion, emotion),
        )

    @staticmethod
    def _score_entry(entry: FaqEntry, question: str, interests: str) -> int:
        score = 0
        for keyword in entry.keywords:
            if keyword and keyword in question:
                score += 10 + len(keyword)
            if keyword and keyword in interests:
                score += 2
        return score
