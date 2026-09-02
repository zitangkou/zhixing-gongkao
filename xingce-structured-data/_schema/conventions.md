# 题目与卷种字段约定 · schema v2

> 版本：v2（2026-09-02）· 取代 v1
> 制定依据：对 2024 / 2025 共 7 个卷文件的**实测字段**归一，而非理想化设计
> 迁移工具：`scripts/xingce/normalize_papers.py`（幂等，可重复执行）
> v1 的主要问题是：文档定义的字段远少于实际使用的字段，且 `options` 路径基准、`type` 词表、材料引用方式三处与实际不一致。

---

## 0. 兼容性说明

- 顶层新增 `schema_version: 2`；读取方应据此分支。
- v2 **不删除任何原始信息**：v1 的自由文本 `source_note` 原文保留在 `provenance.raw_note`。
- 幂等：对已是 v2 的文件重复执行不产生变化。

---

## 1. 卷文件顶层

```json
{
  "schema_version": 2,
  "exam_year": 2025,
  "exam_name": "2025年度国家公务员考试行政职业能力测验",
  "paper_type": "省级",
  "total_questions": 135,
  "actual_question_count": 135,
  "modules": [
    { "name": "政治理论", "number_range": [1, 20], "question_count": 20 }
  ],
  "notes": "构建说明、差异来源等",
  "media_index": "media/media_index.json",
  "sections": []
}
```

`paper_type` 取值固定：`省级` / `市地级` / `行政执法类`
文件名固定：`shengji.json` / `shidi.json` / `xingzhengzhifa.json`

**`modules`（v2 新增，必填）**：显式记录各模块题号闭区间。v1 把它放在 `meta.json`，导致校验题号连续性必须跨文件读；现在卷内自洽。

---

## 2. 模块 section

```json
{ "name": "资料分析", "question_count": 20, "materials": [], "questions": [] }
```

`name` 取值来自六类，**并非每年齐全**：

`政治理论` · `常识判断` · `言语理解与表达` · `数量关系` · `判断推理` · `资料分析`

> ⚠️ 2024 年度**没有独立的「政治理论」**（政治内容并入常识判断，常识 20 / 言语 40 / 判断 40）；2025 起才单列政治理论 20 + 常识 15。**题号模板不可跨年套用**，见 `WORKFLOW.md` §3。

`materials` 仅资料分析（及含长材料的模块）使用。

---

## 3. 单题 question

```json
{
  "number": 76,
  "section": "判断推理",
  "stem": "从所给的四个选项中,选择最合适的一个填入问号处…",
  "items": null,
  "options": null,
  "options_in_media": true,
  "type": "图形推理",
  "answer": null,
  "answer_source": null,
  "explanation": null,
  "media": [
    { "path": "media/figures/q076.jpg", "kind": "figure", "label": "图形推理76题干+选项" }
  ],
  "formulas": [],
  "material_ids": [],
  "provenance": {
    "role": "shared",
    "from_paper": null,
    "from_number": null,
    "diff_label": null,
    "raw_note": "主卷共享"
  },
  "flags": []
}
```

### 3.1 字段清单

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `number` | int | ✅ | **本卷**连续题号 |
| `section` | string | ✅ | 所属模块（v2 新增冗余，便于扁平处理） |
| `stem` | string | ✅ | 题干全文 |
| `items` | array \| null | — | 组合项题干（①②③ 列表）；此时 `options` 放组合结果 |
| `options` | object \| null | ✅* | `{"A":"…","B":"…","C":"…","D":"…"}`；**图形题选项本身是图时可为 `null`** |
| `options_in_media` | bool | ✅* | `options` 为 `null` 时必须为 `true` |
| `type` | string | ✅ | 细题型，取值见 §3.2 **枚举** |
| `topic` | string \| null | ✅ | 考点**板块**，取值受 `_schema/topic-vocabulary.json` 的键约束；未标注为 `null` |
| `tag` | string \| null | ✅ | 考点**专题**，必须属于该题 `topic` 的列表；未标注为 `null` |
| `answer` | string \| null | ✅ | 见 §3.3 取值规范；未入库时为 `null` |
| `answer_source` | string \| null | — | 答案出处标记，如 `answer_book_2026-09` |
| `explanation` | string \| null | ✅ | 解析全文；未入库时为 `null` |
| `media` | array | — | 见 §3.5，**路径相对 `xingce/`** |
| `formulas` | array | — | LaTeX 字符串或公式图 path |
| `material_ids` | array\<string\> | ✅ | 指向 `sections[].materials[].id`，**数组**（实测存在一题引用多篇材料，如 2024 的 `mat2+mat3`）；无引用为 `[]` |
| `provenance` | object | ✅ | 结构化来源，见 §3.4 |
| `flags` | array\<string\> | ✅ | 数据质量标记，见 §3.6；无问题为 `[]` |

> 硬约束：`options == null` ⟺ `options_in_media == true` 且 `media` 非空。校验脚本强制检查。

### 3.2 `type` 枚举（v2 统一为中文）

| 模块 | 允许取值 |
|---|---|
| 政治理论 | `政治理论` |
| 常识判断 | `常识判断` |
| 言语理解与表达 | `选词填空` `片段阅读` `语句排序` `语句填空` `标题选择` `文章阅读` |
| 数量关系 | `数量关系` |
| 判断推理 | `图形推理` `定义判断` `类比推理` `逻辑判断` |
| 资料分析 | `资料分析` |

**v1 → v2 映射表**（迁移脚本据此归一）：

| v1 值 | v2 值 |
|---|---|
| `single_choice` | 按所属模块判定：政治理论 / 常识判断 / 数量关系 |
| `verbal` | `选词填空` |
| `reading` | `片段阅读` |
| `sentence_reorder` | `语句排序` |
| `quantity` | `数量关系` |
| `graphic` | `图形推理` |
| `definition` | `定义判断` |
| `analogy` | `类比推理` |
| `logic` | `逻辑判断` |
| `data_analysis` | `资料分析` |
| 中文值（2024） | 原样保留 |

> `single_choice` 出现在**判断推理**模块时无法由模块推断，按题干内容归类并**必须打 `type_inferred_from_stem` 标记**（2025 三卷各有 5 题属此情况，见 §3.6）。

### 3.3 `answer` 取值规范

| 题型 | 格式 | 例 |
|---|---|---|
| 单选类（含政治理论/常识/言语/数量/判断/资料） | 单个字母 | `"A"` |
| 多选类（若引入） | 字母升序、无分隔 | `"ABD"` |
| 判断类（若引入） | 固定词 | `"正确"` / `"错误"` |

硬约束：`answer` 的字母必须出现在该题 `options` 的键中。

### 3.4 `provenance`（取代自由文本 `source_note`）

| 字段 | 取值 |
|---|---|
| `role` | `shared`（三卷共享）· `province_only`（省级独有）· `shared_with_shidi`（省市地共享）· `diff_book`（差异卷补入）· `mapped_from_shidi`（借市地材料/题顶位）· `backfilled`（补全，来源存疑）· `main`（主卷原生） |
| `from_paper` | `省级` / `市地级` / `行政执法类` / `差异卷` / `null` |
| `from_number` | 来源卷题号（int）或 `null` |
| `diff_label` | 差异卷圈号标注（string/int）或 `null` |
| `raw_note` | **v1 原始 `source_note` 全文，永不丢弃** |
| `source_ref` | `{file, page}`：该题出自哪个扫描 PDF 的第几页。当前多为 `null`，**答案册接入时应顺手补齐**，否则无法回溯原始扫描件 |

v1 自由文本 → v2 解析规则（正则）：

| v1 文本 | v2 结果 |
|---|---|
| `主卷` / `主卷共享` | `role=shared`（`主卷` 单独出现时 `role=main`） |
| `省级数量独有(差异卷29)` | `role=province_only`, `from_paper=差异卷`, `diff_label=29` |
| `与市地共享(市地70)` | `role=shared_with_shidi`, `from_number=70` |
| `省级判断` | `role=province_only` |
| `省级判断补全` | `role=backfilled` |
| `省级判断差异题(差异卷标注57)` | `role=diff_book`, `from_paper=差异卷`, `diff_label=57` |
| `资料映射市地111` | `role=mapped_from_shidi`, `from_paper=市地级`, `from_number=111` |
| `主卷共享（差异题待精确替换）` | `role=shared` + `flag=diff_pending_replace` |

无法解析的文本 → `role=unknown` 并保留 `raw_note`，由校验脚本汇总报告。

### 3.5 媒体路径基准（v2 明确）

**所有 `path` 一律相对年份 `xingce/` 目录**，即写作 `media/figures/q076.jpg`。

> v1 文档示例写 `media/figures/…` 但实际数据存的是 `figures/…`（相对 `media/`），二者矛盾——按文档写导入程序会 100% 解析失败。v2 统一为**自描述路径**，迁移脚本会为全部存量引用补 `media/` 前缀。
> `media_index.json` 的 `pages[].file` / `figures[].file` 同样补前缀；其 `conventions.path_root` 字段中的历史值 `gongkao_2025/` 一并清除。

`kind` 取值：`page` / `figure` / `table` / `chart` / `formula`。

### 3.6 `flags` 数据质量标记

| 标记 | 含义 |
|---|---|
| `type_inferred_from_stem` | `type` 由题干内容推断，非源数据自带 |
| `type_unmapped` | `type` 值不在 v1→v2 映射表内，原样保留待人工判定 |
| `type_unresolved` | 无法判定 `type`（模块与题干均不足以推断） |
| `section_type_mismatch` | 题目内容与所属模块不符（**2025 三卷判断推理各有 5 题**，见下） |
| `material_borrowed` | 材料借自其他卷种，非本卷原生（**2025 省级资料分析 20 题全部如此**） |
| `material_ref_dangling` | `material_ids` 指向不存在的材料，说明**材料本身漏提取**（如 2025 判断推理引用 `m106_110`） |
| `media_missing` | 题目需要图（`options` 为 null 或标记有图）但没有任何有效媒体引用 |
| `media_file_absent` | 有媒体引用但文件实际不存在（**2024 全部**） |
| `diff_pending_replace` | 差异题槽位待精确替换（**2024 市地/执法**） |
| `duplicate_in_paper` | 同一份卷内出现完全相同的题（**2025 执法卷 2 组**） |
| `enumeration_missing` | 组合题 / 计数题**缺条目正文**，题目不完整无法作答（当前 0 例） |
| `answer_missing` | 尚无答案（当前全库 780 题） |

> **门禁语义**：`scripts/xingce/validate_papers.py` 对以上已登记的已知缺陷输出**警告**，对未登记的不一致输出**错误**并以非零码退出。也就是说——已知问题必须显式标记，不允许悄悄存在；新增问题若不登记就会卡住 CI。

> **已知真实缺陷（非格式问题，v2 只负责显式标记，不擅自修数据）**
> 1. 2025 三卷「判断推理」模块末尾 5 题（省级 106–110、市地/执法 97–101）内容实为语句排序 / 语句填空 / 片段阅读 / 数量关系，`provenance.role=backfilled`。推断为补全判断缺口时按错误题号取题，导致**三套卷各缺 5 道真判断推理题**。
> 2. 2025 行政执法卷**卷内重复**：`数量关系#68 ≡ 判断推理#100`、`数量关系#71 ≡ 判断推理#101`（上述缺陷 1 的连带结果——从执法卷取题补省级时，取到的正是它自己重复的那两题）。
> 3. 2025 三卷判断推理引用了**不存在的材料 `m106_110`**：#106「将以上6个句子重新排列」需要前置的 ①–⑥ 句子材料，该材料漏提取。
> 4. 2025 省级「资料分析」20 题全部 `role=mapped_from_shidi`，**无一道省级原生题**。
> 5. 2024 三卷 `media/` 为空，但题目里保留了 37 条媒体引用（全部指向不存在的文件），图形推理与资料分析图表题实际不可作答。
>
> 做真题规律统计时，上述样本必须剔除或单独标注，否则会把别的模块 / 别的卷种的特征误当成本卷规律。

### 3.7 组合题 / 计数题完整性判定

判定「该题是否需要条目正文」必须**同时满足三条**（实现在 `normalize_papers.needs_enumeration`，校验器复用同一函数）：

1. 题干以列举设问收尾：`……相符的有：` / `……正确的有几项？`；
2. **选项形态确实指向条目**：含 ①②③ 的组合项，或全部是 `N 项` 计数项；
3. 此时若 `items` 为空且 `material_ids` 为空 → 打 `enumeration_missing`。

> ⚠️ **只看第 1 条会误伤。** 「关于深化科技体制改革，下列表述**正确的是**：」+ 四个完整陈述句，是标准单选题，题干以冒号收尾但**不需要条目**。本规则初版就漏了第 2 条，把 2025 三卷的政治理论 #9 误判为残缺——而 #9 恰恰是正常题。
>
> 同理，`analysis/` 下两份报告曾把政治理论 1/6/7/11 判为「条目缺失」并列为 P0 回源任务，实际这 4 题的 ①②④ 条目**都在 `items` 字段里**（4/5/4/5 条），属于只看 `stem` 造成的误判。判残缺前务必先看 `items`。

### 3.8 考点标签 `topic` / `tag`

- 词表：[`_schema/topic-vocabulary.json`](../_schema/topic-vocabulary.json)，`topic` 取板块、`tag` 取专题，**必须成对填写**（只填一个视为未标注）；
- **一题一专题**：同一卷内 `tag` 不应重复（2025 省级实测 16 题 16 专题）；
- 无法归类的题 `tag` 留 `null`，进待扩充清单，**不要生造标签**；新标签一经采用必须回写词表，保证跨年统计口径一致；
- 这是「考点频次统计」与「模拟题专题去重」的前提，未标注时校验器只计入覆盖率、不报错。

---

## 4. 材料 materials（v2 统一）

```json
{
  "id": "m111_115",
  "title": "2019—2023年专精特新“小巨人”企业及上市企业数量",
  "kind": "chart_table",
  "number_range": [111, 115],
  "content": "材料全文（纯文本，2024 仅此字段）",
  "table_data": [],
  "media": [ { "path": "media/figures/q111_chart.jpg", "kind": "chart", "label": "各批次柱状图" } ],
  "note": "图表补充说明"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | ✅ | 统一格式 `m{起}_{止}`（按引用它的小题号区间生成）。v1 中 2024 用 `mat1`，迁移时按引用题号重编 |
| `title` | ✅ | 材料标题 |
| `kind` | ✅ | `text` / `table` / `chart` / `chart_table` / `graph_text` |
| `number_range` | ✅ | 该材料覆盖的小题题号闭区间 |
| `content` | ✅ | 材料全文 |
| `table_data` | — | **结构化数值**（`[{列:值}]` 或 `{指标:{年份:值}}`），可直接用于出题与计算校验 |
| `media` | — | 图表图片 |
| `note` | — | 说明文字。v1 的 `chart_data_note`、`material_note` 统一并入 |

小题通过 `material_ids`（数组）关联；v1 中 2024 的 `material_ref` 迁移为 `material_ids`，复合写法 `"mat2+mat3"` 会被拆成两个 id。

---

## 5. meta.json（年份）

在 v1 基础上：`papers.{id}.modules` 改为与卷内 `modules` 同构的数组；新增 `schema_version`；`source_files` 必须与本机实际文件一致（**2024 登记的 `20240124.pdf` 实际缺失，需订正**）。

---

## 6. media_index.json

```json
{
  "year": 2025,
  "pages":   [ { "path": "media/pages/xxx.jpg", "page": 12, "questions": [76, 77], "width": 1929, "height": 2795 } ],
  "figures": [ { "path": "media/figures/q076.jpg", "number": 76, "paper": "省级", "kind": "figure",
                 "source_page": "media/pages/xxx.jpg", "crop_box_frac": [0.1, 0.2, 0.9, 0.6] } ]
}
```

v1 的 `file` 字段统一改名 `path` 并补 `media/` 前缀；删除 `conventions.path_root`（历史遗留 `gongkao_2025/`）。

---

## 7. catalog.json

根目录全库索引，`years[]` 每项含 `year` / `subject` / `status` / `path` / `papers[]` / `media` / `notes`；顶层新增 `known_gaps[]`。**建议后续由脚本生成，不再手工维护**（v1 期间已出现四处进度互相矛盾）。
