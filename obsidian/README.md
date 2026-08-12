# 知行 · Obsidian 整理约定

本目录是 **Obsidian → App** 的内容模板库。在 Obsidian 中整理时，请按各子目录下的 `_demo.md` 格式书写；后续导入会按 `type` + 固定标题解析。

## 目录与 App 模块对照

| 目录 | App 模块 / 表 | 说明 |
|------|----------------|------|
| `知识框架/` | `KnowledgeNode` | 已有同步；文件名 stem = 树 key |
| `行测错题/` | `ManualWrong` | 一题一文 |
| `时政文章/` | `Article` + sections | 对齐现有文章 MD 导入 |
| `人民日报/文章/` | `RmrbArticle` | 时评原文 |
| `人民日报/开采本/` | `ShenlunMineLog` | 一日一篇解剖 |
| `人民日报/规范词/` | `ShenlunNormTerm` | 一词一文 |
| `人民日报/语录/` | 语录条目（可进开采或独立库） | 一条一文 |
| `语料本/` | `CorpusItem` | 一条一文 |
| `English-System/03 TV Shows/` | `TvShow` / `TvEpisode` / `TvScene` | 美剧精学笔记（手写对照，暂不导入） |
| `English-System/02 Daily Expressions/` | `TvExpression` | 口语句型卡字段对照 |

## 通用规则

1. **Frontmatter 必填** `type`、`id`（稳定 id，重复导入才能 merge）。
2. **正文用 `##` 固定标题**，标题名与 demo 一致（解析器认标题，不认顺序以外的自由段落当字段）。
3. **App 专属字段不要写进 md**（或写了也会被忽略）：`next_review_at`、`review_stage`、`mastered`、`my_note`、`is_starred`、语料 `status` 等。
4. **`_demo.md` 仅作样板**，勿当正式内容导入；正式笔记请复制后改 `id` 与正文。
5. 可把整个 `obsidian/` 拷进自己的 vault，或只把需要的子目录链到 vault。

## 同步状态（当前）

- 已实现：`知识框架/` → `POST /api/knowledge/sync` / 后台上传
- 未实现：其余目录的导入器（格式先按本约定整理，导入后即可兼容）
