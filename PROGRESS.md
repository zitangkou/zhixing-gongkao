# 知行公考 · 项目进度

> 更新：2026-08-16
> 定位：纯公考备考应用（时政阅读、资料分析、申论、真题套卷、错题闭环），Taro 4 + Vue 3 + FastAPI + SQLite

## 1. 阶段进度

| 阶段 | 内容 | 状态 |
|---|---|---|
| Phase 0 | 品牌改名（知行公考）+ 端口统一（10087 / 8001） | ✅ |
| Phase 1 | 后端裁剪（删非公考域 + 充值） | ✅ |
| Phase 2 | 前端裁剪 + 品牌换色 | ✅ |
| Phase 3 | 4-Tab 布局 + 今日驾驶舱 + 考试倒计时 | ✅ |
| Phase 4 | `activity_events` 埋点（7 处） | ✅ |
| Phase 5/6 | admin-web 裁剪重建 + 仓库清理 | ✅ |
| P0 | 质量基线：lint 0 问题、核心闭环测试 20 passed、CI 三条门禁 | ✅ |
| P1 | 残留清理：空壳注释 / 爬虫删除 / Obsidian 配置化 / 计划模板公考化 | ✅ |
| P2 | 按域拆分：路由 / schema / model / api / mock + 后台分包 + 迁移收拢 | ✅ |
| 部署 | 一键部署 `deploy.sh` + 宿主机 Nginx 网关 + 整包备份 | ✅ 2026-08-16 |

## 2. 当前质量基线（2026-08-16）

- 后端 `pytest`：**20 passed**（含答题→错题→SRS、套卷交卷、签到积分、RBAC、资料练习 5 个闭环用例）
- 前端 `npm run lint`：**0 problems**（与 `prettier` 稳定共存）
- H5 / 管理后台构建：通过（admin 主入口分包后 59KB）
- CI：GitHub Actions（lint + pytest + admin build）
- 类型检查：`src/api`、`src/mock` 拆分后新增代码零错误

## 3. 已知遗留

| 项 | 说明 |
|---|---|
| `src/mock/shiwuwu-plan.ts` 类型报错 | 拆分前既有（`tsc --noEmit` 可复现），不影响构建 |
| element-plus chunk 1.07MB | 已拆独立 vendor；后续可按需引入（unplugin-vue-components） |
| 行为事件统计页 | `activity_events` 已埋点，无统计/可视化（M4：上岸卡片 / 能力雷达 / 里程碑） |
| 足迹 Admin 入口 | 仅学员端有 growth 数据 |
| LLM 出题 / 云端 ASR | `LLM_ENABLED=false`、`ASR_PROVIDER=none`，按需开启 |
| 支付 / 会员 | 无真实微信/支付宝对接（原充值页已移除） |

## 4. 后续路线（按优先级）

| 优先级 | 事项 |
|---|---|
| 高 | 行为事件统计页（M4：上岸卡片 / 能力雷达 / 里程碑） |
| 中 | 足迹 Admin 入口 |
| 中 | AI 出题、云端语音识别按需开启 |
| 中 | element-plus 按需引入 |
| 低 | 支付 / 会员、爬虫重建（如需自动抓取时政） |

## 5. 最近提交

```text
9e0edb3 chore: 管理后台清理 + 文档/待优化清单同步
0d89ffc refactor(src): 按域拆分 api/mock + 多品牌主题小程序端跟随 + 数据导出/导入前端
222b040 refactor(server): 按域拆分 api/models/schemas + 清理爬虫/权限残留 + 数据导出/导入后端 + CI 与核心测试
73e6183 chore: 删除 admin-web 误生成的垃圾文件
7591219 feat: 多品牌色主题切换（5 套，默认中国红）
```

## 6. 相关文档

- 全量功能清单 → [`FEATURES.md`](./FEATURES.md)
- 架构与模块边界 → [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- 待优化清单 → [`OPTIMIZATION.md`](./OPTIMIZATION.md)
- 部署手册 → [`DEPLOY.md`](./DEPLOY.md)
