# 给智能体 / 协作者的项目说明

本文档用于让后续人类或 AI 在不回溯完整对话的情况下，正确理解并扩展本项目。

---

## 项目目标

1. 将国考行测真题（扫描 PDF）解析为**结构化 JSON**。
2. **按卷种分别保存全量试题**（省级 / 市地级 / 行政执法），不以「一份混合真题」代替三套卷。
3. 保留**图片、表格、公式**等非纯文本元素（整页 + 题级裁剪），供展示与分析。
4. 目录可扩展到**多年份**，字段与卷种文件名保持稳定。

---

## 必读顺序

1. `WORKFLOW.md` — 流程 + **§3 跨年结构差异**（最易踩坑：题号模板不可跨年套用）
2. `README.md` — 目录与题量总览
3. `DATA_STATUS.md` — 当前哪一年可用、有何缺口
4. `_schema/conventions.md` — 改 JSON 时必须遵守的字段
5. 目标年份的 `meta.json` + `papers/*.json`

**数据根目录：** `xingce-structured-data/{YEAR}/xingce/`（即本目录）

> 历史文档提到的 `artifacts/gongkao/`、`gongkao_2025/` 双路径**当前仓库中不存在**，只有一份数据，无需双写、也不存在「别只改一侧」的问题。

---

## 核心业务规则

### 以省级为主卷

- 省级题量最多（2025 为 135），作为全量主卷。
- 市地级、行政执法在共享题基础上，用**差异题**补成各自全量（2025 各 130）。
- 禁止只输出一份「不区分卷种」的混合卷作为最终交付（早期曾有过统一 JSON，现仅作 `all_merged.json` 分析池）。

### 题号

- 每套卷使用**本卷连续题号**。
- 因省级数量为 15 题，判断、资料的起始题号与市地/执法不同（见 `meta.json` 中 `modules`）。
- 差异题可保留 `original_number` / `source_note` / `original_diff_label`，便于追溯注解册。

### 媒体

- 整页：`media/pages/`
- 题级图：`media/figures/`
- 索引：`media/media_index.json`
- 题目内 `media[].path` 使用**相对 media 根**的路径，不写死机器绝对路径。

### 扫描 PDF

- 真题 PDF 多为纯图像，无文字层；解析依赖页面浏览/OCR 类工具，而非 `pdftotext`。
- 差异题多集中在注解册 PDF（如 2025 的省级差异卷、行政执法差异卷）。

---

## 修改数据时

1. 先读对应 `papers/*.json` **全文结构**，再改。
2. 改完运行 `python3 scripts/xingce/validate_papers.py` 校验（题量、题号连续、`type` 枚举、媒体存在性、材料引用、卷内重复、列举条目完整性），不要靠肉眼核对。
3. **状态不要手工改**：`source/EXTRACT_STATUS.json` 与 `meta.json` 的 `modules` 由 `python3 scripts/xingce/sync_status.py` 生成/回填；`updated` / `status` 也由其写入。
4. 更新根目录 `catalog.json` 与 `DATA_STATUS.md`。
5. **考点标签只能走受控词表** `_schema/topic-vocabulary.json`：`topic` 取板块、`tag` 取该板块下的专题，成对填写；无法归类时留 `null` 并进待扩充清单，**不要生造标签**；确需新标签必须先回写词表。
6. **引入新的已知缺陷必须同时给相关题目加 `flags`**（见 `_schema/conventions.md` §3.6）——校验器对已登记缺陷只警告，未登记会以错误退出。禁止为了过校验而删标记或改数据掩盖问题。
7. 格式类变更走 `scripts/xingce/normalize_papers.py`（先 `--dry-run`）。⚠️ 该脚本会跳过已是 v2 的文件，**改规则后必须先 `git checkout` 回退到 v1 再重跑**，否则新规则不生效。

---

## 禁止事项

- 不要发明未解析的题干充作真题正文（可用明确「待补全」占位，并在 DATA_STATUS 登记）。
- 不要把市地题号硬套到省级卷而不做模块边界调整，也不要把某一年的题号模板套给另一年（结构不同，见 `WORKFLOW.md` §3）。
- 不要在本数据目录下另建一套平行的「国考根目录」（历史上曾出现 `gongkao/` 与 `gongkao_2025/` 双份，导致要改两处；现只允许 `xingce-structured-data/{YEAR}/xingce/`）。
- 不要把解析脚本散落在数据目录或临时目录后丢失：可复用的渲染、裁图、校验、组装脚本应放仓库根 `scripts/`，便于跨年重跑。

---

## 2025 数据来源（摘要）

| 文件/卷 | 作用 |
|---------|------|
| 主卷扫描 | 市地级题序主体、资料分析等 |
| 省级差异卷 | 省级独有数量、判断逻辑/图形差异 |
| 行政执法差异卷 | 执法数量/判断/常识法律向差异 |

构建结果：

- `2025/xingce/papers/shengji.json` — 135 题  
- `2025/xingce/papers/shidi.json` — 130 题  
- `2025/xingce/papers/xingzhengzhifa.json` — 130 题  

省级判断末 5 题（111–115）已用差异卷逻辑题（标注 57–61）补全，无「待补全」占位。

---

## 扩展新年份 checklist

- [ ] `./init_year.sh {YEAR}`
- [ ] 原始 PDF 记入 `source/` 或 `meta.source_files`
- [ ] 解析并写入三卷 `papers/*.json`
- [ ] 裁剪/挂接 `media/`，写 `media_index.json`
- [ ] 更新 `meta.json`、`catalog.json`、`DATA_STATUS.md`

详见 `WORKFLOW.md`。
