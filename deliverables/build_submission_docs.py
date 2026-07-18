from __future__ import annotations

from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "deliverables"
TODAY = date.today().strftime("%Y-%m-%d")

BLUE = RGBColor(46, 116, 181)
DARK_BLUE = RGBColor(31, 77, 120)
INK = RGBColor(20, 27, 36)
MUTED = RGBColor(90, 96, 108)
LIGHT_BLUE = "E8EEF5"
LIGHT_GRAY = "F2F4F7"
PALE_GREEN = "EAF4EF"
PALE_GOLD = "FFF4D6"


def set_font(run, size: float | None = None, bold: bool | None = None, color: RGBColor | None = None) -> None:
    run.font.name = "Microsoft YaHei"
    run._element.rPr.rFonts.set(qn("w:ascii"), "Microsoft YaHei")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "Microsoft YaHei")
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_text(cell, text: str, bold: bool = False, color: RGBColor | None = None) -> None:
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.15
    r = p.add_run(text)
    set_font(r, size=9.5, bold=bold, color=color or INK)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def set_table_width(table, widths: list[float]) -> None:
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    for row in table.rows:
        for idx, width in enumerate(widths):
            row.cells[idx].width = Inches(width)


def add_table(doc: Document, headers: list[str], rows: list[list[str]], widths: list[float]) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    set_table_width(table, widths)
    for idx, text in enumerate(headers):
        cell = table.rows[0].cells[idx]
        set_cell_shading(cell, LIGHT_BLUE)
        set_cell_text(cell, text, bold=True, color=DARK_BLUE)
    for row_data in rows:
        row = table.add_row()
        for idx, text in enumerate(row_data):
            set_cell_text(row.cells[idx], text)
    doc.add_paragraph()


def add_kv_table(doc: Document, rows: list[tuple[str, str]], fill: str = LIGHT_GRAY) -> None:
    table = doc.add_table(rows=0, cols=2)
    table.style = "Table Grid"
    set_table_width(table, [1.6, 4.9])
    for label, value in rows:
        row = table.add_row()
        set_cell_shading(row.cells[0], fill)
        set_cell_text(row.cells[0], label, bold=True, color=DARK_BLUE)
        set_cell_text(row.cells[1], value)
    doc.add_paragraph()


def add_para(doc: Document, text: str = "", style: str | None = None, bold: bool = False, color: RGBColor | None = None) -> None:
    p = doc.add_paragraph(style=style)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.15
    r = p.add_run(text)
    set_font(r, size=11, bold=bold, color=color or INK)


def add_bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(item)
        set_font(r, size=10.5, color=INK)


def add_numbers(doc: Document, items: list[str]) -> None:
    for item in items:
        p = doc.add_paragraph(style="List Number")
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.15
        r = p.add_run(item)
        set_font(r, size=10.5, color=INK)


def add_callout(doc: Document, title: str, body: str, fill: str = PALE_GOLD) -> None:
    table = doc.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    set_table_width(table, [6.5])
    cell = table.rows[0].cells[0]
    set_cell_shading(cell, fill)
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    rt = p.add_run(title)
    set_font(rt, size=10.5, bold=True, color=DARK_BLUE)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    rb = p2.add_run(body)
    set_font(rb, size=10, color=INK)
    doc.add_paragraph()


def add_heading(doc: Document, text: str, level: int = 1) -> None:
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        set_font(run, bold=True, color=BLUE if level <= 2 else DARK_BLUE)


def setup_doc(title: str, subtitle: str, preset: str) -> Document:
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)
    section.header_distance = Inches(0.49)
    section.footer_distance = Inches(0.49)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(11)
    normal.font.color.rgb = INK
    for name, size, color in [("Heading 1", 16, BLUE), ("Heading 2", 13, BLUE), ("Heading 3", 12, DARK_BLUE)]:
        style = styles[name]
        style.font.name = "Microsoft YaHei"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = color

    header = section.header.paragraphs[0]
    header.text = f"{title} | {preset}"
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for run in header.runs:
        set_font(run, size=8.5, color=MUTED)

    footer = section.footer.paragraphs[0]
    footer.text = "AI景区数字人导游 灵山胜境示范版"
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in footer.runs:
        set_font(run, size=8.5, color=MUTED)

    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_after = Pt(4)
    run = title_p.add_run(title)
    set_font(run, size=24, bold=True, color=RGBColor(0, 0, 0))
    sub_p = doc.add_paragraph()
    sub_p.paragraph_format.space_after = Pt(14)
    sub = sub_p.add_run(subtitle)
    set_font(sub, size=12.5, color=MUTED)
    add_kv_table(
        doc,
        [
            ("项目名称", "AI景区数字人导游软件"),
            ("示范景区", "灵山胜境"),
            ("版本日期", TODAY),
            ("适用对象", "评审专家、部署人员、景区运营管理人员、演示人员"),
        ],
    )
    return doc


def build_manual() -> Path:
    doc = setup_doc(
        "AI景区数字人导游部署和使用手册",
        "灵山胜境示范版 | 覆盖游客交互端、管理后台、Dify 知识库和数字人引擎",
        "compact_reference_guide",
    )

    add_heading(doc, "1. 文档目的与系统范围")
    add_para(doc, "本文档说明 AI 景区数字人导游软件在本地开发环境、比赛演示环境和景区终端设备上的部署、配置、启动、验证和使用方法。系统围绕灵山胜境示范景区建设，覆盖游客交互端和管理后台两类使用场景。")
    add_table(
        doc,
        ["端侧", "功能范围", "使用对象"],
        [
            ["游客交互端", "文字问答/文本问答、语音输入、语音播报、个性化路线推荐、数字人形象展示、可选 SadTalker 讲解视频", "游客、讲解员、评审演示人员"],
            ["管理后台", "知识库管理、数字人配置（形象、声音与生成策略）、游客感受度报告、数据看板/数据大屏概览", "景区管理员、运营人员、内容维护人员"],
            ["AI 能力层", "Dify RAG、灵山胜境知识库、浏览器 ASR/TTS、SadTalker 数字人视频生成", "系统部署和维护人员"],
        ],
        [1.25, 3.65, 1.6],
    )
    add_callout(doc, "实现状态说明", "当前仓库已完成游客端、Dify RAG、语音输入、语音播报、轻量数字人和 SadTalker 可选接入。管理后台作为比赛目标版本的重要组成部分，本文档给出部署与使用流程，后续开发可按总体设计文档落地。", fill=PALE_GREEN)
    add_table(
        doc,
        ["目标类别", "比赛要求覆盖", "本文档落地说明"],
        [
            ["游客交互侧", "文字问答/文本输入、语音输入、语音播报、数字人表情、口型同步、情感互动、个性化路线推荐。", "第 5-8 章说明前后端启动、Dify 问答、浏览器语音和数字人展示方式。"],
            ["管理后台侧", "知识库管理、数字人配置/数字人形象管理、游客感受度报告、数据看板/数据大屏概览。", "第 9 章说明目标后台使用流程，当前可先通过 Dify 控制台、知识库文件和日志数据演示。"],
            ["非功能指标", "构建本地景区知识库；事实性问答准确率目标不低于 90%；语音问答延迟目标控制在 5 秒内；系统稳定可演示。", "第 4 章说明本地知识库接入，第 10 章给出验收测试，第 11 章给出设备部署建议。"],
        ],
        [1.25, 3.1, 2.15],
    )

    add_heading(doc, "2. 环境要求")
    add_table(
        doc,
        ["类别", "推荐配置", "说明"],
        [
            ["操作系统", "Windows 10/11", "本地开发和演示按 Windows 路径编写，Linux 部署需替换路径和启动脚本。"],
            ["前端", "Node.js 22 LTS 或兼容版本，npm 10+", "Vue 3 + Vite 项目。PowerShell 限制时使用 npm.cmd。"],
            ["后端", "Python 3.12，FastAPI，Uvicorn", "后端虚拟环境位于 services/api-server/.venv。"],
            ["RAG 平台", "Dify Chat App", "免费版可上传单个合并 Markdown 知识库文件。"],
            ["浏览器", "Chrome 或 Edge", "语音识别和语音播报依赖浏览器 Web Speech API。"],
            ["数字人", "SadTalker，可选 NVIDIA GPU", "真实视频生成较慢，正式演示建议预生成高频问答视频。"],
        ],
        [1.25, 2.2, 3.05],
    )

    add_heading(doc, "3. 目录与配置文件")
    add_para(doc, "项目根目录为 D:\\ai-scenic-guide。核心目录如下：")
    add_bullets(
        doc,
        [
            "apps/visitor-web：游客交互端 Vue 应用。",
            "services/api-server：FastAPI 后端服务和接口测试。",
            "data/knowledge/lingshan：灵山胜境本地知识库维护文件。",
            "data/avatar：数字人形象图片资源。",
            "data/generated：SadTalker 生成结果目录，已加入 .gitignore。",
            "deliverables：比赛提交文档和 PPT 输出目录。",
        ],
    )
    add_table(
        doc,
        ["环境变量", "示例值", "作用"],
        [
            ["GUIDE_ANSWER_PROVIDER", "dify 或 mock", "切换 Dify RAG 或本地兜底问答。"],
            ["GUIDE_DIFY_API_BASE_URL", "https://api.dify.ai/v1", "Dify Chat App API 地址。"],
            ["GUIDE_DIFY_API_KEY", "你的应用 API Key", "后端访问 Dify 应用的凭证，不提交到 Git。"],
            ["GUIDE_AVATAR_PROVIDER", "disabled 或 sadtalker", "切换轻量数字人和真实视频数字人。"],
            ["GUIDE_SADTALKER_ROOT", "D:\\ai-scenic-guide-engines\\SadTalker", "SadTalker 独立安装目录。"],
            ["GUIDE_SADTALKER_SOURCE_IMAGE", "D:\\ai-scenic-guide\\data\\avatar\\guide-avatar.png", "SadTalker 使用的导游形象图。"],
        ],
        [2.0, 2.35, 2.15],
    )

    add_heading(doc, "4. Dify 知识库配置")
    add_numbers(
        doc,
        [
            "进入 Dify 控制台，创建知识库，建议名称为“灵山胜境 AI 数字人导游知识库”。",
            "上传 data/knowledge/lingshan/lingshan_dify_free_upload.md。免费版一次只能上传一个文件时，直接使用该合并文件。",
            "创建 Chatbot 或 Chatflow，并关联该知识库。",
            "在应用提示词中设置灵山胜境导游身份、强时效信息提醒、佛教文化礼仪提醒和个性化路线推荐规则。",
            "复制 Dify 应用 API Key，写入 services/api-server/.env。",
        ],
    )
    add_callout(doc, "强时效规则", "门票、优惠、演出时间、开放时间、交通管制、天气和临时闭馆不可编造实时结论，必须提示以官方小程序、现场公告、游客中心或工作人员说明为准。")

    add_heading(doc, "5. 后端启动")
    add_numbers(
        doc,
        [
            "打开命令行，进入 D:\\ai-scenic-guide\\services\\api-server。",
            "首次部署时创建并激活虚拟环境，执行 pip install -r requirements.txt。",
            "确认 .env 中 GUIDE_ANSWER_PROVIDER=dify，且 GUIDE_DIFY_API_KEY 已填写。",
            "执行 .venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000。",
            "打开 http://127.0.0.1:8000/api/v1/health，返回 status=ok 即后端可用。",
        ],
    )

    add_heading(doc, "6. 前端启动")
    add_numbers(
        doc,
        [
            "打开新命令行，进入 D:\\ai-scenic-guide\\apps\\visitor-web。",
            "首次部署时执行 npm.cmd install。",
            "开发演示执行 npm.cmd run dev。",
            "浏览器打开 http://localhost:5173。",
            "生产构建执行 npm.cmd run build，生成 dist 静态文件，可交由 Nginx 或景区终端本地 Web 服务托管。",
        ],
    )

    add_heading(doc, "7. SadTalker 数字人部署")
    add_para(doc, "SadTalker 作为独立引擎安装在项目外部，避免把源码、模型权重和生成视频提交到业务仓库。推荐路径为 D:\\ai-scenic-guide-engines\\SadTalker。")
    add_bullets(
        doc,
        [
            "安装 SadTalker 依赖和模型权重后，配置 GUIDE_AVATAR_PROVIDER=sadtalker。",
            "配置 GUIDE_SADTALKER_PYTHON 指向 SadTalker 的 Python 环境。",
            "配置 GUIDE_SADTALKER_PREPROCESS=full 时需确保相关模型权重完整。",
            "访问 http://127.0.0.1:8000/api/v1/avatar/status 验证真实数字人是否可用。",
            "正式演示建议只对欢迎语和高频讲解词使用真实视频，其他回答使用轻量嘴型动画兜底。",
        ],
    )

    add_heading(doc, "8. 游客端使用流程")
    add_numbers(
        doc,
        [
            "进入游客端首页，查看灵山胜境数字人导游形象。",
            "点击推荐问题，例如“灵山胜境有哪些必看景点？”或手动输入问题。",
            "需要语音输入时点击麦克风，允许浏览器使用麦克风，说出问题。",
            "开启“识别后发送”后，语音识别结果会自动提交。",
            "开启“自动播报”后，导游回答会自动朗读。",
            "如果 SadTalker 可用，可打开“真实数字人”开关，等待生成并播放讲解视频。",
        ],
    )

    add_heading(doc, "9. 管理后台使用流程")
    add_para(doc, "管理后台面向景区运营方，用于把游客交互数据转化为内容维护和服务优化动作。目标版本建议提供 /admin 入口和管理员登录。")
    add_table(
        doc,
        ["后台模块", "主要操作", "产出结果"],
        [
            ["知识库管理", "上传讲解词、文史资料、常见问答；维护灵山胜境知识文件；同步到 Dify 知识库。", "可追溯的知识版本、更新记录和上线状态。"],
            ["数字人配置", "上传导游形象图，配置服装风格、欢迎语、声音、SadTalker 开关和生成策略。", "更贴合灵山佛教文化与景区终端展示的数字人形象。"],
            ["游客感受度报告", "分析问答记录、关注点、情绪倾向、未命中问题和投诉建议。", "周报/月报、热门诉求、服务改进建议。"],
            ["数据看板/数据大屏概览", "展示服务人次、热门问答、热门景点、游客满意度趋势、平均停留和消费结构。", "运营态势看板和管理决策依据。"],
        ],
        [1.45, 3.15, 1.9],
    )
    add_callout(doc, "后台当前替代操作", "在管理后台尚未完全编码前，知识库维护可先通过 data/knowledge/lingshan 文件和 Dify 控制台完成；游客洞察可先使用 05_visitor_insights.md 和日志统计作为演示数据源。")

    add_heading(doc, "10. 验收测试")
    add_table(
        doc,
        ["测试项", "测试问题或动作", "期望结果"],
        [
            ["知识问答", "灵山胜境为什么有名？", "回答包含太湖马山、小灵山缘起、灵山大佛、梵宫或世界佛教论坛等要点。"],
            ["路线推荐", "带老人孩子游览怎么安排？", "推荐亲子/轻松路线，并提醒观光车、体力和安全。"],
            ["时效兜底", "今天九龙灌浴几点开始？", "可给资料参考时间，但必须提醒以当日公告为准。"],
            ["语音输入", "点击麦克风并说出问题", "输入框出现识别文本，可自动或手动发送。"],
            ["数字人", "开启自动播报或真实数字人", "轻量嘴型动画或 SadTalker 视频随回答展示。"],
            ["后台演示", "查看知识库、游客报告、数据看板/大屏设计", "能说明内容维护、数字人配置、反馈分析和运营指标闭环。"],
        ],
        [1.35, 2.4, 2.75],
    )

    add_heading(doc, "11. 景区设备部署建议")
    add_bullets(
        doc,
        [
            "触摸屏或一体机使用 Chrome/Edge 全屏模式，固定打开游客端地址。",
            "后端可部署在本机或局域网服务器，前端 API 地址指向后端内网 IP。",
            "现场噪声较大时使用定向麦克风，并在浏览器中提前授予麦克风权限。",
            "高频问答建议预生成语音或数字人视频，减少游客等待。",
            "断网时保留 mock 兜底问答，避免终端完全不可用。",
        ],
    )

    out = OUT / "AI景区数字人导游_部署和使用手册.docx"
    doc.save(out)
    return out


def build_design_doc() -> Path:
    doc = setup_doc(
        "AI景区数字人导游产品总体设计文档",
        "灵山胜境示范版 | 面向游客交互端与景区管理后台的一体化设计",
        "standard_business_brief",
    )

    add_heading(doc, "1. 项目背景与建设目标")
    add_para(doc, "国家持续推进文旅产业数字化转型，传统景区导览存在导游资源紧张、讲解内容固定、互动能力不足、游客反馈难以量化等问题。本项目以灵山胜境为示范景区，构建具备文字、语音、表情、口型同步、情感互动和知识库问答能力的 AI 数字人导游系统，同时为景区管理方提供知识维护、数字人形象管理、游客感受度分析和数据看板能力。")
    add_bullets(
        doc,
        [
            "游客侧目标：实时智能问答、个性化路线推荐、语音输入输出、数字人表情和口型同步展示。",
            "管理侧目标：知识库管理、数字人配置/数字人形象管理、游客感受度报告、数据看板/数据大屏概览。",
            "技术目标：至少使用一个可 API 调用的大模型/RAG 平台，构建本地灵山胜境知识库，事实性问答准确率目标不低于 90%，语音问答延迟目标控制在 5 秒内。",
        ],
    )

    add_heading(doc, "2. 需求范围")
    add_table(
        doc,
        ["需求类别", "功能要求", "设计响应"],
        [
            ["多模态交互", "支持语音输入、文本输入，数字人以语音、表情、口型同步方式回答。", "前端集成 Web Speech ASR/TTS、轻量数字人动画和 SadTalker 可选视频。"],
            ["智能问答", "准确回答历史、文化、景点特色等问题。", "Dify RAG 关联灵山胜境本地知识库，后端统一封装问答接口。"],
            ["个性化推荐", "按历史、自然、亲子等兴趣推荐路线。", "前端提取兴趣标签，Dify 提示词和知识库提供路线模板。"],
            ["知识库管理", "管理员上传、更新和维护讲解词、文史资料、FAQ。", "目标后台提供文档上传、版本记录、Dify 同步状态和回滚能力。"],
            ["数字人配置/数字人形象管理", "配置外观、服装、声音，使其贴合景区文化。", "目标后台提供头像图、欢迎语、声音、SadTalker 策略和预生成视频管理。"],
            ["游客感受度报告", "分析交互记录、关注点、情绪趋势和建议。", "目标后台基于问答日志和满意度数据生成周报/月报。"],
            ["数据看板/数据大屏概览", "展示服务人次、热门问答、游客满意度趋势等。", "目标后台展示实时服务指标和样例行为数据洞察。"],
        ],
        [1.35, 2.35, 2.8],
    )

    add_heading(doc, "3. 总体架构")
    add_para(doc, "系统采用前后端分离架构。游客端和管理后台通过 HTTP 调用 FastAPI 后端；后端统一封装 Dify RAG、Mock 兜底、SadTalker 数字人生成、日志与运营数据服务。知识库以灵山胜境资料为核心，Dify 负责检索增强生成，后端负责稳定接口、错误兜底和审计日志。")
    add_table(
        doc,
        ["层级", "组件", "职责"],
        [
            ["终端展示层", "游客端 Vue 应用、管理后台 Vue 应用、景区大屏", "提供游客问答、语音交互、数字人展示和运营管理界面。"],
            ["业务 API 层", "FastAPI 服务", "统一处理聊天、数字人、知识库、报表、配置和健康检查接口。"],
            ["AI 能力层", "Dify RAG、Web Speech、SadTalker", "完成知识问答、语音识别/合成、口型视频生成。"],
            ["数据资源层", "灵山知识库、问答日志、游客反馈、行为数据", "为问答准确性、路线推荐和管理洞察提供数据基础。"],
            ["部署运行层", "本地 PC、景区终端、可选 GPU 推理机", "支撑比赛演示和景区设备部署。"],
        ],
        [1.2, 2.15, 3.15],
    )

    add_heading(doc, "4. 游客交互端设计")
    add_bullets(
        doc,
        [
            "对话问答：游客输入问题后，前端调用 POST /api/v1/chat，后端返回回答、来源、情绪、延迟和兜底标记。",
            "语音输入：浏览器麦克风识别中文语音，可自动发送或填入输入框后人工确认。",
            "语音播报：浏览器 TTS 朗读导游回答，可播放、暂停、继续和重播。",
            "数字人展示：轻量模式显示待机、聆听、检索、讲解状态；SadTalker 模式生成真实讲解视频。",
            "路线推荐：根据“历史文化、自然风光、亲子家庭、半日游”等兴趣提供灵山胜境路线。",
        ],
    )

    add_heading(doc, "5. 管理后台设计")
    add_para(doc, "管理后台是本赛题管理侧评分的关键模块，目标是让景区方能持续运营 AI 导游，而不是只做一次性演示。后台建议采用与游客端同源的 Vue 管理应用，后端增加 /api/v1/admin/* 接口。")
    add_table(
        doc,
        ["模块", "核心页面", "关键数据"],
        [
            ["知识库管理", "文档列表、上传更新、切分预览、同步 Dify、版本回滚", "knowledge_documents、dataset_sync_jobs、source_files"],
            ["数字人配置", "头像/半身像上传、声音选择、欢迎语、SadTalker 生成策略", "avatar_profiles、voice_profiles、avatar_jobs"],
            ["游客感受度报告", "热门问题、关注景点、未命中问题、情绪趋势、服务建议", "chat_messages、feedback_records、sentiment_reports"],
            ["数据看板/数据大屏概览", "服务人次、热门问答、游客满意度趋势、平均停留、消费结构", "dashboard_metrics、visitor_behavior_samples"],
            ["系统配置", "Dify Key 检查、CORS、接口健康、日志下载", "app_settings、health_checks、audit_logs"],
        ],
        [1.35, 3.2, 1.95],
    )

    add_heading(doc, "6. 灵山胜境知识库与 RAG 设计")
    add_para(doc, "知识库来自主办方示范景区公开资料包，已整理为维护版 Markdown 和 Dify 免费版单文件。内容覆盖灵山历史文化、核心景点、路线、服务提醒、游客行为洞察。")
    add_table(
        doc,
        ["知识主题", "内容", "回答策略"],
        [
            ["概况历史", "太湖马山、小灵山缘起、祥符禅寺、现代灵山建设", "回答“为什么有名”“历史故事”等问题。"],
            ["核心景点", "灵山大佛、九龙灌浴、梵宫、五印坛城、祥符禅寺等", "回答景点特色和讲解词。"],
            ["路线推荐", "历史文化、自然风光、亲子家庭、半日游", "按游客兴趣和体力推荐顺路路线。"],
            ["服务提醒", "演出、票务、餐饮、住宿、文明游览", "强时效信息必须提醒以官方公告为准。"],
            ["游客洞察", "777 条灵山/拈花相关行为样例", "支撑管理后台大屏和感受度报告。"],
        ],
        [1.4, 2.75, 2.35],
    )

    add_heading(doc, "7. 数字人与多模态设计")
    add_para(doc, "系统采用“稳定交互优先、真实数字人增强”的策略：基础体验使用浏览器语音和轻量动画保证低延迟；高价值演示或高频讲解使用 SadTalker 生成真实视频，提高自然度和展示效果。")
    add_bullets(
        doc,
        [
            "ASR：浏览器 Web Speech Recognition，语言设置为 zh-CN。",
            "TTS：浏览器 Web Speech Synthesis，避免额外语音服务成本。",
            "轻量数字人：CSS/组件动画表现待机、聆听、思考、讲解状态。",
            "SadTalker：后端生成 mp4，支持缓存，建议 GPU 或预生成高频视频。",
            "兜底策略：真实视频生成失败时不影响文字问答和轻量播报。",
        ],
    )

    add_heading(doc, "8. 后端接口设计")
    add_table(
        doc,
        ["接口", "方法", "用途"],
        [
            ["/api/v1/health", "GET", "健康检查，用于部署验证和监控。"],
            ["/api/v1/chat", "POST", "游客问答入口，返回 answer、sources、emotion、latency_ms、fallback。"],
            ["/api/v1/avatar/status", "GET", "检查 SadTalker 数字人生成能力是否可用。"],
            ["/api/v1/avatar/video", "POST", "根据回答文本生成数字人讲解视频。"],
            ["/api/v1/admin/knowledge", "GET/POST", "目标后台知识库列表、上传和同步。"],
            ["/api/v1/admin/avatar", "GET/PUT", "目标后台数字人形象和声音配置。"],
            ["/api/v1/admin/reports", "GET", "目标后台游客感受度报告。"],
            ["/api/v1/admin/dashboard", "GET", "目标后台数据看板/数据大屏指标。"],
        ],
        [2.0, 0.9, 3.6],
    )

    add_heading(doc, "9. 数据设计")
    add_table(
        doc,
        ["数据表/文件", "字段示例", "用途"],
        [
            ["chat_sessions", "session_id、device_id、created_at、last_active_at", "记录游客会话。"],
            ["chat_messages", "message_id、session_id、role、content、latency_ms、fallback", "分析热门问题、未命中问题和服务质量。"],
            ["feedback_records", "message_id、rating、sentiment、comment、created_at", "生成游客感受度报告。"],
            ["knowledge_documents", "doc_id、name、version、status、updated_by", "后台管理知识库版本。"],
            ["avatar_profiles", "profile_id、image_path、voice_name、provider、enabled", "后台管理数字人形象和声音。"],
            ["visitor_behavior_samples", "attraction_name、stay_duration、total_cost、satisfaction", "支撑数据看板/数据大屏和样例洞察。"],
        ],
        [1.7, 2.5, 2.3],
    )

    add_heading(doc, "10. 部署与运行设计")
    add_bullets(
        doc,
        [
            "本地演示：前端 Vite 运行在 5173，后端 FastAPI 运行在 8000，Dify 通过公网 API 调用。",
            "景区终端：前端可构建为静态文件，后端部署在本机或局域网服务器，触摸屏全屏打开游客端。",
            "GPU 推理：SadTalker 可部署在独立 GPU 机器，后端通过本地进程或未来的推理服务调用。",
            "断网保障：Dify 不可用时后端可切换 mock 兜底，至少保持基础问答与提示。",
            "内容更新：后台上传知识文件后同步 Dify，保留版本和回滚记录。",
        ],
    )

    add_heading(doc, "11. 质量保障")
    add_table(
        doc,
        ["质量目标", "保障措施"],
        [
            ["事实准确率", "建立灵山胜境标准问题集；强时效信息统一提醒官方公告；Dify 回答保留来源；目标事实性问答准确率不低于 90%。"],
            ["响应稳定性", "FastAPI 统一错误结构、超时控制、Dify 失败兜底、前端加载状态；语音问答延迟目标控制在 5 秒内。"],
            ["交互自然度", "语音输入、语音播报、轻量嘴型、SadTalker 视频和展示模式配合。"],
            ["数据安全", ".env 不提交 Git；API Key 仅在后端使用；日志避免记录敏感凭证。"],
            ["可部署性", "前后端独立启动，静态构建可托管，生成视频和模型权重不入仓库。"],
        ],
        [1.55, 4.95],
    )

    add_heading(doc, "12. 实现状态与后续计划")
    add_table(
        doc,
        ["模块", "当前状态", "下一步"],
        [
            ["游客端文字问答", "已实现", "补充更多灵山标准测试问题。"],
            ["Dify RAG", "已接入并更新灵山知识库", "观察召回效果并优化切分。"],
            ["语音输入/播报", "已实现浏览器方案", "评估生产级 ASR/TTS 服务。"],
            ["数字人", "轻量动画已实现，SadTalker 可选接入", "预生成高频讲解视频，优化口型稳定性。"],
            ["管理后台", "总体设计已纳入目标版本", "开发 /admin 页面、日志存储、报表和大屏接口。"],
            ["提交材料", "部署手册、设计文档、PPT 本次生成", "录制 7 分钟以内演示视频。"],
        ],
        [1.4, 2.4, 2.7],
    )

    add_heading(doc, "13. 评分项对应关系")
    add_table(
        doc,
        ["评分项", "对应设计"],
        [
            ["功能完整度", "游客端多模态交互 + 管理后台知识库管理、数字人配置、游客感受度报告、数据看板设计。"],
            ["技术与创新性", "Dify RAG、本地知识库、SadTalker、浏览器语音、数字人状态联动。"],
            ["行业实用与体验性", "围绕导游资源、个性化问答、路线推荐、游客反馈闭环解决真实痛点。"],
            ["文档质量", "提供部署使用手册、总体设计文档、方案介绍 PPT 和后续演示视频脚本基础。"],
        ],
        [1.55, 4.95],
    )

    out = OUT / "AI景区数字人导游_产品总体设计文档.docx"
    doc.save(out)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manual = build_manual()
    design = build_design_doc()
    print(manual)
    print(design)


if __name__ == "__main__":
    main()
