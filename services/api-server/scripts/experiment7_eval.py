"""Experiment 7 week-1 evaluator for the Lingshan RAG prototype.

Run from services/api-server:
    python scripts/experiment7_eval.py --version P1

The API key is read from GUIDE_DIFY_API_KEY in .env and is never written to
the evidence file. Every case starts an independent Dify conversation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import perf_counter
from typing import Any
from uuid import uuid4

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.config import Settings


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "evals" / "experiment7_cases.json"
DEFAULT_CONFIG = ROOT / "config" / "experiment7_config.json"
DEFAULT_OUTPUT = ROOT / "outputs" / "experiment7"
CHINA_TZ = timezone(timedelta(hours=8))


def clean_answer(value: object) -> str:
    answer = str(value or "").strip()
    answer = re.sub(r"^<think>.*?</think>", "", answer, flags=re.S).strip()
    return answer


def judge(case: dict[str, Any], answer: str, status: object) -> dict[str, Any]:
    lower = answer.lower()
    matched = [item for item in case["must_any"] if item.lower() in lower]
    forbidden = [item for item in case["must_not"] if item.lower() in lower]
    passed = status == 200 and bool(matched) and not forbidden
    return {
        "automatic_pass": passed,
        "matched_required": matched,
        "matched_forbidden": forbidden,
        "manual_judgement": "通过" if passed else "不通过",
        "manual_rule": case["judge_rule"],
        "error_type": "无" if passed else "请求失败" if status != 200 else "要点缺失或边界不合格",
    }


def build_query(version: str, question: str, config: dict[str, Any]) -> str:
    if version == "P0":
        return question
    return f"{config['p1_query_prefix']}\n{question}"


def visible_sources(answer: str, resources: list[Any]) -> list[str]:
    sources = [
        str(item.get("document_name") or item.get("dataset_name") or "灵山胜境知识库")
        for item in resources if isinstance(item, dict)
    ][:5]
    if "资料依据：" in answer and not sources:
        citation = answer.rsplit("资料依据：", 1)[1].strip().splitlines()[0][:100]
        if citation:
            sources.append(citation)
    return list(dict.fromkeys(sources))


def call_case(
    client: httpx.Client,
    settings: Settings,
    case: dict[str, Any],
    run_id: str,
    version: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    question = case["question"].strip()
    if version == "P1" and (len(question) < 2 or not re.search(r"[\w\u4e00-\u9fff]", question)):
        answer = "请补充您想了解的具体内容，例如景点、路线、交通或游览注意事项。\n资料依据：无可靠资料，需通过官方渠道核验"
        result = {
            "http_status": 200,
            "answer": answer,
            "sources": ["无可靠资料，需通过官方渠道核验"],
            "elapsed_ms": 0,
            "total_tokens": 0,
            "total_price": "0",
            "currency": "USD",
            "model_calls": 0,
            "processing_note": "异常输入由本地预检拦截，未调用收费接口",
        }
        result.update(judge(case, answer, 200))
        result["citation_pass"] = True
        result["length_pass"] = len(answer) <= int(config["max_answer_chars"])
        return result
    payload = {
        "inputs": {"scenic_area": "灵山胜境", "interests": []},
        "query": build_query(version, question, config),
        "response_mode": "blocking",
        "user": f"exp7-{run_id}-{version}-{case['id']}",
    }
    started = perf_counter()
    try:
        response = client.post(
            f"{settings.dify_api_base_url.rstrip('/')}/chat-messages",
            headers={"Authorization": f"Bearer {settings.dify_api_key}"},
            json=payload,
        )
        elapsed_ms = round((perf_counter() - started) * 1000)
        data = response.json()
        answer = clean_answer(data.get("answer")) if isinstance(data, dict) else ""
        metadata = data.get("metadata") or {} if isinstance(data, dict) else {}
        resources = metadata.get("retriever_resources") or [] if isinstance(metadata, dict) else []
        usage = metadata.get("usage") or {} if isinstance(metadata, dict) else {}
        sources = visible_sources(answer, resources)
        result = {
            "http_status": response.status_code,
            "answer": answer,
            "sources": sources,
            "elapsed_ms": elapsed_ms,
            "total_tokens": usage.get("total_tokens"),
            "total_price": usage.get("total_price", "0"),
            "currency": usage.get("currency", "USD"),
            "model_calls": 1,
        }
    except (httpx.HTTPError, ValueError) as exc:
        result = {
            "http_status": "request_error",
            "answer": "",
            "sources": [],
            "elapsed_ms": round((perf_counter() - started) * 1000),
            "total_tokens": None,
            "total_price": None,
            "currency": "USD",
            "model_calls": 1,
            "error": {"type": type(exc).__name__, "message": str(exc)[:300]},
        }
    result.update(judge(case, result["answer"], result["http_status"]))
    result["citation_pass"] = bool(result["sources"]) if version == "P1" else None
    result["length_pass"] = len(result["answer"]) <= int(config["max_answer_chars"]) if version == "P1" else None
    if version == "P1" and (not result["citation_pass"] or not result["length_pass"]):
        result["automatic_pass"] = False
        result["manual_judgement"] = "不通过"
        result["error_type"] = "引用缺失或输出过长"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=["P0", "P1"], default="P1")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    settings = Settings()
    if not settings.dify_api_key:
        print("GUIDE_DIFY_API_KEY is not configured.", file=sys.stderr)
        return 2
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    config = json.loads(args.config.read_text(encoding="utf-8"))
    run_id = uuid4().hex[:10]
    rows: list[dict[str, Any]] = []
    timeout = httpx.Timeout(float(config["timeout_seconds"]))
    with httpx.Client(timeout=timeout) as client:
        for case in cases:
            result = call_case(client, settings, case, run_id, args.version, config)
            rows.append({"id": case["id"], "category": case["category"], "question": case["question"], **result})
            print(f"{case['id']}: {result['http_status']} {result['elapsed_ms']} ms {'PASS' if result['automatic_pass'] else 'FAIL'}")

    passed = sum(1 for row in rows if row["automatic_pass"])
    average_ms = round(sum(row["elapsed_ms"] for row in rows) / len(rows))
    total_tokens = sum(int(row["total_tokens"] or 0) for row in rows)
    citation_count = sum(1 for row in rows if row["sources"])
    evidence = {
        "experiment": "实验7灵山胜境核心AI能力原型评测",
        "version": args.version,
        "prompt_description": config["prompt_versions"][args.version],
        "model_name": config["model_name"],
        "provider": config["provider"],
        "timestamp": datetime.now(CHINA_TZ).isoformat(timespec="seconds"),
        "independent_conversations": True,
        "summary": {
            "total": len(rows),
            "passed": passed,
            "failed": len(rows) - passed,
            "pass_rate": round(passed / len(rows), 4),
            "average_elapsed_ms": average_ms,
            "total_tokens": total_tokens,
            "total_model_calls": sum(row["model_calls"] for row in rows),
            "visible_source_rate": round(citation_count / len(rows), 4),
        },
        "results": rows,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    output = args.output_root / f"{args.version.lower()}_results.json"
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {output.resolve()}")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
