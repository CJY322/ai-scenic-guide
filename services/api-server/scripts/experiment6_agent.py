"""Single-agent tool loop for a Lingshan visit plan.

Run from services/api-server:
    python scripts/experiment6_agent.py --start-time 09:00

The normal run calls the configured Dify direct-model app. No arbitrary model
function name, shell command, or path is ever executed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import monotonic, sleep
from typing import Any, Callable, Literal, Protocol
from uuid import uuid4

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.config import Settings


PROJECT_ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE_ROOT = PROJECT_ROOT / "data" / "knowledge" / "lingshan"
OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "outputs" / "experiment6"
TIMEZONE = timezone(timedelta(hours=8))


class ToolFailure(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class StrictArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class RouteArgs(StrictArgs):
    route_type: Literal["half_day", "family"]


class NoticeArgs(StrictArgs):
    kind: Literal["performance", "accessibility"]


class EndTimeArgs(StrictArgs):
    start_time: str
    duration_minutes: int = Field(ge=60, le=480)

    @field_validator("start_time")
    @classmethod
    def valid_time(cls, value: str) -> str:
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
            raise ValueError("start_time must use HH:MM (24-hour clock)")
        return value


class SaveArgs(StrictArgs):
    filename: str = Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,39}\.txt$")
    content: str = Field(min_length=10, max_length=2000)

    @field_validator("filename")
    @classmethod
    def valid_filename(cls, value: str) -> str:
        if value.rsplit(".", 1)[0].upper() in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
            raise ValueError("reserved device filename")
        return value


TOOL_SCHEMAS: dict[str, type[StrictArgs]] = {
    "get_route": RouteArgs,
    "get_visit_notice": NoticeArgs,
    "estimate_end_time": EndTimeArgs,
    "save_plan": SaveArgs,
}

TOOL_DESCRIPTIONS = {
    "get_route": "Read a route from 03_routes.md. args: {route_type: half_day|family}.",
    "get_visit_notice": "Read a notice from 04_service_tips.md. args: {kind: performance|accessibility}.",
    "estimate_end_time": "Calculate a clock time. args: {start_time: HH:MM, duration_minutes: integer 60..480}.",
    "save_plan": "Write a new plan text file after human approval. args: {filename: safe .txt name, content: 10..2000 chars}.",
}


def _heading_section(path: Path, title: str) -> str:
    # The path is fixed by program code. The model cannot provide it.
    data = path.read_text(encoding="utf-8")
    match = re.search(rf"^## {re.escape(title)}[^\n]*\n(.*?)(?=^## |\Z)", data, re.M | re.S)
    if not match:
        raise ToolFailure("SOURCE_MISSING", f"section {title} was not found")
    return match.group(0).strip()


class ToolRegistry:
    """Allowlisted, schema-checked tool implementations."""

    def __init__(self, output_root: Path = OUTPUT_ROOT) -> None:
        self.output_root = output_root.resolve()

    def get_route(self, args: RouteArgs) -> dict[str, Any]:
        title = "半日游推荐" if args.route_type == "half_day" else "亲子家庭路线"
        section = _heading_section(KNOWLEDGE_ROOT / "03_routes.md", title)
        route_match = re.search(r"^(.+ -> .+)$", section, re.M)
        if not route_match:
            raise ToolFailure("SOURCE_FORMAT", "route line was not found")
        stops = [stop.strip() for stop in route_match.group(1).split("->")]
        return {
            "source": "03_routes.md", "title": section.splitlines()[0].lstrip("# "),
            "stops": stops, "duration_minutes": 210 if args.route_type == "half_day" else 240,
            "duration_note": "半日游资料为3—4小时，计算取中值3.5小时" if args.route_type == "half_day" else "亲子路线资料为4小时",
        }

    def get_visit_notice(self, args: NoticeArgs) -> dict[str, str]:
        title = "演出与开放信息" if args.kind == "performance" else "安全与设备部署提醒"
        section = _heading_section(KNOWLEDGE_ROOT / "04_service_tips.md", title)
        if args.kind == "accessibility":
            section = section.split("设备侧部署：", 1)[0].strip()
        return {"source": "04_service_tips.md", "kind": args.kind, "text": section}

    def estimate_end_time(self, args: EndTimeArgs) -> dict[str, Any]:
        start = datetime.strptime(args.start_time, "%H:%M")
        end = start + timedelta(minutes=args.duration_minutes)
        return {
            "start_time": args.start_time,
            "duration_minutes": args.duration_minutes,
            "end_time": end.strftime("%H:%M"),
            "next_day": end.date() != start.date(),
            "kind": "estimate_not_live_schedule",
        }

    def save_plan(self, args: SaveArgs) -> dict[str, str]:
        plans = self.output_root / "plans"
        plans.mkdir(parents=True, exist_ok=True)
        destination = (plans / args.filename).resolve()
        if destination.parent != plans.resolve():
            raise ToolFailure("ACCESS_DENIED", "filename leaves the plan directory")
        try:
            with destination.open("x", encoding="utf-8") as handle:
                handle.write(args.content)
        except FileExistsError as exc:
            raise ToolFailure("ALREADY_EXISTS", "plan already exists; it was not overwritten") from exc
        return {"saved_path": str(destination), "bytes": str(destination.stat().st_size)}

    def validate(self, name: str, arguments: Any) -> StrictArgs:
        schema = TOOL_SCHEMAS.get(name)
        if schema is None:
            raise ToolFailure("TOOL_NOT_ALLOWED", f"{name!r} is not in the allowlist")
        try:
            return schema.model_validate(arguments)
        except ValidationError as exc:
            raise ToolFailure("INVALID_ARGUMENTS", str(exc)) from exc

    def execute(self, name: str, arguments: StrictArgs) -> dict[str, Any]:
        handler = getattr(self, name, None)
        if handler is None or name not in TOOL_SCHEMAS:
            raise ToolFailure("TOOL_NOT_ALLOWED", f"{name!r} is not in the allowlist")
        return handler(arguments)


class Model(Protocol):
    def complete(self, prompt: str, timeout_seconds: float) -> tuple[str, dict[str, Any]]: ...


class DifyModel:
    """Dify Chat App adapter. Every call gets the full tool transcript in query."""

    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.dify_api_base_url.rstrip("/")
        self.api_key = settings.dify_direct_app_api_key
        if not self.api_key:
            raise ToolFailure("MODEL_CONFIG", "GUIDE_DIFY_DIRECT_APP_API_KEY is not configured")

    def complete(self, prompt: str, timeout_seconds: float) -> tuple[str, dict[str, Any]]:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(
                f"{self.base_url}/chat-messages",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"inputs": {"scenic_area": "灵山胜境", "interests": []},
                      "query": prompt, "response_mode": "blocking", "user": f"exp6-{uuid4().hex}"},
            )
            response.raise_for_status()
            data = response.json()
        return str(data.get("answer", "")), {
            "message_id": data.get("message_id"),
            "usage": (data.get("metadata") or {}).get("usage"),
        }


def parse_decision(answer: str) -> dict[str, Any]:
    answer = re.sub(r"^<think>.*?</think>", "", answer.strip(), flags=re.S).strip()
    answer = re.sub(r"^```(?:json)?\s*|\s*```$", "", answer, flags=re.I).strip()
    position = answer.find("{")
    if position < 0:
        raise ToolFailure("MODEL_FORMAT", "model output contains no JSON object")
    try:
        item, _ = json.JSONDecoder().raw_decode(answer[position:])
    except json.JSONDecodeError as exc:
        raise ToolFailure("MODEL_FORMAT", f"invalid JSON: {exc.msg}") from exc
    if not isinstance(item, dict) or item.get("action") not in {"tool", "final"}:
        raise ToolFailure("MODEL_FORMAT", "action must be tool or final")
    if item["action"] == "tool":
        if set(item) != {"action", "name", "arguments"} or not isinstance(item["name"], str) or not isinstance(item["arguments"], dict):
            raise ToolFailure("MODEL_FORMAT", "tool decision needs name and arguments object only")
    elif set(item) != {"action", "answer"} or not isinstance(item["answer"], str):
        raise ToolFailure("MODEL_FORMAT", "final decision needs answer string only")
    return item


def redact_log(value: Any) -> Any:
    """Keep keys, phone numbers, and email addresses out of persisted events."""
    if isinstance(value, dict):
        return {key: redact_log(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_log(item) for item in value]
    if isinstance(value, str):
        value = re.sub(r"\bapp-[A-Za-z0-9]{8,}\b", "[REDACTED_KEY]", value)
        value = re.sub(r"\b1[3-9]\d{9}\b", "[REDACTED_PHONE]", value)
        value = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[REDACTED_EMAIL]", value)
    return value


@dataclass(frozen=True)
class Task:
    goal: str
    start_time: str = "09:00"
    mode: Literal["route_plan", "save_plan"] = "route_plan"
    require_save: bool = False


@dataclass(frozen=True)
class Limits:
    max_steps: int = 6
    model_timeout_seconds: float = 30.0
    tool_timeout_seconds: float = 2.0
    total_timeout_seconds: float = 120.0
    approval_timeout_seconds: float = 30.0
    max_errors: int = 2


class Harness:
    def __init__(
        self, model: Model, registry: ToolRegistry | None = None,
        limits: Limits = Limits(), approval: Callable[[str, dict[str, Any]], bool | None] | None = None,
        log_root: Path = OUTPUT_ROOT,
    ) -> None:
        self.model = model
        self.registry = registry or ToolRegistry(log_root)
        self.limits = limits
        self.approval = approval or self._interactive_approval
        self.log_root = log_root

    def _interactive_approval(self, name: str, arguments: dict[str, Any]) -> bool | None:
        print(f"CONFIRM {name}: filename={arguments.get('filename')}, content_chars={len(arguments.get('content', ''))}")
        print(f"Content to write:\n{arguments.get('content', '')}")
        print("Effect: create one new text file under outputs/experiment6/plans; existing files are never overwritten.")
        print(f"Type yes to approve, no to reject within {self.limits.approval_timeout_seconds:g} seconds: ", end="", flush=True)
        deadline = monotonic() + self.limits.approval_timeout_seconds
        if os.name == "nt":
            import msvcrt

            letters: list[str] = []
            while monotonic() < deadline:
                if not msvcrt.kbhit():
                    sleep(0.05)
                    continue
                character = msvcrt.getwch()
                if character in "\r\n":
                    break
                if character == "\b":
                    if letters:
                        letters.pop()
                    continue
                letters.append(character)
            else:
                print("\nConfirmation timed out.")
                return None
            reply = "".join(letters).strip().lower()
            print()
        else:
            import select

            readable, _, _ = select.select([sys.stdin], [], [], self.limits.approval_timeout_seconds)
            if not readable:
                print("\nConfirmation timed out.")
                return None
            reply = sys.stdin.readline().strip().lower()
        return True if reply == "yes" else False if reply == "no" else None

    def _prompt(self, task: Task, transcript: list[dict[str, Any]]) -> str:
        tools = "\n".join(f"- {name}: {description}" for name, description in TOOL_DESCRIPTIONS.items())
        return (
            "你是灵山胜境单Agent的决策器。每次只输出一个JSON对象，不能输出Markdown或解释。\n"
            "调用工具格式：{\"action\":\"tool\",\"name\":\"工具名\",\"arguments\":{...}}\n"
            "最终回答格式：{\"action\":\"final\",\"answer\":\"中文回答\"}\n"
            "你只能从以下工具中选择。根据前面的工具结果决定下一步；工具错误也会返回给你。\n"
            f"{tools}\n"
            "路线任务的最终回答必须使用已读取的路线、实际计算的结束时间、演出时刻的当日核验提示，"
            "并写出资料文件名。估计结束时间不是演出或闭园承诺。"
            "若目标要求保存文件，必须调用save_plan，并等待人工确认；不得声称未执行的操作已经完成。\n"
            f"任务模式：{task.mode}\n目标：{task.goal}\n入园时间：{task.start_time}\n"
            f"已有调用与工具结果（JSON）：{json.dumps(transcript, ensure_ascii=False)}\n"
            "现在输出下一步的单个JSON对象。"
        )

    def _success(self, task: Task, answer: str, results: dict[str, dict[str, Any]]) -> tuple[bool, str]:
        if task.mode == "save_plan":
            saved = results.get("save_plan", {}).get("saved_path")
            return (bool(saved and Path(saved).exists() and answer.strip()), "saved file and final answer required")
        route = results.get("get_route")
        notice = results.get("get_visit_notice")
        timing = results.get("estimate_end_time")
        if not route or not notice or not timing:
            return False, "route, notice, and end-time tool results are required"
        if task.require_save and not results.get("save_plan", {}).get("saved_path"):
            return False, "saving was requested but the plan was not saved"
        if timing.get("start_time") != task.start_time or timing.get("duration_minutes") != route.get("duration_minutes"):
            return False, "end-time calculation must use the route duration and task start time"
        required = [route["stops"][0], route["stops"][-2], timing["end_time"], "03_routes.md"]
        if any(token not in answer for token in required):
            return False, "final answer misses a route stop, computed time, or source"
        if not ("当日" in answer or "官方" in answer):
            return False, "final answer misses the current-schedule caveat"
        return True, "required tool evidence and answer details verified"

    def run(self, task: Task) -> dict[str, Any]:
        run_id = f"exp6-{datetime.now(TIMEZONE):%Y%m%d-%H%M%S}-{uuid4().hex[:8]}"
        self.log_root.mkdir(parents=True, exist_ok=True)
        log_path = self.log_root / f"{run_id}.jsonl"
        transcript: list[dict[str, Any]] = []
        results: dict[str, dict[str, Any]] = {}
        start = monotonic()
        errors = 0
        steps = 0

        def event(kind: str, **fields: Any) -> None:
            row = {"task_id": run_id, "time": datetime.now(TIMEZONE).isoformat(timespec="seconds"),
                   "event": kind, "step": steps, "elapsed_ms": round((monotonic() - start) * 1000), **fields}
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(redact_log(row), ensure_ascii=False) + "\n")

        def finish(status: str, reason: str, answer: str = "") -> dict[str, Any]:
            event("finished", status=status, reason=reason, answer=answer[:2000])
            return {"task_id": run_id, "status": status, "reason": reason,
                    "answer": answer, "steps": steps,
                    "elapsed_ms": round((monotonic() - start) * 1000),
                    "log_path": str(log_path), "tool_results": results}

        event("started", goal=task.goal, start_time=task.start_time, mode=task.mode)
        for _ in range(self.limits.max_steps):
            remaining = self.limits.total_timeout_seconds - (monotonic() - start)
            if remaining <= 0:
                return finish("time_limit", "total runtime limit reached")
            steps += 1  # One step means one model decision, even if the decision is invalid.
            try:
                raw, metadata = self.model.complete(self._prompt(task, transcript), min(remaining, self.limits.model_timeout_seconds))
                if monotonic() - start >= self.limits.total_timeout_seconds:
                    return finish("time_limit", "total runtime limit reached after model call")
                decision = parse_decision(raw)
                logged_decision = dict(decision)
                if decision["action"] == "tool" and decision["name"] == "save_plan":
                    logged_decision["arguments"] = {k: (v if k != "content" else f"{len(v)} chars") for k, v in decision["arguments"].items()}
                event("model_decision", decision=logged_decision, model_metadata=metadata)
            except (ToolFailure, httpx.HTTPError, TimeoutError, ValueError) as exc:
                code = exc.code if isinstance(exc, ToolFailure) else "MODEL_TIMEOUT" if isinstance(exc, (httpx.TimeoutException, TimeoutError)) else "MODEL_ERROR"
                event("model_error", error_type=code, message=str(exc)[:500])
                errors += 1
                if errors > self.limits.max_errors or code == "MODEL_TIMEOUT":
                    return finish("model_error", code)
                transcript.append({"model_error": {"code": code, "message": str(exc)[:500]}})
                continue
            if decision["action"] == "final":
                good, reason = self._success(task, decision["answer"], results)
                if good:
                    return finish("completed", reason, decision["answer"])
                event("final_check_failed", reason=reason)
                errors += 1
                if errors > self.limits.max_errors:
                    return finish("incomplete", reason, decision["answer"])
                transcript.append({"final_rejected": reason})
                continue
            name, args = decision["name"], decision["arguments"]
            try:
                checked = self.registry.validate(name, args)
                if name == "save_plan":
                    try:
                        approved = self.approval(name, checked.model_dump())
                    except (EOFError, KeyboardInterrupt):
                        approved = None
                    event("approval", tool=name, filename=checked.filename, approved=approved)
                    if approved is None:
                        return finish("approval_required", "confirmation was not provided; no write occurred")
                    if not approved:
                        return finish("approval_rejected", "user refused; no write occurred")
                timeout = min(self.limits.tool_timeout_seconds, self.limits.total_timeout_seconds - (monotonic() - start))
                if timeout <= 0:
                    return finish("time_limit", "total runtime limit reached before tool call")
                executor = ThreadPoolExecutor(max_workers=1)
                future = executor.submit(self.registry.execute, name, checked)
                try:
                    result = future.result(timeout=timeout)
                except FutureTimeout:
                    future.cancel()
                    event("tool_error", tool=name, error_type="TOOL_TIMEOUT")
                    return finish("tool_timeout", "tool wait timed out; cancellation is not guaranteed; check output before any retry")
                finally:
                    executor.shutdown(wait=False, cancel_futures=True)
                results[name] = result
                event("tool_result", tool=name, arguments={k: (v if k != "content" else f"{len(v)} chars") for k, v in checked.model_dump().items()}, result=result)
                transcript.append({"tool_call": {"name": name, "arguments": checked.model_dump()}, "tool_result": result})
            except ToolFailure as exc:
                event("tool_error", tool=name, error_type=exc.code, message=exc.message[:500])
                errors += 1
                if errors > self.limits.max_errors:
                    return finish("tool_error", exc.code)
                transcript.append({"tool_call": {"name": name, "arguments": args},
                                   "tool_error": {"code": exc.code, "message": exc.message[:500]}})
            except Exception as exc:
                event("tool_error", tool=name, error_type="TOOL_EXCEPTION", message=f"{type(exc).__name__}: {exc}"[:500])
                if name == "save_plan":
                    return finish("write_status_unknown", "save failed after approval; inspect the plan directory before retrying")
                errors += 1
                if errors > self.limits.max_errors:
                    return finish("tool_error", "TOOL_EXCEPTION")
                transcript.append({"tool_call": {"name": name, "arguments": args},
                                   "tool_error": {"code": "TOOL_EXCEPTION", "message": type(exc).__name__}})
        return finish("step_limit", f"maximum {self.limits.max_steps} model decisions reached")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-time", default="09:00")
    parser.add_argument("--family", action="store_true")
    parser.add_argument("--save", action="store_true", help="Allow the model to propose saving a plan; asks before writing")
    args = parser.parse_args()
    EndTimeArgs.model_validate({"start_time": args.start_time, "duration_minutes": 60})
    route = "亲子家庭" if args.family else "半日"
    goal = f"请根据灵山胜境资料推荐{route}路线，从{args.start_time}入园，计算预计结束时间，说明演出时间以官方当日信息为准。"
    if args.save:
        goal += "请把方案保存为exp6_visit_plan.txt。"
    task = Task(goal=goal, start_time=args.start_time, mode="route_plan", require_save=args.save)
    outcome = Harness(DifyModel(Settings())).run(task)
    print(json.dumps({k: v for k, v in outcome.items() if k != "tool_results"}, ensure_ascii=False, indent=2))
    return 0 if outcome["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
