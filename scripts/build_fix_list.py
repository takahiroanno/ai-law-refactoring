#!/usr/bin/env python3
"""改正候補一覧ページ (fix_targets.html) を生成する。

入力:
  results/items.json        条文全文つきの候補（join_items.py の出力）
  results/amendments.jsonl  現行→改正イメージ（LLM起草）
  concepts.json             ハイライト用の概念別パターン
使い方: python3 scripts/build_fix_list.py <analog_regulationディレクトリ> <出力HTML>
"""
import html
import json
import re
import sys
from pathlib import Path

base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
out_path = Path(sys.argv[2]) if len(sys.argv) > 2 else base / "results/fix_targets.html"

cat = json.load(open(base / "concepts.json", encoding="utf-8"))
regexes = {c["id"]: [re.compile(p) for p in c["regex"]] for c in cat["concepts"]}
short_label = {
    "C01_taimen_shutto": "対面・出頭", "C02_jicchi_kakunin": "実地・立入", "C03_shomen_kofu": "書面交付",
    "C04_genpon_fukusuu": "原本・部数", "C05_oin_shomei": "押印・署名", "C06_sonaeoki_etsuran": "備置き・縦覧",
    "C07_butsuri_keiji": "物理掲示", "C08_kokoku_gentei": "官報・新聞公告", "C09_keitai_teiji": "携帯・提示",
    "C10_jochu_sennin": "常駐・専任", "C11_teiki_kensa": "定期検査", "C12_taimen_koshu": "講習・実習",
    "C13_baitai_shitei": "媒体名指し", "C14_yubin_sotatsu": "郵便・送達", "C15_koto_yomikikase": "口頭・読み聞かせ",
    "C16_inshi_genkin": "印紙・現金", "C17_keiyu_teishutsu": "経由提出", "C18_jisan_madoguchi": "持参・引渡し",
}

items = json.load(open(base / "results/items.json", encoding="utf-8"))
amend = {}
for line in open(base / "results/amendments.jsonl", encoding="utf-8"):
    if line.strip():
        r = json.loads(line)
        amend[r["id"]] = r

MAXLEN = 3000

def esc(s):
    return html.escape(str(s or ""))

def highlight(text, item):
    """条文テキストに <mark>（概念パターン）と <mark class=cp>（変更箇所）を付けてエスケープ出力。"""
    spans = []
    a = amend.get(item["id"], {})
    cp = a.get("current_phrase") or item.get("quote") or ""
    if cp:
        i = text.find(cp)
        if i >= 0:
            spans.append((i, i + len(cp), "cp"))
    for cre in regexes.get(item["concept"], []):
        for m in cre.finditer(text):
            spans.append((m.start(), m.end(), "pat"))
    # 重なりは変更箇所(cp)優先で整理
    spans.sort(key=lambda s: (s[0], 0 if s[2] == "cp" else 1))
    merged, last_end = [], 0
    for s, e, k in spans:
        if s < last_end:
            continue
        merged.append((s, e, k))
        last_end = e
    outp, pos = [], 0
    for s, e, k in merged:
        outp.append(esc(text[pos:s]))
        cls = ' class="cp"' if k == "cp" else ""
        outp.append(f"<mark{cls}>{esc(text[s:e])}</mark>")
        pos = e
    outp.append(esc(text[pos:]))
    h = "".join(outp)
    return h

def card(item):
    a = amend.get(item["id"], {})
    concept = short_label.get(item["concept"], esc(item["concept"]))
    text = item["text"]
    truncated = len(text) > MAXLEN
    body_text = text[:MAXLEN]
    jobun = highlight(body_text, item).replace("\n", "<br>")
    cap = f'（{esc(item["caption"].strip("（）"))}）' if item["caption"] else ""
    hid = ' <span class="tag shu">隠れ</span>' if item.get("is_hidden") and item["kind"] == "judgment" else ""
    atype = f'<span class="tag ai">{esc(a["amendment_type"])}</span>' if a.get("amendment_type") else ""
    note = f'<p class="note">留意: {esc(a["note"])}</p>' if a.get("note") else ""
    trunc_note = f'<p class="note">（条文が長いため先頭{MAXLEN:,}字のみ表示。全文は法令XML参照）</p>' if truncated else ""
    amended = esc(a.get("amended_phrase", "（改正イメージ未生成）"))
    current = esc(a.get("current_phrase") or item.get("quote") or "")
    return f"""<details class="item" id="{item['id']}">
<summary><span class="tag">{concept}</span> <b>{esc(item['law_title'])}</b>　{esc(item['article'])}{cap}{hid} {atype}</summary>
<div class="body">
<p class="lbl">条文（{esc(item['law_num'])}）　<mark>薄色=概念パターン</mark>　<mark class="cp">濃色=変更箇所</mark></p>
<div class="jobun">{jobun}</div>{trunc_note}
<table class="diff">
<tr><th>現行</th><td class="cur">{current}</td></tr>
<tr><th>改正イメージ</th><td class="new">{amended}</td></tr>
</table>
{note}
<p class="reason">判定理由: {esc(item['reason'])}</p>
</div>
</details>"""

def section(items_):
    return "\n".join(card(x) for x in items_)

high = [x for x in items if x["kind"] == "judgment" and x["digital_potential"] == "high"]
med = [x for x in items if x["kind"] == "judgment" and x["digital_potential"] == "medium"]
low = [x for x in items if x["kind"] == "judgment" and x["digital_potential"] == "low"]
disc = [x for x in items if x["kind"] == "discovery"]
key = lambda x: (x["concept"], x["law_title"])

page = f"""<title>アナログ規制 改正候補一覧</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@500;600;700&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap">
<style>
:root{{
  --paper:#faf9f6; --paper2:#f1efe9; --ink:#22303c; --ink2:#5a6a78;
  --ai:#2d5f8a; --ai-soft:#eef3f7; --shu:#b0432c; --shu-soft:#f7ece8;
  --mark:#f3e2c0; --markcp:#f0c9ba;
  --line:#d9d5cc; --line2:#e8e5de; --new-soft:#e9f2e9; --new:#3d6b40;
  --mincho:"Shippori Mincho","Hiragino Mincho ProN","Yu Mincho",serif;
  --gothic:"Zen Kaku Gothic New","Hiragino Kaku Gothic ProN","Yu Gothic",sans-serif;
}}
@media (prefers-color-scheme: dark){{
  :root:not([data-theme="light"]){{
    --paper:#141c26; --paper2:#1b2531; --ink:#e3e0d8; --ink2:#98a4b0;
    --ai:#7fb0d8; --ai-soft:#1d2a38; --shu:#e08a71; --shu-soft:#32241f;
    --mark:#4a3d22; --markcp:#54301f;
    --line:#33404e; --line2:#26313d; --new-soft:#1e2c1e; --new:#93c095;
  }}
}}
:root[data-theme="dark"]{{
  --paper:#141c26; --paper2:#1b2531; --ink:#e3e0d8; --ink2:#98a4b0;
  --ai:#7fb0d8; --ai-soft:#1d2a38; --shu:#e08a71; --shu-soft:#32241f;
  --mark:#4a3d22; --markcp:#54301f;
  --line:#33404e; --line2:#26313d; --new-soft:#1e2c1e; --new:#93c095;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--gothic);line-height:1.8;font-size:15px}}
.wrap{{max-width:880px;margin:0 auto;padding:0 22px 96px}}
header{{padding:64px 0 20px;border-bottom:3px double var(--line)}}
.eyebrow{{font-size:12px;letter-spacing:.22em;color:var(--ai);font-weight:700;margin:0 0 14px}}
h1{{font-family:var(--mincho);font-weight:700;font-size:clamp(26px,5vw,38px);line-height:1.4;margin:0 0 10px;text-wrap:balance}}
.lede{{color:var(--ink2);max-width:46em;margin:0}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);margin:26px 0 0}}
.stat{{background:var(--paper);padding:13px 16px 10px}}
.stat b{{display:block;font-family:var(--mincho);font-size:24px;font-weight:600;font-variant-numeric:tabular-nums;color:var(--ai)}}
.stat.warn b{{color:var(--shu)}}
.stat span{{font-size:12px;color:var(--ink2)}}
h2{{font-family:var(--mincho);font-weight:600;font-size:22px;margin:64px 0 4px;text-wrap:balance}}
h2 .cnt{{color:var(--shu);font-variant-numeric:tabular-nums}}
.sub{{font-size:13px;color:var(--ink2);margin:0 0 14px}}
.filter{{margin:28px 0 0;display:flex;gap:10px;align-items:center}}
.filter input{{flex:1;max-width:420px;padding:9px 14px;border:1px solid var(--line);background:var(--paper);color:var(--ink);font-family:var(--gothic);font-size:14px}}
.filter input:focus{{outline:2px solid var(--ai);outline-offset:1px}}
.filter small{{color:var(--ink2)}}
.tag{{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.04em;padding:1px 8px;border-radius:2px;background:var(--ai-soft);color:var(--ai);white-space:nowrap}}
.tag.shu{{background:var(--shu-soft);color:var(--shu)}}
.tag.ai{{background:var(--new-soft);color:var(--new)}}
details.item{{border:1px solid var(--line);border-bottom:none;background:var(--paper)}}
details.item:last-of-type{{border-bottom:1px solid var(--line)}}
details.item summary{{cursor:pointer;padding:10px 14px;font-size:14px;line-height:1.7;list-style-position:outside}}
details.item summary:hover{{background:var(--paper2)}}
details.item summary:focus-visible{{outline:2px solid var(--ai);outline-offset:-2px}}
details.item[open]{{background:var(--paper2)}}
.body{{padding:4px 18px 18px;border-top:1px solid var(--line2)}}
.lbl{{font-size:12px;color:var(--ink2);margin:10px 0 6px}}
.jobun{{font-family:var(--mincho);font-size:14.5px;line-height:2.1;background:var(--paper);
  border:1px solid var(--line2);padding:14px 18px;max-height:340px;overflow-y:auto}}
mark{{background:var(--mark);color:inherit;padding:0 1px}}
mark.cp{{background:var(--markcp);font-weight:700}}
table.diff{{border-collapse:collapse;width:100%;font-size:14px;margin:14px 0 0;line-height:1.8}}
table.diff th{{width:7em;background:var(--paper);border:1px solid var(--line2);padding:8px 12px;text-align:left;white-space:nowrap;vertical-align:top}}
table.diff td{{border:1px solid var(--line2);padding:8px 12px}}
table.diff td.cur{{font-family:var(--mincho);background:var(--shu-soft)}}
table.diff td.new{{font-family:var(--mincho);background:var(--new-soft)}}
.note{{font-size:12.5px;color:var(--ink2);margin:8px 0 0}}
.reason{{font-size:13px;color:var(--ink2);margin:10px 0 0}}
footer{{margin-top:72px;border-top:3px double var(--line);padding-top:16px;font-size:12.5px;color:var(--ink2)}}
.hiddenrow{{display:none !important}}
</style>
<div class="wrap">
<header>
  <p class="eyebrow">LLM判定に基づく一覧｜条文・改正イメージつき｜2026-08-22</p>
  <h1>アナログ規制 改正候補一覧</h1>
  <p class="lede">現行法律2,100本のスキャン候補からLLMが精読・真陽性と判定した条文（145件）と、検索網に載っていなかった発見条文（54件）。各件をクリックすると<b>条文全文（アナログ箇所ハイライト）と現行→改正イメージ</b>が開く。改正イメージはLLMの一次起草であり、法制執務上の精査を経ていない。</p>
  <div class="stats">
    <div class="stat warn"><b>{len(high)}</b><span>改正候補（high）</span></div>
    <div class="stat"><b>{len(med)}</b><span>要検討（medium）</span></div>
    <div class="stat"><b>{len(disc)}</b><span>発見パスの新規発見</span></div>
    <div class="stat"><b>{len(low)}</b><span>対象外（物理性が本質）</span></div>
  </div>
  <div class="filter">
    <input id="q" type="search" placeholder="法律名・概念・キーワードで絞り込み（例: 民法、官報、経由）" aria-label="一覧の絞り込み">
    <small id="qcount"></small>
  </div>
</header>

<h2>Ⅰ. 改正候補 <span class="cnt">{len(high)}件</span> — デジタル化可能性 high</h2>
<p class="sub">オンライン化・電子交付・電子公告・遠隔化等でそのまま代替可能性が高いと判定された条文。</p>
{section(sorted(high, key=key))}

<h2>Ⅱ. 要検討 <span class="cnt">{len(med)}件</span> — デジタル化可能性 medium</h2>
<p class="sub">部分的な電子化・併用化の余地があるが、制度設計の検討を要するもの。</p>
{section(sorted(med, key=key))}

<h2>Ⅲ. 発見パスの新規発見 <span class="cnt">{len(disc)}件</span></h2>
<p class="sub">25概念のいずれにもヒットしなかった条文からLLMが精読で発見したアナログ前提。ここから7概念（C19〜C25）を候補網に採用済み。</p>
{section(disc)}

<h2>Ⅳ. 対象外 <span class="cnt">{len(low)}件</span> — 物理性それ自体が保護法益</h2>
<p class="sub">アナログ前提は真だが、身柄・実物検査・真意確認など物理性に本質的な意味があると判定されたもの。参考として記録（改正イメージは付さない）。</p>
{section(sorted(low, key=key))}

<h2>Ⅴ. なぜ前回の一括見直しで拾えなかったか</h2>
<p class="sub">デジタル臨調のアナログ規制一括見直し（2022〜24年・約1万条項）との差分の構造的な理由。</p>
<div class="jobun" style="font-family:var(--gothic);font-size:13.5px;line-height:1.9;max-height:none">
① <b>語彙リスト方式の網目</b> — 前回は7類型を「目視」「実地」「対面」等の代表語彙に落とし、各府省がその語で洗い出す方式。「立会いをもってしなければ効力を生じない」「〜を経由して」「読み聞かせ」のような言い回しは語彙にも自己申告にも掛からない。<br>
② <b>射程が「行政規制」に限定</b> — 私法（民法・会社法）・司法手続（公証・民訴）・選挙・刑事は射程外か別トラック。<br>
③ <b>省庁自己申告のバイアス</b> — 「解釈で運用可能」「改正コスト大」は「該当なし」に整理されやすい。<br>
④ <b>旧仮名・戦前法の死角</b> — カタカナ表記（縦覧ニ供シ・呈示）は現代語キーワードと不一致。<br>
⑤ <b>横並び比較の不在</b> — 同型手続の電磁的代替の有無（立法格差）は法令横断の全文突合をして初めて見える。<br>
⑥ <b>当時の技術水準</b> — 2022年時点の機械処理は文字列一致が上限で、概念判定・精読の大規模適用は不可能だった。
</div>

<footer>
出典: <code>analog_regulation/results/items.json</code>（条文突合済み候補199件）・<code>amendments.jsonl</code>（改正イメージ）。
元データは e-Gov 法令XML（現行法律2,100本・2025年5月版、<code>data/laws_xml.tar.gz</code> に同梱）。
改正イメージはLLMの一次起草であり、既存の電磁的代替特例・進行中の改正との突合、法制執務上の精査を要する。
</footer>
</div>
<script>
const q=document.getElementById('q'),cnt=document.getElementById('qcount');
const cards=[...document.querySelectorAll('details.item')];
function apply(){{
  const v=q.value.trim().toLowerCase();let n=0;
  for(const el of cards){{
    const hit=!v||el.textContent.toLowerCase().includes(v);
    el.classList.toggle('hiddenrow',!hit); if(hit)n++;
  }}
  cnt.textContent=v?`${{n}}件が該当`:'';
}}
q.addEventListener('input',apply);
</script>
"""
out_path.write_text(page, encoding="utf-8")
print("wrote", out_path, f"{len(page):,} bytes, cards={len(items)}")
