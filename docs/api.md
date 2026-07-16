# 第一阶段接口说明

## GET /api/v1/health

用于前端、部署脚本或人工验收确认后端进程可用。

响应字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| status | string | 固定为 `ok` |
| service | string | 服务标识 |
| version | string | 当前 API 版本 |

## POST /api/v1/chat

游客文字问答接口。第一阶段由 Mock Guide Service 返回模拟景区回答，后续可替换为 RAG 服务。

请求字段：

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| session_id | string | 必填，去空格后 1-100 字符 |
| question | string | 必填，去空格后 1-500 字符 |
| interests | string[] | 可选，最多 5 项，每项 1-50 字符 |

响应字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| request_id | string | 后端生成的请求编号 |
| answer | string | 导游式回答 |
| sources | array | 来源标签，无来源时为空数组 |
| emotion | string | `neutral`、`friendly`、`happy`、`concerned`、`serious` |
| latency_ms | integer | 后端处理耗时 |
| fallback | boolean | 未命中 Mock 数据时为 `true` |

统一错误结构：

```json
{
  "error": {
    "code": "INVALID_QUESTION",
    "message": "请求参数不符合要求",
    "request_id": "req-20260710-000001"
  }
}
```
