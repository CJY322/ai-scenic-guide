import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from app.schemas.admin import (
    AdminAnalyticsReportResponse,
    AdminDashboardOverviewResponse,
    AdminHotQuestion,
    AdminSentimentMetric,
    AdminServiceSuggestion,
    AdminTopicMetric,
    AdminTrendPoint,
)
from app.schemas.chat import SourceItem

SentimentLabel = Literal["positive", "neutral", "concerned"]

TOPIC_KEYWORDS: dict[str, list[str]] = {
    "景点讲解": ["景点", "灵山大佛", "九龙灌浴", "梵宫", "五印坛城", "祥符禅寺", "大佛"],
    "路线规划": ["路线", "半日", "一日", "怎么走", "顺序", "老人", "孩子", "亲子"],
    "票务开放": ["门票", "票价", "预约", "优惠", "开放", "几点", "营业"],
    "交通停车": ["交通", "停车", "公交", "地铁", "怎么去", "自驾"],
    "服务设施": ["厕所", "卫生间", "游客中心", "观光车", "无障碍", "轮椅"],
    "安全文明": ["安全", "注意", "下雨", "防晒", "滑", "寺院", "文明"],
    "餐饮购物": ["美食", "吃饭", "餐厅", "素斋", "小吃", "购物"],
    "数字人体验": ["数字人", "语音", "播报", "口型", "视频", "导游"],
}

POSITIVE_KEYWORDS = ["喜欢", "满意", "好玩", "漂亮", "值得", "推荐", "感谢", "不错", "方便"]
CONCERNED_KEYWORDS = ["投诉", "不好", "不满意", "差", "贵", "排队", "迷路", "找不到", "危险", "摔", "累", "下雨"]


@dataclass(frozen=True)
class InteractionRecord:
    timestamp: datetime
    session_id: str | None
    request_id: str
    question: str
    answer: str
    emotion: str
    fallback: bool
    latency_ms: int
    topics: list[str]
    sentiment: SentimentLabel


class AnalyticsService:
    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or Path(__file__).resolve().parents[4]
        self.analytics_path = self.project_root / "data" / "analytics" / "interactions.jsonl"

    def record_interaction(
        self,
        *,
        session_id: str | None,
        request_id: str,
        question: str,
        answer: str,
        emotion: str,
        fallback: bool,
        latency_ms: int,
        sources: list[SourceItem],
    ) -> None:
        self.analytics_path.parent.mkdir(parents=True, exist_ok=True)
        topics = self._classify_topics(question, sources)
        payload = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "session_id": session_id,
            "request_id": request_id,
            "question": question,
            "answer": answer[:1000],
            "emotion": emotion,
            "fallback": fallback,
            "latency_ms": latency_ms,
            "sources": [source.model_dump(exclude_none=True) for source in sources],
            "topics": topics,
            "sentiment": self._classify_sentiment(question, emotion, fallback),
        }
        with self.analytics_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def build_report(self) -> AdminAnalyticsReportResponse:
        records = self._load_records()
        now = datetime.now()
        today = now.date()
        week_start = today - timedelta(days=6)
        today_records = [record for record in records if record.timestamp.date() == today]
        week_records = [record for record in records if week_start <= record.timestamp.date() <= today]
        active_records = week_records or records

        return AdminAnalyticsReportResponse(
            generated_at=now.isoformat(timespec="seconds"),
            total_interactions=len(records),
            today_interactions=len(today_records),
            week_interactions=len(week_records),
            unique_sessions_today=len({record.session_id for record in today_records if record.session_id}),
            avg_latency_ms=self._avg_latency(active_records),
            fallback_rate=self._fallback_rate(active_records),
            estimated_satisfaction_score=self._satisfaction_score(active_records),
            hot_questions=self._hot_questions(active_records),
            topic_metrics=self._topic_metrics(active_records),
            sentiment_metrics=self._sentiment_metrics(active_records),
            trend=self._trend(records, today),
            service_suggestions=self._service_suggestions(active_records),
        )

    def build_overview(self) -> AdminDashboardOverviewResponse:
        report = self.build_report()
        return AdminDashboardOverviewResponse(
            generated_at=report.generated_at,
            today_service_count=report.today_interactions,
            week_service_count=report.week_interactions,
            unique_sessions_today=report.unique_sessions_today,
            hot_questions=report.hot_questions[:5],
            satisfaction_trend=report.trend,
            topic_metrics=report.topic_metrics[:6],
        )

    def _load_records(self) -> list[InteractionRecord]:
        if not self.analytics_path.exists():
            return []

        records: list[InteractionRecord] = []
        for line in self.analytics_path.read_text(encoding="utf-8-sig").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
                records.append(
                    InteractionRecord(
                        timestamp=datetime.fromisoformat(str(item.get("timestamp"))),
                        session_id=str(item.get("session_id")) if item.get("session_id") else None,
                        request_id=str(item.get("request_id", "")),
                        question=str(item.get("question", "")),
                        answer=str(item.get("answer", "")),
                        emotion=str(item.get("emotion", "friendly")),
                        fallback=bool(item.get("fallback", False)),
                        latency_ms=int(item.get("latency_ms", 0)),
                        topics=[str(topic) for topic in item.get("topics", [])],
                        sentiment=self._normalize_sentiment(item.get("sentiment")),
                    )
                )
            except (ValueError, TypeError, json.JSONDecodeError):
                continue
        return records

    def _classify_topics(self, question: str, sources: list[SourceItem]) -> list[str]:
        haystack = question + " " + " ".join(
            f"{source.title} {source.section or ''}" for source in sources
        )
        topics = [
            topic for topic, keywords in TOPIC_KEYWORDS.items() if any(keyword in haystack for keyword in keywords)
        ]
        return topics or ["综合咨询"]

    def _classify_sentiment(self, question: str, emotion: str, fallback: bool) -> SentimentLabel:
        if fallback or any(keyword in question for keyword in CONCERNED_KEYWORDS) or emotion in {"concerned", "serious"}:
            return "concerned"
        if any(keyword in question for keyword in POSITIVE_KEYWORDS) or emotion == "happy":
            return "positive"
        return "neutral"

    def _hot_questions(self, records: list[InteractionRecord]) -> list[AdminHotQuestion]:
        counter = Counter(record.question.strip() for record in records if record.question.strip())
        return [AdminHotQuestion(question=question, count=count) for question, count in counter.most_common(8)]

    def _topic_metrics(self, records: list[InteractionRecord]) -> list[AdminTopicMetric]:
        counter: Counter[str] = Counter()
        for record in records:
            counter.update(record.topics or ["综合咨询"])
        total = sum(counter.values()) or 1
        return [
            AdminTopicMetric(topic=topic, count=count, ratio=round(count / total, 4))
            for topic, count in counter.most_common()
        ]

    def _sentiment_metrics(self, records: list[InteractionRecord]) -> list[AdminSentimentMetric]:
        counter = Counter(record.sentiment for record in records)
        total = len(records) or 1
        labels = ["positive", "neutral", "concerned"]
        return [
            AdminSentimentMetric(label=label, count=counter[label], ratio=round(counter[label] / total, 4))
            for label in labels
        ]

    def _trend(self, records: list[InteractionRecord], today: datetime.date) -> list[AdminTrendPoint]:
        by_date: dict[str, list[InteractionRecord]] = defaultdict(list)
        start = today - timedelta(days=6)
        for record in records:
            record_date = record.timestamp.date()
            if start <= record_date <= today:
                by_date[record_date.isoformat()].append(record)

        points: list[AdminTrendPoint] = []
        for offset in range(7):
            date_value = start + timedelta(days=offset)
            key = date_value.isoformat()
            day_records = by_date.get(key, [])
            sentiments = Counter(record.sentiment for record in day_records)
            points.append(
                AdminTrendPoint(
                    date=key,
                    service_count=len(day_records),
                    satisfaction_score=self._satisfaction_score(day_records),
                    positive_count=sentiments["positive"],
                    neutral_count=sentiments["neutral"],
                    concerned_count=sentiments["concerned"],
                )
            )
        return points

    def _service_suggestions(self, records: list[InteractionRecord]) -> list[AdminServiceSuggestion]:
        suggestions: list[AdminServiceSuggestion] = []
        topic_metrics = self._topic_metrics(records)
        fallback_rate = self._fallback_rate(records)
        concerned_ratio = next(
            (metric.ratio for metric in self._sentiment_metrics(records) if metric.label == "concerned"),
            0,
        )

        if topic_metrics:
            top_topic = topic_metrics[0]
            suggestions.append(
                AdminServiceSuggestion(
                    title=f"优先优化“{top_topic.topic}”相关讲解",
                    detail=f"近一周该主题占比 {top_topic.ratio:.0%}，建议补充更细的讲解词、路线提示和推荐问题。",
                    priority="high" if top_topic.ratio >= 0.35 else "medium",
                )
            )
        if fallback_rate >= 0.15:
            suggestions.append(
                AdminServiceSuggestion(
                    title="补充 Dify 知识库或本地 FAQ",
                    detail=f"未命中率约 {fallback_rate:.0%}，建议把高频未命中问题整理进知识库。",
                    priority="high",
                )
            )
        if concerned_ratio >= 0.25:
            suggestions.append(
                AdminServiceSuggestion(
                    title="关注游客疑虑和现场服务提示",
                    detail=f"疑虑类咨询约 {concerned_ratio:.0%}，可在游客中心、导览牌和数字人欢迎语中前置说明。",
                    priority="medium",
                )
            )
        if not suggestions:
            suggestions.append(
                AdminServiceSuggestion(
                    title="保持当前讲解质量",
                    detail="近期游客咨询平稳，可继续观察热门问题，并定期更新演出、票务和路线信息。",
                    priority="low",
                )
            )
        return suggestions[:5]

    @staticmethod
    def _avg_latency(records: list[InteractionRecord]) -> int:
        if not records:
            return 0
        return round(sum(record.latency_ms for record in records) / len(records))

    @staticmethod
    def _fallback_rate(records: list[InteractionRecord]) -> float:
        if not records:
            return 0
        return round(sum(1 for record in records if record.fallback) / len(records), 4)

    @staticmethod
    def _satisfaction_score(records: list[InteractionRecord]) -> float:
        if not records:
            return 0
        score_map = {"positive": 94, "neutral": 84, "concerned": 68}
        total = 0
        for record in records:
            total += score_map[record.sentiment]
            if record.fallback:
                total -= 12
        return round(max(0, min(100, total / len(records))), 1)

    @staticmethod
    def _normalize_sentiment(value: Any) -> SentimentLabel:
        if value in {"positive", "neutral", "concerned"}:
            return value
        return "neutral"
