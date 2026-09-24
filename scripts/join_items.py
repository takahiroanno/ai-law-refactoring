#!/usr/bin/env python3
"""LLM判定(llm_judgments)・発見(llm_discoveries)の各件を条文全文と突合し、
改正イメージ生成・一覧ページ生成の入力となる items.json を作る。"""
import json
import sys
from pathlib import Path

base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
corpus = Path(sys.argv[2]) if len(sys.argv) > 2 else base / "data/articles.jsonl"
out = Path(sys.argv[3]) if len(sys.argv) > 3 else base / "results/items.json"

# (law_title, article_title) -> record（法令名重複時は先勝ち）
idx = {}
for line in open(corpus, encoding="utf-8"):
    r = json.loads(line)
    idx.setdefault((r["law_title"], r["article_title"]), r)

items = []
miss = 0
for i, line in enumerate(open(base / "results/llm_judgments.jsonl", encoding="utf-8")):
    if not line.strip():
        continue
    r = json.loads(line)
    if not r.get("is_true_positive"):
        continue
    art = idx.get((r["law_title"], r["article"]))
    if art is None:
        miss += 1
        continue
    items.append({
        "id": f"J{i:03d}", "kind": "judgment",
        "concept": r["concept"], "law_title": r["law_title"], "law_num": art["law_num"],
        "article": r["article"], "caption": art["caption"],
        "text": art["text"], "reason": r["reason"],
        "digital_potential": r["digital_potential"], "is_hidden": r.get("is_hidden", False),
    })

disc = json.load(open(base / "results/llm_discoveries.json", encoding="utf-8"))
for i, r in enumerate(disc):
    art = idx.get((r["law_title"], r["article"]))
    items.append({
        "id": f"D{i:03d}", "kind": "discovery",
        "concept": r.get("proposed_concept", ""), "law_title": r["law_title"],
        "law_num": art["law_num"] if art else "", "article": r["article"],
        "caption": art["caption"] if art else "",
        "text": art["text"] if art else "", "quote": r.get("quote", ""),
        "reason": r.get("analog_assumption", ""),
        "digital_potential": None, "is_hidden": True,
    })
    if art is None:
        miss += 1

json.dump(items, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"items={len(items)} (judgment={sum(1 for x in items if x['kind']=='judgment')},"
      f" discovery={sum(1 for x in items if x['kind']=='discovery')}) miss={miss} -> {out}")
