# 国考行测真题结构化数据

将国家公务员考试《行政职业能力测验》真题解析为结构化 JSON，并保留图片、公式等非文本元素，供展示与数据分析使用。

**仓库内根目录：** `xingce-structured-data/`（本文档所在目录）

> 历史文档中出现的 `artifacts/gongkao/` 与 `gongkao_2025/` 是早期工作位置的路径命名，**当前仓库中均不存在**，一律以本目录为准。

---

## 1. 目录结构

```
xingce-structured-data/
├── README.md                 # 本文件（总览）
├── AGENTS.md                 # 给智能体/协作者的接续说明
├── DATA_STATUS.md            # 各年入库状态与缺口
├── WORKFLOW.md               # 解析与补全工作流（唯一权威流程文档）
├── CHANGELOG.md              # 变更记录
├── catalog.json              # 机器可读全库索引
├── init_year.sh              # 新建年份一键初始化
├── _schema/
│   └── conventions.md        # 字段与卷种约定
├── _templates/
│   └── year_xingce/          # 空年份模板
└── {YEAR}/xingce/
    ├── meta.json             # 年份元信息
    ├── source/               # 原始 PDF 登记 + EXTRACT_STATUS.json（进度）
    ├── _extract/             # 分模块中间 JSON（渐进落盘，可中断续接）
    ├── papers/
    │   ├── shengji.json          # 省级（主卷，题量最多）
    │   ├── shidi.json            # 市地级
    │   ├── xingzhengzhifa.json   # 行政执法类
    │   └── all_merged.json       # 可选：跨卷合并池
    └── media/
        ├── pages/            # 整页扫描图
        ├── figures/          # 题级裁剪图
        ├── formulas/         # 公式截图（可选）
        └── media_index.json
```

---

## 2. 三类试卷与题量（以 2025 为例）

| 卷种 | 文件 | 总题量 | 数量关系 | 题号要点 |
|------|------|--------|----------|----------|
| **省级**（主卷） | `shengji.json` | **135** | **15** | 数 66–80；判 81–115；资 116–135 |
| 市地级 | `shidi.json` | 130 | 10 | 数 66–75；判 76–110；资 111–130 |
| 行政执法类 | `xingzhengzhifa.json` | 130 | 10 | 同市地骨架，常识/数量/判断含差异题 |

**2025 模块构成：** 政治理论 20 + 常识 15 + 言语 30 + 数量 15 + 判断 35 + 资料 20。
**构建原则：** 以省级全量为主；市地 / 行政执法 = 共享题 + 差异题补全。

> ⚠️ **上表仅适用 2025 及之后**。2024 年度结构不同：**无独立政治理论模块**，常识 20 / 言语 40 / 判断 40，题号为 常 1–20 → 言 21–60 → 数 61–75 → 判 76–115 → 资 116–135。**题号模板不可跨年套用**，详见 [WORKFLOW.md §3](WORKFLOW.md)。

---

## 3. 当前进度（摘要）

| 年份 | 状态 | 三卷题量 | 媒体 | 说明 |
|------|------|---------|------|------|
| **2025** | ready | 135 / 130 / 130 | 31 页 + 32 图 | 三卷齐全，差异已补，无「待补全」占位 |
| **2024** | papers_assembled | 135 / **125** / **125** | **0** | 省级完整；市地/执法以省级为底组装，差异槽位待精修；**图形媒体全缺**；源 PDF 缺主卷一份 |
| 2023 | empty | — | — | 仅目录初始化，源 PDF 已备（4 份） |
| 2022 | empty | — | — | 仅目录初始化，源 PDF 已备（4 份） |
| 2021 | 未初始化 | — | — | 源 PDF 已备（3 份），仓库内无年份目录 |
| 2020 | 未初始化 | — | — | 源 PDF 已备（3 份），仓库内无年份目录 |

**全库共性缺口**：三卷均**未收录 `answer` / `explanation` 字段**，无法支撑「按真题规律出题」的实证分析。

详细缺口、补全记录、媒体数量见 **[DATA_STATUS.md](DATA_STATUS.md)**。

---

## 4. 新建一年份

```bash
cd xingce-structured-data
./init_year.sh 2021
# 生成 2021/xingce/{meta,papers,media,source}
# 然后：放入 PDF → 解析三卷 → 更新 catalog.json 与 DATA_STATUS.md
```

完整步骤见 **[WORKFLOW.md](WORKFLOW.md)**。

---

## 5. 相关文档

| 文档 | 用途 |
|------|------|
| [AGENTS.md](AGENTS.md) | 智能体接续：先读什么、禁止什么、如何改数据 |
| [WORKFLOW.md](WORKFLOW.md) | 从 PDF 到 JSON / 图片的标准流程（含 §3 跨年结构差异） |
| [ANSWER_INGESTION_PLAN.md](ANSWER_INGESTION_PLAN.md) | **当前进行中**：2025 答案接入与真题规律实证计划 |
| [DATA_STATUS.md](DATA_STATUS.md) | 各年状态、缺口与补全记录 |
| [CHANGELOG.md](CHANGELOG.md) | 变更历史 |
| [_schema/conventions.md](_schema/conventions.md) | 题目 JSON 字段约定（**当前 schema v2**） |

机器索引：`catalog.json`。

---

## 6. 工具脚本

脚本放在仓库根 `scripts/xingce/`（不混入数据目录），**仅用标准库**，任意 Python 3 可直接运行。

```bash
# 校验 v2 不变式：题量、题号连续、type 枚举、媒体存在性、材料引用、卷内重复、
# 列举条目完整性；并输出答案与考点标签覆盖率
python3 scripts/xingce/validate_papers.py                # 全部年份
python3 scripts/xingce/validate_papers.py --year 2025    # 单年
# 退出码非 0 表示有「未登记」的新问题；已登记的已知缺陷只输出警告

# v1 → v2 迁移（含 --merged 重建跨卷去重分析池）
python3 scripts/xingce/normalize_papers.py --dry-run --merged   # 先看报告
python3 scripts/xingce/normalize_papers.py --merged             # 实际写入

# 生成每年标准状态文件 + 回填 meta.modules（勿手工编辑 EXTRACT_STATUS）
python3 scripts/xingce/sync_status.py
```

⚠️ **改了 `normalize_papers.py` 的规则后必须回退重跑**：脚本对已是 `schema_version: 2` 的文件会直接跳过，新字段与新标记不会生效。正确做法是先 `git checkout -- xingce-structured-data/20*/xingce/papers/ xingce-structured-data/20*/xingce/media/media_index.json` 回到 v1，再依次跑 `normalize → sync_status → validate`。

依赖外部工具（尚未安装，渲染 PDF 前需装）：`brew install poppler imagemagick`，或改用 PyMuPDF，见 `WORKFLOW.md` §8。
