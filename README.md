# AI景区数字人导游 - 灵山胜境示范版

本项目面向“灵山胜境”示范景区，提供一个本地可运行的 AI 数字人导游系统：游客可通过 Vue 页面进行文字或语音提问，FastAPI 后端对接 Dify RAG 返回导游式回答，前端支持语音播报、语音输入、轻量数字人展示，并可选接入 SadTalker 生成真实数字人讲解视频。

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Axios、@lucide/vue
- 后端：Python 3.12、FastAPI、Pydantic、Pytest
- RAG：Dify Chat App API
- 数据：`data/knowledge/lingshan/` 灵山胜境知识库，`data/mock/faq.json` 离线兜底问答数据
- 数字人：前端轻量数字人组件，可选 SadTalker 真实讲解视频

## 目录结构

```text
D:\ai-scenic-guide
├─ apps
│  └─ visitor-web
├─ services
│  └─ api-server
├─ data
│  ├─ avatar
│  ├─ knowledge
│  │  └─ lingshan
│  └─ mock
├─ docs
└─ README.md
```

## 启动后端

```powershell
cd /d D:\ai-scenic-guide\services\api-server
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

后端地址：

- Swagger 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/v1/health

## 启动前端

```powershell
cd /d D:\ai-scenic-guide\apps\visitor-web
npm.cmd run dev
```

前端地址：http://localhost:5173

## Dify 接入

灵山胜境知识库位于：`data/knowledge/lingshan/`。

Dify 免费版可直接上传：

```text
data/knowledge/lingshan/lingshan_dify_free_upload.md
```

后端通过环境变量切换问答服务：

```text
GUIDE_ANSWER_PROVIDER=mock
GUIDE_ANSWER_PROVIDER=dify
```

启用 Dify 时，在 `services/api-server/.env` 中配置：

```text
GUIDE_ANSWER_PROVIDER=dify
GUIDE_DIFY_API_BASE_URL=https://api.dify.ai/v1
GUIDE_DIFY_API_KEY=你的Dify应用APIKey
```

详细说明见：`docs/dify-lingshan-rag.md`。

## 已实现阶段

- 第二阶段：灵山胜境知识库 + Dify RAG。
- 第三阶段：浏览器端导游语音播报，见 `docs/phase-three-tts.md`。
- 第四阶段：游客语音输入，见 `docs/phase-four-asr.md`。
- 第五阶段：数字人导游形象与展示模式，见 `docs/phase-five-digital-guide.md`。
- 第六阶段：SadTalker 真实数字人接入，见 `docs/phase-six-sadtalker-avatar.md`。

## 核心接口

### 健康检查

```http
GET /api/v1/health
```

### 文字问答

```http
POST /api/v1/chat
Content-Type: application/json
```

```json
{
  "session_id": "web-550e8400-e29b-41d4-a716-446655440000",
  "question": "灵山胜境有哪些必看景点？",
  "interests": ["历史文化"]
}
```

### 数字人视频

```http
GET /api/v1/avatar/status
POST /api/v1/avatar/video
```

## 测试

```powershell
cd /d D:\ai-scenic-guide\services\api-server
.venv\Scripts\python.exe -m pytest tests
```

前端构建：

```powershell
cd /d D:\ai-scenic-guide\apps\visitor-web
npm.cmd run build
```

## 常见问题

- `npm ENOENT package.json`：进入 `D:\ai-scenic-guide\apps\visitor-web` 后再执行 npm 命令。
- 前端 CORS 报错：确认后端已启动，并且请求地址为 `http://127.0.0.1:8000`。
- Dify 没有接通：确认 `.env` 里 `GUIDE_ANSWER_PROVIDER=dify` 和 `GUIDE_DIFY_API_KEY` 已配置。
- SadTalker 不可用：确认 `.env` 中 `GUIDE_AVATAR_PROVIDER=sadtalker`、SadTalker 路径、Python 路径和模型权重都正确。
- 不要提交 `.env`、`data/generated/`、SadTalker 源码和模型权重。
