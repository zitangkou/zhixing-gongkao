# 变更记录

## 2026-09-02（七）

### 2022 三卷组装完成（papers_assembled）

- 新增 `scripts/xingce/assemble_2022.py`：**主卷为省级卷**（数量15/判断76起/资料116起），按"省级=主卷直接、市地=省级共享+市地差异、执法=省级共享+市地共享+执法独有"组装三卷。
- 产出 `2022/xingce/papers/{shengji,shidi,xingzhengzhifa,all_merged}.json` 与 `_extract/diff_map.json`。
- 题量：省级 135 / 市地 130 / 执法 130。市地=省级共享63+市地差异67；执法=省级共享43+市地共享47+执法独有35+数量无独有。
- 执法差异题用普通数字编号（常识68-74/言语75-85/判断86-92/资料93-102），非圈号。`20226369.pdf` 两页为执法差异补页。
- 校验 `validate_papers.py --year 2022`：**0 错误 / 34 警告**（图形题media类）。
- 已知缺口：常识第4题扫描件标注"缺"以占位题记录；执法判断/言语市地共享圈号OCR残缺按题量推算（记入note待核）；图形/图表题media_missing（省级12/市地10/执法9）。
- `meta.json` / `catalog.json` / `DATA_STATUS.md` 同步为 `papers_assembled`。

## 2026-09-02（六）

### 2021 两卷组装完成（papers_assembled）

- 新增 `scripts/xingce/assemble_2021.py`：主卷为市地级底版（130题），省级=市地共享86+省级独有49（判断/资料offset+5）。无行政执法卷。
- 产出 `2021/xingce/papers/{shengji,shidi,all_merged}.json` 与 `_extract/diff_map.json`。
- 题量：省级 135 / 市地 130。省级共享分布：常识13/言语25/数量9/判断29/资料10。
- 校验 `validate_papers.py --year 2021`：**0 错误 / 26 警告**（图形题media类）。
- 已知缺口：media_missing（市地13/省级11）；答案与解析待接入。
- `meta.json` / `catalog.json` / `DATA_STATUS.md` 同步为 `papers_assembled`。

## 2026-09-02（五）

### 2020 两卷组装完成（papers_assembled）

- 新增 `scripts/xingce/assemble_2020.py`：主卷为市地级底版（130题），省级=市地共享83+省级独有52（判断/资料offset+5）。无行政执法卷。
- 产出 `2020/xingce/papers/{shengji,shidi,all_merged}.json` 与 `_extract/diff_map.json`。
- 题量：省级 135 / 市地 130。省级共享分布：常识10/言语22/数量10(全部)/判断31/资料10。
- 差异题从 `20202548.pdf` 第39页开始（非仅 `20204954.pdf`）。
- 校验 `validate_papers.py --year 2020`：**0 错误 / 19 警告**（图形题media类）。
- 已知缺口：media_missing（省级16/市地13）；答案与解析待接入。
- `meta.json` / `catalog.json` / `DATA_STATUS.md` 同步为 `papers_assembled`。

## 2026-09-02（四）

### 2025 三卷答案+解析全部入库（answers_ingested）

**全库首次实现真题答案覆盖**——2025 三卷 395 题的 `answer` / `explanation` / `answer_source` 全部填入，覆盖率 100%。

- **数据来源**：4 份解析册扫描 PDF（`~/真题文档/2025/解析/{20250124,20252548,20254972,20257377}.pdf`），无文字层，逐页渲染读图提取。主卷页码 2-48 = 市地级 130 题（题号 1-130）；差异题页码 43-77 = 圈号 ①-⑩⑨ 共 109 题（省级/执法独有题）。
- **提取产出**：`2025/xingce/_extract/raw_2025*.json`（4 份原始提取，合计 239 条答案）。
- **映射方式**：市地主卷题号直接对应；省级/执法通过**跨卷题干相似度匹配**（共享题）+ `provenance.raw_note` 差异卷标注号（独有题）双轨对齐。映射脚本 `scripts/map_answers_2025.py`。
- **合并脚本**：`scripts/merge_answers.py`——答案格式校验（单选∈options键、多选≥2升序、判断∈{正确,错误}）→ 锚点校验 → 写入 papers → 覆盖率报告。支持 `--dry-run`。
- **答案分布**（市地 130 题）：A=31, B=34, C=29, D=36，无多选/判断题。
- **校验结果**：`validate_papers.py --year 2025`：**0 错误 / 20 警告**（警告全部为预存已登记缺陷：判断推理末尾错配题、执法卷内重复、材料悬空，与答案接入无关）。
- **anchor_pending 说明**：234 题标记 `anchor_pending` flag。原因是解析册解析以"完整解析："开头，通常引用题干预设结论或文献原文（如政治题引用"习近平总书记的重要文章《…》指出"），而非题干原句，导致脚本化锚点比对得分低。映射阶段已通过跨卷题干匹配确保答案归属正确，该 flag **不代表答案错误**，仅表示无法通过解析原文自动验证题干一致性。
- **遗留缺口**：① 差异题 Q94（量子成像细节判断）解析在页码 73 被截断，C 项未完成，已跨册合并页码 74 尾部但仍不完整；② 2024/2023 共 780 题答案待接入；③ `subtype` 细题型覆盖率约 40%（仅解析中明确标注的题填入）。
- `meta.json` / `catalog.json` / `DATA_STATUS.md` 状态同步为 `answers_ingested`。

## 2026-09-02（三）

### 2023 三卷组装完成（papers_assembled）

- 新增 `scripts/xingce/assemble_2023.py`：以市地级主卷为底版，按共享关系 + 差异题册组装省级/市地/执法三卷，产出 `2023/xingce/papers/{shengji,shidi,xingzhengzhifa,all_merged}.json` 与 `_extract/diff_map.json`（机器可读差异映射表）。
- 组装规则：省级 = 市地共享 49 题（判断/资料按 offset+5 映射到 76-115 / 116-135）+ 省级独有 86 题；执法 = 市地共享 + 省级共享 + 执法独有，按 市地→省级→独有 顺序连续编号。每题补 `section` 字段、各 section 附带 `materials` 列表。
- 结果题量：省级 135 / 市地 130 / 执法 130。校验 `validate_papers.py`：**0 错误 / 28 警告**（全部为图形题/折线图题 media 类已登记缺陷）。
- 执法数量「省级共享 4 题」题号因原件 OCR 残缺（显示④④④④），按省级数量独有顺序取 41-44，记入 `diff_map.json` 与 CONFIRM_LOG P3 待核。
- `meta.json` / `catalog.json` / `DATA_STATUS.md` 状态同步为 `papers_assembled`。
- 待办：答案与解析接入（2023 解析册接入方案待评估）、图形题裁图（media_missing）。

## 2026-09-02（二）

### schema v2：数据格式统一

**首次把解析流程代码化**，新增两个可复用脚本（此前全库无任何脚本沉淀）：

- `scripts/xingce/normalize_papers.py`：v1→v2 幂等迁移，支持 `--dry-run` / `--year` / `--merged`
- `scripts/xingce/validate_papers.py`：v2 不变式校验，可挂 CI（已登记缺陷→警告，未登记→错误）

**字段归一内容**：

- `type` 统一为 13 个中文枚举（v1 为中英混用，且 `single_choice` 被当作兜底值滥用）；映射规则见 `_schema/conventions.md` §3.2
- `source_note` 自由文本（40+ 种取值）→ 结构化 `provenance{role,from_paper,from_number,diff_label,raw_note}`，原文永不丢弃
- 媒体路径基准统一为**相对 `xingce/`**（v1 数据实际相对 `media/`，而 conventions 示例写的是 `media/…`，按文档写导入会 100% 解析失败）；`media_index.json` 的 `file` 改名 `path` 并补前缀，删除残留的 `conventions.path_root: gongkao_2025/`
- 材料引用 `material_ref`(2024) / `material_id`(2025) → 统一为数组 `material_ids`，支持 2024 的 `"mat2+mat3"` 复合写法；材料 id 统一为 `m{起}_{止}`
- 新增顶层 `modules[].number_range`（题号区间卷内自洽，不再依赖 meta.json）
- 新增 `options_in_media`（图形题选项在图中时 `options` 为 null）、`section` 冗余字段、`flags` 质量标记、`answer`/`explanation`/`answer_source` 空占位
- `all_merged.json` 重建为按「题干+选项+组合项+媒体」哈希去重的分析池，记录每题出现在哪几卷、各卷题号

**迁移暴露的真实缺陷（此前无人发现，均以 flag 登记）**：

1. 2025 三卷判断推理末尾 5 题内容实为语句排序/语句填空/片段阅读/数量关系 → 三套卷各缺 5 道真判断题（`section_type_mismatch`）
2. 2025 行政执法卷**卷内重复**：数量#68≡判断#100、数量#71≡判断#101（`duplicate_in_paper`）
3. 2025 三卷判断推理引用了不存在的材料 `m106_110`，即语句排序题的前置句子材料漏提取（`material_ref_dangling`）
4. 2025 省级资料分析 20 题全部借自市地，无一道省级原生题（`material_borrowed`）
5. 2024 三卷保留 37 条媒体引用但 `media/` 为空，文件全部不存在（`media_file_absent`）

**校验结果**：`validate_papers.py` 从首轮 64 错误收敛到 **0 错误 / 57 警告**（全部为已登记缺陷）。

**跨卷共享率**（去重池副产品）：2024 三卷 385 题 → 135 道去重题（125 道三卷共有 + 10 道省级独有）；2025 为 395 → 145 道。

### 吸收外部分析后的增补（同日）

参考 `analysis/` 两份报告，采纳 6 点、证伪 1 点：

- **新增考点标签字段** `topic`（板块）/ `tag`（专题），配套受控词表 `_schema/topic-vocabulary.json`（初版词表取自报告的 2025 省级 16 专题清单）。这是「考点频次统计」与「模拟题专题去重」的前提，此前规范完全缺失
- **新增 `provenance.source_ref`**（原始 PDF 文件名 + 页码），补齐到扫描件的溯源链
- **新增 `enumeration_missing` 校验**：组合题/计数题缺条目正文时标记。规则要求「题干列举设问 + 选项确为 ①组合/N项 形态 + 无 items 无材料」三条同时成立
- **新增 `scripts/xingce/sync_status.py`**：从 papers 反向生成每年标准 `EXTRACT_STATUS.json`（含答案与标签覆盖率、open_flags 聚合），并回填 `meta.json` 的 `modules`。2025/2023/2022 此前缺该文件、2024 meta 缺 `modules`，均已补齐
- **校验器新增覆盖率输出**：答案覆盖率、考点标签覆盖率（当前均为 0%，作为 P0/P1 的量化目标）
- **OCR 选型具体化**：`RapidOCR` / `PaddleOCR` 本地预筛 + 视觉校对，替代纯人工读图
- ❌ **证伪**：报告将「2025 政治理论 1/6/7/11 条目缺失」列为 P0，实测这 4 题条目全在 `items` 字段（4/5/4/5 条），系只看 `stem` 造成的误判；该伪任务已从计划中作废并写明原因。同理，本仓库初版 `enumeration_missing` 规则也因漏了「选项形态」条件而误伤政治理论 #9（正常单选题），已修正并补正反例自检

## 2026-09-02

### 文档治理（实测核对，非沿用旧表）

- **合并两份流程文档**：原 `WORKFLOW.md`（简版 112 行）与未入库的详细版手册 `WORKFLOW_副本.md`（311 行）合并为唯一权威 `WORKFLOW.md`，副本删除。
- **修正路径漂移**：全部文档中的 `artifacts/gongkao/` 与 `gongkao_2025/` 在当前仓库中并不存在，统一改为 `xingce-structured-data/`；`catalog.json` 的 `root` 同步修正。历史条目保留原文不改写。
- **修正 2024 进度矛盾**：README 记为 `empty`、DATA_STATUS 记为 `papers_assembled`、PROGRESS 记为已入库——实测为三卷 135/125/125、`_extract/` 7 个中间文件齐、**media 为 0**。四处口径已统一。
- **新增跨年结构差异表**（WORKFLOW §3）：2024 无独立政治理论（常识 20 / 言语 40 / 判断 40），2025 起政 20 + 常 15 / 言 30 / 判 35；明确**题号模板不可跨年套用**。
- **新增两条易踩坑**：PDF 文件名后缀规律跨年不一致（2025 为 `20250123/2447/4871/7276`，与手册旧模板不符），必须逐份渲染首页确认角色；本机未装 poppler，渲染会直接失败。
- **登记 2024 源文件缺口**：`meta.source_files` 记 4 份，本机实际缺 `20240124.pdf`。
- **标注字段落地现状**：`sections[].range`、`answer`、`explanation` 三项在约定中存在但实际数据均未写入，`conventions.md` 与 `catalog.json.known_gaps` 均已记录。
- **补全索引**：`catalog.json` 新增 2021 / 2020（`not_initialized`，源 PDF 已备）与 `known_gaps` 字段；DATA_STATUS 补 2024 详细章节、2023/2022 预设值警示、申论未开工说明。

## 2026-08-21

### 多年库骨架

- 建立正式根目录 `artifacts/gongkao/`。
- 约定 `{YEAR}/xingce/{papers,media,source,meta.json}`。
- 增加 `catalog.json`、`init_year.sh`、`_schema/conventions.md`、`_templates/year_xingce`。
- 预创建 2022–2024 空目录。

### 2025 三卷交付

- 以**省级为全量主卷**（135 题，题号 1–135）。
- 市地级、行政执法各 130 题，由共享题 + 差异题补全。
- 产出：
  - `papers/shengji.json`
  - `papers/shidi.json`
  - `papers/xingzhengzhifa.json`
  - `papers/all_merged.json`（分析用合并池）
- 媒体：`media/pages`、`media/figures`、`media_index.json`（与早期 `gongkao_2025` 硬链接/同步）。

### 补全

- 省级判断 111–115 原「待补全」占位，已用差异卷逻辑题（标注 57–61）替换为完整题干与选项。

### 文档沉淀

- `README.md` — 总览  
- `AGENTS.md` — 智能体接续规范  
- `DATA_STATUS.md` — 状态与缺口  
- `WORKFLOW.md` — 解析流程  
- `_schema/conventions.md` — 字段约定  
- `CHANGELOG.md` — 本文件  

### 兼容

- 保留 `artifacts/gongkao_2025/`，避免打断旧引用；正式读写以 `gongkao/` 为准。

---

## 更早（对话内，未单独打 tag）

- 四份 2025 扫描 PDF 解析为结构化题目。
- 用户要求：不按文件拆成多套「假试卷」，最终按**真实卷种**出三套全量。
- 用户要求：省级题量最多，应以省级为准重建。
- 图片/公式非字符元素通过 pages + figures + media 字段保留。
