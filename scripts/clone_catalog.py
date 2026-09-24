#!/usr/bin/env python3
"""条文クローン検出: 全条文を文単位に分解し、可変部をマスクした正規化文の
複製数（法令数・条数）を数える。共通法へ切り出す「モジュール」候補の原料。

使い方: python3 scripts/clone_catalog.py data/articles.jsonl results/clone_catalog.json
"""
import json
import re
import sys
from collections import defaultdict

MINISTER = re.compile(
    r"(内閣総理|厚生労働|経済産業|国土交通|文部科学|農林水産|総務|法務|財務|環境|防衛|外務|復興|デジタル)大臣")
MINORD = re.compile(
    r"(厚生労働|経済産業|国土交通|文部科学|農林水産|総務|法務|財務|環境|防衛|外務|内閣府|デジタル庁|復興庁)(省令|府令)")
KNUM = "[一二三四五六七八九十百千]+"
PATTERNS = [
    (re.compile(rf"第{KNUM}条(の{KNUM})*"), "第〇条"),
    (re.compile(rf"第{KNUM}項"), "第〇項"),
    (re.compile(rf"第{KNUM}号"), "第〇号"),
    (re.compile(rf"第{KNUM}章"), "第〇章"),
    (re.compile(rf"{KNUM}億円"), "〇円"),
    (re.compile(rf"{KNUM}万円"), "〇円"),
    (re.compile(rf"{KNUM}年以下"), "〇年以下"),
    (re.compile(rf"{KNUM}月以下"), "〇月以下"),
    (re.compile(rf"{KNUM}(週間|箇月|日以内|年以内|月以内)"), "〇\\1"),
]
WS = re.compile(r"\s+")


def normalize(s: str) -> str:
    s = WS.sub("", s)
    s = MINISTER.sub("主務大臣", s)
    s = MINORD.sub("主務省令", s)
    for cre, rep in PATTERNS:
        s = cre.sub(rep, s)
    return s


def main(corpus_path, out_path, min_laws=8, min_len=30):
    stats = defaultdict(lambda: {"laws": set(), "count": 0, "raw": None, "src": []})
    for line in open(corpus_path, encoding="utf-8"):
        r = json.loads(line)
        for raw in re.split(r"。", r["text"]):
            raw = raw.strip()
            if len(raw) < min_len:
                continue
            key = normalize(raw)
            if len(key) < min_len:
                continue
            st = stats[key]
            st["count"] += 1
            st["laws"].add(r["law_title"])
            if st["raw"] is None:
                st["raw"] = raw + "。"
            if len(st["src"]) < 8 and r["law_title"] not in [x[0] for x in st["src"]]:
                st["src"].append((r["law_title"], r["article_title"]))
    rows = []
    for key, st in stats.items():
        n = len(st["laws"])
        if n < min_laws:
            continue
        rows.append({
            "normalized": key, "laws": n, "occurrences": st["count"],
            "example": st["raw"],
            "sample_sources": [f"{t} {a}" for t, a in st["src"]],
        })
    rows.sort(key=lambda x: -x["laws"])
    json.dump(rows, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"clone sentences (>= {min_laws} laws): {len(rows)}")
    for r in rows[:15]:
        print(f'{r["laws"]:4}法 {r["occurrences"]:5}回 | {r["normalized"][:70]}')


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
