#!/usr/bin/env bash
# 初始化新一年份目录：./init_year.sh 2024
set -e
YEAR="${1:?用法: $0 <年份，如 2024>}"
ROOT="$(cd "$(dirname "$0")" && pwd)"
TARGET="$ROOT/$YEAR/xingce"

if [ -d "$TARGET/papers" ] && [ "$(ls -A "$TARGET/papers" 2>/dev/null)" ]; then
  echo "已存在且非空: $TARGET"
  exit 1
fi

mkdir -p "$TARGET"/{papers,media/pages,media/figures,media/formulas,source}
cp "$ROOT/_templates/year_xingce/meta.json" "$TARGET/meta.json"
# 写入年份
python3 - "$TARGET/meta.json" "$YEAR" <<'PY'
import json, sys, datetime
path, year = sys.argv[1], int(sys.argv[2])
m = json.load(open(path, encoding="utf-8"))
m["exam_year"] = year
m["exam_name"] = f"{year}年度国家公务员考试"
m["updated"] = datetime.date.today().isoformat()
json.dump(m, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("wrote", path)
PY

# 空 media_index
echo '{"year": '"$YEAR"', "pages": [], "figures": []}' > "$TARGET/media/media_index.json"

echo "已初始化: $TARGET"
echo "下一步: 放入 source PDF → 解析 papers → 更新 catalog.json"
