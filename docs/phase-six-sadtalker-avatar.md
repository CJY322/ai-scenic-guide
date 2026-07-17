# 第六阶段：SadTalker 真实数字人接入

本阶段把“轻量数字人动画”升级为可选的 SadTalker 真实讲解视频生成能力。

当前仓库不会直接内置 SadTalker 源码、模型权重和生成结果。原因是 SadTalker 依赖 PyTorch、ffmpeg 和大模型权重，体积较大，直接提交到业务仓库会影响 GitHub 推送和景区设备部署。推荐把 SadTalker 作为独立引擎安装，然后由本项目后端调用。

## 实现方式

前端流程：

```text
游客提问 -> Dify RAG 回答 -> 后端 SadTalker 生成 mp4 -> 前端播放真实数字人视频
```

后端新增接口：

- `GET /api/v1/avatar/status`：检查真实数字人是否可用。
- `POST /api/v1/avatar/video`：把导游回答文本生成数字人讲解视频。

默认情况下 `GUIDE_AVATAR_PROVIDER=disabled`，页面仍然使用原来的轻量数字人，不影响问答、语音输入和浏览器播报。

## 安装 SadTalker

建议把 SadTalker 放在项目外部，避免误提交到 GitHub：

```powershell
cd /d D:\
mkdir ai-scenic-guide-engines
cd /d D:\ai-scenic-guide-engines
git clone https://github.com/OpenTalker/SadTalker.git
```

进入 `D:\ai-scenic-guide-engines\SadTalker` 后，按照 SadTalker 官方 README 安装 Python 依赖、ffmpeg 和模型权重。

建议使用独立虚拟环境：

```powershell
cd /d D:\ai-scenic-guide-engines\SadTalker
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

模型权重请按 SadTalker 官方说明下载到它要求的目录。没有权重时，本项目接口会返回“生成失败”。

## 准备导游形象图

放一张正脸导游形象图，例如：

```text
D:\ai-scenic-guide\data\avatar\huangshan-guide.png
```

建议图片要求：

- 单人正脸或半身像。
- 脸部清晰，无遮挡。
- 背景干净。
- 不要使用未授权真人肖像。

## 配置后端 `.env`

编辑：

```text
D:\ai-scenic-guide\services\api-server\.env
```

加入或修改：

```text
GUIDE_AVATAR_PROVIDER=sadtalker
GUIDE_GENERATED_ASSETS_PATH=D:\ai-scenic-guide\data\generated
GUIDE_SADTALKER_ROOT=D:\ai-scenic-guide-engines\SadTalker
GUIDE_SADTALKER_PYTHON=D:\ai-scenic-guide-engines\SadTalker\.venv\Scripts\python.exe
GUIDE_SADTALKER_SOURCE_IMAGE=D:\ai-scenic-guide\data\avatar\huangshan-guide.png
GUIDE_SADTALKER_TIMEOUT_SECONDS=300
GUIDE_SADTALKER_PREPROCESS=full
GUIDE_SADTALKER_STILL=true
```

保留你原来的 Dify 配置：

```text
GUIDE_ANSWER_PROVIDER=dify
GUIDE_DIFY_API_BASE_URL=https://api.dify.ai/v1
GUIDE_DIFY_API_KEY=你的Dify应用APIKey
```

## 启动与验证

启动后端：

```powershell
cd /d D:\ai-scenic-guide\services\api-server
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

访问：

```text
http://127.0.0.1:8000/api/v1/avatar/status
```

如果配置正确，会看到：

```json
{
  "enabled": true,
  "provider": "sadtalker",
  "supports_video": true,
  "message": "SadTalker 已配置"
}
```

启动前端：

```powershell
cd /d D:\ai-scenic-guide\apps\visitor-web
npm.cmd run dev
```

打开：

```text
http://localhost:5173
```

如果 `avatar/status` 可用，页面顶部会出现“真实数字人”开关。打开后，新的导游回答会生成并播放 SadTalker 视频。

## 注意事项

- SadTalker 不是实时数字人。CPU 生成可能很慢，建议使用带 NVIDIA GPU 的电脑或单独的推理服务器。
- 首次生成会更慢；相同文本会命中本项目的 mp4 缓存。
- 生成视频保存在 `data/generated/avatar/`，该目录已加入 `.gitignore`，不要提交到 GitHub。
- 当前版本用 Windows SAPI 把文本转成 wav，再交给 SadTalker。景区设备如果没有中文系统语音，声音效果会受影响。
- 如果以后要接第二个数字人项目，可以继续复用现在的 `/api/v1/avatar/*` 接口，不需要重做前端问答。
