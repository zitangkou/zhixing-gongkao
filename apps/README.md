# 知行公考独立题型应用

本目录承载可独立开发、构建和发布的题型产品。每个目录都是完整的 Taro 项目，不通过环境变量切换产品。

| 应用 | 目录 | H5 开发端口 | 产品定位 |
| --- | --- | --- | --- |
| 申论 | `shenlun-app/` | `10088` | 人民日报精读、三刀法拆解、申论专项训练 |
| 政治理论 | `theory-app/` | `10089` | 时政与理论学习、真题化生成、刷题复习 |

后续资料分析、数量关系、言语理解、判断推理等项目，从同一题型应用模板创建，但必须拥有独立的 `package.json`、`config/`、`src/`、路由和构建产物。

统一体验规范见 [`../docs/architecture/vertical-app-design-system.md`](../docs/architecture/vertical-app-design-system.md)。

## 启动

依赖暂时复用仓库根目录已安装的 Taro 工具链，应用源码与构建配置彼此独立。

```bash
cd apps/shenlun-app && npm run dev:h5
cd apps/theory-app && npm run dev:h5
```

微信小程序分别执行 `npm run build:weapp`，并用微信开发者工具打开对应应用目录；正式发布前为每个产品配置独立 AppID。
