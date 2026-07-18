from __future__ import annotations

from dataclasses import dataclass

from app.schemas.chat import RecommendationInterestOption


@dataclass(frozen=True)
class RecommendationProfile:
    id: str
    label: str
    aliases: tuple[str, ...]
    route_title: str
    route_summary: str
    duration: str
    stops: tuple[str, ...]
    focus_points: tuple[str, ...]
    tips: tuple[str, ...]
    suggested_questions: tuple[str, ...]


@dataclass(frozen=True)
class PersonalizedRecommendation:
    matched_interests: list[str]
    route_title: str
    route_summary: str
    duration: str
    stops: list[str]
    focus_points: list[str]
    tips: list[str]
    suggested_questions: list[str]
    interest_options: list[RecommendationInterestOption]


class RecommendationService:
    def __init__(self) -> None:
        self._profiles = _PROFILES

    def list_interest_options(self) -> list[RecommendationInterestOption]:
        return [
            RecommendationInterestOption(
                id=profile.id,
                label=profile.label,
                description=profile.focus_points[0],
            )
            for profile in self._profiles
        ]

    def recommend(self, interests: list[str] | None = None) -> PersonalizedRecommendation:
        normalized_interests = self._normalize_interests(interests or [])
        primary = self._select_primary_profile(normalized_interests)
        matched_interests = self._match_labels(normalized_interests, primary)
        secondary_profiles = [
            profile for profile in self._profiles if profile.id != primary.id and self._score_profile(profile, normalized_interests) > 0
        ][:2]

        focus_points = list(primary.focus_points)
        tips = list(primary.tips)
        suggested_questions = list(primary.suggested_questions)
        for profile in secondary_profiles:
            focus_points.extend(profile.focus_points[:1])
            tips.extend(profile.tips[:1])
            suggested_questions.extend(profile.suggested_questions[:1])

        return PersonalizedRecommendation(
            matched_interests=matched_interests,
            route_title=primary.route_title,
            route_summary=primary.route_summary,
            duration=primary.duration,
            stops=list(primary.stops),
            focus_points=self._dedupe(focus_points)[:6],
            tips=self._dedupe(tips)[:4],
            suggested_questions=self._dedupe(suggested_questions)[:4],
            interest_options=self.list_interest_options(),
        )

    def _select_primary_profile(self, normalized_interests: list[str]) -> RecommendationProfile:
        ranked_profiles = [
            (self._score_profile(profile, normalized_interests), -index, profile)
            for index, profile in enumerate(self._profiles)
        ]
        score, _, profile = max(ranked_profiles, key=lambda item: (item[0], item[1]))
        if score <= 0:
            return _DEFAULT_PROFILE
        return profile

    @staticmethod
    def _score_profile(profile: RecommendationProfile, normalized_interests: list[str]) -> int:
        score = 0
        aliases = tuple(alias.lower() for alias in profile.aliases + (profile.label,))
        for interest in normalized_interests:
            for alias in aliases:
                if alias and (alias in interest or interest in alias):
                    score += 10 + len(alias)
        return score

    def _match_labels(self, normalized_interests: list[str], primary: RecommendationProfile) -> list[str]:
        labels = [
            profile.label
            for profile in self._profiles
            if self._score_profile(profile, normalized_interests) > 0
        ]
        if not labels:
            labels = [primary.label]
        return self._dedupe(labels)[:5]

    @staticmethod
    def _normalize_interests(interests: list[str]) -> list[str]:
        normalized = []
        for interest in interests:
            item = interest.strip().lower()
            if item and item not in normalized:
                normalized.append(item)
        return normalized[:5]

    @staticmethod
    def _dedupe(items: list[str] | tuple[str, ...]) -> list[str]:
        result = []
        for item in items:
            if item and item not in result:
                result.append(item)
        return result


_HISTORY_PROFILE = RecommendationProfile(
    id="history",
    label="历史文化",
    aliases=("历史", "文化", "佛教文化", "古建", "故事", "建筑艺术", "文史", "研学"),
    route_title="历史文化深度路线",
    route_summary="从“小灵山”缘起讲到祥符禅寺、灵山大佛、梵宫与五印坛城，适合愿意听完整文化脉络的游客。",
    duration="约 6 小时",
    stops=(
        "南门",
        "灵山大照壁",
        "祥符禅寺",
        "灵山大佛",
        "灵山梵宫",
        "五印坛城",
        "三圣殿",
    ),
    focus_points=(
        "赵朴初题字与“小灵山”文化序章",
        "玄奘法师、小灵山缘起与祥符禅寺古刹故事",
        "灵山大佛 88 米造像、216 级登云道与佛手手印寓意",
        "梵宫的佛教艺术、木雕、琉璃与世界佛教论坛背景",
        "五印坛城的藏传佛教建筑和曼陀罗象征",
    ),
    tips=(
        "这条线讲解密度高，建议上午入园并预留梵宫参观时间。",
        "进入寺院和殿堂时保持安静，拍照以现场提示为准。",
        "登临大佛台阶较多，老人和儿童需量力而行。",
    ),
    suggested_questions=(
        "按历史文化路线给我讲灵山胜境",
        "祥符禅寺和小灵山有什么关系？",
        "灵山大佛的手印和台阶有什么寓意？",
        "梵宫为什么被称为佛教艺术殿堂？",
    ),
)

_NATURE_PROFILE = RecommendationProfile(
    id="nature",
    label="自然风光",
    aliases=("自然", "风光", "山水", "太湖", "观景", "散步", "轻松", "慢游"),
    route_title="山水观景全景路线",
    route_summary="减少高密度讲解，把菩提大道、太湖视野、曼飞龙塔和灵山精舍串成一条更舒展的观景路线。",
    duration="约 5 小时",
    stops=("南门", "佛足坛", "九龙灌浴", "菩提大道", "灵山大佛平台", "曼飞龙塔", "灵山精舍", "梵宫广场"),
    focus_points=(
        "菩提大道两侧树木与从喧闹走向清净的空间节奏",
        "灵山大佛平台俯瞰太湖、马山半岛与景区轴线",
        "曼飞龙塔的南传佛教建筑和园林景观",
        "灵山精舍的禅意园林、素斋与安静休憩体验",
    ),
    tips=(
        "适合想边走边看、拍照和轻松散步的游客。",
        "夏季注意防晒和补水，雨天留意广场与台阶湿滑。",
        "大佛平台视野好，但登高需根据体力调整。",
    ),
    suggested_questions=(
        "我喜欢自然风光，灵山胜境怎么走？",
        "灵山哪里适合看太湖和拍照？",
        "想走得轻松一点，有什么路线？",
        "灵山精舍适合安排在什么时候？",
    ),
)

_FAMILY_PROFILE = RecommendationProfile(
    id="family",
    label="亲子家庭",
    aliases=("亲子", "家庭", "老人", "孩子", "儿童", "带娃", "轻松游", "无障碍"),
    route_title="亲子家庭轻松路线",
    route_summary="以故事化景点和室内体验为主，控制步行强度，适合带老人、儿童或第一次到访的家庭。",
    duration="约 4 小时",
    stops=("南门", "九龙灌浴", "佛手广场", "百子戏弥勒", "灵山梵宫", "五印坛城", "出口"),
    focus_points=(
        "九龙灌浴用“花开见佛、九龙吐水”的故事方式讲解",
        "百子戏弥勒引导孩子观察不同孩童姿态，理解欢喜与包容",
        "梵宫重点看颜色、穹顶、造型和舞台，不堆叠术语",
        "五印坛城可用转经筒、唐卡和藏式建筑做直观介绍",
    ),
    tips=(
        "建议先核对演出时间，表演前提前到场。",
        "老人和儿童同行时，必要时使用观光车并减少折返。",
        "午后可把梵宫作为室内休息与参观点。",
    ),
    suggested_questions=(
        "带老人孩子游灵山怎么安排？",
        "九龙灌浴怎么讲给孩子听？",
        "亲子游哪些点不要错过？",
        "老人游灵山哪些地方需要少走路？",
    ),
)

_PHOTO_PROFILE = RecommendationProfile(
    id="photo",
    label="摄影打卡",
    aliases=("摄影", "拍照", "打卡", "出片", "观景台", "照片", "拍摄"),
    route_title="摄影打卡取景路线",
    route_summary="围绕入口地标、动态景观、太湖视野、梵宫外观和坛城建筑组织路线，方便拍出代表性画面。",
    duration="约 4-5 小时",
    stops=("灵山大照壁", "九龙灌浴广场", "灵山大佛平台", "梵宫广场", "五印坛城", "曼飞龙塔"),
    focus_points=(
        "大照壁适合作为“灵山胜境”入园第一张照片",
        "九龙灌浴适合拍动态水景和莲花开启瞬间",
        "大佛平台适合拍太湖、景区轴线和大佛近景",
        "梵宫外观、五印坛城和曼飞龙塔适合拍建筑对比",
    ),
    tips=(
        "动态景观建议提前到场占位，避开正中拥挤通道。",
        "殿堂内部拍摄以现场提示为准，不确定时先询问工作人员。",
        "夕阳时分大佛与太湖同框更有层次。",
    ),
    suggested_questions=(
        "灵山胜境有哪些适合拍照的点？",
        "我想拍灵山大佛和太湖，怎么安排？",
        "九龙灌浴拍照要提前多久到？",
        "梵宫和五印坛城哪里更适合打卡？",
    ),
)

_DEFAULT_PROFILE = RecommendationProfile(
    id="first-time",
    label="首次到访",
    aliases=("第一次", "首次", "经典", "重点", "半日", "一日", "必看", "默认"),
    route_title="首次到访重点路线",
    route_summary="覆盖入口标志、动态演出、千年古刹、核心地标和佛教艺术，适合时间有限但想看代表性内容的游客。",
    duration="约 3-4 小时",
    stops=("南门", "灵山大照壁", "五明桥", "九龙灌浴", "祥符禅寺", "灵山大佛", "灵山梵宫", "出口"),
    focus_points=(
        "从大照壁和五明桥建立景区第一印象",
        "优先衔接九龙灌浴和梵宫演出时间",
        "祥符禅寺补足历史文化，大佛作为核心地标",
        "梵宫作为艺术殿堂和室内参观点收尾",
    ),
    tips=(
        "入园后先确认九龙灌浴和梵宫演出时间，再微调顺序。",
        "如果只剩 2 小时，优先看九龙灌浴、灵山大佛和梵宫外观。",
        "节假日建议把排队和步行时间预留得更宽一些。",
    ),
    suggested_questions=(
        "第一次来灵山胜境怎么走？",
        "半日游路线怎么安排？",
        "灵山胜境必看景点有哪些？",
        "九龙灌浴和梵宫演出怎么衔接？",
    ),
)

_PROFILES = (_HISTORY_PROFILE, _NATURE_PROFILE, _FAMILY_PROFILE, _PHOTO_PROFILE, _DEFAULT_PROFILE)
