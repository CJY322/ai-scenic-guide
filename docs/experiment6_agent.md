# 实验6：灵山半日游单 Agent 运行说明

本实验沿用“灵境AI”项目的 `data/knowledge/lingshan/` 资料和已配置的 Dify 直接模型应用。任务是根据入园时间生成半日游路线、计算预计结束时间，并附演出信息核验提醒。正常流程由模型以 JSON 决定下一步调用，程序校验并执行工具。

## 文件

| 路径 | 用途 |
| --- | --- |
| `services/api-server/scripts/experiment6_agent.py` | 单 Agent、四个工具、参数校验、确认与 Harness |
| `services/api-server/scripts/experiment6_cases.py` | 可复现的异常、上限与确认测试 |
| `services/api-server/tests/test_experiment6_agent.py` | 自动化断言 |
| `services/api-server/outputs/experiment6/` | 本机运行日志、测试结果与经确认的方案文件 |

## 运行

在 `services/api-server` 目录执行：

```powershell
.\.venv\Scripts\python.exe scripts\experiment6_agent.py --start-time 09:00
.\.venv\Scripts\python.exe scripts\experiment6_cases.py
.\.venv\Scripts\python.exe -m pytest tests/test_experiment6_agent.py -q --basetemp outputs/experiment6/pytest-tmp
```

模型 Key 从本机 `.env` 中的 `GUIDE_DIFY_DIRECT_APP_API_KEY` 读取，日志不保存 Key。`--family` 改用亲子路线；`--save` 要求保存方案，此时 `save_plan` 会在写入前展示文件名、内容和影响，30 秒内输入 `yes` 才执行，输入 `no` 或不回答都不会写入。

## 边界

工具允许列表：`get_route`、`get_visit_notice`、`estimate_end_time`、`save_plan`。前两个只读指定 Markdown，第三个只做时间计算，第四个只能在 `outputs/experiment6/plans/` 新建 `.txt` 文件且不能覆盖。所有模型参数经过 Pydantic 严格校验；未知工具名、额外字段、越界时长、非法文件名均被拒绝。

每次模型输出一个 JSON 决策：`{"action":"tool","name":"...","arguments":{...}}` 或 `{"action":"final","answer":"..."}`。Harness 将工具结果和错误写回下一次模型输入。默认最多 6 次模型决策；模型调用超时 30 秒，工具等待超时 2 秒，总运行 120 秒，最多容忍 2 次可恢复错误。一次“步”是模型作出的一次决策，包括无效决策。最终答案必须能对照实际路线、计算时间与来源通过程序核验；仅有模型宣称完成不算成功。

工具超时只表示程序停止等待，后台线程未必立即结束。只读工具可检查后重跑；`save_plan` 超时或写入状态不明时先核对文件，禁止直接重复写入。所有运行均写入带任务编号的 JSONL 日志。边界测试使用脚本模型注入错误；正常流程必须使用已配置的真实 Dify 模型应用。
