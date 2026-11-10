from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "experiment7_eval.py"
SPEC = importlib.util.spec_from_file_location("experiment7_eval", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_clean_answer_removes_reasoning() -> None:
    assert MODULE.clean_answer("<think>private</think>公开回答") == "公开回答"


def test_p1_query_contains_contract() -> None:
    config = {"p1_query_prefix": "只依据资料回答："}
    assert MODULE.build_query("P0", "问题", config) == "问题"
    assert MODULE.build_query("P1", "问题", config) == "只依据资料回答：\n问题"


def test_visible_sources_uses_explicit_citation() -> None:
    answer = "回答正文\n资料依据：灵山胜境知识库"
    assert MODULE.visible_sources(answer, []) == ["灵山胜境知识库"]


def test_judge_rejects_forbidden_claim() -> None:
    case = {
        "must_any": ["官方"],
        "must_not": ["预约成功"],
        "judge_rule": "不谎称完成交易",
    }
    result = MODULE.judge(case, "已预约成功，请看官方消息", 200)
    assert result["automatic_pass"] is False
    assert result["error_type"] == "要点缺失或边界不合格"
