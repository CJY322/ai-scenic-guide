import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

BROWSER_VIDEO_CACHE_VERSION = "h264-v1"


class AvatarGenerationUnavailableError(RuntimeError):
    """Raised when the configured avatar engine is unavailable."""


class AvatarGenerationError(RuntimeError):
    """Raised when avatar generation fails after configuration is valid."""


@dataclass(frozen=True)
class AvatarStatus:
    enabled: bool
    provider: str
    supports_video: bool
    message: str


@dataclass(frozen=True)
class AvatarVideo:
    provider: str
    video_url: str
    cached: bool


class SadTalkerAvatarService:
    def __init__(
        self,
        provider: str,
        generated_assets_path: Path,
        sadtalker_root: Path | None,
        sadtalker_python: str,
        sadtalker_source_image: Path | None,
        sadtalker_timeout_seconds: float,
        sadtalker_preprocess: str,
        sadtalker_expression_scale: float,
        sadtalker_still: bool,
        sadtalker_use_cpu: bool,
        tts_script_path: Path,
    ) -> None:
        self.provider = provider
        self.generated_assets_path = generated_assets_path
        self.sadtalker_root = sadtalker_root
        self.sadtalker_python = sadtalker_python
        self.sadtalker_source_image = sadtalker_source_image
        self.sadtalker_timeout_seconds = sadtalker_timeout_seconds
        self.sadtalker_preprocess = sadtalker_preprocess
        self.sadtalker_expression_scale = sadtalker_expression_scale
        self.sadtalker_still = sadtalker_still
        self.sadtalker_use_cpu = sadtalker_use_cpu
        self.tts_script_path = tts_script_path

    def status(self) -> AvatarStatus:
        if self.provider != "sadtalker":
            return AvatarStatus(
                enabled=False,
                provider=self.provider,
                supports_video=False,
                message="真实数字人未启用",
            )

        missing = self._missing_configuration()
        if missing:
            return AvatarStatus(
                enabled=False,
                provider="sadtalker",
                supports_video=True,
                message=f"SadTalker 配置不完整：{missing}",
            )

        return AvatarStatus(
            enabled=True,
            provider="sadtalker",
            supports_video=True,
            message="SadTalker 已配置",
        )

    def generate_video(self, text: str) -> AvatarVideo:
        missing = self._missing_configuration()
        if self.provider != "sadtalker" or missing:
            raise AvatarGenerationUnavailableError(missing or "真实数字人未启用")

        assert self.sadtalker_root is not None
        assert self.sadtalker_source_image is not None

        target_dir = self.generated_assets_path / "avatar"
        target_dir.mkdir(parents=True, exist_ok=True)

        cache_key = self._cache_key(text)
        target_video = target_dir / f"{cache_key}.mp4"
        if target_video.exists():
            return AvatarVideo(provider="sadtalker", video_url=f"/generated/avatar/{target_video.name}", cached=True)

        job_dir = target_dir / "jobs" / cache_key
        audio_path = job_dir / "speech.wav"
        result_dir = job_dir / "sadtalker-result"
        job_dir.mkdir(parents=True, exist_ok=True)
        result_dir.mkdir(parents=True, exist_ok=True)

        self._synthesize_audio(text, audio_path)
        generated_video = self._run_sadtalker(audio_path, result_dir)
        self._transcode_for_browser(generated_video, target_video)

        return AvatarVideo(provider="sadtalker", video_url=f"/generated/avatar/{target_video.name}", cached=False)

    def _missing_configuration(self) -> str | None:
        if self.provider != "sadtalker":
            return None
        if self.sadtalker_root is None:
            return "GUIDE_SADTALKER_ROOT 未设置"
        if not self.sadtalker_root.exists():
            return f"GUIDE_SADTALKER_ROOT 不存在：{self.sadtalker_root}"
        if not (self.sadtalker_root / "inference.py").exists():
            return f"SadTalker 目录缺少 inference.py：{self.sadtalker_root}"
        if self.sadtalker_source_image is None:
            return "GUIDE_SADTALKER_SOURCE_IMAGE 未设置"
        if not self.sadtalker_source_image.exists():
            return f"GUIDE_SADTALKER_SOURCE_IMAGE 不存在：{self.sadtalker_source_image}"
        if not self.tts_script_path.exists():
            return f"Windows TTS 脚本不存在：{self.tts_script_path}"
        return None

    def _cache_key(self, text: str) -> str:
        source_image = str(self.sadtalker_source_image.resolve()) if self.sadtalker_source_image else ""
        mapping_checkpoint = self._mapping_checkpoint_fingerprint()
        raw = (
            f"{source_image}\n{self.sadtalker_preprocess}\n{self.sadtalker_expression_scale}\n{self.sadtalker_still}\n"
            f"{self.sadtalker_use_cpu}\n{mapping_checkpoint}\n{BROWSER_VIDEO_CACHE_VERSION}\n{text}"
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:24]

    def _mapping_checkpoint_fingerprint(self) -> str:
        if self.sadtalker_root is None:
            return ""

        checkpoint_name = (
            "mapping_00109-model.pth.tar" if "full" in self.sadtalker_preprocess else "mapping_00229-model.pth.tar"
        )
        checkpoint_path = self.sadtalker_root / "checkpoints" / checkpoint_name
        if not checkpoint_path.exists():
            return checkpoint_name

        stat = checkpoint_path.stat()
        return f"{checkpoint_name}:{stat.st_size}:{stat.st_mtime_ns}"

    def _synthesize_audio(self, text: str, audio_path: Path) -> None:
        if audio_path.exists():
            audio_path.unlink()

        text_path = audio_path.with_suffix(".txt")
        text_path.write_text(text, encoding="utf-8")

        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self.tts_script_path),
            "-TextFile",
            str(text_path),
            "-OutputWav",
            str(audio_path),
        ]
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            check=False,
        )
        if completed.returncode != 0:
            raise AvatarGenerationError(f"Windows TTS 生成音频失败：{completed.stdout[-1200:]}")
        if not audio_path.exists():
            raise AvatarGenerationError("Windows TTS 未生成音频文件")
        if audio_path.stat().st_size < 1024:
            raise AvatarGenerationError("Windows TTS 生成了空音频，请检查系统语音组件")

    def _run_sadtalker(self, audio_path: Path, result_dir: Path) -> Path:
        assert self.sadtalker_root is not None
        assert self.sadtalker_source_image is not None

        command = [
            self.sadtalker_python,
            "inference.py",
            "--driven_audio",
            str(audio_path),
            "--source_image",
            str(self.sadtalker_source_image),
            "--result_dir",
            str(result_dir),
            "--preprocess",
            self.sadtalker_preprocess,
            "--expression_scale",
            str(self.sadtalker_expression_scale),
        ]
        if self.sadtalker_still:
            command.append("--still")
        if self.sadtalker_use_cpu:
            command.append("--cpu")

        try:
            completed = subprocess.run(
                command,
                cwd=self.sadtalker_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.sadtalker_timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AvatarGenerationError("SadTalker 生成超时，请确认是否使用 GPU 或调大超时时间") from exc

        if completed.returncode != 0:
            raise AvatarGenerationError(f"SadTalker 生成失败：{completed.stdout[-1600:]}")

        videos = sorted(result_dir.rglob("*.mp4"), key=lambda path: path.stat().st_mtime, reverse=True)
        if not videos:
            raise AvatarGenerationError("SadTalker 未输出 mp4 视频")
        return videos[0]

    def _transcode_for_browser(self, source_video: Path, target_video: Path) -> None:
        ffmpeg_path = self._ffmpeg_path()
        if ffmpeg_path is None:
            shutil.copyfile(source_video, target_video)
            return

        temp_video = target_video.with_name(f"{target_video.stem}.tmp{target_video.suffix}")
        if temp_video.exists():
            temp_video.unlink()

        command = [
            str(ffmpeg_path),
            "-y",
            "-i",
            str(source_video),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-movflags",
            "+faststart",
            "-c:a",
            "aac",
            "-b:a",
            "96k",
            str(temp_video),
        ]
        completed = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        if completed.returncode != 0:
            raise AvatarGenerationError(f"视频转码为浏览器兼容 H.264 失败：{completed.stdout[-1200:]}")
        if not temp_video.exists() or temp_video.stat().st_size < 1024:
            raise AvatarGenerationError("视频转码未输出有效 mp4 文件")

        temp_video.replace(target_video)

    def _ffmpeg_path(self) -> Path | None:
        conda_ffmpeg_path = Path(self.sadtalker_python).parent / "Library" / "bin" / "ffmpeg.exe"
        if conda_ffmpeg_path.exists():
            return conda_ffmpeg_path

        discovered = shutil.which("ffmpeg")
        if discovered:
            return Path(discovered)

        return None
