"""Deterministic fault and approval cases; normal case uses the live model separately."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from time import sleep
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.experiment6_agent import (
    Harness, Limits, OUTPUT_ROOT, Task, ToolFailure, ToolRegistry,
)


def tool(name: str, **arguments: object) -> str:
    return json.dumps({"action": "tool", "name": name, "arguments": arguments}, ensure_ascii=False)


def final(answer: str) -> str:
    return json.dumps({"action": "final", "answer": answer}, ensure_ascii=False)


ROUTE_ANSWER = (
    "依据03_routes.md，09:00南门入园，经过灵山大照壁、五明桥、九龙灌浴、"
    "祥符禅寺、灵山大佛、灵山梵宫，预计12:30结束。演出时间请以官方当日公告为准。"
)
ROUTE_TASK = Task("从09:00入园，查询半日路线、演出提示并计算结束时间", "09:00")
ROUTE_STEPS = [
    tool("get_route", route_type="half_day"),
    tool("estimate_end_time", start_time="09:00", duration_minutes=210),
    tool("get_visit_notice", kind="performance"),
    final(ROUTE_ANSWER),
]


class ScriptedModel:
    def __init__(self, replies: list[str]) -> None:
        self.replies = iter(replies)

    def complete(self, prompt: str, timeout_seconds: float) -> tuple[str, dict]:
        return next(self.replies), {"test_double": True}


class OneFailureRegistry(ToolRegistry):
    def __init__(self, output_root: Path) -> None:
        super().__init__(output_root)
        self.fail_next = True

    def get_visit_notice(self, args):
        if self.fail_next:
            self.fail_next = False
            raise ToolFailure("SIMULATED_IO", "temporary source read failure")
        return super().get_visit_notice(args)


class SlowRegistry(ToolRegistry):
    def get_route(self, args):
        sleep(0.05)
        return super().get_route(args)


class SlowModel:
    def complete(self, prompt: str, timeout_seconds: float) -> tuple[str, dict]:
        sleep(0.03)
        return ROUTE_STEPS[0], {"test_double": True}


def run_cases(output_root: Path = OUTPUT_ROOT) -> list[dict]:
    output_root.mkdir(parents=True, exist_ok=True)
    cases = []

    def record(name: str, expected: str, result: dict) -> None:
        assert result["status"] == expected, (name, result)
        cases.append({"case": name, "expected": expected, "actual": result["status"],
                      "reason": result["reason"], "steps": result["steps"],
                      "task_id": result["task_id"], "elapsed_ms": result["elapsed_ms"],
                      "log_path": result["log_path"]})

    # A bad model argument is rejected, fed back, then corrected within the retry budget.
    invalid_then_fixed = [tool("estimate_end_time", start_time="9am", duration_minutes=210)] + ROUTE_STEPS
    record("invalid_argument_then_corrected", "completed",
           Harness(ScriptedModel(invalid_then_fixed), log_root=output_root).run(ROUTE_TASK))

    # The tool exception is returned to the model, which retries that read once.
    transient = ROUTE_STEPS[:3] + [ROUTE_STEPS[2], ROUTE_STEPS[3]]
    record("tool_exception_then_retry", "completed",
           Harness(ScriptedModel(transient), registry=OneFailureRegistry(output_root), log_root=output_root).run(ROUTE_TASK))

    record("step_limit", "step_limit",
           Harness(ScriptedModel([ROUTE_STEPS[0]] * 2),
                   limits=Limits(max_steps=2), log_root=output_root).run(ROUTE_TASK))

    record("total_time_limit", "time_limit",
           Harness(SlowModel(), limits=Limits(total_timeout_seconds=0.01),
                   log_root=output_root).run(ROUTE_TASK))

    record("tool_timeout", "tool_timeout",
           Harness(ScriptedModel([ROUTE_STEPS[0]]), registry=SlowRegistry(output_root),
                   limits=Limits(tool_timeout_seconds=0.01), log_root=output_root).run(ROUTE_TASK))

    filename_yes = f"approval_yes_{uuid4().hex[:8]}.txt"
    content = "灵山半日游：南门入园，参观九龙灌浴、灵山大佛和灵山梵宫。"
    save_call_yes = tool("save_plan", filename=filename_yes, content=content)
    accepted = Harness(
        ScriptedModel([save_call_yes, final("方案已保存，文件可在本机查看。")]),
        approval=lambda _name, _args: True, log_root=output_root,
    ).run(Task("保存游览方案", mode="save_plan"))
    record("approval_yes", "completed", accepted)
    assert (output_root / "plans" / filename_yes).read_text(encoding="utf-8") == content

    filename_no = f"approval_no_{uuid4().hex[:8]}.txt"
    rejected = Harness(
        ScriptedModel([tool("save_plan", filename=filename_no, content=content)]),
        approval=lambda _name, _args: False, log_root=output_root,
    ).run(Task("保存游览方案", mode="save_plan"))
    record("approval_no", "approval_rejected", rejected)
    assert not (output_root / "plans" / filename_no).exists()

    filename_wait = f"approval_wait_{uuid4().hex[:8]}.txt"
    no_response = Harness(
        ScriptedModel([tool("save_plan", filename=filename_wait, content=content)]),
        approval=lambda _name, _args: None, log_root=output_root,
    ).run(Task("保存游览方案", mode="save_plan"))
    record("approval_no_response", "approval_required", no_response)
    assert not (output_root / "plans" / filename_wait).exists()

    # The model cannot call a function not registered in the allowlist.
    not_allowed = Harness(
        ScriptedModel([tool("run_shell", command="echo unsafe")] * 3),
        log_root=output_root,
    ).run(ROUTE_TASK)
    record("tool_not_allowed", "tool_error", not_allowed)

    (output_root / "case_results.json").write_text(
        json.dumps({"cases": cases}, ensure_ascii=False, indent=2), encoding="utf-8")
    return cases


if __name__ == "__main__":
    rows = run_cases()
    for row in rows:
        print(f"{row['case']}: {row['actual']} ({row['steps']} steps)")
    print(f"Saved {OUTPUT_ROOT / 'case_results.json'}")
