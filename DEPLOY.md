# 政考通 Docker 部署

适用于 **暂无域名、通过服务器 IP 访问** 的第一版上线（H5 + 后端 + 管理后台）。

## 架构

| 路径 | 说明 |
|------|------|
| `http://<IP>/` | 移动端 H5 |
| `http://<IP>/api/*` | 用户 API（需 JWT 登录） |
| `http://<IP>/manage/` | 管理后台 |
| `http://<IP>/admin/*` | 管理 API |
| `http://<IP>/health` | 健康检查 |

容器内 Nginx 反代 + Uvicorn，SQLite 数据持久化到 Docker Volume。

## 推荐：Git 部署（勿 scp 整项目）

```bash
# 服务器首次
apt update && apt install -y git docker.io docker-compose-plugin
cd /opt
git clone https://github.com/zitangkou/zhengkao-tong.git
cd zhengkao-tong
cp .env.docker.example .env
nano .env   # SECRET_KEY、ADMIN_PASSWORD

# 配置 Docker 镜像加速（阿里云 ECS 控制台复制专属地址）
sudo tee /etc/docker/daemon.json <<'EOF'
{
  "registry-mirrors": [
    "https://你的ID.mirror.aliyuncs.com"
  ]
}
EOF
sudo systemctl daemon-reload && sudo systemctl restart docker

docker compose up -d --build
```

后续更新：

```bash
cd /opt/zhengkao-tong
bash scripts/deploy-update.sh
```

## 环境变量 `.env`

| 变量 | 说明 |
|------|------|
| `SECRET_KEY` | `openssl rand -hex 32` |
| `ADMIN_PASSWORD` | 管理后台密码 |
| `CORS_ORIGINS` | 同域部署可 `*` |

## 访问

- H5：`http://你的公网IP/`
- 管理后台：`http://你的公网IP/manage/`

首次打开 H5 需注册账号。

## 构建说明

- Dockerfile 会复制根目录 **`.npmrc`**（`legacy-peer-deps=true`），避免容器内 `npm ci` 报 ERESOLVE。
- 已移除 `# syntax=docker/dockerfile:1`，避免部分环境拉 Docker Hub 超时。
- H5 构建使用 `node:20-bookworm-slim`（Taro 需要 `@tarojs/binding-linux-x64-gnu`，Alpine/musl 会失败）。
- Python 依赖使用阿里云 PyPI 镜像，加快国内构建。

## Docker Hub 仍超时时

在 **Mac 本地** build 后传镜像：

```bash
docker compose build
docker save zhengkao-tong-zhengkao:latest | gzip > zhengkao-image.tar.gz
scp zhengkao-image.tar.gz root@<IP>:/opt/
# 服务器
docker load < /opt/zhengkao-image.tar.gz
cd /opt/zhengkao-tong && docker compose up -d
```

## 本地开发

```bash
cd server && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000
npm run dev:h5
cd server/admin-web && npm run dev
```
