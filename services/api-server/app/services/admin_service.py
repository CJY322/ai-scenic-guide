import json
from datetime import datetime
from pathlib import Path

from app.core.config import Settings
from app.schemas.admin import (
    AdminAppSettingsResponse,
    AdminAppSettingsUpdateRequest,
    AdminAvatarProfile,
    AdminAvatarStatus,
    AdminContentStatus,
    AdminDifyStatus,
    AdminFaqEntry,
    AdminKnowledgeFile,
    AdminKnowledgeFileResponse,
    AdminSource,
    AdminStatusSection,
    AdminSystemStatusResponse,
)
from app.services.avatar_service import SadTalkerAvatarService


class AdminDataError(RuntimeError):
    """Raised when admin-managed local data cannot be loaded or saved."""


class AdminService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.project_root = Path(__file__).resolve().parents[4]
        self.api_root = Path(__file__).resolve().parents[2]
        self.env_path = self.api_root / ".env"
        self.knowledge_path = self.project_root / "data" / "knowledge" / "lingshan"
        self.avatar_profile_path = self.project_root / "data" / "admin" / "avatar_profile.json"
        self.recommended_questions_path = self.project_root / "data" / "admin" / "recommended_questions.json"

    def get_status(self) -> AdminSystemStatusResponse:
        faq_entries = self.list_faq_entries()
        recommended_questions = self.list_recommended_questions()
        knowledge_files = self.list_knowledge_files()
        avatar_status = self._avatar_status()

        return AdminSystemStatusResponse(
            api=AdminStatusSection(
                status="ok",
                message=f"{self.settings.service_name} {self.settings.version}",
            ),
            dify=AdminDifyStatus(
                enabled=self.settings.answer_provider == "dify",
                api_base_url=self.settings.dify_api_base_url,
                api_key_configured=bool(self.settings.dify_api_key),
            ),
            avatar=avatar_status,
            content=AdminContentStatus(
                knowledge_file_count=len(knowledge_files),
                faq_entry_count=len(faq_entries),
                recommended_question_count=len(recommended_questions),
                knowledge_path=str(self.knowledge_path),
                faq_path=str(self.settings.mock_data_path),
                recommended_questions_path=str(self.recommended_questions_path),
            ),
        )

    def get_app_settings(self) -> AdminAppSettingsResponse:
        return AdminAppSettingsResponse(
            answer_provider=self.settings.answer_provider,
            dify_api_base_url=self.settings.dify_api_base_url,
            dify_api_key_masked=self._mask_secret(self.settings.dify_api_key),
            dify_timeout_seconds=self.settings.dify_timeout_seconds,
            avatar_provider=self.settings.avatar_provider,
            avatar_assets_path=str(self.settings.avatar_assets_path),
            generated_assets_path=str(self.settings.generated_assets_path),
            sadtalker_root=str(self.settings.sadtalker_root) if self.settings.sadtalker_root else None,
            sadtalker_python=self.settings.sadtalker_python,
            sadtalker_source_image=str(self.settings.sadtalker_source_image)
            if self.settings.sadtalker_source_image
            else None,
            sadtalker_timeout_seconds=self.settings.sadtalker_timeout_seconds,
            sadtalker_preprocess=self.settings.sadtalker_preprocess,
            sadtalker_expression_scale=self.settings.sadtalker_expression_scale,
            sadtalker_still=self.settings.sadtalker_still,
            sadtalker_use_cpu=self.settings.sadtalker_use_cpu,
        )

    def update_app_settings(self, payload: AdminAppSettingsUpdateRequest) -> None:
        updates: dict[str, str] = {}
        if payload.answer_provider is not None:
            updates["GUIDE_ANSWER_PROVIDER"] = payload.answer_provider
        if payload.dify_api_base_url is not None:
            updates["GUIDE_DIFY_API_BASE_URL"] = payload.dify_api_base_url.strip()
        if payload.dify_api_key is not None and payload.dify_api_key.strip():
            updates["GUIDE_DIFY_API_KEY"] = payload.dify_api_key.strip()
        if payload.dify_timeout_seconds is not None:
            updates["GUIDE_DIFY_TIMEOUT_SECONDS"] = str(payload.dify_timeout_seconds)
        if payload.avatar_provider is not None:
            updates["GUIDE_AVATAR_PROVIDER"] = payload.avatar_provider
        if payload.avatar_assets_path is not None:
            updates["GUIDE_AVATAR_ASSETS_PATH"] = payload.avatar_assets_path.strip()
        if payload.generated_assets_path is not None:
            updates["GUIDE_GENERATED_ASSETS_PATH"] = payload.generated_assets_path.strip()
        if payload.sadtalker_root is not None:
            updates["GUIDE_SADTALKER_ROOT"] = payload.sadtalker_root.strip()
        if payload.sadtalker_python is not None:
            updates["GUIDE_SADTALKER_PYTHON"] = payload.sadtalker_python.strip()
        if payload.sadtalker_source_image is not None:
            updates["GUIDE_SADTALKER_SOURCE_IMAGE"] = payload.sadtalker_source_image.strip()
        if payload.sadtalker_timeout_seconds is not None:
            updates["GUIDE_SADTALKER_TIMEOUT_SECONDS"] = str(payload.sadtalker_timeout_seconds)
        if payload.sadtalker_preprocess is not None:
            updates["GUIDE_SADTALKER_PREPROCESS"] = payload.sadtalker_preprocess.strip()
        if payload.sadtalker_expression_scale is not None:
            updates["GUIDE_SADTALKER_EXPRESSION_SCALE"] = str(payload.sadtalker_expression_scale)
        if payload.sadtalker_still is not None:
            updates["GUIDE_SADTALKER_STILL"] = "true" if payload.sadtalker_still else "false"
        if payload.sadtalker_use_cpu is not None:
            updates["GUIDE_SADTALKER_USE_CPU"] = "true" if payload.sadtalker_use_cpu else "false"

        if not updates:
            return

        self._write_env_updates(updates)

    def get_avatar_profile(self) -> AdminAvatarProfile:
        if not self.avatar_profile_path.exists():
            return AdminAvatarProfile()

        try:
            raw_profile = json.loads(self.avatar_profile_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise AdminDataError("数字人形象档案读取失败") from exc
        if not isinstance(raw_profile, dict):
            raise AdminDataError("数字人形象档案格式应为对象")
        return AdminAvatarProfile(**raw_profile)

    def save_avatar_profile(self, profile: AdminAvatarProfile) -> AdminAvatarProfile:
        self.avatar_profile_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.avatar_profile_path.write_text(
                json.dumps(profile.model_dump(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise AdminDataError("数字人形象档案保存失败") from exc
        return self.get_avatar_profile()

    def list_knowledge_files(self) -> list[AdminKnowledgeFile]:
        if not self.knowledge_path.exists():
            return []

        files: list[AdminKnowledgeFile] = []
        for path in sorted(self.knowledge_path.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
                continue
            files.append(
                AdminKnowledgeFile(
                    name=path.name,
                    path=path.relative_to(self.knowledge_path).as_posix(),
                    size_bytes=path.stat().st_size,
                    updated_at=self._format_mtime(path),
                )
            )
        return files

    def read_knowledge_file(self, relative_path: str) -> AdminKnowledgeFileResponse:
        path = self._resolve_knowledge_file(relative_path)
        try:
            content = path.read_text(encoding="utf-8-sig")
        except OSError as exc:
            raise AdminDataError("知识库文件读取失败") from exc

        return AdminKnowledgeFileResponse(
            name=path.name,
            path=path.relative_to(self.knowledge_path).as_posix(),
            content=content,
            updated_at=self._format_mtime(path),
        )

    def save_knowledge_file(self, relative_path: str, content: str) -> AdminKnowledgeFileResponse:
        path = self._resolve_knowledge_file(relative_path, allow_missing=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise AdminDataError("知识库文件保存失败") from exc
        return self.read_knowledge_file(path.relative_to(self.knowledge_path).as_posix())

    def list_faq_entries(self) -> list[AdminFaqEntry]:
        try:
            raw_entries = json.loads(self.settings.mock_data_path.read_text(encoding="utf-8-sig"))
        except OSError as exc:
            raise AdminDataError("FAQ 文件读取失败") from exc
        except json.JSONDecodeError as exc:
            raise AdminDataError("FAQ 文件不是有效 JSON") from exc

        if not isinstance(raw_entries, list):
            raise AdminDataError("FAQ 文件格式应为数组")

        entries: list[AdminFaqEntry] = []
        for item in raw_entries:
            if not isinstance(item, dict):
                continue
            source = item.get("source") if isinstance(item.get("source"), dict) else {}
            entries.append(
                AdminFaqEntry(
                    keywords=[str(keyword) for keyword in item.get("keywords", [])],
                    answer=str(item.get("answer", "")),
                    source=AdminSource(
                        title=str(source.get("title", "管理后台")),
                        section=str(source.get("section")) if source.get("section") else None,
                    ),
                    emotion=item.get("emotion", "friendly"),
                )
            )
        return entries

    def save_faq_entries(self, entries: list[AdminFaqEntry]) -> None:
        self.settings.mock_data_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [entry.model_dump(exclude_none=True) for entry in entries]
        try:
            self.settings.mock_data_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise AdminDataError("FAQ 文件保存失败") from exc

    def list_recommended_questions(self) -> list[str]:
        default_questions = [
            "灵山胜境有哪些必看景点？",
            "九龙灌浴和灵山大佛怎么讲？",
            "带老人孩子游览怎么安排？",
            "半日游路线怎么走？",
        ]
        if not self.recommended_questions_path.exists():
            return default_questions

        try:
            raw_questions = json.loads(self.recommended_questions_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return default_questions
        if not isinstance(raw_questions, list):
            return default_questions

        questions = [str(question).strip() for question in raw_questions if str(question).strip()]
        return questions[:12] or default_questions

    def save_recommended_questions(self, questions: list[str]) -> None:
        normalized_questions = []
        for question in questions:
            normalized_question = question.strip()
            if normalized_question and normalized_question not in normalized_questions:
                normalized_questions.append(normalized_question)

        self.recommended_questions_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.recommended_questions_path.write_text(
                json.dumps(normalized_questions[:12], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            raise AdminDataError("推荐问题保存失败") from exc

    def _resolve_knowledge_file(self, relative_path: str, allow_missing: bool = False) -> Path:
        if not relative_path or Path(relative_path).is_absolute():
            raise AdminDataError("知识库路径无效")

        candidate = (self.knowledge_path / relative_path).resolve()
        knowledge_root = self.knowledge_path.resolve()
        if candidate != knowledge_root and knowledge_root not in candidate.parents:
            raise AdminDataError("知识库路径越界")
        if candidate.suffix.lower() not in {".md", ".txt"}:
            raise AdminDataError("仅支持 Markdown 或文本文件")
        if not allow_missing and not candidate.exists():
            raise AdminDataError("知识库文件不存在")
        return candidate

    def _avatar_status(self) -> AdminAvatarStatus:
        service = SadTalkerAvatarService(
            provider=self.settings.avatar_provider,
            generated_assets_path=self.settings.generated_assets_path,
            sadtalker_root=self.settings.sadtalker_root,
            sadtalker_python=self.settings.sadtalker_python,
            sadtalker_source_image=self.settings.sadtalker_source_image,
            sadtalker_timeout_seconds=self.settings.sadtalker_timeout_seconds,
            sadtalker_preprocess=self.settings.sadtalker_preprocess,
            sadtalker_expression_scale=self.settings.sadtalker_expression_scale,
            sadtalker_still=self.settings.sadtalker_still,
            sadtalker_use_cpu=self.settings.sadtalker_use_cpu,
            tts_script_path=self.settings.sadtalker_tts_script_path,
        )
        status = service.status()
        generated_video_count = 0
        avatar_output_path = self.settings.generated_assets_path / "avatar"
        if avatar_output_path.exists():
            generated_video_count = len(list(avatar_output_path.glob("*.mp4")))

        return AdminAvatarStatus(
            provider=status.provider,
            enabled=status.enabled,
            supports_video=status.supports_video,
            source_image_exists=bool(
                self.settings.sadtalker_source_image and self.settings.sadtalker_source_image.exists()
            ),
            generated_video_count=generated_video_count,
            message=status.message,
        )

    def _write_env_updates(self, updates: dict[str, str]) -> None:
        lines = self._read_env_lines()
        existing_keys = {line.split("=", 1)[0].strip() for line in lines if "=" in line and not line.lstrip().startswith("#")}
        new_lines = []
        for line in lines:
            if "=" not in line or line.lstrip().startswith("#"):
                new_lines.append(line)
                continue
            key = line.split("=", 1)[0].strip()
            if key in updates:
                new_lines.append(f"{key}={self._format_env_value(updates[key])}")
            else:
                new_lines.append(line)

        missing_updates = [key for key in updates if key not in existing_keys]
        if missing_updates and new_lines and new_lines[-1].strip():
            new_lines.append("")
        for key in missing_updates:
            new_lines.append(f"{key}={self._format_env_value(updates[key])}")

        self.env_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.env_path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
        except OSError as exc:
            raise AdminDataError(".env 保存失败") from exc

    def _read_env_lines(self) -> list[str]:
        if self.env_path.exists():
            return self.env_path.read_text(encoding="utf-8-sig").splitlines()
        example_path = self.api_root / ".env.example"
        if example_path.exists():
            return example_path.read_text(encoding="utf-8-sig").splitlines()
        return []

    @staticmethod
    def _format_env_value(value: str) -> str:
        if value == "":
            return ""
        if any(char.isspace() for char in value) or value.startswith(("#", '"', "'")):
            return json.dumps(value, ensure_ascii=False)
        return value

    @staticmethod
    def _format_mtime(path: Path) -> str:
        return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")

    @staticmethod
    def _mask_secret(value: str | None) -> str | None:
        if not value:
            return None
        if len(value) <= 8:
            return "********"
        return f"{value[:4]}...{value[-4:]}"
