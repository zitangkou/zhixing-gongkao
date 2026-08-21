# 真题数据化工作流

从扫描 PDF 到可分析 JSON 的推荐流程。

---

## 阶段 0：初始化年份

```bash
cd artifacts/gongkao
./init_year.sh 2024
```

生成：

- `{YEAR}/xingce/meta.json`
- `{YEAR}/xingce/papers/`
- `{YEAR}/xingce/media/{pages,figures,formulas}/`
- `{YEAR}/xingce/source/`

---

## 阶段 1：收集源文件

1. 将原始 PDF 放入 `source/`，或仅在 `meta.source_files` 中登记文件名。
2. 区分：**完整试卷** vs **差异题注解册**（省级差异、行政执法差异）。
3. 确认该年三类卷题量（通常省 135、市地/执法 130；以当年大纲为准）。

---

## 阶段 2：页面提取与文本解析

1. 扫描件无文字层时，用页面级工具按页抽取题干与选项（不要依赖空的 `pdftotext`）。
2. 按模块归类：政治 / 常识 / 言语 / 数量 / 判断 / 资料。
3. 标注每题所属卷种：共享 / 仅省级 / 仅市地 / 仅行政执法。
4. 资料分析单独保存 `materials`（材料正文、表格结构化 `table_data` 如有）。

---

## 阶段 3：组装三套全量卷

### 原则

- **先做省级全量**（题号连续、数量 15、后续模块题号后移）。
- 再做市地、行政执法：共享题复制 + 差异题替换/追加，题量凑满官方结构。

### 省级题号模板（2025 及同类年份）

```
政 1–20 → 常 21–35 → 言 36–65 → 数 66–80 → 判 81–115 → 资 116–135
```

### 市地 / 执法题号模板

```
政 1–20 → 常 21–35 → 言 36–65 → 数 66–75 → 判 76–110 → 资 111–130
```

### 字段

每题至少：`number`, `stem`, `options`, `type`, `paper`。  
差异题增加：`source_note`、`original_number`（可选）。  
有图：`media: [{ "path": "media/figures/...", "kind": "figure", "label": "..." }]`。

写出：

- `papers/shengji.json`
- `papers/shidi.json`
- `papers/xingzhengzhifa.json`

可选：`papers/all_merged.json` 仅作跨卷对比，不作为「唯一真题」。

---

## 阶段 4：图片与公式

1. 导出需要的整页到 `media/pages/`。
2. 图形推理、几何、资料图表裁剪到 `media/figures/`。
3. 公式可截图入 `media/formulas/`，或题内 `formulas` 存 LaTeX。
4. 更新 `media/media_index.json`（path、题号、kind、可选 crop 框）。
5. 题目 `media[].path` 与索引一致。

---

## 阶段 5：校验

- [ ] 三卷 `actual_question_count` 符合官方题量  
- [ ] 题号在模块内连续、无重复  
- [ ] 无残留「待补全」占位（或已在 DATA_STATUS 登记）  
- [ ] 省级数量为 15，另两卷为 10  
- [ ] 资料 `materials` 与小题对应  
- [ ] 媒体文件真实存在  

---

## 阶段 6：登记

1. 更新 `{YEAR}/xingce/meta.json`（status、updated、modules 区间）。
2. 更新根 `catalog.json` 对应 year 条目。
3. 更新 `DATA_STATUS.md`。

---

## 常见坑

| 问题 | 处理 |
|------|------|
| 题号在常识/数量等模块重复 | 用「模块 + 题号」或题干前缀索引，组装时按 section 取题 |
| 只解析了市地卷 | 必须再处理差异卷，否则省级/执法不完整 |
| 混合成一份 130 题交差 | 不符合本项目交付标准 |
| 图片绝对路径 | 改为相对 `media/` |
| 占位题忘记补 | 在 DATA_STATUS 列出，补全文后去掉占位标记 |
