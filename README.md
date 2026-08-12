# 知行公考

纯公考备考应用 — 基于 **Taro 4 + Vue 3 + TypeScript + NutUI + Pinia** 的跨端应用（微信小程序 + H5）。

Slogan：**以「上岸」为唯一目标**

## 功能

- 今日驾驶舱：考试倒计时、今日清单、复习提醒、昨日足迹
- 公考主线：时政阅读、资料分析、申论/人民日报、知识框架、真题套卷
- 练习闭环：多种刷题模式、错题本（文章/手动）、艾宾浩斯复习、复习中心
- 积分、签到、排行榜、知行足迹

**全量功能说明（各模块明细）→ [FEATURES.md](./FEATURES.md)**

## 快速开始

```bash
cd ~/Projects/zhixing-gongkao
npm install
npm run dev:h5      # H5 开发 http://localhost:10087（默认连真实 API）
npm run dev:weapp   # 微信小程序，用开发者工具打开 dist 目录
```

后端另开终端：

```bash
cd server
source .venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

## Mock 与真实 API

- **默认连真实 API**（`USE_MOCK` 未设置或非 `true`）
- 纯前端本地演示（不启后端）时：

```bash
USE_MOCK=true npm run dev:h5
```

此时 `src/mock/service.ts` 覆盖登录、文章、计划、人民日报、足迹、知识复习、错题、资料分析等接口。生产 / Docker **不要**开启 `USE_MOCK`。

## 技术说明

- 主色调：深蓝 `#1E3A5F`（暗色 `#3D5A7A`）
- 生产部署与数据备份见 `deploy-ali.md`

## 目录结构

```
src/
├── api/          # 接口封装
├── components/   # 公共组件
├── constants/    # 常量
├── mock/         # Mock 数据与服务
├── pages/        # 页面
├── store/        # Pinia 状态
├── styles/       # 全局样式
└── utils/        # 工具函数（记忆曲线、出题等）
```
