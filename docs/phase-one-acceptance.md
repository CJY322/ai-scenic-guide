# 第一阶段验收记录

## 自动化测试

运行目录：`D:\ai-scenic-guide\services\api-server`

```powershell
.venv\Scripts\activate
pytest -v
```

当前验证结果：2026-07-10 已通过 `7 passed in 0.71s`。

覆盖用例：

- T01：`GET /api/v1/health` 返回 200 和 `status=ok`
- T02：正常中文问题返回 200、非空 answer 和 request_id
- T03：空问题返回 422 统一错误结构
- T04：超过 500 字问题返回 422
- T05：interests 超过 5 项返回 422
- T06：Mock 未命中返回 `fallback=true`
- T07：服务层异常返回 500 统一错误结构且不暴露堆栈

## 前端构建

运行目录：`D:\ai-scenic-guide\apps\visitor-web`

```powershell
npm.cmd run build
```

当前验证结果：2026-07-10 已通过 `vue-tsc --noEmit && vite build`，生成生产包位于 `apps/visitor-web/dist`。

## 联调 Smoke Test

- `GET http://127.0.0.1:8000/api/v1/health` 返回 `status=ok`
- `POST http://127.0.0.1:8000/api/v1/chat` 命中 Mock FAQ，返回 `fallback=false`、`emotion=happy` 和来源标签
- `GET http://127.0.0.1:5173` 返回 200，Vite 页面可访问

## 人工验收清单

- F01：打开 `http://localhost:5173`，显示欢迎区和推荐问题
- F02：输入问题并按 Enter，出现游客消息和导游回复
- F03：连续点击发送，加载期间不会重复提交
- F04：发送空格，不调用后端并显示输入提示
- F05：关闭后端后发送，页面提示连接失败并允许重试
- F06：发送长文本，消息自动换行且页面不横向溢出

## 阶段出口

当 F01-F06 完成人工确认，并完成 1-2 分钟演示录屏后，第一阶段可进入第二阶段 RAG 知识库接入。
