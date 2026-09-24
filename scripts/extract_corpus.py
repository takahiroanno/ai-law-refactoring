#!/usr/bin/env python3
"""gitlaw-jp の法令標準XML (current.xml) から条文単位のコーパスを抽出する。

出力: JSONL（1行 = 1条）
  law_id, law_num, law_title, article_num, caption, text
本則 (MainProvision) のみを対象とする（附則は経過措置が中心のため除外）。
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def sentence_text(elem: ET.Element) -> str:
    """要素配下のテキストを連結（Ruby等の子要素も含む）。"""
    return "".join(elem.itertext())


def extract_article(article: ET.Element) -> dict:
    title = article.find("ArticleTitle")
    caption = article.find("ArticleCaption")
    parts = []
    for para in article.iter("Paragraph"):
        buf = []
        for tag in ("ParagraphSentence", "ParagraphCaption"):
            el = para.find(tag)
            if el is not None:
                buf.append(sentence_text(el))
        # 号 (Item) とその下位も回収する
        for item in para.iter():
            if item.tag in ("ItemSentence", "Subitem1Sentence", "Subitem2Sentence",
                            "Subitem3Sentence", "TableStruct", "List"):
                buf.append(sentence_text(item))
        parts.append("".join(buf))
    return {
        "article_num": article.get("Num", ""),
        "article_title": sentence_text(title) if title is not None else "",
        "caption": sentence_text(caption) if caption is not None else "",
        "text": "\n".join(p for p in parts if p),
    }


def main(laws_dir: str, out_path: str) -> None:
    laws = sorted(Path(laws_dir).glob("*/*/current.xml"))
    n_laws = n_articles = 0
    with open(out_path, "w", encoding="utf-8") as out:
        for xml_path in laws:
            try:
                root = ET.parse(xml_path).getroot()
            except ET.ParseError as e:
                print(f"parse error: {xml_path}: {e}", file=sys.stderr)
                continue
            law_id = xml_path.parent.name
            law_num_el = root.find("LawNum")
            title_el = root.find(".//LawTitle")
            law_num = sentence_text(law_num_el) if law_num_el is not None else ""
            law_title = sentence_text(title_el) if title_el is not None else ""
            main = root.find(".//MainProvision")
            if main is None:
                continue
            n_laws += 1
            for article in main.iter("Article"):
                rec = extract_article(article)
                if not rec["text"]:
                    continue
                rec.update(law_id=law_id, law_num=law_num, law_title=law_title)
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n_articles += 1
    print(f"laws={n_laws} articles={n_articles} -> {out_path}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
