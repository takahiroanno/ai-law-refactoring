#!/usr/bin/env python3
"""共通法モジュールカタログ (module_catalog.html) を生成する。
入力: results/module_catalog.json, results/package_unions.json
使い方: python3 scripts/build_module_catalog.py . results/module_catalog.html
"""
import html
import json
import sys
from pathlib import Path

base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else base / "results/module_catalog.html"

data = json.load(open(base / "results/module_catalog.json", encoding="utf-8"))
unions = json.load(open(base / "results/package_unions.json", encoding="utf-8"))
mods = {m["id"]: m for m in data["modules"]}

# パッケージ構成（表示順）
PACKAGES = [
    ("行政制裁法", ["M08", "M07", "M01", "M06", "M02", "M05", "M03", "M04"],
     "罰則・過料・両罰・没収追徴・国外犯・自首減免の定型。各法に残るのは「どの義務違反に、どの水準の刑を割り当てるか」の対応表だけでよい。刑法総則が既に共通部分を持つが、行政罰の定型はコピペのまま。"),
    ("行政調査法", ["M11", "M09", "M10", "M12", "M13"],
     "立入検査・報告徴収・身分証提示・犯罪捜査解釈禁止・みなし公務員をワンセットで規定。各法は「誰が・何を・どの範囲で」のパラメータだけを定める。ドイツの行政手続法や韓国の行政調査基本法に相当する層が日本にはない。"),
    ("公示・公表法", ["M16", "M22"],
     "公示・公告・公表の方法（官報・ウェブ・掲示）とその効力発生を一元規定。媒体の技術更新（電子官報・国のウェブ公示基盤）を1法の改正で全法令に波及させられるようになる。"),
    ("行政手続法の拡張", ["M15", "M14"],
     "聴聞・審査請求の特例や届出定型は、既に行政手続法・行政不服審査法という共通法があるのに、各法が特例・再記述を重ねている層。共通法側のデフォルトを強くし、個別法の上書きを減らす方向。"),
    ("法令用語法（デジタル手続法の拡張）", ["M18", "M17"],
     "「電磁的記録」「電磁的方法」等の共通定義を1箇所に置き、各法は参照するだけにする。デジタル関係用語が343法にローカル再定義されている現状は、デジタル改革のたびに全法改正が必要になる構造そのもの。"),
    ("権限委任法", ["M23", "M24"],
     "大臣→地方支分部局長、国→都道府県知事への委任定型。委任の一般ルールと告示による特定へ。"),
    ("指定法人共通法", ["M20"],
     "指定試験機関・登録検査機関・指定紛争解決機関などの「民間機関への行政事務委託」ガバナンス（指定基準・業務規程・役員認可・休廃止許可・監督命令・指定取消）を一般法化。37種の変種が195法に散在。"),
    ("法人清算共通法", ["M19"],
     "特別法上の法人（組合・共済等）の清算手続が民法法人時代の条文のコピペで174法に残存。一般法人法・会社法の清算規定への参照に一本化。"),
    ("独法通則法への一本化", ["M21"],
     "独立行政法人は通則法という共通法が既にあるのに、個別法が通則法との接続定型（役員・資本金・積立金・区分経理）を毎回書き直している。個別法設置スキームの見直し。"),
    ("参照機構の機械可読化", ["M27"],
     "「読み替え適用表」は共通化ではなく参照機構そのもののコスト。729法・4,760箇所の読み替え表は、機械可読な参照解決（溶け込み自動生成）が整えば大幅に圧縮できる。"),
]
OTHER = [m for m in data["modules"] if m["id"] not in {mid for _, ids, _ in PACKAGES for mid in ids}]

# モジュール別の「関数シグネチャ」注記
SIG = {
    "M08": "罰則(対象行為, 法定刑) — 各法に残すのは対応表のみ",
    "M07": "過料(対象行為, 上限額)",
    "M01": "両罰(対象条文リスト, 法人重科の有無)",
    "M06": "守秘義務(対象者, 罰則水準)",
    "M02": "没収追徴(対象財産)",
    "M05": "賄賂罪(みなし公務員の範囲)",
    "M03": "国外犯(対象条文)",
    "M04": "自首減免(対象条文)",
    "M11": "立入検査(主体, 対象施設, 検査対象物件)",
    "M09": "犯罪捜査解釈禁止() — 引数なしの完全定型",
    "M10": "身分証提示(様式) — 「関係人／関係者」「請求があるとき」等12変種が516法に",
    "M12": "報告徴収(対象者, 事項)",
    "M13": "みなし公務員(対象者)",
    "M16": "公示(方法=官報|ウェブ|掲示, 効力発生時期)",
    "M22": "備置閲覧(書類, 場所) — 電子公表への一本化候補",
    "M15": "聴聞・審査請求特例(適用除外範囲)",
    "M14": "届出(事項, 軽微変更の除外)",
    "M18": "電磁的記録・電磁的方法の定義() — 343法にローカル再定義",
    "M17": "定義柱書() — 用語集の構文定型",
    "M23": "権限委任(委任先=地方支分部局)",
    "M24": "事務委任(委任先=都道府県知事)",
    "M20": "指定法人制度(指定基準, 業務規程, 監督措置)",
    "M19": "法人清算(清算人選任, 債権申出公告, 除斥)",
    "M21": "独法設置(名称, 目的, 資本金, 区分経理)",
    "M27": "読み替え表 — 参照機構のランタイムコスト",
    "M25": "経過措置委任()",
    "M26": "実施規定委任(政令|省令)",
    "M28": "登記対抗力()",
    "M29": "先取特権順位(民法参照)",
    "M30": "欠格条項(拒否事由リスト)",
    "M31": "会議体運営(定足数, 議事録)",
}

def esc(s):
    return html.escape(str(s or ""))

def module_card(m):
    sig = SIG.get(m["id"], "")
    vs = "".join(
        f'<div class="variant"><p class="vmeta">{v["laws"]}法に複製｜例: {esc("、".join(v["sources"][:2]))}</p>'
        f'<p class="vtext">{esc(v["example"])}</p></div>'
        for v in m["top_variants"][:3])
    return f"""<details class="item" id="{m['id']}">
<summary><span class="mid">{m['id']}</span> <b>{esc(m['name'])}</b>
<span class="nums">{m['laws']}法・{m['occurrences']:,}箇所・変種{m['clone_variants']}</span></summary>
<div class="body">
<p class="sig">{esc(sig)}</p>
{vs}
</div>
</details>"""

pkg_html = []
for name, ids, desc in PACKAGES:
    u = unions.get(name, "")
    cards = "\n".join(module_card(mods[i]) for i in ids if i in mods)
    pkg_html.append(f"""<section>
<h2>{esc(name)} <span class="cnt">{u}法に波及</span></h2>
<p class="sub">{esc(desc)}</p>
{cards}
</section>""")
other_cards = "\n".join(module_card(m) for m in OTHER)

page = f"""<title>共通法モジュールカタログ</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;600;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
:root{{
  --paper:#faf9f6; --paper2:#f1efe9; --ink:#22303c; --ink2:#5a6a78;
  --ai:#2d5f8a; --ai-soft:#eef3f7; --shu:#b0432c; --shu-soft:#f7ece8;
  --line:#d9d5cc; --line2:#e8e5de;
  --mincho:"Shippori Mincho","Hiragino Mincho ProN","Yu Mincho",serif;
  --gothic:"Zen Kaku Gothic New","Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,monospace;
}}
@media (prefers-color-scheme: dark){{
  :root:not([data-theme="light"]){{
    --paper:#141c26; --paper2:#1b2531; --ink:#e3e0d8; --ink2:#98a4b0;
    --ai:#7fb0d8; --ai-soft:#1d2a38; --shu:#e08a71; --shu-soft:#32241f;
    --line:#33404e; --line2:#26313d;
  }}
}}
:root[data-theme="dark"]{{
  --paper:#141c26; --paper2:#1b2531; --ink:#e3e0d8; --ink2:#98a4b0;
  --ai:#7fb0d8; --ai-soft:#1d2a38; --shu:#e08a71; --shu-soft:#32241f;
  --line:#33404e; --line2:#26313d;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--gothic);line-height:1.8;font-size:15px}}
.wrap{{max-width:840px;margin:0 auto;padding:0 22px 96px}}
header{{padding:64px 0 20px;border-bottom:3px double var(--line)}}
.eyebrow{{font-size:12px;letter-spacing:.22em;color:var(--ai);font-weight:700;margin:0 0 14px}}
h1{{font-family:var(--mincho);font-weight:700;font-size:clamp(26px,5vw,38px);line-height:1.4;margin:0 0 10px;text-wrap:balance}}
.lede{{color:var(--ink2);max-width:44em;margin:0}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);margin:26px 0 0}}
.stat{{background:var(--paper);padding:13px 16px 10px}}
.stat b{{display:block;font-family:var(--mincho);font-size:24px;font-weight:600;font-variant-numeric:tabular-nums;color:var(--ai)}}
.stat.warn b{{color:var(--shu)}}
.stat span{{font-size:12px;color:var(--ink2)}}
h2{{font-family:var(--mincho);font-weight:600;font-size:21px;margin:56px 0 4px;text-wrap:balance}}
h2 .cnt{{color:var(--shu);font-size:14px;font-variant-numeric:tabular-nums}}
.sub{{font-size:13px;color:var(--ink2);margin:0 0 12px}}
details.item{{border:1px solid var(--line);border-bottom:none;background:var(--paper)}}
details.item:last-of-type{{border-bottom:1px solid var(--line)}}
details.item summary{{cursor:pointer;padding:9px 14px;font-size:14px;line-height:1.7}}
details.item summary:hover{{background:var(--paper2)}}
details.item summary:focus-visible{{outline:2px solid var(--ai);outline-offset:-2px}}
details.item[open]{{background:var(--paper2)}}
.mid{{font-family:var(--mono);font-size:11.5px;color:var(--shu);letter-spacing:.03em}}
.nums{{float:right;font-size:12px;color:var(--ink2);font-variant-numeric:tabular-nums}}
.body{{padding:2px 18px 16px;border-top:1px solid var(--line2)}}
.sig{{font-family:var(--mono);font-size:13px;color:var(--ai);margin:10px 0 8px}}
.variant{{border-left:3px solid var(--line);padding:6px 14px;margin:8px 0;background:var(--paper)}}
.vmeta{{font-size:11.5px;color:var(--ink2);margin:0 0 3px}}
.vtext{{font-family:var(--mincho);font-size:14px;line-height:1.95;margin:0}}
.tablebox{{overflow-x:auto;border:1px solid var(--line);margin:16px 0}}
table{{border-collapse:collapse;width:100%;font-size:13.5px;line-height:1.7}}
th{{background:var(--paper2);font-weight:700;text-align:left;white-space:nowrap}}
th,td{{padding:8px 12px;border-bottom:1px solid var(--line2);vertical-align:top}}
tr:last-child td{{border-bottom:none}}
td.num{{font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap}}
ul{{padding-left:1.3em;margin:10px 0}}
li{{margin:6px 0}}
li::marker{{color:var(--ai)}}
footer{{margin-top:72px;border-top:3px double var(--line);padding-top:16px;font-size:12.5px;color:var(--ink2)}}
</style>
<div class="wrap">
<header>
  <p class="eyebrow">法令クローン検出｜2026-08-22</p>
  <h1>共通法モジュールカタログ<br>——法体系のDRYリファクタリング素材集</h1>
  <p class="lede">現行法律2,100本・96,780条を文単位でクローン検出し（可変部＝大臣名・条番号・金額等をマスクして正規化）、<b>8法以上に複製されている定型文619種</b>を機能別31モジュールに分類した。ソフトウェアでいえば「各ファイルにコピペされている関数を洗い出し、ライブラリに切り出す準備をした」状態。</p>
  <div class="stats">
    <div class="stat"><b>619</b><span>クローン文（8法以上に複製）</span></div>
    <div class="stat"><b>31</b><span>機能モジュール</span></div>
    <div class="stat warn"><b>78%</b><span>いずれかのモジュールを含む法律（1,542/1,985法）</span></div>
    <div class="stat warn"><b>920<span style="font-size:14px">法</span></b><span>罰則定型の複製先（最大モジュール）</span></div>
  </div>
</header>

<h2>サマリ：切り出し候補の全体像</h2>
<div class="tablebox"><table>
<tr><th>提案する共通法</th><th>収容モジュール</th><th>波及法令数</th><th>既存の土台</th></tr>
<tr><td><b>行政制裁法</b></td><td>罰則本体・過料・両罰・守秘義務罰・没収追徴・賄賂・国外犯・自首減免</td><td class="num">1,084</td><td>刑法総則（but行政罰定型は未収容）</td></tr>
<tr><td><b>行政調査法</b></td><td>立入検査・犯罪捜査解釈禁止・身分証提示・報告徴収・みなし公務員</td><td class="num">929</td><td>なし（韓国には行政調査基本法が存在）</td></tr>
<tr><td>参照機構の機械可読化</td><td>読み替え適用表</td><td class="num">729</td><td>e-LAWS（溶け込みの自動化が未整備）</td></tr>
<tr><td>行政手続法の拡張</td><td>聴聞・審査請求特例・届出定型</td><td class="num">572</td><td>行政手続法・行政不服審査法</td></tr>
<tr><td>公示・公表法</td><td>官報公示・公表義務・備置閲覧</td><td class="num">562</td><td>官報発行法（2023）が入口</td></tr>
<tr><td><b>法令用語法</b></td><td>電磁的記録等の定義・定義柱書</td><td class="num">500</td><td>デジタル手続法（射程が行政手続のみ）</td></tr>
<tr><td>権限委任法</td><td>地方支分部局委任・知事委任</td><td class="num">363</td><td>地方自治法（機関委任廃止後の再整理）</td></tr>
<tr><td>独法通則法への一本化</td><td>機構設立定型</td><td class="num">345</td><td>独立行政法人通則法</td></tr>
<tr><td>指定法人共通法</td><td>指定試験機関・登録機関等の統治</td><td class="num">195</td><td>なし</td></tr>
<tr><td>法人清算共通法</td><td>清算手続パッケージ</td><td class="num">174</td><td>一般法人法・会社法</td></tr>
</table></div>

<h2>DRY違反の「実物」：同一機能・12変種</h2>
<p class="sub">同じ機能なのに表記が揺れている実例。身分証提示モジュール（M10・516法）には「関係人／関係者」「これを提示／提示」「請求があるとき／あつたとき」等の変種が12種、犯罪捜査解釈禁止（M09・584法）には「解してはならない」162法 vs 「解釈してはならない」128法という二大方言が併存する。機能は同一、実装がコピペで分岐した——ソフトウェアなら即リファクタリング対象。</p>

{chr(10).join(pkg_html)}

<section>
<h2>その他のモジュール</h2>
{other_cards}
</section>

<h2>実装アプローチ（現実的な移行経路）</h2>
<ul>
<li><b>参照方式（import）</b>: 新規立法から共通法参照を義務化。法制局の審査基準に「例文コピペ禁止・共通法○条を引用」のリンター規則を入れる。既存法は改正機会ごとに置換（strangler fig）。</li>
<li><b>オーバーライド方式（デジタル手続法型）</b>: 個別法を書き換えずに「個別法の規定にかかわらず〜できる」と横断上書きする1本を通す。公示方法・電磁的記録定義はこの型が速い。</li>
<li><b>テンプレートの機械可読化</b>: 例文（内閣法制局テンプレート）を法令XML上で「この文は共通テンプレ#Xのインスタンス」とアノテーションする。切り出し前でも、一括改正のコストが激減する。</li>
</ul>

<h2>留意</h2>
<ul>
<li>検出は正規化後の<b>完全一致</b>のみ。言い回しが少し違う実質的クローンは拾えていないため、ここの数字は<b>下限値</b>。</li>
<li>罰則の法定刑や検査対象はモジュールの「引数」であり、共通化とは「引数だけを各法に残す」こと。実体的な差異を消す提案ではない。</li>
<li>対象は法律のみ（政令・省令を含めれば複製規模はさらに大きい）。データは2025年5月版法令ミラー準拠。</li>
</ul>

<footer>
生成: <code>scripts/clone_catalog.py</code>（文単位クローン検出）→ <code>scripts/curate_modules.py</code>（機能分類・再集計）→ 本ページ。
機械可読データ: <code>results/clone_catalog.json</code>（619クローン文）・<code>results/module_catalog.json</code>（31モジュール）・<code>results/package_unions.json</code>。
元データ: e-Gov法令XML（現行法律2,100本、<code>data/laws_xml.tar.gz</code>）。
</footer>
</div>
"""
out_path.write_text(page, encoding="utf-8")
print("wrote", out_path, f"{len(page):,} bytes")
