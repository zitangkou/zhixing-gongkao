# 变更记录

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
