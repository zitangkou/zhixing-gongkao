# 题目与卷种字段约定

机器与人均应遵守以下结构，保证多年数据可合并分析。

---

## 1. 卷文件顶层

```json
{
  "exam_year": 2025,
  "exam_name": "2025年度国家公务员考试行政职业能力测验",
  "paper_type": "省级",
  "total_questions": 135,
  "actual_question_count": 135,
  "notes": "构建说明、差异来源等",
  "media_index": "media/media_index.json",
  "sections": []
}
```

`paper_type` 取值：

- `省级`
- `市地级`
- `行政执法类`

文件名固定：

| paper_type | 文件名 |
|------------|--------|
| 省级 | `shengji.json` |
| 市地级 | `shidi.json` |
| 行政执法类 | `xingzhengzhifa.json` |

---

## 2. 模块 section

```json
{
  "name": "政治理论",
  "question_count": 20,
  "questions": [],
  "materials": []
}
```

`name` 固定六类（顺序建议与试卷一致）：

1. `政治理论`
2. `常识判断`
3. `言语理解与表达`
4. `数量关系`
5. `判断推理`
6. `资料分析`

`materials` 仅资料分析使用：材料原文、表格等。

---

## 3. 单题 question

### 必填

| 字段 | 类型 | 说明 |
|------|------|------|
| number | int | **本卷**连续题号 |
| stem | string | 题干 |
| options | object | `{"A":"...","B":"...","C":"...","D":"..."}` |

### 强烈建议

| 字段 | 类型 | 说明 |
|------|------|------|
| type | string | 如 `逻辑判断`、`图形推理`、`定义判断`、`资料分析` |
| paper | string | 与卷顶层 paper_type 一致或更细标签 |
| media | array | 见下 |
| source_note | string | 差异题、映射、共享说明 |

### 可选

| 字段 | 类型 | 说明 |
|------|------|------|
| subtype | string | 如 `削弱`、`加强`、`翻译推理` |
| original_number | int | 来源卷或注解册原题号 |
| original_diff_label | int/string | 差异卷圈号标注 |
| formulas | array | LaTeX 字符串或公式图 path |
| answer | string | 若入库解析答案 |
| explanation | string | 若入库解析 |

### media 项

```json
{
  "path": "media/figures/q076.jpg",
  "kind": "figure",
  "label": "图形推理76题干+选项"
}
```

`kind` 建议：`page` | `figure` | `table` | `formula`。

---

## 4. meta.json（年份）

```json
{
  "exam_year": 2025,
  "exam_name": "...",
  "subject": "行政职业能力测验",
  "subject_code": "xingce",
  "papers": {
    "shengji": {
      "paper_type": "省级",
      "total_questions": 135,
      "modules": {},
      "file": "papers/shengji.json"
    },
    "shidi": {
      "paper_type": "市地级",
      "total_questions": 130,
      "modules": {},
      "file": "papers/shidi.json"
    },
    "xingzhengzhifa": {
      "paper_type": "行政执法类",
      "total_questions": 130,
      "modules": {},
      "file": "papers/xingzhengzhifa.json"
    }
  },
  "source_files": [],
  "media": {
    "pages_dir": "media/pages",
    "figures_dir": "media/figures",
    "formulas_dir": "media/formulas",
    "index": "media/media_index.json"
  },
  "status": "ready | empty | partial",
  "updated": "YYYY-MM-DD"
}
```

`modules` 建议记录各模块题号闭区间，便于校验。

---

## 5. media_index.json

建议结构：

```json
{
  "year": 2025,
  "pages": [
    { "path": "media/pages/p12.jpg", "page": 12, "questions": [76, 77] }
  ],
  "figures": [
    {
      "path": "media/figures/q076.jpg",
      "number": 76,
      "paper": "市地级",
      "kind": "figure"
    }
  ]
}
```

path 必须可相对年份 `xingce/` 解析。

---

## 6. catalog.json

根目录全库索引：`years[]` 中每项含 `year`、`status`、`path`、`papers[]`（id / file / total_questions）。  
新增或完成一年后必须更新。
