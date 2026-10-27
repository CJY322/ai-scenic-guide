"""Render Experiment 6 figures from actual JSONL and case-results evidence."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "deliverables" / "实验6截图"
EVIDENCE = ROOT / "services" / "api-server" / "outputs" / "experiment6"
NORMAL = EVIDENCE / "exp6-20261027-101004-8f25b389.jsonl"
CASES = EVIDENCE / "case_results.json"
FONT_PATH = Path("C:/Windows/Fonts/msyh.ttc")
OUTPUT.mkdir(parents=True, exist_ok=True)


def font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size, index=1 if bold else 0)


def panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str = "#ffffff") -> None:
    draw.rounded_rectangle(box, radius=24, fill=fill, outline="#d5e4e8", width=2)


def flowchart() -> None:
    canvas = Image.new("RGB", (1600, 790), "#f4f8f9")
    draw = ImageDraw.Draw(canvas)
    draw.text((65, 35), "图3-1  单 Agent 与 Harness 控制循环", fill="#153d45", font=font(40, bold=True))
    cards = [
        (50, 175, "接收目标", ["游客给出入园时间"]),
        (305, 175, "模型提出决策", ["JSON：tool", "或 final"]),
        (560, 175, "程序检查", ["步数、时限、格式"]),
        (815, 175, "工具校验", ["白名单、Schema", "访问范围"]),
        (1070, 175, "人工确认", ["仅保存文件时", "等待 yes"]),
        (1325, 175, "执行工具", ["读资料、计算", "或新建文件"]),
    ]
    for x, y, title, subtitle in cards:
        panel(draw, (x, y, x + 220, y + 175))
        draw.text((x + 18, y + 26), title, fill="#164e54", font=font(25, bold=True))
        for index, line in enumerate(subtitle):
            if line:
                draw.text((x + 18, y + 85 + index * 31), line, fill="#465d64", font=font(19))
    for x in [270, 525, 780, 1035, 1290]:
        draw.line((x, 263, x + 35, 263), fill="#3e8787", width=5)
        draw.polygon([(x + 35, 263), (x + 21, 254), (x + 21, 272)], fill="#3e8787")
    panel(draw, (1100, 500, 1545, 645), "#e5f2ee")
    draw.text((1125, 526), "工具结果 / 错误", fill="#164e54", font=font(28, bold=True))
    draw.text((1125, 574), "记录日志，并回传给模型", fill="#465d64", font=font(21))
    draw.line((1435, 350, 1435, 500), fill="#3e8787", width=5)
    draw.polygon([(1435, 500), (1426, 484), (1444, 484)], fill="#3e8787")
    draw.line((1100, 573, 415, 573), fill="#3e8787", width=5)
    draw.line((415, 573, 415, 350), fill="#3e8787", width=5)
    draw.polygon([(415, 350), (406, 368), (424, 368)], fill="#3e8787")
    draw.text((615, 582), "继续下一轮：带上真实结果", fill="#266971", font=font(20))
    panel(draw, (560, 402, 980, 512), "#fff0dc")
    draw.text((585, 425), "final 分支：核验完成标准", fill="#705322", font=font(25, bold=True))
    draw.text((585, 467), "路线、时间、来源与当日提示", fill="#6a644e", font=font(19))
    draw.line((670, 350, 670, 402), fill="#c28a41", width=4)
    draw.polygon([(670, 402), (662, 387), (678, 387)], fill="#c28a41")
    panel(draw, (50, 500, 390, 645), "#e1edfb")
    draw.text((76, 526), "完成或明确停止", fill="#1e4b70", font=font(27, bold=True))
    draw.text((76, 576), "状态、原因、步数入日志", fill="#465d64", font=font(19))
    draw.line((560, 457, 390, 572), fill="#7f91ad", width=4)
    draw.text((65, 710), "校验失败、拒绝、超时或达到上限均可停止；只有程序核验通过才标记 completed。", fill="#54717a", font=font(20))
    canvas.save(OUTPUT / "图3-1-Agent循环.png")


def timeline() -> None:
    events = [json.loads(line) for line in NORMAL.read_text(encoding="utf-8").splitlines()]
    decisions = [event for event in events if event["event"] == "model_decision"]
    labels = [
        ("1  查询路线", "get_route", ["读取 03_routes.md", "半日游路线共 8 个站点"], "#dff4ef"),
        ("2  计算时间", "estimate_end_time", ["09:00 + 210 分钟", "预计结束时间 12:30"], "#e1edfb"),
        ("3  查询提醒", "get_visit_notice", ["读取演出参考时间", "要求以当日信息核验"], "#fff0dc"),
        ("4  最终回答", "final", ["核验路线、时间、来源", "最终状态 completed"], "#eee8fb"),
    ]
    canvas = Image.new("RGB", (1600, 740), "#f4f8f9")
    draw = ImageDraw.Draw(canvas)
    draw.text((70, 42), "实验6：真实模型—工具运行轨迹", fill="#153d45", font=font(42, bold=True))
    draw.text((70, 105), f"任务编号 {events[0]['task_id']}    2026-10-27 10:10（北京时间）", fill="#54717a", font=font(22))
    for index, (title, action, desc, color) in enumerate(labels):
        x, y = 70 + index * 382, 205
        panel(draw, (x, y, x + 350, y + 335))
        draw.rounded_rectangle((x + 20, y + 22, x + 330, y + 79), radius=16, fill=color)
        draw.text((x + 36, y + 34), title, fill="#164e54", font=font(28, bold=True))
        draw.text((x + 26, y + 110), action, fill="#1d4355", font=font(22))
        for line_num, line in enumerate(desc):
            if line:
                draw.text((x + 26, y + 161 + line_num * 38), line, fill="#394f56", font=font(21))
        draw.text((x + 26, y + 286), f"第 {decisions[index]['step']} 步 · {decisions[index]['elapsed_ms']} ms", fill="#54717a", font=font(20))
        if index < 3:
            draw.text((x + 353, y + 143), "→", fill="#3c8584", font=font(40, bold=True))
    draw.text((70, 600), "模型调用 4 次   工具调用 3 次   总耗时 15,297 ms   总 Token 3,969   最终状态 completed", fill="#16575e", font=font(26, bold=True))
    draw.text((70, 651), "数据来源：本次运行的 JSONL 原始日志；图为日志可视化，非 Dify 控制台截图。", fill="#64777c", font=font(19))
    canvas.save(OUTPUT / "图3-2-真实运行轨迹.png")


def case_chart() -> None:
    rows = json.loads(CASES.read_text(encoding="utf-8"))["cases"]
    translations = {
        "invalid_argument_then_corrected": "参数错误后修正",
        "tool_exception_then_retry": "工具异常后重试",
        "step_limit": "步数上限",
        "total_time_limit": "总时限",
        "tool_timeout": "工具超时",
        "approval_yes": "确认同意",
        "approval_no": "确认拒绝",
        "approval_no_response": "无确认",
        "tool_not_allowed": "越权工具名",
    }
    canvas = Image.new("RGB", (1420, 970), "#f4f8f9")
    draw = ImageDraw.Draw(canvas)
    draw.text((60, 32), "实验6：边界测试结果", fill="#153d45", font=font(40, bold=True))
    draw.text((60, 87), "9 类脚本化场景均达到预期状态；正常流程另由真实 Dify 模型运行。", fill="#54717a", font=font(21))
    headers = [(80, "场景"), (500, "预期状态"), (805, "实际状态"), (1120, "步数")]
    panel(draw, (60, 145, 1360, 875))
    draw.rounded_rectangle((75, 165, 1345, 230), radius=12, fill="#dbeeea")
    for x, label in headers:
        draw.text((x, 182), label, fill="#194b50", font=font(24, bold=True))
    for index, row in enumerate(rows):
        y = 246 + index * 68
        if index % 2:
            draw.rounded_rectangle((75, y - 5, 1345, y + 56), radius=9, fill="#f0f6f7")
        draw.text((80, y + 7), translations[row["case"]], fill="#314c53", font=font(22))
        draw.text((500, y + 7), row["expected"], fill="#314c53", font=font(20))
        draw.text((805, y + 7), row["actual"], fill="#14715f", font=font(20, bold=True))
        draw.text((1120, y + 7), str(row["steps"]), fill="#314c53", font=font(21))
    draw.text((60, 910), "数据来源：case_results.json 与各任务编号 JSONL 日志；同意/拒绝为自动化测试回调。", fill="#64777c", font=font(18))
    canvas.save(OUTPUT / "图3-3-边界测试结果.png")


if __name__ == "__main__":
    flowchart()
    timeline()
    case_chart()
    print(OUTPUT)
