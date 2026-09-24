#!/usr/bin/env python3
"""LLM判定用サンプルを作る。

verify: 概念ごとに findings から層化サンプル（デジタル代替なし優先）＋条文全文
discover: どの概念にもヒットしなかった条文から、義務規定を優先してサンプル
"""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

random.seed(42)

corpus_path, findings_path, out_dir = sys.argv[1:4]
out = Path(out_dir)
out.mkdir(parents=True, exist_ok=True)

# 条文全文の索引（メモリ節約のためオフセット索引）
articles = {}
with open(corpus_path, encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        key = (r["law_id"], r["article_title"])
        articles[key] = r

by_concept = defaultdict(list)
hit_keys = set()
with open(findings_path, encoding="utf-8") as f:
    for line in f:
        r = json.loads(line)
        by_concept[r["concept"]].append(r)
        hit_keys.add((r["law_id"], r["article"]))

N_VERIFY = 16
for cid, rows in by_concept.items():
    no_alt = [r for r in rows if not r["article_has_digital_alt"]]
    with_alt = [r for r in rows if r["article_has_digital_alt"]]
    random.shuffle(no_alt)
    random.shuffle(with_alt)
    picked = no_alt[:12] + with_alt[:4]
    picked = picked[:N_VERIFY]
    recs = []
    for r in picked:
        art = articles.get((r["law_id"], r["article"]), {})
        recs.append({
            "concept": cid,
            "law_title": r["law_title"],
            "law_num": r["law_num"],
            "article": r["article"],
            "caption": r["caption"],
            "patterns": r["patterns"],
            "article_has_digital_alt": r["article_has_digital_alt"],
            "text": art.get("text", "")[:1600],
        })
    (out / f"verify_{cid}.jsonl").write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in recs), encoding="utf-8")

# 発見パス: 未ヒット条文。義務規定（しなければならない/してはならない）を優先
unhit_oblig, unhit_rand = [], []
for key, r in articles.items():
    if key in hit_keys:
        continue
    if len(r["text"]) < 80:
        continue
    if "しなければならない" in r["text"] or "してはならない" in r["text"]:
        unhit_oblig.append(r)
    else:
        unhit_rand.append(r)
random.shuffle(unhit_oblig)
random.shuffle(unhit_rand)

N_AGENTS, PER = 4, 100
for k in range(N_AGENTS):
    chunk = unhit_oblig[k * 60:(k + 1) * 60] + unhit_rand[k * 40:(k + 1) * 40]
    recs = [{
        "law_title": r["law_title"], "law_num": r["law_num"],
        "article": r["article_title"], "caption": r["caption"],
        "text": r["text"][:1800],
    } for r in chunk]
    (out / f"discover_{k}.jsonl").write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in recs), encoding="utf-8")

print("verify files:", len(by_concept), "discover files:", N_AGENTS,
      "unhit_oblig:", len(unhit_oblig), "unhit_rand:", len(unhit_rand))
