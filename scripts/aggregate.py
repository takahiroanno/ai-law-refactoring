#!/usr/bin/env python3
"""findings.jsonl から報告書用の集計 (aggregates.json / CSV) を作る。"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

findings_path, summary_path, out_dir = sys.argv[1:4]
out = Path(out_dir)
out.mkdir(parents=True, exist_ok=True)

summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
law_digital = set(summary["law_digital_alt"])  # 法令内にデジタル代替の語があるもの

per_concept = defaultdict(lambda: {"articles": 0, "laws": set(),
                                   "no_alt_articles": 0, "laws_no_alt": set()})
per_law = defaultdict(lambda: defaultdict(int))
law_titles = {}

with open(findings_path, encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        cid, lid = r["concept"], r["law_id"]
        law_titles[lid] = r["law_title"]
        pc = per_concept[cid]
        pc["articles"] += 1
        pc["laws"].add(lid)
        if not r["article_has_digital_alt"]:
            pc["no_alt_articles"] += 1
        if lid not in law_digital:
            pc["laws_no_alt"].add(lid)
        per_law[lid][cid] += 1

# 概念別サマリ
with open(out / "concept_summary.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["concept", "hit_articles", "hit_laws",
                "articles_without_digital_alt", "laws_without_any_digital_alt_provision"])
    for cid in sorted(per_concept):
        pc = per_concept[cid]
        w.writerow([cid, pc["articles"], len(pc["laws"]),
                    pc["no_alt_articles"], len(pc["laws_no_alt"])])

# 法令別「アナログ密度」ランキング（ヒット概念の多様性×条数、デジタル代替の有無つき）
rows = []
for lid, cmap in per_law.items():
    total = sum(cmap.values())
    rows.append({
        "law_id": lid,
        "law_title": law_titles[lid],
        "total_hits": total,
        "distinct_concepts": len(cmap),
        "has_digital_alt_provision": lid in law_digital,
        "concepts": ";".join(f"{c}:{n}" for c, n in sorted(cmap.items(), key=lambda x: -x[1])),
    })
rows.sort(key=lambda r: (-r["distinct_concepts"], -r["total_hits"]))
with open(out / "law_ranking.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# 優先ターゲット: 法令レベルでもデジタル代替規定が皆無なのにヒット概念が多い法令
priority = [r for r in rows if not r["has_digital_alt_provision"]][:100]
with open(out / "priority_laws_no_digital_alt.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(priority)

print("laws with hits:", len(rows),
      "| laws w/o any digital-alt provision:", sum(1 for r in rows if not r["has_digital_alt_provision"]))
print("top5:", [(r["law_title"], r["distinct_concepts"], r["total_hits"]) for r in rows[:5]])
