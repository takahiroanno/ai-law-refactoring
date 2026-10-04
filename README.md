# AIで法律をリファクタリングする

現行法律2,100本・96,780条を、AI（Claude Fable 5）で全件読み解いて整理し直す試みの成果物一式です。
アプローチは2つあります。

1. アナログ規制改革を「文言ベース」から「概念ベース」へ ― キーワード検索では拾えないアナログ前提の条文を概念単位で採掘し、87件の改正候補を抽出した。
2. 法体系のDRY（Don't Repeat Yourself）― 8法以上に複製されている定型文619種を検出し、切り出すべき「共通法モジュール」31種に整理した。

議員・安野貴博のいち提案草案（土日の自由研究）であり、チームみらいの決定や党の公式見解ではありません。
改正イメージはLLMの一次起草で、法制執務上の精査を経ていません。個別条文は必ず原文を確認してください。

## 何が出たか

### 1. アナログ規制 改正候補 87件

| 指標 | 値 |
|---|---|
| スキャン対象 | 現行法律 2,100本 / 96,780条（本則のみ） |
| アナログ概念 | 25概念（うち7概念はLLMが新規に発見） |
| 候補ヒット | 延べ24,179件（条×概念）・1,426法に分布 |
| 電磁的代替規定が法令内に一切ない法律 | 899法 |
| LLM精読による真陽性 | 145件（うちデジタル化可能性 high が87件、medium 49件、low 9件） |

- 一覧（読み物）: [docs/amendment-candidates-87.md](docs/amendment-candidates-87.md)
- 一覧（条文全文・変更箇所ハイライト・現行→改正イメージつきHTML）: [docs/html/fix-targets.html](docs/html/fix-targets.html)
- 表計算用: [data/amendment_candidates_87.csv](data/amendment_candidates_87.csv) / 全199件は [data/all_candidates_199.csv](data/all_candidates_199.csv)
- 手法と概念体系: [docs/concept-mining.md](docs/concept-mining.md)（読み物）・[docs/methodology.md](docs/methodology.md)（詳細）

デジタル臨時行政調査会のアナログ規制一括見直しは「対面」「フロッピーディスク」といった単語の検索と一括改正でした。
本分析はその一歩先で、単語には現れないが書かれ方そのものがアナログ前提になっている条文を探しています。例えば次のようなものです。

> 財産の調査及びその目録の作成は、後見監督人があるときは、その立会いをもってしなければ、その効力を生じない。（民法 第853条）

「対面」の語がないまま、物理的同席が効力要件になっている条文です。「〜を経由して」（紙リレー前提の申請経路）は法律全体で507箇所、
「被保険者証に記載し、これを返付する」型の紙証憑の往復運用は803条文・332法に分布していました。

### 2. 共通法モジュール 31種（DRYリファクタリング）

| 指標 | 値 |
|---|---|
| クローン文（8法以上に完全一致で複製されている定型文） | 619種 |
| 機能別モジュール | 31種 |
| いずれかのモジュールを含む法律 | 1,542法 / 1,985法（78%） |
| 最大モジュール（罰則本体）の複製先 | 920法・4,164箇所 |

- 読み物: [docs/common-law-modules.md](docs/common-law-modules.md)
- カタログ（変種の実例つきHTML）: [docs/html/module-catalog.html](docs/html/module-catalog.html)
- 機械可読: [results/module_catalog.json](results/module_catalog.json) / [results/clone_catalog.json](results/clone_catalog.json)

「犯罪捜査のために認められたものと解してはならない」が162法、「解釈してはならない」が128法。
機能は同一で、実装がコピペで分岐した状態です。ソフトウェアなら即リファクタリング対象になります。

## リポジトリの歩き方

```
README.md                        この文書
concepts.json                    アナログ概念カタログ25種（正規表現の候補網つき）
docs/
  amendment-candidates-87.md     改正候補87件（概念別・現行→改正イメージ）
  concept-mining.md              概念採掘の手法と結果（読み物）
  common-law-modules.md          共通法モジュールの全体像（読み物）
  methodology.md                 手法・概念体系・集計の詳細
  html/fix-targets.html          87件の一覧ページ（条文全文つき）
  html/module-catalog.html       共通法モジュールカタログ
data/
  amendment_candidates_87.csv    87件のCSV
  all_candidates_199.csv         199件（high/medium/low/発見パス）のCSV
  README.md                      法令XMLの取得方法（本体は非同梱）
results/                         機械可読の生データ（下表）
scripts/                         パイプライン一式
```

| results/ | 中身 |
|---|---|
| `concept_summary.csv` | 概念別のヒット条数・法令数・電磁的代替の有無 |
| `law_ranking.csv` | 法令別アナログ密度ランキング（1,353法） |
| `priority_laws_no_digital_alt.csv` | 電磁的代替規定がゼロの優先法令100法 |
| `items.json` | 条文全文と突合済みの候補199件 |
| `amendments.jsonl` | 各候補の改正イメージ（現行→改正後） |
| `llm_judgments.jsonl` | 検証パスの生判定287件 |
| `llm_discoveries.json` | 発見パスの生データ54件（採用見送り分も記録） |
| `llm_verification.md` | 概念別の適合率と、そこから挙がった一括改正の型 |
| `clone_catalog.json` | 8法以上に複製された定型文619種 |
| `module_catalog.json` | 機能別31モジュール（複製規模つき） |

## 再現手順

```bash
scripts/fetch_laws.sh                                  # 法令XMLを data/laws/ に取得
python3 scripts/extract_corpus.py data/laws data/articles.jsonl
python3 scripts/scan_concepts.py concepts.json data/articles.jsonl data/findings.jsonl data/summary.json
python3 scripts/aggregate.py data/findings.jsonl data/summary.json results
python3 scripts/join_items.py . data/articles.jsonl results/items.json
python3 scripts/build_fix_list.py . docs/html/fix-targets.html
python3 scripts/build_public_tables.py                 # CSV と Markdown 一覧を再生成

python3 scripts/clone_catalog.py data/articles.jsonl results/clone_catalog.json   # DRY側
python3 scripts/curate_modules.py results/clone_catalog.json results/module_catalog.json
python3 scripts/build_module_catalog.py . docs/html/module-catalog.html
```

③のLLM判定（候補の真陽性判定と新概念の発見）は、10体の並列サブエージェントで実施しています。
生成物は `results/llm_judgments.jsonl` と `results/llm_discoveries.json` に入っているので、
スキャンまでを回せば判定結果を再利用して一覧を組み直せます。

## 限界

1. 政令・省令が未収録。アナログ規制の物量は省令層（様式・手続細目）に集中するため、ここが次の一手の筆頭です。
2. 候補網は再現率を優先しており、正規表現層の適合率は概念により25〜81%。今回のLLM判定は全24,179候補のうち287件のサンプルにとどまります。
3. クローン検出は正規化後の完全一致のみ。言い回しが少し違う実質的クローンは拾えていないため、619種という数字は下限です。
4. 「アナログであること」と「改めるべきこと」は別。刑事手続の身柄、危険物の実物検査、遺言の真意確認など、物理性それ自体が保護法益のものは low として区別しています。
5. 条文の鮮度は2025年5月時点のミラー準拠。直近の改正は未反映の可能性があります。

## 出典・ライセンス

- 法令データ: e-Gov法令検索の全法令XML（法律のみ・2025年5月版）を、GitHubミラー [39la/gitlaw-jp](https://github.com/39la/gitlaw-jp) 経由で利用。法令の条文そのものは著作権の対象外（著作権法13条）です。
- コード・文書: [MIT License](LICENSE)。改正イメージ・判定理由・分類はLLMの生成物であり、正確性を保証するものではありません。

国会・他党の議員の方、法制局・省庁の方で関心がある方はぜひご一報ください。連携しながら具体化を進めたいと考えています。
