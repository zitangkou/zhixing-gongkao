#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main runner: execute parts a/b/c, write JSON, validate."""
import json, os, sys

base = os.path.dirname(os.path.abspath(__file__))

# Shared state
Q = []
def add(raw, num, ans, exp, subtype=None, anchor="", pending=False, note=""):
    Q.append({"raw_number": raw, "number": num, "is_difference": True,
              "answer": ans, "explanation": exp, "subtype": subtype,
              "anchor_stem": anchor, "pending": pending, "note": note})

# Execute each part in shared namespace
ns = {"Q": Q, "add": add, "json": json, "os": os}
for part in ["extract_20254972_a.py", "extract_20254972_b.py", "extract_20254972_c.py"]:
    path = os.path.join(base, part)
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()
    exec(compile(code, path, "exec"), ns)

# Use Q from the exec namespace (part A redefines Q=[])
Q = ns.get("Q", Q)
print(f"\nTotal questions extracted: {len(Q)}")

# Write JSON
output = {
    "source_pdf": "20254972",
    "page_range": [50, 73],
    "questions": Q,
}

out_path = os.path.join(base, "raw_20254972.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"Written to: {out_path}")

# Validate JSON
with open(out_path, "r", encoding="utf-8") as f:
    data = json.load(f)
print(f"JSON valid: True")
print(f"source_pdf: {data['source_pdf']}")
print(f"page_range: {data['page_range']}")

nums = [q["number"] for q in data["questions"]]
print(f"Question count: {len(nums)}")
print(f"Number range: {min(nums)} ~ {max(nums)}")

expected = set(range(min(nums), max(nums)+1))
actual = set(nums)
missing = sorted(expected - actual)
if missing:
    print(f"MISSING (跳号): {missing}")
else:
    print("跳号: 无（连续序列）")

dupes = [n for n in nums if nums.count(n) > 1]
if dupes:
    print(f"DUPLICATE: {sorted(set(dupes))}")
else:
    print("重复: 无")

pending = [q for q in data["questions"] if q.get("pending")]
print(f"Pending: {len(pending)}")
for p in pending:
    print(f"  - #{p['number']} ({p['raw_number']}): {p['note'][:100]}")

all_diff = all(q["is_difference"] for q in data["questions"])
print(f"All is_difference=True: {all_diff}")

# Check all have explanation starting with 完整解析
bad_exp = [q["number"] for q in data["questions"] if not q["explanation"].startswith("完整解析：")]
if bad_exp:
    print(f"Explanation not starting with 完整解析：: {bad_exp}")
else:
    print("All explanations start with 完整解析：: True")
