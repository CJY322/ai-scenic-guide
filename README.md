# AI景区数字人导游 - 第一阶段MVP

第一阶段交付的是一个本地可运行的文字版景区 AI 导游：游客在 Vue 页面输入问题，前端通过 HTTP 调用 FastAPI 后端，后端基于模拟景区 FAQ 返回导游式回答、来源、情绪和处理耗时。

## 技术栈

- 前端：Vue 3、TypeScript、Vite、Axios、@lucide/vue
- 后端：Python 3.12、FastAPI、Pydantic、Pytest
- 数据：`data/mock/faq.json` 模拟景区问答数据

## 目录结构

```text
D:\ai-scenic-guide
├─ apps
│  └─ visitor-web
│     ├─ src
│     │  ├─ api
│     │  ├─ components
│     │  ├─ types
│     │  └─ views
│     ├─ .env.development
│     └─ package.json
├─ services
│  └─ api-server
│     ├─ app
│     │  ├─ api
│     │  ├─ core
│     │  ├─ schemas
│     │  ├─ services
│     │  └─ main.py
│     ├─ tests
│     ├─ requirements.txt
│     └─ .env.example
├─ data
│  └─ mock
├─ docs
└─ README.md
```

## 环境要求

- Node.js 23.9.0 或 Node.js 22 LTS
- npm 10.x
- Python 3.12.7
- Chrome 或 Edge 浏览器

如果 PowerShell 提示 `npm.ps1 cannot be loaded because running scripts is disabled`，请使用 `npm.cmd` 执行 npm 命令，例如 `npm.cmd install`。

## 启动后端

```powershell
cd /d D:\ai-scenic-guide\services\api-server
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

后端地址：

- Swagger 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/v1/health

## 启动前端

只在包含 `package.json` 的目录执行前端命令：

```powershell
cd /d D:\ai-scenic-guide\apps\visitor-web
npm.cmd install
npm.cmd run dev
```

前端地址：http://localhost:5173

## 核心接口

### 健康检查

```http
GET /api/v1/health
```

```json
{
  "status": "ok",
  "service": "ai-scenic-guide-api",
  "version": "0.1.0"
}
```

### 文字问答

```http
POST /api/v1/chat
Content-Type: application/json
```

```json
{
  "session_id": "web-550e8400-e29b-41d4-a716-446655440000",
  "question": "景区有哪些值得参观的景点？",
  "interests": ["历史文化"]
}
```

成功响应：

```json
{
  "request_id": "req-20260710-000001",
  "answer": "如果您喜欢历史文化，建议优先参观……",
  "sources": [{ "title": "景区简介（模拟数据）", "section": "主要景点" }],
  "emotion": "friendly",
  "latency_ms": 120,
  "fallback": false
}
```

错误响应：

```json
{
  "error": {
    "code": "INVALID_QUESTION",
    "message": "请求参数不符合要求",
    "request_id": "req-20260710-000002"
  }
}
```

## 测试

```powershell
cd /d D:\ai-scenic-guide\services\api-server
.venv\Scripts\activate
pytest -v
```

已覆盖：健康检查、正常问答、空问题、超长问题、兴趣数量超限、Mock 未命中兜底、服务异常统一错误结构。

## 常见问题

- `npm ENOENT package.json`：进入 `D:\ai-scenic-guide\apps\visitor-web` 后再执行 npm 命令。
- 前端 CORS 报错：确认后端已启动，并且请求地址为 `http://127.0.0.1:8000`。
- 接口 404：核对路径是否为 `/api/v1/chat` 或 `/api/v1/health`。
- Python 找不到依赖：确认已激活 `services\api-server\.venv` 并重新执行 `pip install -r requirements.txt`。

## 下一阶段

第二阶段可在不修改前端接口契约的前提下，把 `services/api-server/app/services/guide_service.py` 中的 Mock 服务替换为 Dify、RAGFlow 或自研 RAG 知识库服务。
## 第二阶段：黄山知识库 + Dify RAG

已新增黄山风景区知识库文件：`data/knowledge/huangshan/`。

Dify 接入说明见：`docs/dify-huangshan-rag.md`。

后端通过环境变量切换问答服务：

```text
GUIDE_ANSWER_PROVIDER=mock   # 使用第一阶段本地 Mock
GUIDE_ANSWER_PROVIDER=dify   # 调用 Dify Chat App API
```

启用 Dify 时，在 `services/api-server/.env` 中配置：

```text
GUIDE_ANSWER_PROVIDER=dify
GUIDE_DIFY_API_BASE_URL=https://api.dify.ai/v1
GUIDE_DIFY_API_KEY=你的Dify应用APIKey
```

前端接口保持不变，仍然调用 `POST /api/v1/chat`。

## 第三阶段：导游语音播报

已在游客端增加浏览器原生 TTS 播报能力：

- 导游回答支持播放、暂停、继续和重播。
- 顶部支持“自动播报”开关。
- 语音播放失败或浏览器不支持时，不影响文字问答。

说明文档见：`docs/phase-three-tts.md`。

## 第四阶段：游客语音输入

已在游客端增加浏览器原生 ASR 语音输入能力：

- 输入框旁边支持麦克风语音识别。
- 顶部支持“识别后发送”开关。
- 麦克风权限拒绝或浏览器不支持时，不影响文字问答。

说明文档见：`docs/phase-four-asr.md`。

## 第五阶段：数字人导游形象与展示模式

已在游客端增加轻量数字人导游形象：

- 支持待机、聆听、检索和讲解状态。
- 导游语音播报时有说话动画。
- 支持适合景区终端的大屏展示模式。

说明文档见：`docs/phase-five-digital-guide.md`。

## 第六阶段：SadTalker 真实数字人接入

已新增可选 SadTalker 适配：

- 后端提供 `/api/v1/avatar/status` 和 `/api/v1/avatar/video`。
- 前端在 SadTalker 配置可用时显示“真实数字人”开关。
- 默认仍使用轻量数字人，不影响 Dify 问答、语音播报和语音输入。

SadTalker 安装、导游形象图和 `.env` 配置见：`docs/phase-six-sadtalker-avatar.md`。

