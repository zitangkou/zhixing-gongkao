#!/usr/bin/env bash
# 在服务器 /opt/zhengkao-tong 下执行：拉代码并重建容器
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "缺少 .env，请先: cp .env.docker.example .env 并编辑"
  exit 1
fi

git fetch origin
if ! git pull --ff-only; then
  echo "检测到本地改动阻塞 pull，将丢弃与远程冲突的 tracked 文件（.env 不受影响）..."
  git reset --hard origin/main
fi
docker compose up -d --build
docker compose ps
echo "健康检查: curl -s http://127.0.0.1/health"
