# 知行公考 · 项目进度

> 更新：2026-08-28
> 定位：纯公考备考应用矩阵（综合母应用 + 申论/政治理论垂直应用 + 内容运营 + 真题库），Taro 4 + Vue 3 + FastAPI + SQLite

## 1. 阶段进度

| 阶段 | 内容 | 状态 |
|---|---|---|
| Phase 0 | 品牌改名（知行公考）+ 端口统一（10087 / 8001） | ✅ |
| Phase 1 | 后端裁剪（删非公考域 + 充值） | ✅ |
| Phase 2 | 前端裁剪 + 品牌换色 | ✅ |
| Phase 3 | 4-Tab 布局 + 今日驾驶舱 + 考试倒计时 | ✅ |
| Phase 4 | `activity_events` 埋点（7 处） | ✅ |
| Phase 5/6 | admin-web 裁剪重建 + 仓库清理 | ✅ |
| P0 | 质量基线：lint 0 errors、核心闭环测试 21 passed、CI 三条门禁 | ✅ |
| P1 | 残留清理：空壳注释 / 爬虫删除 / Obsidian 配置化 / 计划模板公考化 | ✅ |
| P2 | 按域拆分：路由 / schema / model / api / mock + 后台分包 + 迁移收拢 | ✅ |
| 部署 | 一键部署 `deploy.sh` + 宿主机 Nginx 网关 + 整包备份 | ✅ 2026-08-16 |
| 真题资产 | 2025 国考三卷题面与媒体已入库（答案/解析/细题型待补）；2024 省级 135 题已入库、市地/执法卷已组装（差异精确替换待完善），见 `xingce-structured-data/DATA_STATUS.md` | 🟡 2026-08-23 |
| 双产品 Sprint 0 | 申论/政治理论 PRD、共享底座设计、`product_key` 后端上下文、公开配置、前端请求/上传注入和产品 Store | 🟡 2026-08-23 第一批完成 |
| 双产品 Sprint 0 | 通用今日任务、五态学习状态机、服务端草稿与跨端断点恢复、产品隔离、前端任务 Store | ✅ 2026-08-23 第二批完成 |
| 申论 Sprint 1 | 垂直今日首页、审核文章自动编排、单主任务入口、阅读/三刀进度回写、Mock 演示数据 | ✅ 2026-08-23 第一批完成 |
| 申论 Sprint 1 | 小题短作答、三项规则自检、自动草稿、表达沉淀入规范词库、今日任务完成页 | ✅ 2026-08-23 第二批完成 |
| 政治理论 Sprint 1 | 垂直今日首页、3题/证据质量门、权威文章自动编排、独立蓝色主题与三产品动态导航 | ✅ 2026-08-23 第一批完成 |
| 政治理论 Sprint 1 | 无答案读前定向、原文精读门、证据题过滤、测验结果回写、逐题错因归类与完成页 | ✅ 2026-08-23 第二批完成 |
| 内容运营 Sprint 1 | 10个固定栏目模板、四渠道变体、母资产/深链/排期、教研与运营双审核状态机、Admin API | ✅ 2026-08-23 第一批完成 |
| 内容运营 Sprint 1 | 管理后台模板浏览、发布包新建/编辑、渠道文案维护、审核推进与驳回、审核中编辑锁定 | ✅ 2026-08-23 第二批完成 |
| 内容运营 Sprint 1 | 月历式内容排期、待发布素材包 JSON 导出、人工发布清单与导出状态门 | ✅ 2026-08-23 第三批完成 |
| 内容运营 Sprint 1 | 发布包结构化栏目槽位、模板字段校验、缺项阻断送审、旧库自动补列 | ✅ 2026-08-23 第四批完成 |
| 内容运营 Sprint 1 | 已发布文章一键生成结构化母稿与四平台草稿、渠道深链归因、缺项人工补齐与重复生成保护 | ✅ 2026-08-23 第五批完成 |
| 内容运营 Sprint 1 | 未来7天内容库存、双科配比、审核积压、待发布与未排期提醒，状态变更实时刷新 | ✅ 2026-08-23 第六批完成 |
| 垂类应用独立化 | 申论/政治理论拆为 `apps/` 独立 Taro 工程（端口 10088/10089），独立认证与账号、红色 Tab 导航、每日训练/学习闭环、反馈与训练历史 | ✅ 2026-08-23~24 |
| 部署升级 | 单 Docker 镜像编译三套 H5（综合 `/` + 申论 `/shenlun/` + 理论 `/theory/`），共用一个 FastAPI；compose 绑定可配（默认 127.0.0.1）+ healthcheck | ✅ 2026-08-24 |
| 内容运营·日常 | 每日多渠道运营启动（`content/daily/`）；发布包按 campaign 隔离去重修复 | ✅ 2026-08-24~25 |
| 原应用流程回填 | 定义迁移基线（`docs/architecture/original-app-feature-inventory.md`）；申论三刀法/资产复盘/文章采集、理论读前定向与复习/结构化精读/证据测验已回填；错题闭环回填中 | 🟡 2026-08-24~26 |
| 内容运营·双审核留痕 | `ContentReviewRecord` 审核留痕表 + 流转 checklist + review-config/reference-library API + 后台 UI（**未提交**） | 🟡 进行中 |
| 理论错题复习 | theory-app `StudyRecord`/`ReviewTask` 复习模型 + 新页 `question/review.vue`（**未提交**） | 🟡 进行中 |

## 2. 当前质量基线（2026-08-23 实测）

- 后端 `server/.venv/bin/python -m pytest -q`：**24 passed，70 warnings**（warning 来自 `python-jose` 使用即将弃用的 `datetime.utcnow()`）
- 前端 `npm run lint`：**0 errors，85 warnings**；门禁通过，但格式类 warning 已重新积累，不能再表述为“0 problems”
- 管理后台构建：2026-08-23 实测通过（主入口 59.57KB，Element Plus chunk 1.07MB）
- H5 构建：本机运行时卡在 `system-configuration` Rust worker 的 macOS `NULL object` panic，已中止；更像本机构建环境问题，但本次不能记为通过
- CI：GitHub Actions（lint + pytest + admin build）
- 类型检查：`src/api`、`src/mock` 拆分后新增代码零错误
- 规模快照：学员端 **53 个页面路由**、**24 个共享组件**；FastAPI **107 个 `/api` 路由**、**109 个 `/admin` 路由**

## 3. 已知遗留

| 项 | 说明 |
|---|---|
| `src/mock/shiwuwu-plan.ts` 类型报错 | 拆分前既有（`tsc --noEmit` 可复现），不影响构建 |
| 前端 lint warning | 当前 85 条，集中在 Vue 属性顺序、标签换行与缩进；无 error，但应避免继续增长 |
| FastAPI 元信息仍为旧品牌 | `server/app/main.py` 的 title/description 仍写“政考通 / 政治理论学习”，影响 `/docs` 展示 |
| 依赖弃用告警 | 后端测试产生 37 条 `python-jose` 的 `datetime.utcnow()` 弃用 warning |
| H5 本机构建异常 | `npm run build:h5` 触发 `system-configuration` Rust worker 的 macOS `NULL object` panic 后挂起；需在 CI 或干净 Node 环境复核 |
| element-plus chunk 1.07MB | 已拆独立 vendor；后续可按需引入（unplugin-vue-components） |
| 行为事件统计页 | `activity_events` 已埋点，无统计/可视化（M4：上岸卡片 / 能力雷达 / 里程碑） |
| 足迹 Admin 入口 | 仅学员端有 growth 数据 |
| LLM 出题 / 云端 ASR | `LLM_ENABLED=false`、`ASR_PROVIDER=none`，按需开启 |
| 支付 / 会员 | 无真实微信/支付宝对接（原充值页已移除） |

## 4. 后续路线（按优先级）

产品路线已调整为垂直题型矩阵：优先孵化申论，其次政治理论、资料分析、数量关系、言语理解、判断推理；详细需求与共享边界见 [`PRODUCT_SPLIT_PLAN.md`](./PRODUCT_SPLIT_PLAN.md)。现有综合应用继续作为能力母体和验证场，不立即复制成六套代码。

2026-08-23 首期范围进一步收敛：只实现**申论、政治理论**两个垂直产品，其余四科暂停独立产品开发。共同底座按题型插件设计，为资料、数量、言语、判断保留接入契约但不提前开发；账号运营从审核后的教学母资产派生内容，以首训完成和留存衡量转化。执行方案见 [`TWO_PRODUCT_MVP_PLAN.md`](./TWO_PRODUCT_MVP_PLAN.md)。

| 优先级 | 事项 |
|---|---|
| 高 | **小程序发布**（知行策论/知行日知）：✅ 双 AppID 已填、产品名定稿、域名 `zhixinggk.ltd`（备案终审中）、weapp 生产构建完成（各 1.0MB）；**剩余**：备案通过 → `certbot --nginx -d zhixinggk.ltd` 上 HTTPS → 微信后台配 request 合法域名 + 隐私保护指引 → 上传提审 |
| 高 | 收尾未提交改动：content-ops 双审核留痕、theory 错题复习（测试 24 passed，待提交） |
| 高 | 行为事件统计页（M4：上岸卡片 / 能力雷达 / 里程碑） |
| 高 | 修正 FastAPI `/docs` 的旧品牌元信息，并清理/约束 lint warning |
| 中 | 足迹 Admin 入口 |
| 中 | AI 出题、云端语音识别按需开启 |
| 中 | element-plus 按需引入 |
| 低 | 支付 / 会员、爬虫重建（如需自动抓取时政） |

## 5. 最近提交

```text
6ea7b20 feat(theory): restore original wrong-question loop
effc281 feat(theory): restore original evidence quiz flow
906fbb0 fix(content-ops): scope duplicate packages by campaign
17d824b feat(theory): migrate original structured reading
e3f4c2e feat(theory): restore original orientation and review flow
c2d374b feat(shenlun): migrate article capture workflow
53898e0 feat(shenlun): migrate original asset review loop
dab8bab feat(shenlun): restore original three-knife workflow
d3ad94c docs(architecture): define original app migration baseline
6534591 fix(auth): refine vertical app form layout
bf7b56b feat(content): start daily multi-channel operations
2e8d2c0 feat(deploy): publish vertical h5 apps
4c60892 feat(shenlun): add feedback and training history
2c535f2 feat(theory): complete daily learning loop
b508b2a feat(shenlun): complete standalone daily training flow
f0f60fd feat(shenlun): add standalone reading flow
242ba43 feat: complete standalone account basics
aa1fc79 feat: add standalone app authentication
c78b359 feat: unify standalone apps with red tab navigation
f01b602 feat: split shenlun and theory into standalone apps
d4fa99a feat: add content inventory dashboard
5220a11 feat: generate channel drafts from reviewed articles
```

## 6. 相关文档

- 全量功能清单 → [`FEATURES.md`](./FEATURES.md)
- 架构与模块边界 → [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- 待优化清单 → [`OPTIMIZATION.md`](./OPTIMIZATION.md)
- 部署手册 → [`DEPLOY.md`](./DEPLOY.md)
- 公共知识库项目总览 → `Obsidian/00-公共知识库/项目/知行公考.md`
- 垂直题型产品矩阵 → [`PRODUCT_SPLIT_PLAN.md`](./PRODUCT_SPLIT_PLAN.md)
- 产品与真题整体实施方案 → [`DETAILED_IMPLEMENTATION_PLAN.md`](./DETAILED_IMPLEMENTATION_PLAN.md)
- 政治理论 × 申论双产品 MVP → [`TWO_PRODUCT_MVP_PLAN.md`](./TWO_PRODUCT_MVP_PLAN.md)
- 模板化账号内容运营 → [`CONTENT_OPERATIONS_PLAN.md`](./CONTENT_OPERATIONS_PLAN.md)
- 申论开发 PRD → [`docs/products/shenlun-prd.md`](./docs/products/shenlun-prd.md)
- 政治理论开发 PRD → [`docs/products/theory-prd.md`](./docs/products/theory-prd.md)
- 多题型共享底座 → [`docs/architecture/product-foundation.md`](./docs/architecture/product-foundation.md)
