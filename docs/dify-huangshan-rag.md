# 黄山知识库与 Dify RAG 接入说明

更新时间：2026-07-16

## 目标

第二阶段把第一阶段的 Mock Guide Service 替换为 Dify RAG。前端仍然调用原接口：

```http
POST /api/v1/chat
```

后端根据环境变量决定使用本地 Mock 还是 Dify：

- `GUIDE_ANSWER_PROVIDER=mock`：使用 `data/mock/faq.json`
- `GUIDE_ANSWER_PROVIDER=dify`：调用 Dify Chat App API

## 一、创建 Dify 知识库

在 Dify 控制台中创建知识库，建议名称：

```text
黄山风景区导游知识库
```

如果使用 Dify 免费版，一次只能上传一个文件，直接上传这个合并文件：

```text
data/knowledge/huangshan/huangshan_dify_free_upload.md
```

原始拆分文件仍保留在 `data/knowledge/huangshan/00_source_index.md` 到 `06_safety_visit_tips.md`，用于后期维护和更新。维护时先改拆分文件，再重新生成单文件上传版。

建议索引方式：高质量索引。切分方式可先使用 Dify 自动切分，后续根据召回效果再调整。

## 二、创建 Dify 应用

在 Dify 中创建 Chatbot 或 Chatflow，并关联刚才创建的“黄山风景区导游知识库”。

建议系统提示词：

```text
你是黄山风景区的 AI 数字人导游。请基于知识库回答游客问题，语气亲切、稳妥、像现场导游。涉及开放时间、门票、索道、天气、临时管制、优惠政策等强时效信息时，不要编造，必须提示游客以黄山风景区官方公告、黄山旅游官方平台、现场游客中心和工作人员说明为准。若知识库没有可靠信息，请说明暂未查询到可靠资料，并建议拨打旅游咨询电话 0559-2590999。
```

建议输入变量：

- `scenic_area`：默认“黄山风景区”
- `interests`：前端传入游客兴趣，可为空数组

## 三、配置后端环境变量

复制示例配置：

```powershell
cd /d D:\ai-scenic-guide\services\api-server
copy .env.example .env
```

编辑 `.env`：

```text
GUIDE_ANSWER_PROVIDER=dify
GUIDE_DIFY_API_BASE_URL=https://api.dify.ai/v1
GUIDE_DIFY_API_KEY=你的Dify应用APIKey
GUIDE_DIFY_TIMEOUT_SECONDS=30
```

不要把 `.env` 提交到 Git。

## 四、启动并验证

启动后端：

```powershell
cd /d D:\ai-scenic-guide\services\api-server
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动前端：

```powershell
cd /d D:\ai-scenic-guide\apps\visitor-web
npm.cmd run dev
```

浏览器打开：

```text
http://localhost:5173/
```

建议测试问题：

- 黄山为什么有名？
- 黄山一日游路线怎么走？
- 从黄山北站怎么去黄山风景区？
- 西海大峡谷适合老人走吗？
- 黄山门票多少钱？
- 今天索道开了吗？

其中“门票多少钱”“今天索道开了吗”这类问题应触发强时效提醒，不应编造实时价格或开放状态。

## 五、可选：用脚本导入知识库

如果你希望用 Dify Knowledge API 批量导入 Markdown 文件，先在 Dify 中创建知识库并取得 Dataset ID，然后设置环境变量：

```powershell
$env:DIFY_KNOWLEDGE_API_KEY="你的Dify知识库APIKey"
$env:DIFY_DATASET_ID="你的DatasetID"
$env:DIFY_KNOWLEDGE_API_BASE_URL="https://api.dify.ai/v1"
```

运行：

```powershell
cd /d D:\ai-scenic-guide\services\api-server
.venv\Scripts\python.exe scripts\import_huangshan_knowledge.py
```

## 六、上线前检查

- Dify 应用回答是否带来源。
- 对强时效问题是否拒绝编造。
- 前端是否显示回答和来源标签。
- 后端 `.env` 是否没有提交到 Git。
- `GUIDE_ANSWER_PROVIDER=mock` 能否回退到第一阶段 Mock。

