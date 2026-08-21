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

1. `README.md` — 目录与题量总览  
2. `DATA_STATUS.md` — 当前哪一年可用、有何缺口  
3. `_schema/conventions.md` — 改 JSON 时必须遵守的字段  
4. 目标年份的 `meta.json` + `papers/*.json`

**正式数据路径：** `artifacts/gongkao/{YEAR}/xingce/`  
**不要**把新年份数据只写到 `gongkao_2025/`（那是 2025 早期兼容路径）。

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
2. 改完后核对：`actual_question_count` 与各 section 的 `question_count`、题号连续性。
3. 更新该年 `meta.json` 的 `updated` / `status`。
4. 更新根目录 `catalog.json` 与 `DATA_STATUS.md`。
5. 不要删除旧路径 `gongkao_2025/`，除非用户明确要求迁移删除。

---

## 禁止事项

- 不要发明未解析的题干充作真题正文（可用明确「待补全」占位，并在 DATA_STATUS 登记）。
- 不要把市地题号硬套到省级卷而不做模块边界调整。
- 不要在 `artifacts/` 下新增与 `gongkao/` 平行的第二套「国考根目录」。
- 不要把临时解析脚本长期放在 `artifacts/`（应放临时目录）。

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
