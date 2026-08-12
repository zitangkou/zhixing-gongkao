# 知行 · 全量功能清单

> 产品名：**知行** · Slogan：**读得进，练得出**
> 定位：以公考为主线的个人学习与复盘系统，兼顾英语、读书、身心健康、财务管理。
> 技术：Taro 4 + Vue 3（H5 / 微信小程序）+ FastAPI + Admin（Vue 3 + Element Plus）+ SQLite
>
> ⚠️ **维护约定**：每次新增 / 优化 / 删除功能，必须同步更新本文档对应章节。
> 新增功能前先查阅本文档，防止功能重复或与全局不兼容。
> 配套开发规范见 [`PROJECT_PROMPT.md`](./PROJECT_PROMPT.md)，架构细节见 [`ARCHITECTURE.md`](./ARCHITECTURE.md)。

---

## 目录

1. [产品结构总览](#1-产品结构总览)
2. [学员端功能（按模块）](#2-学员端功能按模块)
3. [管理后台](#3-管理后台)
4. [后端能力域](#4-后端能力域)
5. [共享组件清单](#5-共享组件清单)
6. [横切能力](#6-横切能力)
7. [部署与数据备份](#7-部署与数据备份)
8. [已知缺口与未挂入口](#8-已知缺口与未挂入口)
9. [维护协议](#9-维护协议)

---

## 1. 产品结构总览

### 底部 Tab（3 个）

| Tab | 页面 | 作用 |
|-----|------|------|
| **学习** | `pages/index/index` | 首页：公考主线 + 能力拓展 + 时政推荐 + 复习提醒 |
| **练习** | `pages/question/index` | 刷题模式、错题、套卷、申论训练入口 |
| **我的** | `pages/user/index` | 账号、签到、积分、成长足迹、各模块折叠入口、深色模式 |

### 能力地图

```
知行
├── 公考主线
│   ├── 时政阅读（文章 + 思维导图 + 出题刷题）
│   ├── 资料分析（公式库 + 题型库 + 秒杀技巧 + 专项练习）
│   ├── 申论 · 人民日报（时评 / 开采 / 词库 / 阶梯训练）
│   ├── 知识框架（考点树 + 笔记 / 星标 / 复习）
│   └── 真题套卷（开考 → 交卷 → 成绩）
├── 练习闭环
│   ├── 多种刷题模式 + 艾宾浩斯复习
│   ├── 复习中心（聚合到期任务）
│   ├── 文章错题本
│   └── 行测错题本（手动录入、图片、考点关联）
├── 能力拓展
│   ├── 英语（文章 / 生词 / 跟读 / 音标 / 语法）
│   ├── 剧集英语（剧集 / 场景 / 表达库 / 每周回顾）
│   ├── 读书（今日输出 / 书架 / 人物卡 / 一书一页）
│   ├── 语料本（采集 / 标签 / 知识点挂载）
│   └── 健康（心理 / 身体 / 习惯 · 8 周恢复计划）
├── 生活管理
│   ├── 学习计划（今日清单 / 本周 / 复盘）
│   ├── 事件复盘（时间线 / 知识框架关联）
│   ├── 账本（支出 / 借贷 / 还款）
│   └── 财富（快照 / 原则 / 日志 / 复盘）
└── 成长与账号
    ├── 签到 · 积分 · 排行榜
    ├── 知行足迹（周进度聚合）
    └── 资料 · 反馈 · 充值 · 深色模式
```

### 页面路由总览（98 页）

| 模块 | 页面数 | 路由前缀 |
|------|--------|----------|
| 认证 | 2 | `pages/auth/` |
| 首页 | 1 | `pages/index/` |
| 时政文章 | 2 | `pages/article/` |
| 刷题练习 | 8 | `pages/question/` |
| 用户中心 | 8 | `pages/user/` |
| 语料本 | 2 | `pages/corpus/` |
| 学习计划 | 4 | `pages/plan/` |
| 知识框架 | 1 | `pages/knowledge/` |
| 事件复盘 | 2 | `pages/events/` |
| 复习中心 | 2 | `pages/review/` |
| 真题套卷 | 4 | `pages/exam/` |
| 资料分析 | 9 | `pages/ziliao/` |
| 英语 | 16 | `pages/english/` |
| 人民日报/申论 | 7 | `pages/rmrb/` |
| 读书 | 7 | `pages/dushu/` |
| 健康 | 7 | `pages/health/` |
| 账本 | 6 | `pages/ledger/` |
| 财富 | 7 | `pages/wealth/` |

---

## 2. 学员端功能（按模块）

### 2.1 学习首页

**路径**：`pages/index/index`

- 品牌渐变 Banner + 积分入口（PointsBadge）
- 快捷入口：签到、去练习、今日清单、排行
- **公考主线**：时政阅读、资料分析、申论·人民日报、知识框架、真题套卷
- **能力拓展**：英语、读书、健康、本周计划
- 今日复习任务提醒（到期数量 → 复习中心）
- 时政必读轮播（FeaturedCarousel）+ 推荐阅读（上拉分页）

### 2.2 登录注册

**路径**：`pages/auth/login`、`pages/auth/register`

- 账号密码登录 / 注册
- 是否开放注册由服务端 `ALLOW_REGISTER` 控制（前端读 `/api/config`）

### 2.3 时政文章

**路径**：`pages/article/detail`、`pages/article/mindmap`

- 正文阅读（目录 ArticleOutline、分节翻页 SectionPager）
- 分节已读进度
- 关联知识框架 Tab
- 全屏思维导图（MindMap 组件）
- 读完可进入刷题

### 2.4 刷题练习（Tab）

**路径**：`pages/question/*`

| 页面 | 路由 | 说明 |
|------|------|------|
| 练习首页 | `index` | 刷题模式入口：今日精选 / 随机 / 时间线 / 重点突破 / 按文章练 / 错题重练 |
| 答题 | `taking` | 逐题作答 → 对错与解析 → 结果（正确率、排名、积分） |
| 按文章选题 | `article-pick` | 选择文章后进入该文章题目 |
| 复习答题 | `review` | 复习中心跳转的答题流 |
| 文章错题本 | `wrong` | 错题列表、重做、移除 |
| 行测错题列表 | `manual-list` | 手动录入错题列表；按科目筛选 |
| 行测错题练习 | `manual-quiz` | 错题重做模式 |
| 行测错题编辑 | `manual-edit` | 录入/编辑；可拍照上传图；关联知识考点；掌握标记 |

### 2.5 真题套卷

**路径**：`pages/exam/list` → `detail` → `taking` → `result`

- 筛选：真题 / 自定义 / 模拟
- 试卷详情：题目数、限时、历史 attempt
- 限时作答、交卷
- 成绩与解析、历史记录

### 2.6 资料分析

**路径**：`pages/ziliao/*`

| 页面 | 路由 | 说明 |
|------|------|------|
| 资料分析首页 | `index` | Hub：统计卡 + 公式库/题型库/技巧库/专项练习入口 |
| 公式库列表 | `formulas` | 分类筛选 chips + 公式卡片（LatexBlock 渲染） |
| 公式详情 | `formula-detail` | 公式 + 白话释义 + 例题 |
| 题型库列表 | `types` | 题型分类浏览 |
| 题型详情 | `type-detail` | 题型说明 + 解题步骤 |
| 秒杀技巧列表 | `tricks` | 技巧分类浏览 |
| 技巧详情 | `trick-detail` | 技巧说明 + 适用场景 + 示例 |
| 专项练习 | `drill` | 进度圆点 + 材料折叠 + 逐题作答 + 计时 + 底部导航 |
| 练习结果 | `result` | 分数卡 + 正确率 + 错题解析 + 重做/错题本/返回 |

### 2.7 知识框架

**路径**：`pages/knowledge/index`

- 多棵考点树切换与浏览（KnowledgeTree 组件）
- 节点操作：备注、标重点、掌握度
- 知识点复习（SRS 间隔重复）
- 数据可由 Obsidian Markdown 同步（管理端上传 / 服务端 sync）

### 2.8 复习中心

**路径**：`pages/review/hub`、`pages/review/quiz`

- 聚合到期复习任务（文章错题、手动错题、知识点）
- 按来源分组展示
- 进入复习答题流

### 2.9 学习计划

**路径**：`pages/plan/today`、`week`、`day`、`review`

| 页面 | 说明 |
|------|------|
| 今日清单 | 完成 / 跳过、备注、增删临时任务 |
| 今日复盘 | 完成度、弱项、明日重点、心情 |
| 本周总览 | 按日查看 |
| 按日详情 | 单日任务列表 |

- 模板由管理端按「星期」配置，可复制到另一天

### 2.10 事件复盘

**路径**：`pages/events/index`、`pages/events/edit`

- 事件列表（时间线）
- 录入/编辑：标题、日期、地点、核心内容、补充联想
- 语音输入（VoiceInputBtn）
- 归属知识框架（KnowledgePointPicker）
- 删除二次确认

### 2.11 人民日报 / 申论

**路径**：`pages/rmrb/*`

| 页面 | 路由 | 说明 |
|------|------|------|
| 学习概览 | `index` | 本周开采天数、规范词、今日状态 |
| 时评列表 | `article-list` | 时评文章浏览 |
| 时评详情 | `article-detail` | 阅读 + 结构化解剖 |
| 开采本 | `mines` | 按日记录论点/规范词/骨架等 |
| 开采编辑 | `mine-edit` | 编辑开采记录 |
| 规范词库 | `terms` | 学习 / 掌握状态 |
| 阶梯训练 | `drill` | 造句 · 仿写 · 口述 |

### 2.12 英语

**路径**：`pages/english/*`

| 页面 | 路由 | 说明 |
|------|------|------|
| 英语概览 | `index` | 今日/本周分钟、待复习生词、最近学习 |
| 英文文章列表 | `article-list` | 文章浏览 |
| 英文文章详情 | `article-detail` | 阅读；点词发音/加生词；句末加入跟读本 |
| 生词本 | `vocab` | 复习与掌握 |
| 跟读课列表 | `speaking-list` | 口语课程 |
| 跟读详情 | `speaking-detail` | 句子练习；可上传录音 |
| 语法列表 | `grammar` | 课程列表 |
| 语法详情 | `grammar-detail` | 课程学习 |
| 音标列表 | `phonetic` | DJ 48 音标与进度 |
| 音标详情 | `phonetic-detail` | 音标学习 |

#### 剧集英语（子模块）

| 页面 | 路由 | 说明 |
|------|------|------|
| 剧集列表 | `tv/index` | 剧集浏览 |
| 剧集详情 | `tv/show` | 分集列表 |
| 分集详情 | `tv/episode` | 场景列表 |
| 场景精学 | `tv/scene-study` | 逐句精学 |
| 表达库 | `tv/expression-bank` | 收藏的表达 |
| 每周回顾 | `tv/weekly` | 周学习汇总 |

### 2.13 读书

**路径**：`pages/dushu/*`

| 页面 | 路由 | 说明 |
|------|------|------|
| 读书概览 | `index` | 本周阅读天数 / 输出次数 |
| 书架 | `shelf` | 在读 / 想读 / 已读 CRUD |
| 书详情 | `book-detail` | 书籍信息 + 最近输出 + 子功能入口 |
| 今日阅读 | `today` | 选书 → 预览目标 → 专注读 → 按书类模板输出（可语音输入） |
| 知识资产 | `assets` | 每日卡 / 人物卡 / 一书一页 Tab 浏览 |
| 人物卡编辑 | `person-edit` | 人物卡 CRUD |
| 一书一页编辑 | `summary-edit` | 书摘摘要 CRUD |

### 2.14 语料本

**路径**：`pages/corpus/index`、`pages/corpus/edit`

- 语料采集（CorpusSelectCapture 组件：选中文字 → 采集）
- 标签、来源、知识点挂载
- 沉淀到规范词

### 2.15 健康

**路径**：`pages/health/*`

面向备考期身心恢复（**自我管理工具，非医疗诊断**）。

| 页面 | 路由 | 说明 |
|------|------|------|
| 概览 | `index` | 当前第几周 / 阶段、连续打卡、三域入口、本周趋势 |
| 今日打卡 | `today` | 阶段微任务勾选 + 习惯/身体/心理指标一次保存 |
| 心理训练 | `mind` | 能量与焦虑；暴露阶梯任务；CBT 焦虑五问；反刍限时；本周小计 |
| 身体 | `body` | 胃舒适度、湿气感、湿疹/皮炎严重度、散步分钟、关联备注；本周对照 |
| 习惯 | `habits` | 心情、睡眠、饮食规律勾选；本周列表 |
| 晚间复盘 | `review` | 今日最好的事、明日小目标；可补 CBT / 反刍 |
| 阶段说明 | `phase` | 8 周分 4 阶段只读说明；可重置计划起点 |

方法对应（白话）：行为激活（先充电/散步）、CBT、暴露阶梯、反刍刹车、节律习惯。

### 2.16 账本

**路径**：`pages/ledger/*`

| 页面 | 路由 | 说明 |
|------|------|------|
| 账本首页 | `index` | 收支概览 + 最近记录 |
| 支出编辑 | `expense-edit` | 记支出（金额、分类、备注、图片） |
| 借贷编辑 | `loan-edit` | 记借出/借入 |
| 借贷详情 | `loan-detail` | 借贷明细 + 还款记录 |
| 还款编辑 | `repay-edit` | 记还款 |
| 往来对象 | `person` | 按人汇总往来 |

### 2.17 财富

**路径**：`pages/wealth/*`

| 页面 | 路由 | 说明 |
|------|------|------|
| 财富首页 | `index` | 财务概览入口 |
| 总览 | `overview` | 资产/负债/净值 |
| 快照编辑 | `snapshot-edit` | 定期财务快照 |
| 原则 | `rules` | 个人财务原则 |
| 日志列表 | `journal` | 财务日志 |
| 日志编辑 | `journal-edit` | 记日志 |
| 周期复盘 | `review` | 阶段性财务复盘 |

### 2.18 我的 · 成长与账号

**路径**：`pages/user/*`

| 页面 | 路由 | 说明 |
|------|------|------|
| 我的首页 | `index` | 头像/昵称 + 签到/积分/排行快捷 + 各模块折叠入口 + 深色模式开关 |
| 个人资料 | `profile` | 头像（≤2MB）、昵称/邮箱/手机、改密 |
| 签到 | `signin` | 日历（SignCalendar）、连续天数、积分 |
| 积分明细 | `points` | 收入/支出流水 |
| 刷题排行 | `rank` | 日 / 周 / 月 / 总（RankList） |
| 知行足迹 | `growth` | 签到/本周分钟/正确率/积分；五领域进度条；本周投入柱状图 |
| 反馈建议 | `feedback` | 提交文本 |
| 充值 | `recharge` | 套餐 UI（**模拟支付**，见缺口） |

---

## 3. 管理后台

**访问**：部署后 `https://域名/manage/`（本地 `admin-web` 开发服）

| 菜单 | 能力 |
|------|------|
| 文章管理 | 列表/筛选；新建编辑；Markdown 导入；置顶/今日推荐；审核发布；题目 CRUD / AI 出题 / 导入 / 批量审核 |
| 分类管理 | 分类树 CRUD |
| 用户管理 | 学员列表（积分、状态等） |
| 知识框架 | 上传 md、树与节点、同步状态、删树 |
| 学习计划 | 按星期的任务模板；复制到另一天；启停 |
| 试卷题库 | 真题/自定义/模拟卷与题目；导入上传 |
| 英语学习 | 英文文章、口语课、音标 |
| 资料分析 | 公式、题型、秒杀技巧、练习资源 |
| 人民日报 | 时评文章、规范词分类、骨架模版、句式类型、论证方法 |
| 系统设置 | `SystemSetting` 键值编辑；角色权限矩阵（只读） |

管理员独立登录（与学员 JWT 分离），RBAC 权限矩阵。

---

## 4. 后端能力域

公开前缀：`/api`（需登录的接口走 App JWT）

| 域 | 代表能力 |
|----|----------|
| 配置/认证 | 公开配置、注册、登录 |
| 用户 | 资料、改密、头像上传 |
| 文章/刷题 | 日更与推荐、答题、错题、测验完成与排行 |
| 学习记录 | 阅读记录、分节已读 |
| 签到积分 | 签到、积分、流水、总榜 |
| 充值反馈 | 套餐列表、模拟下单、反馈 |
| 复习 | 复习任务列表与完成（SRS 间隔重复） |
| 计划 | 今日/周/日清单、任务 CRUD、日复盘 |
| 知识 | 树列表、详情、同步、节点更新、知识点复习 |
| 行测错题 | CRUD + 图片上传 |
| 套卷 | 试卷、开考、作答、交卷、历史 |
| 资料分析 | 公式/题型/技巧 CRUD、专项练习、提交、结果 |
| 英语 | 文章、生词、发音、跟读、语法、音标、学习日志、统计 |
| 剧集英语 | 剧集、分集、场景、表达、学习会话、每周回顾 |
| ASR/TTS | 语音转写（可配阿里/腾讯，默认前端 Web Speech）；发音 |
| 申论 RMRB | 元数据、统计、时评、开采、词库、训练、骨架模版 |
| 语料本 | 语料 CRUD、标签、知识点挂载 |
| 事件复盘 | 事件 CRUD、知识框架关联 |
| 足迹 | `GET /api/growth/overview` |
| 健康 | overview / phases / tasks / daily / week / reset / focus |
| 读书 | stats / books / daily / persons / summaries |
| 账本 | 支出 / 借贷 / 还款 / 往来对象 |
| 财富 | 快照 / 原则 / 日志 / 复盘 |

管理端前缀：`/admin`（文章、用户、知识、计划、试卷、英语、资料分析、人民日报、设置、角色等）。

---

## 5. 共享组件清单

| 组件 | 文件 | 用途 | 使用页面 |
|------|------|------|----------|
| AppTabBar | `AppTabBar.vue` | 自定义底部 TabBar（3 tab） | 首页、练习、我的 |
| AppFeedback | `AppFeedback.vue` | 全局 Toast / Confirm 宿主 | AppTabBar 内嵌（小程序）/ body 挂载（H5） |
| ArticleCard | `ArticleCard.vue` | 文章卡片 | 首页推荐、文章列表 |
| ArticleOutline | `ArticleOutline.vue` | 文章目录 | 文章详情 |
| ArticleSections | `ArticleSections.vue` | 文章分节内容 | 文章详情 |
| SectionPager | `SectionPager.vue` | 分节翻页器 | 文章详情 |
| BrandLogo | `BrandLogo.vue` | 品牌 Logo | 登录、首页 |
| CorpusSelectCapture | `CorpusSelectCapture.vue` | 选中文字采集 | 语料本 |
| FeaturedCarousel | `FeaturedCarousel.vue` | 必读轮播 | 首页 |
| KnowledgeTree | `KnowledgeTree.vue` | 知识树递归展示 | 知识框架 |
| KnowledgePointPicker | `KnowledgePointPicker.vue` | 知识点选择弹层 | 事件编辑、错题编辑 |
| LatexBlock | `LatexBlock.vue` | KaTeX 公式渲染 | 资料分析公式页 |
| MindMap | `MindMap.vue` | 思维导图 | 文章思维导图 |
| PointsBadge | `PointsBadge.vue` | 积分徽章 | 首页 Banner |
| QuestionItem | `QuestionItem.vue` | 题目卡片 | 答题、错题 |
| RankList | `RankList.vue` | 排行榜列表 | 排行页 |
| SignCalendar | `SignCalendar.vue` | 签到日历 | 签到页 |
| VoiceInputBtn | `VoiceInputBtn.vue` | 语音输入按钮 | 事件编辑、读书输出 |
| WheelPicker | `WheelPicker.vue` | 滚轮选择器 | 健康、账本 |

---

## 6. 横切能力

| 主题 | 说明 |
|------|------|
| 鉴权 | 学员 JWT；管理员独立 token；RBAC 权限矩阵 |
| 积分规则 | 签到/阅读/答对等；部分基数可在系统设置里配 |
| 深色主题 | CSS 变量（`--zk-*`）+ `theme-dark` class + 「我的」开关；`utils/theme.ts` 同步原生壳 |
| 品牌色 | 亮色 `#D0021B` / 暗色 `#E85D6A`；`useBrandColor()` 供图标 props |
| 媒体文件 | 头像、错题图、跟读录音、账本图片 → `data/uploads/`（**不进 SQLite**） |
| Mock 模式 | `USE_MOCK=true npm run dev:h5` 走本地 Mock；默认连真实 API |
| LLM | `llm_enabled` 控制 AI 出题等，默认关闭 |
| 爬虫 | 代码保留但触发与定时已关闭 |
| 注册开关 | 生产建议 `ALLOW_REGISTER=false` |
| 反馈系统 | `utils/platform.ts`：showToast / showConfirm / promptText / copyText（禁止直接调 Taro.showToast） |
| 导航封装 | `utils/platform.ts`：navigateTo / switchTab |
| 表单防丢 | `utils/formFlush.ts`：保存前 flush 语音输入 |
| 记忆曲线 | `utils/memoryCurve.ts`：SRS 间隔重复计算 |

---

## 7. 部署与数据备份

详见 [`deploy-ali.md`](./deploy-ali.md)（本地开发启动、Docker 发版、**整包 data 备份与恢复**）。

要点：

- 生产数据在 Docker 卷中：`zhengkao.db` + `uploads/` + `knowledge/`
- 只备份库文件会丢图片；请整包 tar
- 服务器 cron 日备 + 本机/网盘异地
- **禁止** `docker compose down -v`（会删卷）

---

## 8. 已知缺口与未挂入口

| 项 | 现状 |
|----|------|
| 充值页 | 路由与页面有，**「我的」未挂菜单**；支付为 mock |
| 英语语法 Admin | 有 API/组件，**英语后台 tabs 未挂语法** |
| 爬虫 | Admin 触发接口已注释关闭 |
| 健康/读书/足迹 | 无独立 Admin CRUD（用户侧数据为主） |
| 支付 | 无真实微信/支付宝对接 |
| 账本/财富 Admin | 无管理端入口（纯用户侧数据） |
| 事件复盘 Admin | 无管理端入口 |
| 语料本 Admin | 无管理端入口 |

---

## 9. 维护协议

> **每次功能变更必须执行以下流程，防止功能重复或全局不兼容。**

### 9.1 新增功能前

1. **查本文档**：确认是否已有相同/相似功能（查能力地图 + 页面路由总览）
2. **查 PROJECT_PROMPT.md**：确认布局、样式、交互遵循全局规范
3. **查 app.config.ts**：确认路由未重复
4. **查共享组件清单**：优先复用，禁止重复造轮子

### 9.2 新增/优化/删除功能后

1. **更新本文档**：
   - 能力地图（§1）：新增/调整节点
   - 页面路由总览（§1）：更新页面数
   - 对应模块章节（§2）：补充页面表格或修改说明
   - 管理后台（§3）：如有新菜单
   - 后端能力域（§4）：如有新 API 域
   - 共享组件清单（§5）：如有新组件
   - 已知缺口（§8）：如修复了缺口或产生新缺口
2. **更新 PROJECT_PROMPT.md**：如涉及新的交互模式或布局类型
3. **更新 ARCHITECTURE.md**：如涉及新的数据模型或服务层

### 9.3 快速对照入口

| 想了解 | 看哪里 |
|--------|--------|
| 全部页面 | `src/app.config.ts` → `pages` 数组 |
| 全部组件 | `src/components/` 目录 |
| 全部 Store | `src/store/` 目录 |
| 后台菜单 | `server/admin-web/src/config/nav.ts` |
| 后台路由 | `server/admin-web/src/router/index.ts` |
| API 接口 | `src/api/index.ts`（学员端）/ `server/app/api/`（后端） |
| 数据模型 | `server/app/models/__init__.py` |

---

*最后更新：2026-08-01 · 基于 app.config.ts 98 个页面路由 + 19 个共享组件全量整理*
