# data/

## 同梱しているもの

| ファイル | 中身 |
|---|---|
| `amendment_candidates_87.csv` | デジタル化可能性 high と判定された87件（法令名・条・判定理由・現行→改正イメージ） |
| `all_candidates_199.csv` | 上記に medium 49件・low 9件・発見パス 54件を加えた全量 |

いずれも `scripts/build_public_tables.py` が `results/items.json` と `results/amendments.jsonl` から生成する。
文字コードは UTF-8 (BOM 付き。Excel でそのまま開けるようにしている)。

## 同梱していないもの: 法令XML本体

分析対象の e-Gov 法令XML（現行法律2,100本・約38MB圧縮）はリポジトリに含めていない。
取得は次のコマンドで行う。

```bash
scripts/fetch_laws.sh          # → data/laws/{元号3桁}/{法令ID}/current.xml
```

出典は e-Gov 法令検索の `all_xml.zip` を法令ごとに展開した GitHub ミラー
[aluqas/gitlaw-jp](https://github.com/aluqas/gitlaw-jp)。分析に使ったのは 2025年5月時点の
スナップショットで、**最新スナップショットとは条文が異なりうる**（`REF=<branch>` で固定できる）。

e-Gov 法令API v2 (`https://laws.e-gov.go.jp/api/2/`) が使える環境なら、政令・省令を含む
全法令種別を直接取得するほうが望ましい。分析時のセッションはネットワークポリシーで
API に到達できなかったため、法律のみのミラーを使っている。
