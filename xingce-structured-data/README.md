# 国考行测真题结构化数据

将国家公务员考试《行政职业能力测验》真题解析为结构化 JSON，并保留图片、公式等非文本元素，供展示与数据分析使用。

**正式库根目录：** `artifacts/gongkao/`  
**兼容旧路径：** `artifacts/gongkao_2025/`（2025 早期产出，仍保留）

---

## 1. 目录结构

```
gongkao/
├── README.md                 # 本文件（总览）
├── AGENTS.md                 # 给智能体/协作者的接续说明
├── DATA_STATUS.md            # 各年入库状态与缺口
├── WORKFLOW.md               # 解析与补全工作流
├── CHANGELOG.md              # 变更记录
├── catalog.json              # 机器可读全库索引
├── init_year.sh              # 新建年份一键初始化
├── _schema/
│   └── conventions.md        # 字段与卷种约定
├── _templates/
│   └── year_xingce/          # 空年份模板
└── {YEAR}/xingce/
    ├── meta.json             # 年份元信息
    ├── papers/
    │   ├── shengji.json          # 省级（主卷，题量最多）
    │   ├── shidi.json            # 市地级
    │   ├── xingzhengzhifa.json   # 行政执法类
    │   └── all_merged.json       # 可选：跨卷合并池
    ├── media/
    │   ├── pages/            # 整页扫描图
    │   ├── figures/          # 题级裁剪图
    │   ├── formulas/         # 公式截图（可选）
    │   └── media_index.json
    └── source/               # 原始 PDF 说明或文件
```

---

## 2. 三类试卷与题量（2025 起）

| 卷种 | 文件 | 总题量 | 数量关系 | 题号要点 |
|------|------|--------|----------|----------|
| **省级**（主卷） | `shengji.json` | **135** | **15** | 数 66–80；判 81–115；资 116–135 |
| 市地级 | `shidi.json` | 130 | 10 | 数 66–75；判 76–110；资 111–130 |
| 行政执法类 | `xingzhengzhifa.json` | 130 | 10 | 同市地骨架，常识/数量/判断含差异题 |

**统一模块：** 政治理论 20 + 常识 15 + 言语 30 + 资料 20。  
**构建原则：** 以省级全量为主；市地 / 行政执法 = 共享题 + 差异题补全。

---

## 3. 当前进度（摘要）

| 年份 | 状态 | 说明 |
|------|------|------|
| **2025** | ready | 三卷齐全；media 已挂接；见 `DATA_STATUS.md` |
| 2024 | empty | 目录已初始化，待解析 |
| 2023 | empty | 同上 |
| 2022 | empty | 同上 |

详细缺口、占位补全记录、媒体数量见 **[DATA_STATUS.md](DATA_STATUS.md)**。

---

## 4. 新建一年份

```bash
cd artifacts/gongkao
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
| [DATA_STATUS.md](DATA_STATUS.md) | 各年状态、2025 补全记录、已知问题 |
| [WORKFLOW.md](WORKFLOW.md) | 从 PDF 到 JSON / 图片的标准流程 |
| [CHANGELOG.md](CHANGELOG.md) | 变更历史 |
| [_schema/conventions.md](_schema/conventions.md) | 题目 JSON 字段约定 |

机器索引：`catalog.json`。
