#!/usr/bin/env python3
"""概念カタログ (concepts.json) の候補網を条文コーパスに適用する。

出力:
  findings.jsonl : 1行 = 1(条, 概念) ヒット。matched パターン・抜粋・デジタル代替規定の有無つき
  summary.json   : 概念別・法令別の集計
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


def build(concepts_path):
    cat = json.loads(Path(concepts_path).read_text(encoding="utf-8"))
    concepts = []
    for c in cat["concepts"]:
        concepts.append({
            "id": c["id"],
            "label": c["label"],
            "patterns": [(p, re.compile(p)) for p in c["regex"]],
        })
    digital = re.compile("|".join(map(re.escape, cat["digital_alt_patterns"])))
    return concepts, digital


def snippet(text, start, end, width=60):
    s = max(0, start - width)
    e = min(len(text), end + width)
    return ("…" if s > 0 else "") + text[s:e].replace("\n", "／") + ("…" if e < len(text) else "")


def main(concepts_path, corpus_path, findings_path, summary_path):
    concepts, digital = build(concepts_path)
    per_concept = defaultdict(lambda: {"articles": 0, "laws": set()})
    per_law = defaultdict(lambda: defaultdict(int))
    law_titles = {}
    law_digital = defaultdict(bool)   # 法令内のどこかにデジタル代替規定があるか
    n = 0
    with open(corpus_path, encoding="utf-8") as f, open(findings_path, "w", encoding="utf-8") as out:
        for line in f:
            rec = json.loads(line)
            text = rec["caption"] + "\n" + rec["text"]
            law_id = rec["law_id"]
            law_titles[law_id] = rec["law_title"]
            has_digital = bool(digital.search(text))
            if has_digital:
                law_digital[law_id] = True
            for c in concepts:
                hits = []
                first = None
                for pat, cre in c["patterns"]:
                    m = cre.search(text)
                    if m:
                        hits.append(pat)
                        if first is None or m.start() < first.start():
                            first = m
                if not hits:
                    continue
                out.write(json.dumps({
                    "concept": c["id"],
                    "law_id": law_id,
                    "law_title": rec["law_title"],
                    "law_num": rec["law_num"],
                    "article": rec["article_title"],
                    "caption": rec["caption"],
                    "patterns": hits,
                    "snippet": snippet(text, first.start(), first.end()),
                    "article_has_digital_alt": has_digital,
                }, ensure_ascii=False) + "\n")
                per_concept[c["id"]]["articles"] += 1
                per_concept[c["id"]]["laws"].add(law_id)
                per_law[law_id][c["id"]] += 1
                n += 1
    summary = {
        "total_findings": n,
        "concepts": {
            cid: {"articles": v["articles"], "laws": len(v["laws"])}
            for cid, v in sorted(per_concept.items())
        },
        "law_digital_alt": {k: v for k, v in law_digital.items() if v},
        "top_laws_per_concept": {},
        "law_titles": law_titles,
    }
    for cid in per_concept:
        rows = sorted(((per_law[l][cid], l) for l in per_law if per_law[l][cid]), reverse=True)[:30]
        summary["top_laws_per_concept"][cid] = [
            {"law_id": l, "law_title": law_titles[l], "articles": cnt} for cnt, l in rows
        ]
    Path(summary_path).write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"findings={n}")
    for cid, v in sorted(per_concept.items()):
        print(f"  {cid}: articles={v['articles']} laws={len(v['laws'])}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
