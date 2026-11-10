# 实验7核心AI能力原型运行说明

## 原型范围

原型只验证“灵山胜境可信导游问答与路线建议”主链路：游客输入、Dify 云端模型与知识库检索、输出清洗、规则检查和证据保存。购票支付、实时票务和整站集成不属于本原型范围。

## 配置与密钥

- 集中配置：`services/api-server/config/experiment7_config.json`
- 固定测试集：`services/api-server/evals/experiment7_cases.json`
- 密钥：仅从本机 `.env` 的 `GUIDE_DIFY_API_KEY` 读取，不进入代码与评测结果。

## 运行

在 `services/api-server` 目录执行：

```powershell
.\.venv\Scripts\python.exe scripts\experiment7_eval.py --version P0
.\.venv\Scripts\python.exe scripts\experiment7_eval.py --version P1
```

证据输出到 `outputs/experiment7/`。每条记录包含回答、来源、规则判定、错误类型、响应时间、Token、调用次数和接口费用。

P0 是第1周初版，直接提交原问题；P1 是第2周修订版，增加输入预检、可信回答约束、可见资料依据、长度检查及失败记录。两版使用同一模型、同一知识库和同一测试集。
