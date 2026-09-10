#!/usr/bin/env python3
"""data/vocab.jsonl -> views/*.md 생성. views는 파생물이니 직접 고치지 말 것."""
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VOCAB = ROOT / "data" / "vocab.jsonl"
VIEWS = ROOT / "views"

POS_LABEL = {
    "n": "명사", "v": "동사", "adj": "형용사", "adv": "부사",
    "phr": "구문", "idiom": "관용구", "phrasal_verb": "구동사",
}


def load():
    return [json.loads(l) for l in VOCAB.read_text(encoding="utf-8").splitlines() if l.strip()]


def entry_md(e):
    out = [f"### {e['word']}", ""]
    head = f"*{POS_LABEL.get(e['pos'], e['pos'])}*"
    if e.get("level"):
        head += f" · {e['level']}"
    if e.get("register") and e["register"] != "neutral":
        head += f" · {e['register']}"
    if e.get("ipa"):
        head += f" · {e['ipa']}"
    out += [head, "", f"**{e['meaning_ko']}**", ""]
    if e.get("meaning_en"):
        out += [f"> {e['meaning_en']}", ""]
    for s in e["sentences"]:
        out.append(f"- {s['en']}")
        if s.get("ko"):
            out.append(f"  - {s['ko']}")
        if s.get("note"):
            out.append(f"  - 💡 {s['note']}")
    out.append("")
    if e.get("collocations"):
        out += [f"**연어**: {', '.join(e['collocations'])}", ""]
    if e.get("synonyms"):
        out += [f"**유의어**: {', '.join(e['synonyms'])}", ""]
    if e.get("confusables"):
        out.append("**구분**:")
        out += [f"- {c}" for c in e["confusables"]]
        out.append("")
    return out


def main():
    entries = sorted(load(), key=lambda e: e["word"].lower())
    VIEWS.mkdir(exist_ok=True)

    lines = [f"# 단어장 (총 {len(entries)}개)", "", "`data/vocab.jsonl`에서 자동 생성. 직접 수정 금지.", ""]
    for e in entries:
        lines += entry_md(e)
        lines.append("---")
        lines.append("")
    (VIEWS / "wordlist.md").write_text("\n".join(lines), encoding="utf-8")

    by_tag = defaultdict(list)
    for e in entries:
        for t in e.get("tags", []) or ["untagged"]:
            by_tag[t].append(e)
    lines = ["# 주제별 색인", ""]
    for tag in sorted(by_tag, key=lambda t: (-len(by_tag[t]), t)):
        lines.append(f"## {tag} ({len(by_tag[tag])})")
        lines += [f"- **{e['word']}** — {e['meaning_ko']}" for e in by_tag[tag]]
        lines.append("")
    (VIEWS / "by-tag.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"wrote views/wordlist.md, views/by-tag.md ({len(entries)} entries)")

    import build_html
    build_html.main()

    import build_pwa
    build_pwa.main()


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
