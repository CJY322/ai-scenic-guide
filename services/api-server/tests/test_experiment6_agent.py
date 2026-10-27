from pathlib import Path

import pytest

from scripts.experiment6_agent import (
    EndTimeArgs, RouteArgs, SaveArgs, ToolFailure, ToolRegistry, redact_log,
)
from scripts.experiment6_cases import run_cases


def test_tools_read_real_route_and_calculate_clock_time(tmp_path: Path) -> None:
    tools = ToolRegistry(tmp_path)
    route = tools.execute("get_route", RouteArgs(route_type="half_day"))
    end = tools.execute(
        "estimate_end_time",
        EndTimeArgs(start_time="09:00", duration_minutes=route["duration_minutes"]),
    )
    assert route["source"] == "03_routes.md"
    assert route["stops"][0] == "南门入园"
    assert route["stops"][-2] == "灵山梵宫"
    assert end["end_time"] == "12:30"


def test_schema_and_allowlist_reject_invalid_calls(tmp_path: Path) -> None:
    tools = ToolRegistry(tmp_path)
    for name, args, code in [
        ("estimate_end_time", {"start_time": "9am", "duration_minutes": 210}, "INVALID_ARGUMENTS"),
        ("estimate_end_time", {"start_time": "09:00", "duration_minutes": 999}, "INVALID_ARGUMENTS"),
        ("save_plan", {"filename": "../escape.txt", "content": "a complete example plan"}, "INVALID_ARGUMENTS"),
        ("run_shell", {"command": "echo hi"}, "TOOL_NOT_ALLOWED"),
    ]:
        with pytest.raises(ToolFailure) as caught:
            tools.validate(name, args)
        assert caught.value.code == code


def test_save_plan_never_overwrites_existing_file(tmp_path: Path) -> None:
    tools = ToolRegistry(tmp_path)
    args = SaveArgs(filename="example.txt", content="a complete example plan")
    saved = tools.save_plan(args)
    with pytest.raises(ToolFailure) as caught:
        tools.save_plan(args)
    assert caught.value.code == "ALREADY_EXISTS"
    assert Path(saved["saved_path"]).read_text(encoding="utf-8") == args.content


def test_harness_failure_and_confirmation_cases(tmp_path: Path) -> None:
    cases = run_cases(tmp_path)
    assert len(cases) == 9
    assert all(row["actual"] == row["expected"] for row in cases)
    assert (tmp_path / "case_results.json").exists()


def test_log_redacts_keys_and_contact_details() -> None:
    result = redact_log({"text": "app-Abcdef12345678 13800138000 guest@example.com"})["text"]
    assert "app-Abcdef12345678" not in result
    assert "13800138000" not in result
    assert "guest@example.com" not in result
