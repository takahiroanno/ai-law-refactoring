#!/usr/bin/env python3
"""クローン文（clone_catalog.json）を機能別「モジュール」に分類し、
モジュール単位の複製規模（法令数・出現回数）をコーパス全体から再集計する。

出力: results/module_catalog.json
使い方: python3 scripts/curate_modules.py data/articles.jsonl results/clone_catalog.json results/module_catalog.json
"""
import json
import re
import sys
from collections import defaultdict

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from clone_catalog import normalize  # 同じ正規化を使う

# モジュール定義: (id, 名前, 提案する共通法, 判定関数)
# 順序が優先順位（先にマッチしたモジュールに帰属）
MODULES = [
    ("M01", "両罰規定", "行政制裁法", lambda s: "使用人その他の従業者が" in s and "業務に関し" in s),
    ("M02", "没収・追徴", "行政制裁法", lambda s: "没収" in s or "追徴" in s),
    ("M03", "国外犯適用", "行政制裁法", lambda s: "日本国外において" in s and "罪" in s),
    ("M04", "自首減免", "行政制裁法", lambda s: "自首したとき" in s),
    ("M05", "賄賂罪", "行政制裁法", lambda s: "賄賂" in s),
    ("M06", "秘密漏えい罪・守秘義務", "行政制裁法", lambda s: "秘密を漏ら" in s),
    ("M07", "過料", "行政制裁法", lambda s: "過料に処" in s),
    ("M08", "罰則本体（拘禁刑・罰金・併科）", "行政制裁法", lambda s: re.search(r"(拘禁刑|罰金)に処", s)),
    ("M09", "犯罪捜査解釈禁止", "行政調査法", lambda s: "犯罪捜査のために認められたものと解" in s),
    ("M10", "身分証明書の携帯・提示", "行政調査法", lambda s: "証明書を携帯し" in s),
    ("M11", "立入検査・質問", "行政調査法", lambda s: ("立入" in s or "立ち入" in s) or ("検査を拒み" in s)),
    ("M12", "報告徴収・虚偽報告", "行政調査法", lambda s: "報告をせず" in s or "報告を求める" in s),
    ("M13", "みなし公務員", "行政調査法", lambda s: "法令により公務に従事する職員とみなす" in s),
    ("M14", "届出義務・変更届出（軽微除外）", "行政手続法の拡張", lambda s: "届出をせず" in s or "軽微な変更については" in s),
    ("M15", "聴聞・審査請求の特例", "行政手続法の拡張", lambda s: "聴聞" in s or "審査請求" in s or "行政不服審査法" in s or "意見の聴取" in s),
    ("M16", "官報公示・公表義務", "公示・公表法", lambda s: "官報に公示" in s or ("遅滞なく" in s and ("公表しなければ" in s or "公示しなければ" in s)) or "その旨を公示しなければ" in s),
    ("M17", "定義規定の柱書", "法令用語法", lambda s: "掲げる用語の意義は" in s),
    ("M18", "電磁的記録・電磁的方法の定義", "法令用語法（デジタル手続法の拡張）", lambda s: "人の知覚によ" in s and "認識することができない方式" in s or "電子情報処理組織を使用する方法その他の情報通信の技術を利用する方法" in s),
    ("M19", "清算手続パッケージ", "法人清算共通法（一般法人法への一本化）", lambda s: "清算人" in s or ("債権者" in s and "催告" in s and "申出" in s)),
    ("M20", "指定試験機関・登録機関・紛争解決機関の統治", "指定法人共通法", lambda s: any(k in s for k in ("指定試験機関", "試験事務", "登録申請者", "紛争解決等業務", "指定紛争解決機関", "業務規程"))),
    ("M21", "独立行政法人・機構の設立定型", "独法通則法への一本化", lambda s: "通則法" in s or "機構の役員" in s or "機構の資本金" in s or ("機構は、" in s and ("国庫に納付" in s or "経理を区分" in s or "出資" in s))),
    ("M22", "財務諸表等の備置き・閲覧", "情報公示法（電子公表への一本化）", lambda s: "財務諸表等" in s),
    ("M23", "権限委任（地方支分部局）", "権限委任法", lambda s: "委任することができる" in s and ("局長" in s or "所長" in s)),
    ("M24", "都道府県知事等への事務委任", "権限委任法", lambda s: "都道府県知事が行うこととすることができる" in s),
    ("M25", "経過措置の命令委任", "法令経過措置法", lambda s: "合理的に必要と判断される範囲内" in s),
    ("M26", "政省令への包括委任（実施規定）", "（現状維持・様式は共通化）", lambda s: "実施のため必要な事項は" in s or "施行に関し必要な事項は" in s),
    ("M27", "読み替え適用表", "（参照機構の機械可読化）", lambda s: "読み替えるものとする" in s),
    ("M28", "登記の対抗力", "商業登記法への一本化", lambda s: "登記の後でなければ" in s or ("登記" in s and "対抗することができない" in s)),
    ("M29", "先取特権の順位", "民法への参照一本化", lambda s: "先取特権" in s),
    ("M30", "欠格条項", "資格・欠格共通法", lambda s: "受けることができない" in s or "役員となることができない" in s),
    ("M31", "協議会・審議会の運営定型", "会議体共通法", lambda s: "協議会の運営に関し必要な事項" in s or "協議会を組織する" in s or "委員の任期" in s or "議事録を作成しなければ" in s),
]


def classify(s):
    for mid, name, target, fn in MODULES:
        if fn(s):
            return mid
    return None


def main(corpus_path, clones_path, out_path):
    meta = {m[0]: {"name": m[1], "target": m[2]} for m in MODULES}
    agg = defaultdict(lambda: {"laws": set(), "occurrences": 0})
    # コーパス全体を再走査してモジュール単位の規模を測る
    for line in open(corpus_path, encoding="utf-8"):
        r = json.loads(line)
        seen = set()
        for raw in re.split(r"。", r["text"]):
            raw = raw.strip()
            if len(raw) < 30:
                continue
            mid = classify(normalize(raw))
            if mid:
                agg[mid]["occurrences"] += 1
                seen.add(mid)
        for mid in seen:
            agg[mid]["laws"].add(r["law_title"])

    # クローン文をモジュールに割り付け（代表文として上位を保持）
    clones = json.load(open(clones_path, encoding="utf-8"))
    variants = defaultdict(list)
    unassigned = []
    for c in clones:
        mid = classify(c["normalized"])
        if mid:
            variants[mid].append({"laws": c["laws"], "example": c["example"][:180],
                                  "sources": c["sample_sources"][:3]})
        else:
            unassigned.append(c)

    catalog = []
    for mid, m in meta.items():
        a = agg.get(mid)
        if not a:
            continue
        vs = sorted(variants.get(mid, []), key=lambda v: -v["laws"])
        catalog.append({
            "id": mid, "name": m["name"], "proposed_common_law": m["target"],
            "laws": len(a["laws"]), "occurrences": a["occurrences"],
            "clone_variants": len(vs), "top_variants": vs[:5],
        })
    catalog.sort(key=lambda x: -x["laws"])
    json.dump({"modules": catalog,
               "unassigned_top": [{"laws": c["laws"], "normalized": c["normalized"][:120]}
                                  for c in unassigned[:40]]},
              open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{'id':4} {'laws':>5} {'occ':>6} {'var':>4}  name")
    for c in catalog:
        print(f"{c['id']:4} {c['laws']:5} {c['occurrences']:6} {c['clone_variants']:4}  {c['name']} → {c['proposed_common_law']}")
    print("unassigned top:", len(unassigned))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
