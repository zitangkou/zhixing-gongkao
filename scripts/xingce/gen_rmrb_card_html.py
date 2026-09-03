#!/usr/bin/env python3
"""
政治理论模拟题 → 公众号 HTML + 小红书单题卡片 生成器

数据源：iCloud 云盘 政治理论/物料/2026-09-04/题目/*.json（20题）
产出：
  1. 公众号 HTML（仿人民日报内容运营「时评精拆」系列风格，中国红 #D0021B）
  2. 小红书单题卡片 20 张（1242×1660 PNG）
     - 每张卡片开头放置「上一题答案 + 简短解析」（第1题无上一题，直接题干）
     - 最后一张答案速查卡汇总全部答案

用法：
  python3 scripts/xingce/gen_rmrb_card_html.py
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ── 路径 ──────────────────────────────────────────────
ICLOUD_ROOT = Path("/Users/dnn/Library/Mobile Documents/com~apple~CloudDocs/政治理论")
DATE_STR = "2026-09-04"
ARTICLE_TITLE = "携手各国发展振兴，改革完善全球治理"
DATE_DIR = ICLOUD_ROOT / "物料" / DATE_STR
JSON_PATH = DATE_DIR / "题目" / f"人民日报{DATE_STR}_{ARTICLE_TITLE}_20题.json"
GZH_DIR = DATE_DIR / "公众号"
XHS_DIR = DATE_DIR / "小红书" / "图片"

GZH_HTML = GZH_DIR / f"人民日报{DATE_STR}_{ARTICLE_TITLE}_20题_公众号.html"

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BRAND_RED = "#D0021B"
PINK_BG = "#FFF5F6"
CREAM_BG = "#FAF9F5"
DARK = "#333333"
MID = "#666666"
W, H = 1242, 1660

DIFF_LABEL = {1: "简单", 2: "中等", 3: "较难"}


# ══════════════════════════════════════════════════════
# 1. 公众号 HTML
# ══════════════════════════════════════════════════════

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def short_answer_line(q):
    """生成简短的上一题答案说明（用于放在下一题开头）"""
    ans = q["answer"]
    # 从解析中提取【正确项】一行
    m = re.search(r"【正确项】([^\n]+)", q["explanation"])
    core = m.group(1).strip() if m else ""
    # 精简：去掉重复的答案字母前缀
    core = re.sub(rf"^{ans}：", "", core)
    return ans, core


def parse_explanation(q):
    """把 explanation 拆成 正确项/干扰项 便于展示"""
    txt = q["explanation"]
    out = {"origin": "", "correct": "", "distractors": [], "conclusion": ""}
    m = re.search(r"【出处】([^\n]*)", txt)
    out["origin"] = m.group(1).strip() if m else ""
    m = re.search(r"【正确项】([^\n]*)", txt)
    out["correct"] = m.group(1).strip() if m else ""
    m = re.search(r"【结论】(故本题选[^\n]*)", txt)
    out["conclusion"] = m.group(1).strip() if m else ""
    # 干扰项行：形如 "  X项（手法）：..."
    for line in txt.split("\n"):
        line = line.strip()
        mm = re.match(r"([A-D])项（([^）]+)）[:：](.*)", line)
        if mm:
            out["distractors"].append({"opt": mm.group(1), "type": mm.group(2), "text": mm.group(3).strip()})
    return out


def gen_gzh_html(questions):
    """生成公众号风格 HTML（完整20题 + 答案 + 解析）"""
    parts = []
    parts.append("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>政治理论模拟题｜携手各国发展振兴，改革完善全球治理</title>
<style>
  body{margin:0;padding:0;background:#FAF9F5;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;color:#333;}
</style>
</head>
<body>
<div style="max-width:680px;margin:0 auto;padding:20px;background:#FFFFFF;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;color:#333;">

  <!-- 报头 -->
  <div style="text-align:center;border-bottom:3px solid #D0021B;padding-bottom:12px;margin-bottom:20px;">
    <div style="font-size:12px;color:#D0021B;letter-spacing:6px;margin-bottom:4px;">人民时评 · 精读系列</div>
    <div style="font-size:28px;font-weight:bold;color:#D0021B;letter-spacing:2px;">政治理论模拟题</div>
    <div style="font-size:12px;color:#999;margin-top:6px;">人民日报头版文章 · 公考政治理论出题</div>
  </div>
""")

    # 开篇引导
    parts.append("""
  <!-- 开篇引导 -->
  <div style="background:#FFF5F6;padding:15px;border-radius:8px;border-left:4px solid #D0021B;margin-bottom:20px;">
    <p style="margin:0;font-size:14px;color:#4A4A4A;line-height:1.7;">
      <b>【政治理论模拟题】2026-09-04 期</b><br>
      素材：《携手各国发展振兴，改革完善全球治理》<br>
      主题：上合组织 · 全球治理 · 命运共同体 · 大国外交<br>
      题量：20 题｜价值分 92/100（高可用）
    </p>
  </div>
""")

    # 逐题
    for i, q in enumerate(questions, 1):
        num = f"{i:02d}"
        expl = parse_explanation(q)
        parts.append(f"""
  <!-- 第{num}题 -->
  <h2 style="color:#D0021B;font-size:17px;border-bottom:2px solid #D0021B;padding-bottom:8px;">📌 第{num}题（{q['subtype']}｜难度{DIFF_LABEL.get(q['difficulty'], q['difficulty'])}｜答案{q['answer']}）</h2>
  <p style="font-size:14px;color:#333;line-height:1.8;margin:10px 0;"><b>考点：</b>{q['topic']} / {q['tag']}</p>
  <p style="font-size:15px;color:#1A1A1A;line-height:1.8;margin:10px 0;font-weight:500;">{esc(q['stem'])}</p>
  <table style="width:100%;border-collapse:collapse;margin:10px 0 15px;font-size:13px;">
""")
        for label in ["A", "B", "C", "D"]:
            mark = " ✅" if label == q["answer"] else ""
            bg = "#FFF5F6" if label == q["answer"] else "#FFFFFF"
            parts.append(f"""    <tr style="background:{bg};"><td style="padding:8px;border:1px solid #eee;width:28px;font-weight:bold;color:#D0021B;">{label}</td><td style="padding:8px;border:1px solid #eee;color:#333;">{esc(q['options'][label])}{mark}</td></tr>""")
        parts.append("""  </table>
  <div style="background:#FAF9F5;padding:12px 15px;border-radius:8px;margin-bottom:8px;">
    <p style="margin:0 0 6px;font-size:13px;color:#D0021B;"><b>【解析】</b></p>
""")
        if expl["origin"]:
            parts.append(f'    <p style="margin:2px 0;font-size:12px;color:#666;">📎 出处：{esc(expl["origin"])}</p>')
        if expl["correct"]:
            parts.append(f'    <p style="margin:2px 0;font-size:13px;color:#333;"><b>✓ 正确项：</b>{esc(expl["correct"])}</p>')
        if expl["distractors"]:
            parts.append('    <p style="margin:2px 0;font-size:12px;color:#666;"><b>干扰项：</b></p>')
            for d in expl["distractors"]:
                parts.append(f'    <p style="margin:2px 0 2px 14px;font-size:12px;color:#666;">· {d["opt"]}项（{d["type"]}）：{esc(d["text"])}</p>')
        parts.append(f'    <p style="margin:6px 0 0;font-size:13px;color:#D0021B;"><b>{esc(expl["conclusion"] or f"故本题选{q["answer"]}。")}</b></p>')
        parts.append("  </div>")

    # 页脚
    parts.append("""
  <!-- 页脚 -->
  <div style="text-align:center;border-top:2px solid #D0021B;padding-top:12px;margin-top:20px;">
    <div style="font-size:12px;color:#D0021B;">政治理论模拟题 · 每日一练</div>
    <div style="font-size:11px;color:#999;margin-top:4px;">素材来源：人民日报 2026-09-04 第01版 ｜ 价值分 92/100</div>
  </div>
</div>
</body>
</html>""")
    return "\n".join(parts)


# ══════════════════════════════════════════════════════
# 2. 小红书单题卡片
# ══════════════════════════════════════════════════════

def gen_card_html(questions, idx):
    """生成第 idx 张卡片 HTML（idx 从 1 起）。
    布局：上一题答案+简短解析（顶部）→ 当前题干 → 选项 → 底部页码。
    """
    q = questions[idx - 1]
    total = len(questions)
    prev_html = ""
    if idx > 1:
        prev = questions[idx - 2]
        ans, core = short_answer_line(prev)
        prev_html = f"""
  <div style="background:#F3F7FB;border-left:6px solid #2E7D32;border-radius:12px;padding:26px 36px;margin-bottom:28px;">
    <div style="font-size:30px;font-weight:bold;color:#2E7D32;letter-spacing:2px;margin-bottom:10px;">上题答案 · 第{idx-1:02d}题 → {ans}</div>
    <div style="font-size:28px;color:#333;line-height:1.6;">{esc(core)}</div>
  </div>"""

    # 选项列表
    opts_html = ""
    for label in ["A", "B", "C", "D"]:
        opts_html += f"""
    <div style="display:flex;align-items:flex-start;padding:22px 28px;border:2px solid #eee;border-radius:14px;margin-bottom:20px;">
      <div style="min-width:56px;height:56px;border-radius:50%;background:#F2F2F2;color:#333;font-size:30px;font-weight:bold;display:flex;align-items:center;justify-content:center;margin-right:20px;">{label}</div>
      <div style="font-size:29px;color:#333;line-height:1.55;padding-top:6px;">{esc(q['options'][label])}</div>
    </div>"""

    inner = f"""
<div style="width:{W}px;height:{H}px;background:#fff;position:relative;display:flex;flex-direction:column;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;">
  <div style="background:{PINK_BG};padding:30px 56px;display:flex;justify-content:space-between;align-items:center;border-bottom:3px solid {BRAND_RED};">
    <span style="color:{BRAND_RED};font-size:32px;font-weight:bold;letter-spacing:5px;">政治理论打卡</span>
    <span style="color:{MID};font-size:26px;">第{idx:02d}/{total:02d}题</span>
  </div>
  <div style="background:{BRAND_RED};padding:30px 56px;">
    <span style="color:#fff;font-size:44px;font-weight:bold;letter-spacing:3px;">第{idx:02d}题 · {q['tag']}</span>
  </div>
  <div style="flex:1;padding:36px 56px;overflow:hidden;">
    {prev_html}
    <div style="font-size:32px;color:#1A1A1A;line-height:1.7;font-weight:500;margin-bottom:26px;">{esc(q['stem'])}</div>
    {opts_html}
  </div>
  <div style="padding:30px 56px;border-top:2px solid #eee;display:flex;justify-content:space-between;align-items:center;">
    <span style="color:{MID};font-size:24px;">人民日报 · 政治理论</span>
    <span style="color:{BRAND_RED};font-size:28px;font-weight:bold;">{idx}/{total}</span>
  </div>
</div>"""
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<style>*{{box-sizing:border-box;margin:0;padding:0;}}body{{margin:0;padding:0;background:#fff;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;}}</style>
</head><body>{inner}</body></html>"""


def gen_answer_card_html(questions):
    """答案速查卡（最后一张）：汇总全部答案 + 第20题答案"""
    total = len(questions)
    last = questions[-1]
    ans, core = short_answer_line(last)
    rows = ""
    # 4行×5列
    for i in range(0, total, 5):
        chunk = questions[i:i + 5]
        cells = ""
        for q in chunk:
            cells += f'<div style="flex:1;background:#F7F7F7;border-radius:12px;padding:20px 10px;text-align:center;margin-right:14px;"><div style="font-size:24px;color:#999;">第{q["question_id"][-3:]}题</div><div style="font-size:40px;font-weight:bold;color:{BRAND_RED};margin-top:8px;">{q["answer"]}</div></div>'
        rows += f'<div style="display:flex;margin-bottom:14px;">{cells}</div>'
    inner = f"""
<div style="width:{W}px;height:{H}px;background:#fff;position:relative;display:flex;flex-direction:column;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;">
  <div style="background:{PINK_BG};padding:30px 56px;display:flex;justify-content:space-between;align-items:center;border-bottom:3px solid {BRAND_RED};">
    <span style="color:{BRAND_RED};font-size:32px;font-weight:bold;letter-spacing:5px;">政治理论打卡</span>
    <span style="color:{MID};font-size:26px;">答案速查</span>
  </div>
  <div style="background:{BRAND_RED};padding:30px 56px;">
    <span style="color:#fff;font-size:44px;font-weight:bold;letter-spacing:3px;">全 20 题答案速查</span>
  </div>
  <div style="flex:1;padding:40px 56px;overflow:hidden;">
    <div style="background:#F3F7FB;border-left:6px solid #2E7D32;border-radius:12px;padding:24px 30px;margin-bottom:30px;">
      <div style="font-size:30px;font-weight:bold;color:#2E7D32;letter-spacing:2px;margin-bottom:8px;">第20题答案 → {ans}</div>
      <div style="font-size:27px;color:#333;line-height:1.6;">{esc(core)}</div>
    </div>
    {rows}
    <div style="font-size:24px;color:#999;text-align:center;margin-top:26px;line-height:1.6;">答案分布 A/B/C/D 各 5 题 · 与真题一致</div>
  </div>
  <div style="padding:30px 56px;border-top:2px solid #eee;display:flex;justify-content:space-between;align-items:center;">
    <span style="color:{MID};font-size:24px;">人民日报 · 政治理论</span>
    <span style="color:{BRAND_RED};font-size:28px;font-weight:bold;">答案速查</span>
  </div>
</div>"""
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<style>*{{box-sizing:border-box;margin:0;padding:0;}}body{{margin:0;padding:0;background:#fff;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;}}</style>
</head><body>{inner}</body></html>"""


def render_png(html_path, png_path):
    """Chrome headless 渲染 HTML → PNG"""
    cmd = [
        CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
        "--force-device-scale-factor=1",
        "--window-size=1242,1660",
        f"--screenshot={png_path}",
        f"file://{html_path}",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(png_path) or os.path.getsize(png_path) == 0:
        raise RuntimeError(f"渲染失败: {png_path}\n{r.stderr[-500:]}")
    return png_path


def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    questions = data["questions"]
    total = len(questions)
    print(f"数据源: {JSON_PATH} | 共 {total} 题")

    # ── 1. 公众号 HTML ──
    GZH_DIR.mkdir(parents=True, exist_ok=True)
    html = gen_gzh_html(questions)
    GZH_HTML.write_text(html, encoding="utf-8")
    print(f"✅ 公众号 HTML: {GZH_HTML} ({GZH_HTML.stat().st_size} bytes)")

    # ── 2. 小红书卡片 ──
    XHS_DIR.mkdir(parents=True, exist_ok=True)
    tmpdir = XHS_DIR / "_tmp"
    tmpdir.mkdir(parents=True, exist_ok=True)

    # 封面（红底大标题，仿小红书封面A）
    cover_html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<style>*{{box-sizing:border-box;margin:0;padding:0;}}body{{margin:0;padding:0;background:#fff;}}</style>
</head><body>
<div style="width:{W}px;height:{H}px;background:{BRAND_RED};position:relative;overflow:hidden;font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;">
  <div style="position:absolute;top:90px;left:0;right:0;text-align:center;color:rgba(255,255,255,0.85);font-size:30px;letter-spacing:14px;">政治理论 · 每日一练</div>
  <div style="position:absolute;top:320px;left:0;right:0;text-align:center;color:#fff;font-size:92px;font-weight:bold;line-height:1.35;letter-spacing:2px;padding:0 70px;">
    携手各国发展振兴<br>改革完善全球治理
  </div>
  <div style="position:absolute;top:980px;left:0;right:0;text-align:center;color:#ffd9dc;font-size:38px;line-height:1.7;padding:0 100px;">上合组织 · 全球治理 · 命运共同体</div>
  <div style="position:absolute;bottom:150px;left:0;right:0;text-align:center;color:#fff;font-size:38px;letter-spacing:6px;">政治理论模拟题 · 20 题</div>
  <div style="position:absolute;bottom:64px;left:0;right:0;text-align:center;color:rgba(255,255,255,0.55);font-size:24px;letter-spacing:3px;">人民日报 2026-09-04 · 价值分 92/100</div>
  <div style="position:absolute;top:0;left:0;width:18px;height:{H}px;background:rgba(255,255,255,0.18);"></div>
  <div style="position:absolute;top:0;right:0;width:18px;height:{H}px;background:rgba(255,255,255,0.18);"></div>
</div>
</body></html>"""
    (tmpdir / "cover.html").write_text(cover_html, encoding="utf-8")
    render_png(tmpdir / "cover.html", XHS_DIR / "00_封面.png")
    print("✅ 封面: 00_封面.png")

    # 20 张单题卡
    for i, _ in enumerate(questions, 1):
        html = gen_card_html(questions, i)
        hp = tmpdir / f"card_{i:02d}.html"
        hp.write_text(html, encoding="utf-8")
        pp = XHS_DIR / f"{i:02d}_第{i:02d}题.png"
        render_png(hp, pp)
        print(f"✅ 卡片 {i:02d}/{total}: {pp.name}")

    # 答案速查卡
    ans_html = gen_answer_card_html(questions)
    (tmpdir / "answer.html").write_text(ans_html, encoding="utf-8")
    render_png(tmpdir / "answer.html", XHS_DIR / "21_答案速查.png")
    print("✅ 答案速查: 21_答案速查.png")

    # 清理临时文件
    import shutil
    shutil.rmtree(tmpdir, ignore_errors=True)

    print("\n" + "=" * 50)
    print(f"完成！公众号 HTML + {total} 张单题卡 + 封面 + 答案速查卡")
    print(f"公众号: {GZH_HTML}")
    print(f"小红书: {XHS_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    main()
