import fs from "node:fs/promises";
import path from "node:path";
import { Presentation, PresentationFile } from "@oai/artifact-tool";

const OUT_DIR = "D:/ai-scenic-guide/deliverables";
const FINAL_PPTX = `${OUT_DIR}/AI景区数字人导游_方案介绍PPT.pptx`;
const PREVIEW_DIR = `${OUT_DIR}/rendered/ppt`;

const W = 1280;
const H = 720;
const colors = {
  ink: "#111827",
  muted: "#5B6472",
  line: "#CDD3DD",
  panel: "#F3F6FA",
  pale: "#F8FAFC",
  blue: "#2563EB",
  lightBlue: "#DBEAFE",
  green: "#12805C",
  lightGreen: "#DDF7EC",
  gold: "#8A6100",
  lightGold: "#FFF2CC",
};

function addText(slide, text, position, style = {}) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    position,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    fontSize: style.fontSize ?? 20,
    bold: style.bold ?? false,
    color: style.color ?? colors.ink,
    alignment: style.alignment ?? "left",
  };
  return shape;
}

function addBox(slide, position, fill = colors.panel, lineFill = colors.line) {
  return slide.shapes.add({
    geometry: "roundRect",
    position,
    fill,
    line: { style: "solid", fill: lineFill, width: 1 },
    borderRadius: "rounded-sm",
  });
}

function addRule(slide, left, top, width) {
  slide.shapes.add({
    geometry: "rect",
    position: { left, top, width, height: 2 },
    fill: colors.line,
    line: { style: "solid", fill: colors.line, width: 0 },
  });
}

function addFooter(slide, page) {
  addText(slide, "AI景区数字人导游｜灵山胜境示范版", { left: 56, top: 672, width: 520, height: 24 }, { fontSize: 13, color: colors.muted });
  addText(slide, String(page).padStart(2, "0"), { left: 1184, top: 672, width: 40, height: 24 }, { fontSize: 13, color: colors.muted, alignment: "right" });
}

function addHeader(slide, title, page, kicker = "方案介绍") {
  slide.background.fill = "white";
  addText(slide, kicker, { left: 56, top: 34, width: 360, height: 28 }, { fontSize: 15, bold: true, color: colors.blue });
  addText(slide, title, { left: 56, top: 76, width: 980, height: 58 }, { fontSize: 38, bold: true, color: colors.ink });
  addRule(slide, 56, 146, 1168);
  addFooter(slide, page);
}

function addBullets(slide, items, left, top, width, gap = 54, fontSize = 22) {
  items.forEach((item, idx) => {
    const y = top + idx * gap;
    slide.shapes.add({
      geometry: "ellipse",
      position: { left, top: y + 9, width: 10, height: 10 },
      fill: colors.blue,
      line: { style: "solid", fill: colors.blue, width: 0 },
    });
    addText(slide, item, { left: left + 24, top: y, width, height: 42 }, { fontSize, color: colors.ink });
  });
}

function addPill(slide, text, left, top, width, fill, color = colors.ink) {
  addBox(slide, { left, top, width, height: 44 }, fill, "none");
  addText(slide, text, { left: left + 14, top: top + 10, width: width - 28, height: 24 }, { fontSize: 17, bold: true, color, alignment: "center" });
}

function addStat(slide, value, label, left, top, width = 250, fill = colors.pale) {
  addBox(slide, { left, top, width, height: 120 }, fill);
  addText(slide, value, { left: left + 22, top: top + 22, width: width - 44, height: 42 }, { fontSize: 34, bold: true, color: colors.blue });
  addText(slide, label, { left: left + 22, top: top + 72, width: width - 44, height: 32 }, { fontSize: 17, color: colors.muted });
}

function slide1(presentation) {
  const slide = presentation.slides.add();
  slide.background.fill = "white";
  addText(slide, "AI景区数字人导游", { left: 72, top: 142, width: 820, height: 78 }, { fontSize: 58, bold: true });
  addText(slide, "灵山胜境示范版", { left: 72, top: 236, width: 620, height: 58 }, { fontSize: 42, bold: true, color: colors.blue });
  addText(slide, "面向游客交互与景区运营管理的一体化智能导览系统", { left: 72, top: 330, width: 720, height: 42 }, { fontSize: 24, color: colors.muted });
  addRule(slide, 72, 404, 620);
  addText(slide, "文字问答｜语音输入｜语音播报｜路线推荐｜数字人讲解｜知识库管理｜数据看板", { left: 72, top: 436, width: 940, height: 34 }, { fontSize: 20, color: colors.ink });
  addBox(slide, { left: 874, top: 112, width: 286, height: 386 }, colors.lightBlue, "none");
  addText(slide, "灵山胜境\nAI 导游终端", { left: 910, top: 210, width: 214, height: 120 }, { fontSize: 34, bold: true, color: colors.ink, alignment: "center" });
  addText(slide, "初赛方案介绍 PPT\n团队信息提交前填写", { left: 72, top: 612, width: 360, height: 48 }, { fontSize: 16, color: colors.muted });
}

function slide2(presentation) {
  const slide = presentation.slides.add();
  addHeader(slide, "景区导览正在从“讲解设备”变成“互动服务”", 2, "需求场景");
  addBullets(slide, [
    "旺季导游资源紧张，游客问题无法被及时、个性化响应。",
    "传统录音导览内容固定，难以回答实时路线、文化故事和服务问题。",
    "游客反馈分散在口头咨询和零散评价中，管理方缺少可量化洞察。",
    "比赛要求同时覆盖游客交互端和管理后台，形成服务与运营闭环。"
  ], 82, 206, 930, 76, 24);
  addBox(slide, { left: 904, top: 210, width: 236, height: 246 }, colors.lightGold, "none");
  addText(slide, "目标", { left: 936, top: 242, width: 172, height: 32 }, { fontSize: 25, bold: true, color: colors.gold, alignment: "center" });
  addText(slide, "7x24 在线\n懂灵山知识\n支持路线推荐\n能沉淀反馈", { left: 922, top: 300, width: 200, height: 116 }, { fontSize: 22, bold: true, color: colors.ink, alignment: "center" });
}

function slide3(presentation) {
  const slide = presentation.slides.add();
  addHeader(slide, "方案用一个闭环连接游客体验和景区运营", 3, "总体方案");
  const y = 218;
  const nodes = [
    ["游客端", "文本/语音提问\n数字人讲解", 74],
    ["FastAPI 后端", "统一接口\n日志与兜底", 324],
    ["Dify RAG", "灵山知识检索\n大模型回答", 574],
    ["管理后台", "知识维护\n报告与大屏", 824],
  ];
  nodes.forEach(([title, body, left]) => {
    addBox(slide, { left, top: y, width: 190, height: 160 }, colors.pale);
    addText(slide, title, { left: left + 18, top: y + 24, width: 154, height: 32 }, { fontSize: 24, bold: true, color: colors.blue, alignment: "center" });
    addText(slide, body, { left: left + 18, top: y + 72, width: 154, height: 68 }, { fontSize: 19, color: colors.ink, alignment: "center" });
  });
  [274, 524, 774].forEach((left) => {
    slide.shapes.add({
      geometry: "rightArrow",
      position: { left, top: y + 56, width: 54, height: 44 },
      fill: colors.line,
      line: { style: "solid", fill: colors.line, width: 0 },
    });
  });
  addText(slide, "游客问题、知识更新、交互日志和运营指标在同一套系统里流转。", { left: 104, top: 456, width: 920, height: 38 }, { fontSize: 24, bold: true, color: colors.ink, alignment: "center" });
}

function slide4(presentation) {
  const slide = presentation.slides.add();
  addHeader(slide, "当前原型已经覆盖游客端核心体验", 4, "产品展示");
  addStat(slide, "文字问答", "Dify RAG 返回答案和来源", 72, 212, 245);
  addStat(slide, "语音输入", "浏览器中文 ASR", 360, 212, 245, colors.lightGreen);
  addStat(slide, "语音播报", "浏览器 TTS 自动朗读", 648, 212, 245);
  addStat(slide, "数字人", "轻量动画 + SadTalker 可选", 936, 212, 245, colors.lightGreen);
  addBullets(slide, [
    "游客可通过推荐问题、文本框或麦克风提问。",
    "回答会自动带出灵山胜境知识、路线推荐和强时效提醒。",
    "展示模式适合景区触摸屏或比赛现场大屏演示。"
  ], 96, 414, 980, 58, 22);
}

function slide5(presentation) {
  const slide = presentation.slides.add();
  addHeader(slide, "灵山知识库让回答从泛化介绍变成景区讲解", 5, "知识库与 RAG");
  addBox(slide, { left: 72, top: 204, width: 488, height: 350 }, colors.pale);
  addText(slide, "知识来源", { left: 104, top: 234, width: 300, height: 32 }, { fontSize: 25, bold: true, color: colors.blue });
  addBullets(slide, [
    "主办方灵山胜境公开资料包",
    "景点结构化数据集",
    "历史文化与个性化游览指南",
    "旅游行为分析数据"
  ], 108, 296, 390, 50, 20);
  addBox(slide, { left: 638, top: 204, width: 488, height: 350 }, colors.pale);
  addText(slide, "回答规则", { left: 670, top: 234, width: 300, height: 32 }, { fontSize: 25, bold: true, color: colors.green });
  addBullets(slide, [
    "优先回答灵山胜境主景区",
    "路线推荐按历史、自然、亲子、半日游生成",
    "门票和演出等时效信息不编造",
    "尊重佛教文化场所礼仪"
  ], 674, 296, 390, 50, 20);
}

function slide6(presentation) {
  const slide = presentation.slides.add();
  addHeader(slide, "管理后台负责把系统变成可运营产品", 6, "管理后台");
  const items = [
    ["知识库管理", "上传文史资料、FAQ 和讲解词；同步 Dify；保留版本与回滚。"],
    ["数字人配置", "管理头像、服装风格、欢迎语、声音和 SadTalker 生成策略。"],
    ["游客感受度报告", "分析热门问题、关注景点、未命中问题、情绪趋势和服务建议。"],
    ["数据看板/数据大屏", "展示服务人次、热门问答、游客满意度趋势、平均停留和消费结构。"],
  ];
  items.forEach(([title, body], i) => {
    const left = i % 2 === 0 ? 82 : 656;
    const top = i < 2 ? 202 : 406;
    addBox(slide, { left, top, width: 468, height: 142 }, i % 2 === 0 ? colors.pale : colors.lightBlue);
    addText(slide, title, { left: left + 26, top: top + 24, width: 410, height: 30 }, { fontSize: 25, bold: true, color: colors.blue });
    addText(slide, body, { left: left + 26, top: top + 66, width: 406, height: 58 }, { fontSize: 19, color: colors.ink });
  });
}

function slide7(presentation) {
  const slide = presentation.slides.add();
  addHeader(slide, "旅游行为数据支撑管理侧洞察展示", 7, "测试数据");
  addStat(slide, "777", "灵山/拈花相关样例记录", 82, 206, 250);
  addStat(slide, "4.01h", "平均停留时长", 374, 206, 250, colors.lightGreen);
  addStat(slide, "916元", "平均总消费", 666, 206, 250);
  addStat(slide, "3-4分", "满意度主要集中区间", 958, 206, 250, colors.lightGold);
  addText(slide, "样例数据可用于后台数据看板：服务人次、热门问答、热门景点、游客满意度趋势、消费结构和运营建议。", { left: 96, top: 424, width: 1020, height: 42 }, { fontSize: 23, bold: true, color: colors.ink, alignment: "center" });
  addText(slide, "数据来源：主办方示范景区公开资料包《景点景区旅游数据行为分析数据.xlsx》。", { left: 96, top: 492, width: 1020, height: 30 }, { fontSize: 18, color: colors.muted, alignment: "center" });
}

function slide8(presentation) {
  const slide = presentation.slides.add();
  addHeader(slide, "技术选型强调可演示、可替换、可部署", 8, "核心技术");
  addBullets(slide, [
    "Vue 3 + Vite：快速构建游客端和后续管理后台。",
    "FastAPI：封装聊天、数字人、健康检查和未来后台接口。",
    "Dify RAG：灵山知识库增强回答，事实性问答准确率目标 >=90%。",
    "Web Speech API：低成本实现语音输入和语音播报。",
    "SadTalker：作为可选真实数字人引擎，生成口型视频。"
  ], 96, 194, 720, 64, 23);
  addPill(slide, "Dify 可替换", 860, 238, 220, colors.lightBlue, colors.blue);
  addPill(slide, "ASR/TTS 可升级", 860, 316, 220, colors.lightGreen, colors.green);
  addPill(slide, "语音问答<5秒", 860, 394, 220, colors.lightGold, colors.gold);
}

function slide9(presentation) {
  const slide = presentation.slides.add();
  addHeader(slide, "部署路径支持比赛演示，也能延伸到景区设备", 9, "部署方案");
  addBox(slide, { left: 92, top: 210, width: 300, height: 220 }, colors.pale);
  addText(slide, "本地演示", { left: 120, top: 246, width: 244, height: 32 }, { fontSize: 26, bold: true, color: colors.blue, alignment: "center" });
  addText(slide, "前端 5173\n后端 8000\nDify 公网 API", { left: 130, top: 306, width: 224, height: 82 }, { fontSize: 22, color: colors.ink, alignment: "center" });
  addBox(slide, { left: 490, top: 210, width: 300, height: 220 }, colors.lightGreen);
  addText(slide, "景区终端", { left: 518, top: 246, width: 244, height: 32 }, { fontSize: 26, bold: true, color: colors.green, alignment: "center" });
  addText(slide, "触摸屏全屏\n局域网后端\n定向麦克风", { left: 528, top: 306, width: 224, height: 82 }, { fontSize: 22, color: colors.ink, alignment: "center" });
  addBox(slide, { left: 888, top: 210, width: 300, height: 220 }, colors.lightGold);
  addText(slide, "增强部署", { left: 916, top: 246, width: 244, height: 32 }, { fontSize: 26, bold: true, color: colors.gold, alignment: "center" });
  addText(slide, "GPU 推理\n高频视频缓存\n离线兜底", { left: 926, top: 306, width: 224, height: 82 }, { fontSize: 22, color: colors.ink, alignment: "center" });
  addText(slide, "部署原则：先保证问答和语音稳定，再逐步增强真实数字人效果。", { left: 132, top: 494, width: 960, height: 34 }, { fontSize: 24, bold: true, color: colors.ink, alignment: "center" });
}

function slide10(presentation) {
  const slide = presentation.slides.add();
  addHeader(slide, "下一阶段重点补齐管理后台和提交演示闭环", 10, "计划与团队");
  addBullets(slide, [
    "开发 /admin 后台：知识库管理、数字人配置、游客感受度报告、数据看板/数据大屏。",
    "建立灵山标准问答测试集，验证事实性回答准确率和强时效兜底。",
    "预生成欢迎语和高频讲解数字人视频，提升演示稳定性。",
    "录制 7 分钟以内演示视频，覆盖游客端、管理后台和部署说明。",
    "团队信息：队名、成员、指导老师、分工可在提交前补充。"
  ], 98, 190, 970, 62, 23);
  addBox(slide, { left: 820, top: 510, width: 300, height: 70 }, colors.lightBlue, "none");
  addText(slide, "提交材料：代码 + 手册 + 设计文档 + PPT + 演示视频", { left: 844, top: 532, width: 252, height: 28 }, { fontSize: 18, bold: true, color: colors.blue, alignment: "center" });
}

async function writeBlob(file, blob) {
  await fs.writeFile(file, new Uint8Array(await blob.arrayBuffer()));
}

async function main() {
  await fs.mkdir(OUT_DIR, { recursive: true });
  await fs.mkdir(PREVIEW_DIR, { recursive: true });
  const presentation = Presentation.create({ slideSize: { width: W, height: H } });
  [slide1, slide2, slide3, slide4, slide5, slide6, slide7, slide8, slide9, slide10].forEach((fn) => fn(presentation));

  for (const [index, slide] of presentation.slides.items.entries()) {
    const png = await presentation.export({ slide, format: "png", scale: 1 });
    await writeBlob(path.join(PREVIEW_DIR, `slide-${String(index + 1).padStart(2, "0")}.png`), png);
    const layout = await slide.export({ format: "layout" });
    await fs.writeFile(path.join(PREVIEW_DIR, `slide-${String(index + 1).padStart(2, "0")}.layout.json`), await layout.text(), "utf-8");
  }
  const montage = await presentation.export({ format: "webp", montage: true, scale: 1 });
  await writeBlob(path.join(PREVIEW_DIR, "deck-montage.webp"), montage);

  const pptx = await PresentationFile.exportPptx(presentation);
  await pptx.save(FINAL_PPTX);
  console.log(FINAL_PPTX);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
