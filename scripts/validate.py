#!/usr/bin/env python3
"""data/vocab.jsonl 무결성 검사. 위반 시 exit 1."""
import json
import sys
from pathlib import Path

VOCAB = Path(__file__).resolve().parent.parent / "data" / "vocab.jsonl"
REQUIRED = ["id", "word", "pos", "meaning_ko", "sentences", "added_at", "srs"]
SRS_REQUIRED = ["status", "reps", "lapses", "interval_days", "due"]
POS = {"n", "v", "adj", "adv", "phr", "idiom", "phrasal_verb"}


def main():
    errors, seen, count = [], set(), 0
    for lineno, line in enumerate(VOCAB.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        count += 1
        try:
            e = json.loads(line)
        except json.JSONDecodeError as err:
            errors.append(f"L{lineno}: JSON 파싱 실패 — {err}")
            continue

        def bad(msg):
            errors.append(f"L{lineno} [{e.get('word', '?')}]: {msg}")

        for f in REQUIRED:
            if f not in e:
                bad(f"필수 필드 누락 '{f}'")
        if e.get("id") in seen:
            bad(f"id 중복 '{e['id']}'")
        seen.add(e.get("id"))
        if e.get("pos") not in POS:
            bad(f"알 수 없는 pos '{e.get('pos')}'")

        sents = e.get("sentences") or []
        if not sents:
            bad("예문이 없음 — 모든 항목은 예문 1개 이상 필요")
        for i, s in enumerate(sents, 1):
            if not s.get("en", "").strip():
                bad(f"예문 {i}: 영문(en)이 비어 있음")
            if not s.get("ko", "").strip():
                bad(f"예문 {i}: 한국어 해석(ko)이 없음 — 모든 예문에 해석 필수")

        for f in SRS_REQUIRED:
            if f not in (e.get("srs") or {}):
                bad(f"srs.{f} 누락")

    if errors:
        print(f"❌ {len(errors)}건 실패 / {count}개 항목", file=sys.stderr)
        for err in errors:
            print("  " + err, file=sys.stderr)
        return 1
    print(f"✅ {count}개 항목 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
