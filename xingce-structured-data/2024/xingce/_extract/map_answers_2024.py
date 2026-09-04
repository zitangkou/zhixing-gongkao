#!/usr/bin/env python3
"""2024 国考行测答案映射脚本

映射逻辑：
- 省级卷：主答案册 Q1-Q135 直映
- 市地卷（125题）：Q1-55 直映主册Q1-55，Q56-65 映主册Q61-70（偏移+5），Q66-125 映主册Q76-135（偏移+10）
- 执法卷（125题）：同市地卷

差异题（市地67题/执法36题）在papers JSON中无对应题干，单独输出为unmatched_diff.json，不参与merge。
"""
import json
from pathlib import Path

EXTRACT = Path(__file__).parent

# 加载主答案册
main_data = json.loads((EXTRACT / "raw_2024_main.json").read_text(encoding="utf-8"))
main_qs = {q["number"]: q for q in main_data["questions"]}

print(f"主答案册: {len(main_qs)} 题 (Q{min(main_qs)}-Q{max(main_qs)})")


def map_paper(name, mapping):
    """根据映射规则生成答案列表。mapping: {paper_qnum: main_qnum}"""
    answers = []
    unmatched = []
    for paper_n, main_n in sorted(mapping.items()):
        if main_n in main_qs:
            mq = main_qs[main_n]
            answers.append({
                "number": paper_n,
                "answer": mq["answer"],
                "explanation": mq["explanation"],
                "subtype": mq.get("subtype", ""),
                "anchor_stem": mq.get("anchor_stem", ""),
                "_mapped_from": f"main_Q{main_n}",
            })
        else:
            unmatched.append({"paper_q": paper_n, "main_q": main_n, "reason": "not found in main"})
    return answers, unmatched


# ═══ 省级卷：Q1-Q135 直映 ═══
sj_mapping = {n: n for n in range(1, 136)}
sj_answers, sj_unmatched = map_paper("shengji", sj_mapping)

# ═══ 市地卷：125题 ═══
sd_mapping = {}
for n in range(1, 56):  # Q1-55 直映
    sd_mapping[n] = n
for n in range(56, 66):  # Q56-65 偏移+5 → 主册Q61-70
    sd_mapping[n] = n + 5
for n in range(66, 126):  # Q66-125 偏移+10 → 主册Q76-135
    sd_mapping[n] = n + 10
sd_answers, sd_unmatched = map_paper("shidi", sd_mapping)

# ═══ 执法卷：同市地 ═══
zf_mapping = dict(sd_mapping)
zf_answers, zf_unmatched = map_paper("xingzhengzhifa", zf_mapping)

# 保存答案文件
for name, answers in [("shengji", sj_answers), ("shidi", sd_answers), ("xzzf", zf_answers)]:
    out = {"year": 2024, "paper": name, "source": "240124.pdf+2425-.pdf (main answer book)",
           "mapping_note": "省级直映; 市地/执法 Q1-55直映,Q56-65偏移+5,Q66-125偏移+10",
           "questions": answers}
    path = EXTRACT / f"answers_{name}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  {name}: {len(answers)} 题 → {path.name}")

# 差异题单独保存（不参与merge）
sd_diff = json.loads((EXTRACT / "raw_2024_shidi_diff.json").read_text(encoding="utf-8"))
zf_diff = json.loads((EXTRACT / "raw_2024_xzzf_diff.json").read_text(encoding="utf-8"))
unmatched_diff = {
    "note": "差异题在papers JSON中无对应题干，无法映射。papers JSON中市地/执法卷仅含省级共享题（题号偏移），缺失全部差异题。",
    "shidi_diff_count": len(sd_diff["questions"]),
    "xzzf_diff_count": len(zf_diff["questions"]),
    "shidi_diff_modules": {},
    "xzzf_diff_modules": {},
}
for q in sd_diff["questions"]:
    mod = q.get("subtype", "unknown")
    unmatched_diff["shidi_diff_modules"][mod] = unmatched_diff["shidi_diff_modules"].get(mod, 0) + 1
for q in zf_diff["questions"]:
    mod = q.get("subtype", "unknown")
    unmatched_diff["xzzf_diff_modules"][mod] = unmatched_diff["xzzf_diff_modules"].get(mod, 0) + 1

(EXTRACT / "unmatched_diff.json").write_text(
    json.dumps(unmatched_diff, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n差异题（无法映射）: 市地{len(sd_diff['questions'])}题, 执法{len(zf_diff['questions'])}题")
print(f"  → 已保存到 unmatched_diff.json")

# 汇总
print(f"\n=== 映射汇总 ===")
print(f"省级: {len(sj_answers)}/135 题映射")
print(f"市地: {len(sd_answers)}/125 题映射")
print(f"执法: {len(zf_answers)}/125 题映射")
if sj_unmatched:
    print(f"省级未匹配: {sj_unmatched}")
if sd_unmatched:
    print(f"市地未匹配: {sd_unmatched}")
if zf_unmatched:
    print(f"执法未匹配: {zf_unmatched}")
