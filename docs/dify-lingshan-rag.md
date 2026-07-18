# 灵山胜境知识库与 Dify RAG 接入说明

更新时间：2026-07-18

## 目标

将游客端原有 Mock Guide Service 切换为 Dify RAG。前端仍然调用原接口：

```http
POST /api/v1/chat
```

后端根据环境变量决定使用本地 Mock 还是 Dify：

- `GUIDE_ANSWER_PROVIDER=mock`：使用 `data/mock/faq.json`
- `GUIDE_ANSWER_PROVIDER=dify`：调用 Dify Chat App API

## 一、创建 Dify 知识库

在 Dify 控制台中创建知识库，建议名称：

```text
灵山胜境 AI 数字人导游知识库
```

如果使用 Dify 免费版，一次只能上传一个文件，直接上传这个合并文件：

```text
data/knowledge/lingshan/lingshan_dify_free_upload.md
```

拆分维护文件保留在 `data/knowledge/lingshan/00_source_index.md` 到 `05_visitor_insights.md`。后续维护时先改拆分文件，再同步更新单文件上传版。

建议索引方式：高质量索引。切分方式可先使用 Dify 自动切分，后续根据召回效果再调整。

## 二、创建 Dify 应用

在 Dify 中创建 Chatbot 或 Chatflow，并关联刚才创建的“灵山胜境 AI 数字人导游知识库”。

建议系统提示词：

```text
你是灵山胜境的 AI 数字人导游，服务对象是在景区终端或手机端咨询的游客。请优先基于知识库回答游客问题，语气亲切、稳妥、像现场导游。

回答要求：
1. 围绕灵山胜境主景区回答，重点覆盖灵山大佛、九龙灌浴、祥符禅寺、灵山梵宫、五印坛城、曼飞龙塔、无尽意斋等内容。
2. 游客问到夜游、禅意小镇、周边休闲时，可补充拈花湾禅意小镇信息，但要说明它是资料包中的联动休闲板块。
3. 根据游客兴趣推荐路线：历史文化、自然风光、亲子家庭、半日重点游。
4. 涉及门票价格、优惠政策、演出时间、开放时间、预约规则、交通管制、天气和临时闭馆等强时效信息时，不要编造实时结论，必须提示游客以景区官方小程序、当日广播、现场公告、游客中心或工作人员说明为准。
5. 景区具有佛教文化属性，回答要尊重宗教场所秩序，提醒游客保持安静、不随意触摸佛像和文物、不在禁止拍照区域拍照。
6. 若知识库没有可靠信息，请说明“暂未在灵山胜境资料中查询到可靠答案”，并建议咨询游客中心或现场工作人员。
```

建议输入变量：

- `scenic_area`：默认“灵山胜境”
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

- 灵山胜境为什么有名？
- 九龙灌浴和灵山大佛有什么看点？
- 第一次来灵山胜境半日游怎么走？
- 带老人孩子游览需要注意什么？
- 灵山梵宫和五印坛城有什么区别？
- 灵山胜境门票多少钱？
- 今天九龙灌浴表演几点开始？

其中“门票多少钱”“今天九龙灌浴表演几点开始”这类问题应触发强时效提醒，不应编造实时价格或开放状态。

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
.venv\Scripts\python.exe scripts\import_lingshan_knowledge.py
```

## 六、上线前检查

- Dify 应用回答是否带来源。
- 对强时效问题是否拒绝编造。
- 前端是否显示回答和来源标签。
- 后端 `.env` 是否没有提交到 Git。
- `GUIDE_ANSWER_PROVIDER=mock` 能否回退到本地兜底问答。

