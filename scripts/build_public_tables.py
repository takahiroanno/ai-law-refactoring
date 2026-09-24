#!/usr/bin/env python3
"""results/ の機械可読データから、公開用の CSV と Markdown 一覧を生成する。

出力:
  data/amendment_candidates_87.csv   デジタル化可能性 high の87件（改正イメージつき）
  data/all_candidates_199.csv        判定145件＋発見54件の全量
  docs/amendment-candidates-87.md    87件の読み物版（概念別・現行→改正イメージ）

使い方: python3 scripts/build_public_tables.py
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FIELDS = [
    "id", "kind", "concept_id", "concept_label", "digital_potential", "is_hidden",
    "law_title", "law_num", "article", "caption", "quote", "reason",
    "amendment_type", "current_phrase", "amended_phrase", "note",
]


def load() -> list[dict]:
    items = json.loads((ROOT / "results/items.json").read_text(encoding="utf-8"))
    amendments = {
        r["id"]: r
        for r in (
            json.loads(line)
            for line in (ROOT / "results/amendments.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    }
    labels = {
        c["id"]: c["label"]
        for c in json.loads((ROOT / "concepts.json").read_text(encoding="utf-8"))["concepts"]
    }

    rows = []
    for it in items:
        amd = amendments.get(it["id"], {})
        concept = it.get("concept", "")
        rows.append({
            "id": it["id"],
            "kind": it.get("kind", ""),
            # 発見パス(kind=discovery)の concept は概念カタログ外の自由記述ラベル
            "concept_id": concept if concept in labels else "",
            "concept_label": labels.get(concept, concept),
            "digital_potential": it.get("digital_potential") or "",
            "is_hidden": "1" if it.get("is_hidden") else "0",
            "law_title": it.get("law_title", ""),
            "law_num": it.get("law_num", ""),
            "article": it.get("article", ""),
            "caption": it.get("caption", ""),
            "quote": (it.get("quote") or "").strip(),
            "reason": (it.get("reason") or "").strip(),
            "amendment_type": amd.get("amendment_type", ""),
            "current_phrase": amd.get("current_phrase", ""),
            "amended_phrase": amd.get("amended_phrase", ""),
            "note": amd.get("note", ""),
        })
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"{path.relative_to(ROOT)}: {len(rows)}件")


def write_markdown(path: Path, rows: list[dict]) -> None:
    groups: dict[str, list[dict]] = {}
    for r in rows:
        groups.setdefault(r["concept_label"], []).append(r)
    order = sorted(groups, key=lambda k: (-len(groups[k]), k))

    out = [
        "# アナログ規制 改正候補 87件",
        "",
        "現行法律2,100本・96,780条を概念ベースで洗い出し、LLMが精読して"
        "「デジタル化可能性 high」と判定した条文の一覧。",
        "改正イメージはLLMの一次起草であり、法制執務上の精査を経ていない。",
        "個別条文は必ず原文（e-Gov法令検索）で確認すること。",
        "",
        "- 全量（medium 49件・low 9件・発見パス 54件を含む199件）: "
        "[`data/all_candidates_199.csv`](../data/all_candidates_199.csv)",
        "- 条文全文つきの一覧ページ: [`docs/html/fix-targets.html`](html/fix-targets.html)",
        "- 「隠れ」= 従来のキーワード型見直し（「対面」「フロッピーディスク」等の単語検索）"
        "では網に掛からなかった条文。",
        "",
    ]
    for label in order:
        items = groups[label]
        out.append(f"## {label}（{len(items)}件）")
        out.append("")
        for r in items:
            hidden = "　【隠れ】" if r["is_hidden"] == "1" else ""
            caption = r["caption"].strip().strip("（）")
            out.append(f"### {r['law_title']}　{r['article']}"
                       + (f"（{caption}）" if caption else "")
                       + hidden)
            out.append("")
            out.append(f"- 法令番号: {r['law_num']}")
            if r["amendment_type"]:
                out.append(f"- 改正の型: {r['amendment_type']}")
            if r["reason"]:
                out.append(f"- 判定理由: {r['reason']}")
            out.append("")
            if r["current_phrase"]:
                out.append(f"> 現行: {r['current_phrase']}")
                out.append(">")
                out.append(f"> 改正イメージ: {r['amended_phrase']}")
                out.append("")
            if r["note"]:
                out.append(f"留意: {r['note']}")
                out.append("")
    path.write_text("\n".join(out), encoding="utf-8")
    print(f"{path.relative_to(ROOT)}: {len(rows)}件 / {len(order)}概念")


def main() -> None:
    rows = load()
    high = [r for r in rows if r["digital_potential"] == "high"]
    write_csv(ROOT / "data/all_candidates_199.csv", rows)
    write_csv(ROOT / "data/amendment_candidates_87.csv", high)
    write_markdown(ROOT / "docs/amendment-candidates-87.md", high)


if __name__ == "__main__":
    main()
