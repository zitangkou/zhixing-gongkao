#!/usr/bin/env bash
# 知行公考 · 一键部署（单台云服务器，Docker Compose）
# 首次使用前先执行一次：bash deploy/setup-docker.sh
# 用法：
#   bash deploy.sh          # 首次部署 / 更新重建
#   bash deploy.sh update   # 同 deploy.sh（拉代码后调用本脚本）
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1 || ! docker compose version >/dev/null 2>&1; then
  echo "未检测到 Docker / Docker Compose，请先执行：bash deploy/setup-docker.sh"
  exit 1
fi

http_get() {
  local url="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsS -o /dev/null "$url"
  else
    python3 -c "import urllib.request,sys; urllib.request.urlopen(sys.argv[1], timeout=5)" "$url"
  fi
}

# ---------- 1/5 准备 .env ----------
if [[ ! -f .env ]]; then
  echo "[1/5] 生成 .env（基于 .env.docker.example，并自动生成密钥）"
  cp .env.docker.example .env
  SECRET="$(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')"
  ADMIN_PASS="$(openssl rand -hex 8 2>/dev/null || head -c 8 /dev/urandom | od -An -tx1 | tr -d ' \n')"
  perl -0pi -e "s/^SECRET_KEY=.*/SECRET_KEY=${SECRET}/; s/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD=${ADMIN_PASS}/" .env
  echo "  已生成 SECRET_KEY；管理员账号：admin / ${ADMIN_PASS}（请保存）"
  echo "  建议继续编辑 .env：DOMAIN=你的域名、CORS_ORIGINS、ALLOW_REGISTER"
else
  echo "[1/5] 使用现有 .env"
fi

HTTP_PORT="$(grep -E '^HTTP_PORT=' .env | head -1 | cut -d= -f2)"
HTTP_PORT="${HTTP_PORT:-8081}"

# ---------- 2/5 构建并启动 ----------
echo "[2/5] 构建并启动容器（http://127.0.0.1:${HTTP_PORT}）"
docker compose up -d --build

# ---------- 3/5 健康检查 ----------
echo "[3/5] 等待健康检查..."
ok=""
for _ in $(seq 1 60); do
  if http_get "http://127.0.0.1:${HTTP_PORT}/health"; then ok=1; break; fi
  sleep 2
done
if [[ -z "$ok" ]]; then
  echo "健康检查失败，请查看日志：docker compose logs"
  exit 1
fi
echo "  /health OK"

# ---------- 4/5 验证关键路由 ----------
echo "[4/5] 验证关键路由"
http_get "http://127.0.0.1:${HTTP_PORT}/" && echo "  /           H5 OK"
http_get "http://127.0.0.1:${HTTP_PORT}/api/config" && echo "  /api/       学员 API OK"
http_get "http://127.0.0.1:${HTTP_PORT}/manage/" && echo "  /manage/    管理后台 OK"

# ---------- 5/5 汇总 ----------
DOMAIN="$(grep -E '^DOMAIN=' .env | head -1 | cut -d= -f2)"
echo ""
echo "部署完成！"
if [[ -n "${DOMAIN:-}" ]]; then
  echo "  H5:        http://${DOMAIN}/"
  echo "  管理后台:  http://${DOMAIN}/manage/  （admin / 见 .env ADMIN_PASSWORD）"
  echo "  若已配置域名网关，请确认 deploy/nginx.conf 已挂到宿主机 Nginx。"
else
  echo "  本机访问:  http://127.0.0.1:${HTTP_PORT}/"
  echo "  管理后台:  http://127.0.0.1:${HTTP_PORT}/manage/"
  echo "  提示: 公网访问需在 .env 设置 HTTP_BIND=0.0.0.0（方案A），"
  echo "        或配置域名网关（方案B，见 deploy/nginx.conf 与 DEPLOY.md）。"
fi
echo ""
echo "常用命令："
echo "  日志:    docker compose logs -f zhixing-gongkao"
echo "  重启:    docker compose restart"
echo "  更新:    git pull && bash deploy.sh"
echo "  备份:    bash deploy/backup.sh（每日定时：bash deploy/install-backup.sh）"
echo "  停止:    docker compose down"
