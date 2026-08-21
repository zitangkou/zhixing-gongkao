# 变更记录

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
