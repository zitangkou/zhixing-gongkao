# 国考行测扫描真题 PDF 解析工作流

> 适用：扫描版（无文字层）国家公务员考试《行政职业能力测验》真题 PDF
> 目标：产出可机读、可扩展、可展示的结构化 JSON + 媒体资源，支持省级 / 市地级 / 行政执法类三卷差异
> 本文件由原 `WORKFLOW.md` 与详细版手册（原 `WORKFLOW_副本.md`）合并而成，是**唯一权威流程文档**

---

## 1. 目标与核心原则

### 1.1 目标

将扫描 PDF 解析为结构化 JSON，完整保留题干、选项、材料、图形/表格/公式引用；以省级卷为母版，市地级与行政执法类通过差异题补全，形成三套独立试卷数据；媒体单独存储，JSON 中只存相对路径。

### 1.2 五条原则

1. **不按 PDF 文件拆卷**：同一年份多份 PDF（主卷、续卷、差异卷）合并视为一套考试，按题号与模块统一编号。
2. **省级为主、差异为辅**：先完整提取省级，再映射市地 / 行政执法差异题。**禁止**只输出一份不分卷种的混合卷作为交付（`all_merged.json` 仅作跨卷分析池）。
3. **媒体可追溯**：图形、表格、复杂公式必须裁剪保存并在题目中引用，路径相对 `xingce/` 可解析。
4. **渐进可恢复**：中间结果写入 `_extract/` 与 `source/EXTRACT_STATUS.json`，支持中断续接，不依赖会话记忆。
5. **大文件不入库**：原始 PDF 只放 `source/`（或仅登记文件名），推送远端时排除。

---

## 2. 目录结构

```
xingce-structured-data/            # 仓库内实际根目录（历史文档中的 artifacts/gongkao 已废弃）
├── catalog.json                   # 多年总索引
├── README.md / AGENTS.md          # 总览 / 协作者接续
├── DATA_STATUS.md                 # 各年完成度与缺口
├── WORKFLOW.md                    # 本文件
├── CHANGELOG.md                   # 变更记录
├── _schema/conventions.md         # 字段与卷种约定
├── _templates/year_xingce/        # 空年份模板
├── init_year.sh                   # 一键初始化年份
└── {YEAR}/xingce/
    ├── meta.json                  # 年份元数据
    ├── source/                    # 原始 PDF + EXTRACT_STATUS.json
    ├── _extract/                  # 分模块中间 JSON（渐进落盘）
    │   ├── changshi.json  yuyan.json  shuliang.json
    │   ├── panduan.json   ziliao.json
    │   └── *_diffs.json           # 差异题（按卷种分文件）
    ├── papers/                    # 最终组装卷
    │   ├── shengji.json  shidi.json  xingzhengzhifa.json
    │   └── all_merged.json        # 可选分析池
    └── media/
        ├── pages/                 # 整页渲染
        ├── figures/               # 题级裁剪图
        ├── formulas/              # 公式截图
        └── media_index.json
```

---

## 3. ⚠️ 跨年结构差异（最容易踩的坑）

**题号模板不能跨年套用。** 已入库两年的内部结构完全不同：

| 年份 | 省级（135）模块构成 | 题号区间 |
|---|---|---|
| **2025** | 政治理论 20 / 常识 15 / 言语 30 / 数量 15 / 判断 35 / 资料 20 | 政 1–20 → 常 21–35 → 言 36–65 → 数 66–80 → 判 81–115 → 资 116–135 |
| **2024** | 常识 20 / 言语 40 / 数量 15 / 判断 40 / 资料 20（**无独立政治理论**） | 常 1–20 → 言 21–60 → 数 61–75 → 判 76–115 → 资 116–135 |

市地级 / 行政执法的通用规律：数量为 10 题（省级为 15），因此判断与资料的起始题号后移，总量 130（2025）或 125（2024 当前组装值）。

**开工前必做**：先渲染该年主卷前 2–3 页，确认当年模块顺序与题量，再据此定 `meta.json` 的 `modules` 区间。不要从任何一年的模板复制题号。

> 2022 / 2023 / 2020 / 2021 尚未解析，其 `meta.json` 里的 135/130/130 是初始化时的**预设值而非已验证事实**，解析时需实测校正。

---

## 4. 解析流程（8 步）

### 步骤 0：初始化年份

```bash
cd xingce-structured-data
./init_year.sh 2023          # 生成 {papers,media/{pages,figures,formulas},source}
# 手工补 _extract/ 目录，复制 PDF 到 source/，编写 meta.json 与 EXTRACT_STATUS.json
```

### 步骤 1：PDF 角色识别

- `pdfinfo xxx.pdf` 看页数与尺寸，判断哪份是主卷 / 续卷 / 差异注解册。
- **文件名后缀不可靠**：手册旧版曾记为 `20XX0124`=主卷、`20XX2548`=续卷、`20XX4972`=言语差异、`20XX7377`=执法差异，但 2025 实际是 `20250123 / 20252447 / 20254871 / 20257276`，后缀规律完全不同。**必须逐份渲染首页确认角色**，一般规律是：30–45MB 为整卷扫描，7–9MB 为差异注解册。
- 差异题多集中在注解册 PDF 中。

### 步骤 2：页面渲染（扫描 PDF 无文字层）

```bash
pdftoppm -png -r 40 -f START -l END source/xxx.pdf /tmp/render/prefix
convert /tmp/render/prefix-01.png -resize 50% /tmp/render/prefix-01_s.png
```

- 分辨率建议：**结构浏览 35–50 dpi**，**精读与裁图 72–100 dpi**。
- 大文件分批、后台渲染，避免超时。
- `pdftotext` 对扫描版输出为空，不要浪费时间；只能「渲染成图 → 视觉阅读」。
- `/tmp` 会被系统清理，**所有正式结果必须落盘到年份目录**。

### 步骤 3：分模块提取（渐进写入 `_extract/`）

按顺序提取，每完成一个模块立即落盘并更新 `EXTRACT_STATUS.json`：

1. 政治理论（若该年单列）
2. 常识判断
3. 言语理解与表达
4. 数量关系
5. 判断推理（图形 → 定义 → 类比 → 逻辑）
6. 资料分析（先材料后小题）

提取要点：

- 填空题、语句排序、逻辑题干较长，务必完整保留原文。
- 图形题：`stem` 写完整问句，`options` 可写「见图形」，并挂 `media`。
- 资料分析：材料正文与表格（可结构化 `table_data`）单独存入 `materials`，再挂小题。
- 页眉页脚、二维码、水印会干扰阅读，需人工甄别。

### 步骤 4：差异题映射

仔细阅读差异卷开头的「注」，例如：

> 行政执法类试卷的判断推理题量也是 40 道，其中市地级试卷中的第 71、75… 省级试卷中的第⑤1、⑤7… 均在行政执法类试卷中出现，不同的题目如下。

- 差异卷常用「圈号」或「第⑤1」标记，**必须对照原文「注」做映射，不可按文件顺序直接合并**。
- 按目标卷题号做**精确槽位替换**（不是追加），差异题保留 `original_number` / `source_note` / `original_diff_label` 便于追溯。
- 单独保存 `xzzf_diffs.json` / `yuyan_diffs.json` / `diffs_note.json`。

### 步骤 5：组装三套全量卷

- `shengji.json`：省级完整题为母版。
- `shidi.json` / `xingzhengzhifa.json`：以省级为底 + 差异题替换，凑满官方题量。
- 统一 `sections` 结构，保证题号在本卷内连续、无重复、模块完整。

### 步骤 6：媒体处理

```bash
# 从渲染页裁剪题级图形
pdftoppm -png -r 100 -f N -l N source/xxx.pdf /tmp/hi
# 裁出题目区域 → media/figures/qXXX.jpg
```

- 整页 → `media/pages/`；题级图形/表格 → `media/figures/qXXX.jpg`；公式 → `media/formulas/` 或题内 `formulas` 存 LaTeX。
- 更新 `media/media_index.json`（path、题号、kind、可选 `crop_box_frac` 裁剪框）。
- 题目内 `media[].path` 与索引一致，且**相对 `xingce/` 可解析**，禁止绝对路径。

### 步骤 7：校验与登记

见下方 §6 校验清单；通过后更新 `meta.json`（`status`/`updated`/`modules`）、根 `catalog.json`、`DATA_STATUS.md`、`CHANGELOG.md`。

---

## 5. 结果格式

字段完整约定见 [`_schema/conventions.md`](_schema/conventions.md)。此处列高频结构。

### 5.1 单题

```json
{
  "number": 61,
  "stem": "题干全文……",
  "options": { "A": "…", "B": "…", "C": "…", "D": "…" },
  "type": "数量关系",
  "paper": "省级",
  "source_note": "主卷共享",
  "media": [
    { "path": "media/figures/q061.jpg", "kind": "figure", "label": "示意图",
      "crop_box_frac": [0.1, 0.2, 0.9, 0.6] }
  ],
  "answer": null,
  "explanation": null
}
```

必填 `number` / `stem` / `options`；强烈建议 `type` / `paper` / `media` / `source_note`；可选 `subtype`（如 `削弱`、`翻译推理`）、`original_number`、`formulas`、`answer`、`explanation`。

> **现状说明**：截至 2026-08，全库 7 个卷文件**均未写入 `answer` / `explanation` 字段**（连 null 占位也没有）。这两项是「按真题规律出题」分析的前置条件，见 `DATA_STATUS.md` 缺口章节。

### 5.2 卷文件顶层

```json
{
  "exam_year": 2025,
  "exam_name": "2025年度国家公务员考试行政职业能力测验",
  "paper_type": "省级",
  "total_questions": 135,
  "actual_question_count": 135,
  "notes": "构建说明、差异来源等",
  "media_index": "media/media_index.json",
  "sections": [
    { "name": "政治理论", "question_count": 20, "questions": [], "materials": [] }
  ]
}
```

`sections[].name` 固定六类（按当年实际构成，2024 无「政治理论」）。`materials` 仅资料分析使用。

> **现状说明**：conventions 与旧手册示例中出现过 `sections[].range`（如 `"1-20"`），但**实际数据均未记录**，题号区间只能从 `questions` 推导。建议后续补齐该字段以便自动校验。

### 5.3 EXTRACT_STATUS.json（进度追踪）

```json
{
  "year": 2024,
  "updated": "2026-08-23",
  "shengji": { "file": "papers/shengji.json", "questions": 135, "status": "complete" },
  "shidi":   { "file": "papers/shidi.json", "questions": 125, "status": "base_assembled",
               "note": "差异替换待精确" },
  "diffs": { "xzzf": "_extract/xzzf_diffs.json (判断12+资料5)" },
  "pending": ["市地言语差异精确提取与槽位替换", "图形题 media 裁剪"],
  "structure_note": "省级135；市地/行政执法以省级为底+差异"
}
```

---

## 6. 校验清单

- [ ] 三卷 `actual_question_count` 与官方题量一致，且等于各 `sections[].question_count` 之和
- [ ] 题号在**本卷内**连续、无重复
- [ ] 省级数量为 15，市地 / 行政执法为 10（以当年大纲为准，勿套用）
- [ ] 该年是否单列「政治理论」已核实，模块构成与 `meta.json.modules` 一致
- [ ] 无残留「待补全」占位题干（或已在 `DATA_STATUS.md` 登记）
- [ ] 资料分析 `materials` 与小题一一对应
- [ ] 所有 `media[].path` 指向的文件真实存在
- [ ] `media_index.json` 与题目内引用一致
- [ ] `meta.json`、`catalog.json`、`DATA_STATUS.md`、`CHANGELOG.md` 四处状态一致

---

## 7. 常见坑速查

| 问题 | 处理 |
|------|------|
| 拿某年的题号模板套新年份 | 先渲染主卷前几页确认当年结构（见 §3） |
| 按 PDF 文件名后缀猜角色 | 后缀规律跨年不一致，必须渲染首页确认 |
| 题号在常识/数量等模块重复 | 用「模块 + 题号」索引，组装时按 section 取题 |
| 只解析了市地主卷 | 必须再处理差异卷，否则省级 / 执法不完整 |
| 差异题直接追加 | 按「注」做精确槽位替换，否则题量虚高 |
| 混合成一份 130 题交差 | 不符合交付标准，必须三卷分别全量 |
| 图片写绝对路径 | 改为相对 `xingce/` 的路径 |
| 占位题忘记补 | 在 `DATA_STATUS.md` 列出，补全后去掉占位标记 |
| 结果只留在 `/tmp` | `/tmp` 会被清理，正式结果必须落盘年份目录 |
| 大 PDF 渲染超时 | 分批、降分辨率、后台运行 |
| 把解析脚本长期留在数据目录 | 脚本放仓库 `scripts/` 或临时目录，不混入数据根 |

---

## 8. 工具依赖

| 用途 | 命令 / 工具 | 本机状态 |
|------|------------|---------|
| PDF 信息 | `pdfinfo` | ❌ 未安装 |
| 页面渲染 | `pdftoppm -png -r 40 -f N -l M` | ❌ 未安装 |
| 图像缩放/裁剪 | `convert`（ImageMagick） | ❌ 未安装 |
| 图像阅读 | 视觉模型读取 PNG | ✅ |
| 状态与组装 | Python 读写 JSON | ✅ |
| Git 推送 | SSH Deploy Key，排除 `source/*.pdf` | ✅ |

> **依赖说明**：`pdfinfo` / `pdftoppm` 来自 poppler，`convert` 来自 ImageMagick。macOS 安装：`brew install poppler imagemagick`。未安装时 PDF 页面渲染会直接失败。
> 可选替代：Python `PyMuPDF`（`fitz`）可在不依赖 poppler 的情况下渲染页面，适合需要跨环境复现时改用。

---

## 9. 执行清单（复制即用）

```
[ ] init_year.sh {YEAR} + 建 _extract/
[ ] 复制 PDF 到 source/，写 meta.json（source_files 填实际文件名）
[ ] pdfinfo + 渲染主卷前 3 页，确认当年模块顺序与题量
[ ] 逐份确认 PDF 角色（主卷 / 续卷 / 差异卷）
[ ] 提取 政治理论（若有）→ _extract/zhengzhi.json
[ ] 提取 常识 → _extract/changshi.json
[ ] 提取 言语 → _extract/yuyan.json
[ ] 提取 数量 → _extract/shuliang.json
[ ] 提取 判断（含图形）→ _extract/panduan.json
[ ] 提取 资料（材料+小题）→ _extract/ziliao.json
[ ] 读差异卷「注」→ 提取差异题 → _extract/*_diffs.json
[ ] 组装 papers/shengji.json（完整）
[ ] 组装 shidi.json / xingzhengzhifa.json（省级为底 + 槽位替换）
[ ] 裁剪媒体 → media/figures/，写 media_index.json
[ ] 跑 §6 校验清单
[ ] 更新 EXTRACT_STATUS / meta / catalog / DATA_STATUS / CHANGELOG
[ ] Git 提交（排除大 PDF）
```

---

## 10. 维护说明

- 本文件是唯一流程文档，原 `WORKFLOW_副本.md` 已并入并删除。
- 每完成一年，把新踩到的坑补进 §7，把确认过的当年结构补进 §3 对照表。
- 后续可扩展：`answer` / `explanation` 字段、`subtype` 细题型标注、知识点与难度标签、可重跑的渲染与校验脚本。
