# 知行公考 · 云服务器一键部署

> 适用：一台云服务器（建议 Ubuntu 22.04 / Debian 12，2核4G+）部署整套 H5 + FastAPI + 管理后台。
> 方案参考：coffee-order 的单机 Docker 部署模式（容器内网端口 + 宿主机 Nginx 网关按域名转发）。
> 更新：2026-08-16

## 快速命令速查

```bash
# ① 一次性：环境准备（每台服务器只跑一次）
apt update && apt install -y git
cd /opt && git clone git@github.com:zitangkou/zhixing-gongkao.git
cd zhixing-gongkao && bash deploy/setup-docker.sh   # Docker 已就绪时会自动跳过，不影响其它项目

# ② 一键部署 / 更新
bash deploy.sh

# ③ 域名网关（可选，正式运营推荐）
cp deploy/nginx.conf /etc/nginx/sites-available/zhixing-gongkao
ln -sf /etc/nginx/sites-available/zhixing-gongkao /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# ④ 备份 / 每日定时备份
bash deploy/backup.sh
bash deploy/install-backup.sh
```

## 与现有项目共存（如服务器已部署 coffee-order）

本项目的部署**与已在跑的项目完全隔离**，不会影响它们：

| 维度 | coffee-order（示例） | 知行公考 | 冲突风险 |
|---|---|---|---|
| compose 项目名 | `coffee-order` | `zhixing-gongkao` | 无（网络 / 卷 / 容器各自独立） |
| 容器名 | `coffee-web` / `coffee-server` / `coffee-mysql` | `zhixing-gongkao` | 无 |
| 宿主端口 | `127.0.0.1:8080` | `127.0.0.1:8081`（默认） | 无；若 8081 被占，改 `.env` 的 `HTTP_PORT` |
| 数据卷 | `coffee-order_*` | `zhixing-gongkao_zhixing-gongkao-data` | 无 |
| 镜像 | `coffee-order-*` | `zhixing-gongkao-zhixing-gongkao` | 无 |

**关键安全点：**

1. **不要重复执行全局 Docker 配置**。`deploy/setup-docker.sh` 已做共存保护：检测到 Docker / Compose 就绪就直接跳过，**不会**覆盖 `/etc/docker/daemon.json`，**不会**重启 docker 守护进程（重启会短暂中断所有容器）。已在跑 coffee-order 的服务器上，直接执行 `bash deploy.sh` 即可。
2. **compose 命令只作用于本项目**。`docker compose up/down/restart` 在项目目录内执行，只影响 `zhixing-gongkao` 项目；不要用 `docker compose down -v`（连本项目的卷也会删）。
3. **域名网关互不覆盖**。宿主机 Nginx 每个项目一个站点文件（`/etc/nginx/sites-available/`），本项目的 `deploy/nginx.conf` 用**独立的 server_name**，不修改其它项目配置；`nginx -t` 通过后再 `reload`。
4. **备份定时任务各自独立**。`deploy/install-backup.sh` 只在 crontab 里追加本项目条目（带项目路径标识），保留已有条目。

## 0. 部署架构（单机）

```text
公网 80/443（宿主机 Nginx 网关，按域名转发）
        │
        ▼
项目容器 Nginx（默认 127.0.0.1:8081）
   ├── /          → 综合 H5 静态页
   ├── /shenlun/  → 申论独立 H5
   ├── /theory/   → 政治理论独立 H5
   ├── /api/      → FastAPI 学员端接口（uvicorn:8000）
   ├── /admin/    → FastAPI 管理端接口（JWT + RBAC）
   ├── /manage/   → 管理后台静态页（admin-dist）
   ├── /uploads/  → data/uploads（头像/错题图）
   └── /health、/docs、/openapi.json → 健康检查 / API 文档
```

## 1. 端口与路由约定

| 路由 | 说明 | 容器内处理 |
|---|---|---|
| `/` | 学员端 H5 | nginx 静态 `try_files` |
| `/shenlun/` | 申论独立 H5 | nginx 子目录静态 `try_files` |
| `/theory/` | 政治理论独立 H5 | nginx 子目录静态 `try_files` |
| `/api/*` | 学员端 API | nginx → uvicorn:8000 |
| `/admin/*` | 管理端 API | nginx → uvicorn:8000 |
| `/manage/*` | 管理后台 | nginx → FastAPI 挂载 admin-dist |
| `/uploads/*` | 上传文件 | nginx `alias` data/uploads |
| `/health` `/docs` `/openapi.json` | 健康检查 / API 文档 | nginx → uvicorn |

宿主机监听由 `.env` 控制：`HTTP_PORT`（默认 `8081`）与 `HTTP_BIND`（默认 `127.0.0.1`）。

两种对外方式：

- **方案 A：IP:端口直连**（测试阶段）——`.env` 设 `HTTP_BIND=0.0.0.0`，访问 `http://IP:8081/`。
- **方案 B：域名网关**（推荐，正式运营）——`HTTP_BIND=127.0.0.1`，宿主机 Nginx 按域名转发到 `127.0.0.1:8081`，安全组只需放行 `22/80/443`。

## 2. 服务器准备

- 安全组放行：`22`（SSH）、`80`、`443`（方案 A 还需放行 `8081`）。
- 连接服务器后安装 git：

```bash
apt update && apt install -y git
```

- 使用 **SSH 方式拉取**：先把服务器的 SSH 公钥添加到 GitHub（Settings → SSH and GPG keys → New SSH key）：

```bash
ssh-keygen -t ed25519 -C "server-zhixing-gongkao" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub    # 复制输出到 GitHub
ssh -T git@github.com        # 验证：Hi <用户名>! You've successfully authenticated...
```

## 3. 获取代码 + 一键部署

```bash
cd /opt
git clone git@github.com:zitangkou/zhixing-gongkao.git
cd zhixing-gongkao

# 一次性：安装 Docker / Compose + 配置镜像加速
bash deploy/setup-docker.sh

# 一键：生成 .env → 构建 → 启动 → 健康检查 → 验证 /、/api、/manage
bash deploy.sh
```

部署完成后可分别访问 `https://你的域名/shenlun/` 与 `https://你的域名/theory/`。两套前端独立构建、独立路由，但账号、内容审核、题库、任务进度和运营后台复用同一个后端。

首次执行 `deploy.sh` 会自动生成 `.env`（随机 `SECRET_KEY` 与 `ADMIN_PASSWORD`，密码会打印在终端），随后建议：

```bash
nano .env    # 配置 DOMAIN、CORS_ORIGINS、ALLOW_REGISTER，确认 HTTP_BIND/HTTP_PORT
```

## 4. 配置域名网关（方案 B）

```bash
cp deploy/nginx.conf /etc/nginx/sites-available/zhixing-gongkao
# 编辑 server_name 为你的域名；确认 proxy_pass 端口与 .env 的 HTTP_PORT 一致
ln -sf /etc/nginx/sites-available/zhixing-gongkao /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# HTTPS（可选）：certbot --nginx -d 你的域名
```

## 5. 更新与运维

```bash
# 更新（拉代码 + 一键重建）
git pull && bash deploy.sh
# 或：bash scripts/deploy-update.sh

# 日志 / 重启 / 停止
docker compose logs -f zhixing-gongkao
docker compose restart
docker compose down

# 备份（整包 tar：SQLite + uploads + knowledge，单文件备份会丢图片）
bash deploy/backup.sh
# 每日 03:00 自动备份（保留 14 天，可配 BACKUP_DIR / BACKUP_RETENTION_DAYS）
bash deploy/install-backup.sh

# 恢复
docker compose exec -T zhixing-gongkao sh -c 'cd /app/server && tar -xzf -' < /opt/backups/zhixing-gongkao_xxx.tar.gz
```

> **禁止** `docker compose down -v`（会删除数据卷）。

## 6. 环境变量要点

| 变量 | 默认 | 说明 |
|---|---|---|
| `SECRET_KEY` | deploy.sh 自动生成 | JWT 密钥 |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | `admin` / 自动生成 | 管理后台账号 |
| `HTTP_PORT` / `HTTP_BIND` | `8081` / `127.0.0.1` | 宿主端口与绑定地址 |
| `DOMAIN` | 空 | 对外域名（deploy.sh 汇总提示用） |
| `CORS_ORIGINS` | `*` | 同域部署可 `*` |
| `ALLOW_REGISTER` | `false` | 是否开放学员端自助注册 |
| `BACKUP_DIR` / `BACKUP_RETENTION_DAYS` | `/opt/backups` / `14` | 备份目录与保留天数 |
| `KNOWLEDGE_KB_DIR` | 空 | 知识框架本地目录（生产留空） |

## 7. 常见问题

- **Docker Hub 超时**：`setup-docker.sh` 已配置多源镜像加速；仍超时可在本机构建后 `docker save/load` 导入（见下）。
- **`npm ci` 报 ERESOLVE**：Dockerfile 会复制根目录 `.npmrc`（`legacy-peer-deps=true`），与本地行为一致。
- **端口被占**：改 `.env` 的 `HTTP_PORT` 后重跑 `bash deploy.sh`。
- **管理后台 404**：确认 `server/admin-dist` 已构建（Dockerfile 会自动构建；本地直接跑需先 `cd server/admin-web && npm run build`）。

## 8. Docker Hub 超时时：本地构建导入

```bash
docker compose build
docker save zhixing-gongkao-zhixing-gongkao:latest | gzip > zhengkao-image.tar.gz
scp zhengkao-image.tar.gz root@<IP>:/opt/
# 服务器
docker load < /opt/zhengkao-image.tar.gz
cd /opt/zhixing-gongkao && docker compose up -d
```

## 9. 本地开发

```bash
cd server && source .venv/bin/activate && uvicorn app.main:app --reload --port 8001
npm run dev:h5
cd server/admin-web && npm run dev
```
